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
| 33 | GPIO13    | EMIT_HI  | ut | ✅ → optik 1A/3A-väljare |
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
1. **ADS1115-pinout rättad** (kritiskt).
2. **SPI-IMU pin 7 → GND**.
3. **NFC matas nu från +5V** (pin 2/4-rail) i st.f. carrierns 3V3 → RF-burst (~100 mA) belastar/brusar
   inte den känsliga 3V3-rail:en som IMU/ADC delar. (PN532-moduler har egen 3,3 V-LDO, tål 5 V.)
4. **5V-rail-skydd:** TVS **SMAJ5.0A** (D) på +5V → GND (transient/back-feed-clamp) + **100 µF bulk**
   (Cbulk5) för CM5-transienter. (Buckens egen strömgräns ger överströmsskydd; ingen seriesäkring →
   undviker 5 A-förlust. USB-C ska EJ sam-anslutas i fält.)
5. **HAT-ID-EEPROM:** AT24C32 (SOIC-8) @**0x50** på ID_SD/ID_SC (GPIO0/1, pin 27/28), egna 3,9 k
   pull-ups, 100 nF, A0/A1/A2→GND, WP→GND (skrivbar). Ger device-tree-auto-ID enligt RPi HAT-spec.

HAT omroutad 4-lager **0 clearance / 0 oanslutna** (569 spår, 23 vias, 50 footprints).

## Effekt-/VBAT-väg dimensionerad för emitter-puls (1A / valbart 3A)
De 2 IR-emittrarna (serie) drivs av CC-sänkan på optiken via emitter-JST:n → emitter-pulsen
(1A default / **3A** med 0R1-override) går genom HAT:ens **delade VBAT-väg** (batteri→säkring→
P-FET→VBAT-nod→buck+emitter+recoil), topp ~7A. Åtgärdat:
- **Omvänd-skydds-P-FET:** AO3401 (SOT-23, ~4A) → **AOD4185** (DPAK, 40V/**40A**/15mΩ) — klarar topp.
- **Säkring:** PTC 3A → **PTC 4A** (håller buck+emitter+recoil utan nuisance-trip).
- **VBAT/+5V/SW power-klass:** spårbredd 0,5 → **0,8 mm**; +5V (CM5 ~2A) och SW_n tillagda i klassen.
- **Optik:** **47µF VBAT-bulk** (C3) tillagd nära emittrarna för 3A-pulsens flanker; **0R1-sense (R2)
  → 2010** (0805 klarade ej ~0,4W i 3A-läget), placerad intill R1 (parallell-sense).
- **Emitter-JST (JST-PH):** 3A är PULSAD topp (56kHz, duty<100% → RMS<2,5A) → inom PH-max. 1A kont. OK.
- **Batteri-JST-XH (3A):** kontinuerligt ~2-2,5A OK; korta shot-toppar inom transient.

## 1A/3A emitter-val — FIRMWARE-STYRT (ingen bygel/lödning)
Istället för löd-DNP: en logik-N-FET **Q2 (AO3400)** på optiken kopplar in/ur parallell-sense-
grenen **R2 (0R068)**, styrd av **EMIT_HI** (HAT GPIO13, pin 33) via emitter-kontaktens 4:e stift
(JST-PH 3→4-pin på båda korten). EMIT_HI **hög = 3A**, **låg/flytande = 1A** (gate-pulldown R6 100k
→ säkert default vid boot). R2=0R068 vald så R2+Rds(FET ~35mΩ) ≈ 0R1 → 0R2‖0R1 ≈ 0,067Ω → ~3A.
FET:en (Rds~35mΩ, 5A) sitter i 3A-grenens lågsida; sense-felet från Rds är kompenserat i R2 och
≤~6% (emitter-ström, ej precisionskritisk; lägre ström = säkrare). Inget i den heta huvud-sense-vägen.

## Buck — LÅST (inga frågetecken)
**AP63203WU** (Diodes, 3A synkron, 3,8–32V in, integrerade FET, TSOT-23-6). Stift VERIFIERADE
mot KiCad:s kurerade symbolbibliotek: 1=FB 2=EN 3=IN 4=GND 5=SW 6=BST. Stödkrets: induktor
**3,3µH (Taiyo-Yuden MD-5050)**, FB-delare **52k3/10k → 5,0V** (Vref 0,8V) + 22pF feedforward,
BST-cap 100nF, Cin 10µF + 100µF, Cout 22µF + 100µF, EN→VIN. IC + induktor placerade intill
varandra → kort SW-nod. Laststudie: CM5 + kamera-CV utan tunga USB ~2–2,5A → 3A med marginal.
Alla footprints är KiCad-standard (ingen blint byggd kraft-footprint). HAT routad 4-lager 0/0.

## (historik) Buck — tidigare rekommendation
- **Laststudie:** CM5 + MIPI-kamera + WiFi för CV, UTAN tunga USB-kringutrustningar → ~2–2,5 A typ,
  topp ~3 A (boot-inrush täcks av bulk). RPi:s "5 A" gäller fullastade USB-portar (har vi ej).
  → **3 A räcker med marginal; 100 µF-bulken hanterar transienter.**
- **Topologi:** på detta auto-routade kort ger en **integrerad modul** (optimerad intern switch-loop)
  bättre EMI/stabilitet än en diskret SMPS som auto-routas. **Rekommenderad konkret modul:
  MPS MPM3650 (6A, integrerad induktor, 2,75–17 V in)** — el-design verifierad mot datablad:
  FB-delare R1=20 k / R2=2,74 k / CF=39 pF (→5,0 V), EN→VIN, VCC-cap 1 µF, Cin 10 µF,
  Cout 22 µF×2 + 100 µF, SW-stift floatande, AGND/PGND→GND.
  *Footprinten (QFN-24 4×6) byggs/verifieras mot MPS land-pattern innan tillverkning — görs ej blint.*
  Nuvarande symbol/footprint är en modul-placeholder (VIN/EN/GND/VOUT + Cin/Cout) tills modulen låses.
