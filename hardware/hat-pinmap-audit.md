# STRILAS — Pinmap-granskning: CM5-carrier ↔ vapen-HAT/FC

Granskning av 40-pin-gränssnittet (CM5-NANO-B standard RPi-pinout) mot `weapon_hat_netlist.py`,
inkl. kraft, signaler och komponent-pinouts. Datum: 2026-06-22.

## 1. 40-pin header — fysiskt stift → RPi-funktion → vårt nät

| Pin | RPi (BCM) | Vårt nät | Riktning | Status |
|----|-----------|----------|----------|--------|
| 1  | 3V3       | +3V3     | in (från carrier) | ✅ |
| 2  | 5V        | +5V      | **ut (back-feed → matar CM5)** | ✅ |
| 3  | GPIO2 SDA1| I2C_SDA  | bidir | ✅ I²C1 |
| 4  | 5V        | +5V      | ut (back-feed) | ✅ |
| 5  | GPIO3 SCL1| I2C_SCL  | ut | ✅ I²C1 |
| 6  | GND       | GND      | — | ✅ |
| 7  | GPIO4     | —        | (ledig) | ✅ |
| 8  | GPIO14    | —        | (ledig) | ✅ |
| 9  | GND       | GND      | — | ✅ |
| 10 | GPIO15    | —        | (ledig) | ✅ |
| 11 | GPIO17    | —        | (ledig) | ✅ |
| 12 | GPIO18 (PWM0) | IR_MOD | ut | ✅ HW-PWM 56 kHz |
| 13 | GPIO27    | TRIG     | in | ✅ |
| 14 | GND       | GND      | — | ✅ |
| 15 | GPIO22    | RACK     | in | ✅ |
| 16 | GPIO23    | MAGREL   | in | ✅ |
| 17 | 3V3       | +3V3     | in | ✅ |
| 18 | GPIO24    | MAGWELL  | in | ✅ |
| 19 | GPIO10 MOSI | MOSI   | ut | ✅ SPI0 |
| 20 | GND       | GND      | — | ✅ |
| 21 | GPIO9 MISO| MISO     | in | ✅ SPI0 |
| 22 | GPIO25    | IMU_INT  | in | ✅ IMU1-INT |
| 23 | GPIO11 SCLK | SCK    | ut | ✅ SPI0 |
| 24 | GPIO8 CE0 | nCS      | ut | ✅ SPI0 CS (IMU1) |
| 25 | GND       | GND      | — | ✅ |
| 26 | GPIO7 CE1 | —        | (ledig) | ✅ |
| 27 | GPIO0 ID_SD | —      | (ledig) | ⓘ ingen HAT-ID-EEPROM |
| 28 | GPIO1 ID_SC | —      | (ledig) | ⓘ ingen HAT-ID-EEPROM |
| 29 | GPIO5     | IMU2_INT | in | ✅ |
| 30 | GND       | GND      | — | ✅ |
| 31 | GPIO6     | IMU3_INT | in | ✅ |
| 32 | GPIO12 (PWM0) | RECOIL_PWM | ut | ✅ HW-PWM |
| 33 | GPIO13    | —        | (ledig) | ✅ |
| 34 | GND       | GND      | — | ✅ |
| 35 | GPIO19    | —        | (ledig) | ✅ |
| 36 | GPIO16    | RECOIL_FAULT | in | ✅ |
| 37 | GPIO26    | MODE0    | in | ✅ |
| 38 | GPIO20    | MODE1    | in | ✅ |
| 39 | GND       | GND      | — | ✅ |
| 40 | GPIO21    | PTT      | in | ✅ |

**Slutsats interface:** alla 8 GND + 2× 3V3 + 2× 5V korrekt placerade; SPI0 (19/21/23/24),
I²C1 (3/5) och HW-PWM (12/32) ligger på rätt funktionsstift. Inga dubbeltilldelningar.

## 2. Kraft

- **5 V back-feed (pin 2/4):** vår 2S→5 V buck matar CM5 via header-5V. ✅ fungerar.
  ⚠️ Bypass:ar carrierns USB-C-ingångsskydd — överväg säkring/TVS på 5V-utgången.
  ⚠️ Buck angiven "≥3 A". CM5 vill officiellt 5 V/5 A; 3 A kan bli knappt under CV-last → **överväg 5 A-marginal.**
- **3V3 (pin 1/17) från carriern** matar 3 IMU + ADC + NFC + pullups. PN532 RF-burst (~100 mA) på
  delad 3V3 → ⚠️ brusrisk mot IMU/ADC; överväg separat LDO eller 5V-matning till NFC.
- **VBAT-grenen:** JST-XH → PTC → P-FET (omvänd-polaritetsskydd) → VBAT → buck + emitter + recoil.
  P-FET AO3401 (G/S/D=1/2/3) rätt orienterad (S=last, D=ingång, G→GND); TVS SMBJ12A (K→VBAT, A→GND)
  rätt för 2S (8,4 V < 12 V standoff). ✅

## 3. I²C-adresser (buss på pin 3/5)
ADS1115 **0x48** (ADDR→GND) · PN532 **0x24** · IIM-42653 **0x68/0x69** (AD0 låg/hög). Inga krockar. ✅

## 4. Komponent-pinouts
- **ADS1115 (VSSOP-10/DGS):** ❌→✅ **RÄTTAD.** Symbolen mappade tidigare 1=VDD/2=GND/3=SCL/4=SDA/5=AIN0
  vilket är fel mot TI SBAS444 (1=ADDR,2=ALERT,3=GND,4=AIN0,8=VDD,9=SDA,10=SCL) → VDD/SDA/SCL hade
  hamnat på fel pads (chippet kunde ej fungera). Nu: 8=VDD, 9=SDA, 10=SCL, 3=GND, 4=AIN0, 1=ADDR→GND.
- **ICM-42688-P (IMU1, SPI):** stift verifierade mot DS-000347. Ingen REGOUT-pinne (VDD+VDDIO-caps räcker).
  pin 7 (RESV) nu →GND per datablad. ✅
- **IIM-42653 (IMU2/3, I²C):** 8=VDD,5=VDDIO,6=GND,7=RESV→GND,12=CS→3V3(I²C),1=AD0,13=SCL,14=SDA,4=INT. ✅
- **Buck (U1):** generisk placeholder (VIN/EN/GND/VOUT på TO-263-7+tab). ⚠️ pinout/FB/induktor måste
  matchas mot den faktiskt valda modulen/IC:n innan tillverkning.

## Åtgärdat i denna granskning
1. ADS1115-pinout rättad (kritiskt). 2. SPI-IMU pin 7 → GND. HAT omroutad 4-lager 0/0.

## Kvar att besluta (ej blockerande för routning)
Buck-modul/IC-val + ev. 5 A-marginal · NFC-matning (isolera RF-burst) · 5V-back-feed-skydd ·
ev. HAT-ID-EEPROM på GPIO0/1.
