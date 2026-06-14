# STRILAS — Receiver-/player-kort (väst + hjälm)

Player-sidan. **Ingen kamera** (det är skytten som ser dig). Varje kort gör två saker:

- **Tar emot skott:** Vishay **TSOP4856** (56 kHz) + **940 nm bandpass** — skottstrålen är 940 nm.
- **Syns för skyttens kamera:** **860 nm IR-konstellations-LED** i känd geometri → PnP-bäring.

Genereras av [`receiver_boards_layout.py`](receiver_boards_layout.py). Två kort:

## 1. Väst-detektor-patch (placera flera → zoner)

![Väst-patch](vest-detector-patch.png)

- **58×42 mm**, 4 sy-/skruvhål. **S1–S3 TSOP4856** framåtriktade + **L1/L2 860 nm**-konstellation (känd diagonal).
- S1–S3 **OR:as** (D1–D3) → **1 DATA-linje per patch** till väst-MCU (ESP32-C5). Zon = vilken patch som fyrar.
- **J1 4-pol:** `VBAT · GND · DATA · LED_EN`. LED_EN delad buss; MCU modulerar konstellationens blink-ID.
- **Placera ~4–6 runt torso** (bröst / rygg / vä / hö) → 360° + zoner.

## 2. Hjälm-halo (360° + huvud-zon + GNSS)

![Hjälm-halo](helmet-halo.png)

- **Ø100 mm ring**, 4 skruvhål. **8× TSOP4856 radiellt utåt** (45°) → 360° azimut för **huvud-zonen**.
- **4× 860 nm**-konstellation högt placerade → syns för skyttens kamera från många vinklar.
- **CENTRUM: GNSS patch-antenn (uppåt)** — hjälmen är högsta punkten = bästa sky-view.
  - **En** antenn = **position** (heading är vapnets dubbelantenn-jobb, separat).
  - U.FL → GNSS-mottagare på väst-noden. GND-plan under patchen. L-band (1,2–1,6 GHz) störs ej av 56 kHz-IR.
  - **Full-system, ej v1-aktiv** — footprint nu, bestyckas senare.

## Våglängdsplan (måste hållas)

| Funktion | Våglängd | På kortet |
|---|---|---|
| Ta emot skott | **940 nm** | TSOP4856 + 940 nm bandpass |
| Synas (konstellation) | **860 nm** | 860 nm-LED |

⚠️ Blanda inte filtren: 940 nm på TSOP, 860 nm på konstellationen.

## Inkoppling (samma för båda)

Varje kort → 4-pol kabel till **väst-noden (ESP32-C5)**: `VBAT · GND · DATA · LED_EN`.
DATA = patchens OR:ade TSOP-utgång (MCU avkodar MilesTag + vet vilken patch = zon).
LED_EN = delad; MCU blinkar konstellationen (frame-synk för skyttens kamera + ID).

## Användning i testet (v1)

Receiver-korten **är** måltavlan: ett kort (eller en patch på ställning/väst) registrerar
skottet (TSOP → ljud/log) **och** lyser med 860 nm-konstellationen så skyttens kamera kan
PnP:a bäringen. GNSS-patchen är vilande i v1 (position mäts med måttband).

## Att verifiera (mätpunkter)

- TSOP-räckvidd @150 m i sol (940 nm bandpass-vinst) — bänk/fält.
- Konstellations-LED-effekt/modulering för kamera-detektion @150 m dag.
- Zon-granularitet (antal patchar) vs önskad upplösning.

---

> **Föråldrad:** `detector-ring-8x-tsop4856.png` (8 TSOP med **kamera** i mitten) var en tidig
> felaktig player-design — player har ingen kamera. **Ersatt av** väst-patch + hjälm-halo ovan.
