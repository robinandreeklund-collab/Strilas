# STRILAS — Hårdvaruritningar

Två fysiskt skilda noder, två kort:

| Kort | Nod | Funktion |
|---|---|---|
| **Vapnets optikmodul** | vapen | precis sikteskamera + IR-**sändare** (860 nm) + IMU + driver |
| Detektor-ring | mål/väst | IR-**mottagare** (TSOP4856) + kamera |

---

## 1. Vapnets optikmodul v1 — precis sikteskamera + IR-emitter + IMU + driver

![Vapnets optikmodul](weapon-emitter-camera-860nm.png)

**Allt vapnet behöver** på ett kort: precist sikte, skottstråle, attityd och driver.
Genereras av [`weapon_emitter_layout.py`](weapon_emitter_layout.py).

**Precisionen** kommer från **sikteskameran** (centrum) som mäter bäringen till målets
IR-konstellation → sub-0,1° (se `../docs/level3-ballistic-architecture.md` §3.2).
**Skottet** är de 4 kollimerade emittrarna, **samboresiktade** runt kameran → strålen
följer siktaxeln (bred kon = bara LOS/ID, inte hitbox).

### Vad som sitter på kortet

| Ref | Del | Roll |
|---|---|---|
| (mitten) | **Sikteskamera: OV5640 NoIR + 860 nm IR-pass + telefoto M12** | **PRECISION** — ser konstellationen → solvePnP → bäring |
| D1–D4 | **ams-OSRAM SFH 4715AS** (860 nm) ×4 + **Carclo 10195** (~Ø20) kollimator | **skott** — kodad 56 kHz-stråle, 100–150 m |
| U2 | **TDK ICM-45686 IMU** (I²C) | attityd mellan kamerabildrutor + rekyl |
| Q1 | **AO3400 N-FET** | switchar emitter-strängen på 56 kHz |
| R1 | **Rsense ~1–3 Ω 2 W** | **sätter & HW-begränsar pulsströmmen = ögonsäkerhet** |
| C1 / Rg / D5 | 220 µF reservoar / 220 Ω gate / SS54 flyback | levererar pulsen + ren switchning |
| J1 | **2×4: IR_MOD·VEMIT·EN·GND / 3V3·SDA·SCL·GND** | mot ESP32-P4 (kamera via FFC) |

### Mått & el

- Kort **Ø80 mm**, emitter-kvadrat **42 mm** (4× Carclo Ø20-optik runt en 25×24-kamera), 3× M2.5.
- **4 LED i serie** → mata **VEMIT** från 2S-batteri / boost (~12 V); **IR_MOD** = 56 kHz från RMT; **IMU** på I²C.
- **Ø80 är stort** p.g.a. fyra Ø20-optiker. Vill du krympa: bestycka **1–2 emittrar** (räcker för skottet) eller role-split.

### ⚠️ Kameran får inte blända sig själv

Sikteskameran (860 nm IR-pass) ser sina **egna** 860 nm-emittrar. Lös med **(a)** baffel
mellan ring och lins + **(b)** emittrar avfyras **bara vid trigger** (kameran läser
konstellationen mellan skott), **eller (c)** emitter på **940 nm** + kamerafilter **860 nm**
= ren våglängdsseparation.

### ⚠️ Ögonsäkerhet (1–3 A kollimerat)

Inte trivialt Class 1. **R1 är hårdvaru-strömgränsen** (inte firmware). Räkna/mät accessible
emission per IEC 60825-1, **sikta 1 A först**, köp räckvidd med mottagar-filtret hellre än ström.

### ⚠️ Kamera = P4-stödd sensor (inte IMX296)

IMX296 (Sony GS) är Pi-native, saknar `esp_cam_sensor`-drivrutin för P4. Använd **OV5640**
(v1, i kitet) eller **ams-OSRAM Mira220** (global shutter, NIR — P4-exempel finns). Mått är
**riktmått** (typiskt ~25×24 mm, M12) — **mät din modul** → `CAM_W/CAM_H/CAM_HOLE`.

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
