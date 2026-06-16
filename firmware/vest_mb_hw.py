"""STRILAS — väst-moderkortets HW-I/O-drivrutin (MicroPython, körs på XIAO ESP32-S3).
Realiserar de tidigare "bänk-kvar"-punkterna i körbar kod:
  • SPI-läsning av 74HC165-kedjan (10 zon-DATA, aktiv-låg → hit-bitmap)
  • TPIC6B595-driver med MJUKVARU-PWM (vibrator-intensitet/mönster per zon)
  • LED_EN-konstellation-broadcast (bildtakt-blink)

NYCKELKNEP: SCK delas av 165 (CLK) och TPIC (SRCK) → ETT fullduplex-SPI-svep läser 165 (på MISO)
SAMTIDIGT som det skriver TPIC (på MOSI). Före svepet: pulsa SH/LD (lås 165-parallellinmatning).
Efter: pulsa RCK (lås TPIC-utgångar). Bit↔zon-mappning härledd ur netlistan (hardware/vest_mb_netlist.py).

Stift (XIAO ESP32-S3, se receiver_place/vest_mb_netlist):
  D8/GPIO7=SCK(delad) · D7/GPIO44=MOSI→TPIC SER · D9/GPIO8=MISO←165 QH ·
  D0/GPIO1=SH/LD(165) · D1/GPIO2=RCK(TPIC) · D2/GPIO3=LED_EN(broadcast)

Portar till ESP-IDF (samma logik). Mappnings-konstanterna matchar netlistan — bekräfta vid bringup.
"""
try:
    from machine import Pin, SPI, Timer
    _HW = True
except ImportError:                       # körs även på PC (sim/test) utan machine-modul
    _HW = False

NZONES = 10
# 74HC165: U2 A..H = DATA1..8, U3 A,B = DATA9,10. Kedja U3.QH→U2.SER→MISO → U2 läses först.
# QH ger H,G,..,A (H först). 16-bitsord w = (byte_U2<<8)|byte_U3, MSB=U2.H=DATA8.
#   → DATA1..8 = bit 8..15 ; DATA9 = bit 0 ; DATA10 = bit 1.  (aktiv-låg: hit = bit==0)
_HIT_BIT = [8, 9, 10, 11, 12, 13, 14, 15, 0, 1]   # zon1..10 → bitindex i 16-bitsläsning
# TPIC6B595: U4 DRAIN0..7 = VIB1..8, U5 DRAIN0..1 = VIB9,10. Kedja U4.SEROUT→U5.SERIN.
# Skriv MSB först: första byten hamnar i U5, andra i U4. DRAINn ← bit n i resp. chip-byte.
#   → bygg 16-bitsord: bit(8+n)=VIB(1+n) för U4-kanal n(0..7); bit n=VIB(9+n) för U5 n(0..1).
_VIB_BIT = [8, 9, 10, 11, 12, 13, 14, 15, 0, 1]   # zon1..10 → bitindex i 16-bits TPIC-skrivning


class VestMB:
    PWM_LEVELS = 16                        # mjukvaru-PWM-upplösning (16 steg)

    def __init__(self, sck=7, mosi=44, miso=8, shld=1, rck=2, led_en=3, spi_hz=4_000_000):
        self._duty = [0] * NZONES          # 0..PWM_LEVELS per zon
        self._phase = 0
        self._hits = 0                     # senaste hit-bitmap (bit z-1 = zon z träffad)
        if not _HW:
            return
        self.spi = SPI(1, baudrate=spi_hz, polarity=0, phase=0,
                       sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
        self.shld = Pin(shld, Pin.OUT, value=1)
        self.rck = Pin(rck, Pin.OUT, value=0)
        self.led_en = Pin(led_en, Pin.OUT, value=0)
        self._rx = bytearray(2)
        self._tx = bytearray(2)
        # PWM-timer ~1 kHz × PWM_LEVELS → uppdaterar TPIC och läser 165 i samma svep
        self.tmr = Timer(0)
        self.tmr.init(freq=1000 * 1, mode=Timer.PERIODIC, callback=self._tick)

    # ---- ett delat SPI-svep: skriv TPIC-mönster + läs 165-hits samtidigt ----
    def _exchange(self, tpic_word):
        if not _HW:
            self._hits = 0
            return 0
        self._tx[0] = (tpic_word >> 8) & 0xFF   # → U5
        self._tx[1] = tpic_word & 0xFF          # → U4
        self.shld.value(0); self.shld.value(1)  # lås 165-parallellinmatning
        self.spi.write_readinto(self._tx, self._rx)
        self.rck.value(1); self.rck.value(0)    # lås TPIC-utgångar
        w = (self._rx[0] << 8) | self._rx[1]
        # aktiv-låg → hit=1 när biten är 0
        self._hits = 0
        for z in range(NZONES):
            if not (w >> _HIT_BIT[z]) & 1:
                self._hits |= (1 << z)
        return self._hits

    # ---- mjukvaru-PWM-tick (kallas av timern) ----
    def _tick(self, _t):
        self._phase = (self._phase + 1) % self.PWM_LEVELS
        word = 0
        for z in range(NZONES):
            if self._duty[z] > self._phase:      # PWM: på medan fas < duty
                word |= (1 << _VIB_BIT[z])
        self._exchange(word)                     # skriv vibb-mönster + läs hits i ETT svep

    # ---- publikt API ----
    def read_hits(self):
        """Returnerar bitmap: bit (z-1) satt = zon z träffad (rå TSOP, aktiv-låg). HW läses i ticken."""
        if not _HW:
            return self._exchange(self._build_word())
        return self._hits

    def set_vibrator(self, zone, level):
        """zone=1..10, level=0..16 (PWM-intensitet). Fyras på ADJUDIKERAD träff (ej rå TSOP)."""
        self._duty[zone - 1] = max(0, min(self.PWM_LEVELS, int(level)))

    def buzz(self, zone, level=16, ms=250):
        """Engångs-buzz på en zon (blockerande paus i sim; använd icke-blockerande i prod)."""
        self.set_vibrator(zone, level)
        if _HW:
            from time import sleep_ms
            sleep_ms(ms)
            self.set_vibrator(zone, 0)

    def _build_word(self):
        w = 0
        for z in range(NZONES):
            if self._duty[z] > 0:
                w |= (1 << _VIB_BIT[z])
        return w

    def constellation(self, on):
        """Sätt konstellations-LED (broadcast till alla patchar). Blinka i kamerans bildtakt."""
        if _HW:
            self.led_en.value(1 if on else 0)


# ---- bänk-självtest: blinka konstellation + cykla vibratorer + skriv ut hits ----
def selftest():
    mb = VestMB()
    print("STRILAS väst-MB självtest:", "HW" if _HW else "SIM (ingen machine-modul)")
    import time
    for z in range(1, NZONES + 1):
        mb.set_vibrator(z, 16); mb.constellation(z % 2)
        print(f"  zon {z}: vib PÅ, hits=0b{mb.read_hits():010b}")
        if _HW: time.sleep_ms(150)
        mb.set_vibrator(z, 0)
    mb.constellation(0)
    print("klart.")


if __name__ == "__main__":
    selftest()
