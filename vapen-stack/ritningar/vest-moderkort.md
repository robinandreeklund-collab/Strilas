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

## Kvarstår (bänk)
Buck-utgång 3,3 V innan XIAO plugg · SPI-läsning av 165-kedjan · TPIC PWM-mönster · LED_EN-broadcast-last (10 grindar).
