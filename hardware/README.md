# STRILAS — Hårdvaruritningar

Två fysiskt skilda noder, två kort:

| Kort | Nod | Funktion |
|---|---|---|
| **Vapnets optikmodul** | vapen | precis sikteskamera + IR-**sändare** (860 nm) + IMU + driver |
| Detektor-ring | mål/väst | IR-**mottagare** (TSOP4856) + kamera |

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
| (mitten) | **Sikteskamera: ams-OSRAM MIRA220MINI (mono, global shutter, NIR) + 860 nm bandpass + M12 (FOV 15–30°)** | **PRECISION** — GS fryser bilden under panorering → korrekta blob-centroider; ser konstellationen → solvePnP → bäring |
| D1–D2 | **940 nm OSLON Black** ×2 + **Carclo 10195** (~Ø20) kollimator | **skott** — kodad 56 kHz-stråle, 100–150 m |
| U2 | **TDK ICM-45686 IMU** (I²C) | attityd mellan kamerabildrutor + rekyl |
| Q1 / R1 | **AO3400 N-FET** / **Rsense ~1–3 Ω 2 W** | switchar + **sätter & HW-begränsar pulsström = ögonsäkerhet** |
| C1 / Rg / D5 | 220 µF reservoar / 220 Ω gate / SS54 flyback | levererar pulsen + ren switchning |
| J1 | **2×4: IR_MOD·VEMIT·EN·GND / 3V3·SDA·SCL·GND** | mot ESP32-P4 (kamera via FFC) |

### Mått & el — och varför prestandan hålls

- Kort **42 × 62 mm** (rundad rektangel), 3× M2.5. **~48 % mindre yta än Ø80**, halva bredden.
- **2 LED i serie** delar effektlasten → 100–150 m bibehålls; mata **VEMIT** från 2S/boost (~12 V).
- **Precision = kameran** (emitterantal påverkar inte). **2 (ej 1) emittrar** sprider effekten →
  *lättare* Class 1. Enda som tappas: framtida **aktiv-fiducial-beacon** (4-punkt) — ej v1-krav.

### ✅ Självbländning — LÖST via våglängdssplit

**SKOTT = 940 nm**, **kamera = 860 nm bandpass** → kameran **avvisar sina egna emittrar**.
Inget timing-/baffelberoende (baffel kvar som backup). Bonus: 940 nm = TSOP-topp, 860 nm =
bättre kisel-QE för konstellationen. (Detaljer: design-resolution §0.)

### ⚠️ Ögonsäkerhet (mätpunkt)

CC-drivern (U3) ger **hårt HW-strömtak** (sense-resistor; firmware bara lägre). ~2 mW in i
ögat @1 m/1 A → **inte trivialt Class 1**. **Mät AE per IEC 60825-1** vid låst pulsformat,
**börja på 1 A**, köp räckvidd med mottagar-filtret. (Design-resolution §3.)

### ✅ Kamera = ams-OSRAM MIRA220MINI (mono GS NIR) — vald

Eftersom vi gör custom PCB byter vi direkt till **rätt** kamera istället för att rita runt
OV5640 och göra om. **Global shutter** är tekniskt korrekt för ett rörligt vapen: rolling
shutter (OV5640) smetar/skevar under panorering → korrumperar blob-centroiderna → bäringsfel
*medan du rör dig*. GS fryser hela bilden. **NIR-förstärkt** → ser 860 nm-konstellationen bättre.

- Köpbar: **MIRA220MINI Sensor Board Mono** (ams-OSRAM, DigiKey). MIPI-CSI + I²C, P4-exempel finns.
- **Footprint/mått från ams-OSRAM:s öppna PCB-filer** (`github.com/ams-OSRAM/ams-Mira-Image-Sensors`)
  → exakt, ingen gissning (löser "mät-din-modul" bättre än OV5640).
- **Inte** OV5640 (gör om), IMX296 (ingen P4-drv) eller Arducam Pivariety (= Pi/libcamera).

**Avvägning (ärlig):** P4-drivrutinen är *exempel-grade* (mer integrationsjobb än mogna OV5640),
högre kostnad + ledtid. Mono är **bättre** för oss (bara IR-blobbar, ingen Bayer → mer känslighet).

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
