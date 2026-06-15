# STRILAS — Hårdvaruritningar

Två fysiskt skilda noder, två kort:

| Kort | Nod | Funktion | Doc |
|---|---|---|---|
| **Vapnets optikmodul** | vapen | precis sikteskamera + IR-**sändare** (940 nm) + IMU + driver | nedan |
| **Väst-detektor-patch** | väst | IR-**mottagare** (TSOP 940 nm) + 860 nm-konstellation | [receiver-boards.md](receiver-boards.md) |
| **Hjälm-halo** | hjälm | 8× TSOP 360° + 860 nm-konstellation + **GNSS-patch** | [receiver-boards.md](receiver-boards.md) |

*(Föråldrad: `detector-ring-8x-tsop4856` hade kamera i mitten — player har ingen kamera; ersatt av väst-patch + hjälm-halo.)*

---

## 1. Vapnets optikmodul v1 (KOMPAKT) — sikteskamera + 2× IR-emitter + IMU + driver

![Vapnets optikmodul](weapon-emitter-camera-860nm.png)

**Allt vapnet behöver** på ett kort: precist sikte, skottstråle, attityd och driver.
Krympt från Ø80 (4 emittrar) till **42×62 mm** *utan prestandaförlust*. Genereras av
[`weapon_emitter_layout.py`](weapon_emitter_layout.py).

> **Full designupplösning (alla problem → beslut):** se
> [`weapon-module-design-resolution.md`](weapon-module-design-resolution.md).

**Precisionen** kommer från **sikteskameran** (centrum) som mäter bäringen till målets
IR-konstellation → sub-0,1° (se `../docs/level3-ballistic-architecture.md` §3.2) — den är
**oförändrad oavsett emitterantal**. **Skottet** är de 2 kollimerade emittrarna, symmetriskt
ovanför kameran → **samboresikt** (parallax ~0,01° @150 m; bred kon = bara LOS/ID).

### Vad som sitter på kortet

| Ref | Del | Roll |
|---|---|---|
| (mitten) | **Sikteskamera: OV5647 NoIR + 860 nm bandpass + M12 (FOV 15–30°)** | **PRECISION** — ser konstellationen → solvePnP → bäring (rolling shutter; fast-pan-grind i firmware) |
| D1–D2 | **940 nm OSLON Black** ×2 + **Carclo 10195** (~Ø20) kollimator | **skott** — kodad 56 kHz-stråle, 100–150 m |
| U2 | **TDK ICM-45686 IMU (SPI)** | attityd mellan kamerabildrutor + rekyl; **array borttagen — verifierat 1 räcker** (drift 0,0005°) |
| U6 / L1 / Rsense | **buck konstantströms-LED-driver** (från 2S) / induktor / sense-resistor | konstantström + **hårt HW-tak = ögonsäkerhet** |
| C1 / Cin / D5 / Q1 | Cout 220 µF / in-cap / freewheel-diod / AO3400 **56 kHz-gate** | switch-passiva + bärvågs-gate |
| Q2 / TVS / F1 | reverse-FET / clamp / PTC | inskydd på VBAT |
| J1 | **2×5 SPI:** VBAT·EN·IR_MOD·SCK·MOSI / GND·3V3·GND·MISO·CS | mot ESP32-P4 (kamera via FFC) |

### Mått & el — och varför prestandan hålls

- Kort **42 × 62 mm** (rundad rektangel), 3× M2.5. **~48 % mindre yta än Ø80**, halva bredden.
- **2 LED i serie** delar effektlasten → 100–150 m bibehålls; **VBAT 2S in**, U6 **buck-CC** steg ner (boost ej nödvändig); **IR_MOD** = 56 kHz på Q1-gaten.
- **1 IMU på SPI** (SPI för hög ODR vid rekyl). Array **borttagen** — fysik-verifieringen visade inter-frame-drift 0,0005° ≪ krav.
- **Precision = kameran** (emitter- & IMU-antal påverkar inte rubrik-precisionen — kameran 90 fps GS är primär referens).

### ✅ Självbländning — LÖST via våglängdssplit

**SKOTT = 940 nm**, **kamera = 860 nm bandpass** → kameran **avvisar sina egna emittrar**.
Inget timing-/baffelberoende (baffel kvar som backup). Bonus: 940 nm = TSOP-topp, 860 nm =
bättre kisel-QE för konstellationen. (Detaljer: design-resolution §0.)

### ⚠️ Ögonsäkerhet (mätpunkt)

Buck-CC-drivern (U6) ger **hårt HW-strömtak** (sense-resistor; firmware bara lägre).
**150 m kräver ~2 A** med medium-lins (10195) → Eavg ≈ 18× *punktkälle*-MPE @100 mm; **extended-
source-relaxationen täcker** men **måste mätas** (AE/skenbar källa per IEC 60825-1).
**Bringup: börja 1 A.** Notera: **ögonexponeringen sätts av 150 m-räckviddskravet (~Ie 59 W/sr),
ej av linsvalet** — medium @ 2 A ≈ minsta möjliga exponering. (Verifiering + design-resolution §3.)

### ⚠️ Kamera = OV5647 (kit), men MÅSTE vara NoIR

Kit-kameran är **Raspberry Pi Camera Model B = OV5647** (5 MP, 1/4″, M12 6 mm/F2.0/60,6° diag),
P4-stödd. **MEN spec säger "IR night vision: nonsupport" → den har IR-cut-filter och ser INTE
860 nm.** Vår precisionsväg kräver att kameran ser målets 860 nm-konstellation, så:
**du måste använda NoIR-varianten** (ta bort IR-cut-filtret, eller köp RPi NoIR-kameran).
Utan det ser sikteskameran ingen konstellation.

- **Stock-lins 6 mm/F2 (~33° H):** fungerar (verifierat SNR ≈ 30 @150 m, kort exp) men mindre
  marginal. **M12-linsen är utbytbar** → längre brännvidd ger mer räckvidd/SNR om du vill.
- Rolling shutter hanteras med kort exponering + modulerade LED + **fast-pan-grind** i firmware.

**GS-uppgradering om grinden blir för begränsande:** **ams-OSRAM MIRA220MINI MONO** (global shutter,
NIR) — köpbar (DigiKey **~$141**), men **eval-/sensorkort**, inte ett färdigt kit → P4-integration
gör du själv (ams-OSRAM-exempel finns); footprint ur deras öppna PCB-filer.

**Inte** IMX296/Arducam Pivariety (= Pi). Fullt kameraval: [`camera-selection.md`](camera-selection.md).

---

## 2. Detektor-ring (MÅLSIDAN) — 8× TSOP4856 + kamera

![Detektor-ring](detector-ring-8x-tsop4856.png)

**Målets/västens** mottagarmodul (du skjuter MOT den) — 8 IR-mottagare i ring runt en
kamera. Genereras av [`detector_ring_layout.py`](detector_ring_layout.py). Separat nod
från vapnet; specen för mått/avkoppling/360°-täckning står i skriptets noter.

> Den här hör hemma på målet/västen, inte på vapnet — vapnet **sänder** (kort 1),
> målet **tar emot** (kort 2).

---

## Nästa steg mot riktig PCB

Dessa ritningar → KiCad: SFH 4715AS- + TSOP4856- + kameramodul-footprints, dragning till
header. Säg till så genererar jag KiCad-footprintsen och ett schema.
