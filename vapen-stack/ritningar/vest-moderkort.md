# STRILAS — väst-moderkort (väst-nod), komplett

100×60 mm, **4-lager** (In1=GND-plan, In2=VBAT-plan), routad **rent** (0 oroutade · 0 clearance · 0 oconnected).
Netlista `hardware/vest_mb_netlist.py` · placering `hardware/receiver_place.py` (vest_mb) · route `hardware/route_vest_mb.py`.

## Vad det är
Fristående väst-nod som **alla 10 patchar + 10 zon-vibratorer pluggas in i**, trådlöst mot vapnets P4 (ESP-NOW/WiFi).

## Arkitektur (verifierad mot datablad)
- **ESP: stackad XIAO ESP32-S3** (2× 1×7 sockel) — **samma som hjälmen → enkel sourcing**. Matas från
  kortets 3V3, programmeras via egen USB-C.
- **Kraft:** 2S-batteri (laddas i docka) → **AP63203**-buck (TSOT23-6, FB 31.6k/10k → 3.33 V @2A) matar
  XIAO + 74HC165 + ERM-motorerna. **VBAT(2S)** distribueras (In2-plan) till varje patch (konstellations-LED).
- **Hit-läsning:** 10× patch-DATA (aktiv-låg 3,3 V) → **2× 74HC165** (parallel-in → SPI). XIAO har bara
  11 GPIO → shift-register sparar stift (delad SCK + SH/LD + QH→MISO). Läser alla 10 zoner med 1 SPI-transaktion.
- **Vibratorer:** 10× ERM-coin-motor (1 per zon, bak mot kroppen) drivs av **2× TPIC6B595** power-shift-register
  (open-drain 150 mA/kanal, inbyggd flyback): MOSI→SERIN, delad SRCK, RCK-latch. Motor: 3V3→motor→DRAIN→GND;
  PWM på kanalen = intensitet/mönster. Fyras på **adjudikerad** träff (ej rå TSOP) — se vest-haptik.md.
- **Konstellation:** LED_EN **broadcast** (1 GPIO) → alla patchar blinkar synkront (torso = 1 stel pose-kropp).

## Stift-budget (XIAO ESP32-S3, 11 GPIO)
SCK(delad 165+TPIC) · MOSI→TPIC · MISO←165 · SH/LD(165) · RCK(TPIC) · LED_EN = **6 GPIO** (5 reserv).

## Zon-kontakt (1×6, ×10)
`VBAT · GND · DATA · LED_EN · +3V3 · VIB` — patch kablas pin 1-4, ERM-motor pin 5-6 (motor+ = 3V3, motor− = VIB→TPIC).

## Köps separat / kund-lödda
XIAO ESP32-S3, 10× väst-patch, 10× ERM-coin-motor, 2S-LiPo. **NextPCB monterar** allt ytmonterat
(buck, 2× 74HC165, 2× TPIC6B595, R/C/L); TH-kontakter (J1–J13) löder du själv.
Underlag: `nextpcb/vest-mb-bom.xls` + `vest-mb-centroid.xls` + `vest-mb-gerbers.zip`.

## Effekt (ärligt)
- ERM ~80 mA @3,3 V, 1–2 zoner samtidigt = försumbart medel; alla 10 (osannolikt) ~0,8 A kort → Cbulk 100 µF vid TPIC.
- VBAT-konstellation: topp kan bli flera A om många patchar blinkar samtidigt → VBAT på In2-plan (låg impedans).

## Färdigställt (tidigare "bänk-kvar") — verifierat i beräkning/kod, ej gissning
- **Buck 3,3 V:** Vout sätts EXAKT av FB-delaren 31,6k/10k → **0,8·(1+31,6/10) = 3,328 V**. 4,7 µH + 22 µF
  = AP63203:s typapplikation för 3,3 V; beräknad utgångsrippel **<10 mV** över hela 2S-spannet
  (ΔIL 35–39 % @1 A, 1,1 MHz). Inga gissade värden — bänk = enbart bekräfta 3,33 V innan XIAO pluggas.
- **SPI-läsning av 165-kedjan** + **TPIC-PWM-mönster:** implementerat i körbar drivrutin
  [`firmware/vest_mb_hw.py`](../../firmware/vest_mb_hw.py) (MicroPython, XIAO ESP32-S3). **Ett delat
  SPI-svep** läser 165 (hits, aktiv-låg) SAMTIDIGT som det skriver TPIC (vibb-mönster); mjukvaru-PWM
  (16 steg) per zon via timer; bit↔zon-mappning härledd ur netlistan. `selftest()` cyklar vibratorer
  + läser hits (kör även i SIM på PC utan `machine`; portar till ESP-IDF).
- **LED_EN broadcast-last:** beräknad — 10× (220R + grind ~700 pF) → τ≈330 ns, full flank ~1,6 µs.
  Konstellationen blinkar i **kamerans bildtakt (≤120 Hz)**, inte snabb bärvåg → **ingen buffert behövs**;
  direkt GPIO-broadcast räcker med stor marginal. (Buffert vore bara aktuellt vid >100 kHz-modulering.)

## Kvarstår (rena bänkmätningar, ej design)
Bekräfta 3,33 V på buck-utgången · kör `vest_mb_hw.selftest()` och bekräfta zon↔bit-mappningen
(1 konstant, matchar netlistan) · trimma vibb-PWM-känslan genom väst-tyget.
