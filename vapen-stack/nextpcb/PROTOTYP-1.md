# STRILAS — Prototyp 1: provskjut mot väst-framsida

Mål: skjut med **optikkortet** (vapnet) mot en **väst-framsida (5 patchar)** och verifiera
(1) skott-mottagning (940 nm → TSOP) och (2) konstellation sedd av kameran (860 nm → PnP).

## Beställ (NextPCB)
| Kort | Antal | Gerber | BOM | Centroid |
|---|---|---|---|---|
| **Optik (prototyp)** | 5 (använd 1) | `optik-gerbers.zip` | **`optik-PROTOTYP-bom.xls`** | **`optik-PROTOTYP-centroid.xls`** |
| **Väst-patch** | **5** (västens framsida) | `vest-patch-gerbers.zip` | `vest-patch-bom.xls` | `vest-patch-centroid.xls` |

NextPCB min-order är oftast 5 st → 5 optik (1 behövs nu) + 5 väst-patchar = en framsida.

> **PROTOTYP-optiken kör IMU på breakout, ej på kortet.** `optik-PROTOTYP-bom.xls` markerar
> **U1 (IIM-42653) + C3/C4/C5 som DNP** (monteras ej); prototyp-centroiden utesluter dem.
> Samma routade optikkort som produktion — bara IMU:n obestyckad. IMU-footprinten finns kvar
> för framtida produktionsversion (då IMU sätts tillbaka på kortet, stelt mot optiska axeln).

- **Optik:** 54×74 mm, **4-lager**. **Väst-patch:** 58×42 mm, **2-lager**. FR-4 1,6 mm, HASL/ENIG.
- Väst-patchen är nu **färdigroutad** (0 oroutade · 0 clearance · 0 oconnected); J1 inflyttad i kortet (tidigare hängde den utanför kanten — fixat).

## Köps separat (ej PCB)
- **ESP32-P4-WIFI6** (Waveshare) — kör optikkortet + kameran.
- **Arducam OV9281 USB-kamera** + **IR-pass-filter** (860 nm). Kör **50–60 fps @1280×800** över
  P4:ans **USB 2.0 OTG High-Speed** (4-pol: VBUS·D−·D+·GND). 120 fps kräver beskärning/MJPEG
  (>480 Mbps full ruta) — ej nödvändigt för prototypen.
- **GY-601N1 breakout-IMU** (välj **ICM-42688**-varianten = närmast vår familj) → P4 via **SPI**:
  `VCC=3V3 · GND · SCL=SCLK · SDA=SDI(MOSI) · SA0=SDO(MISO) · CS · INT` (3–5 V @8 mA).
  Ger IMU direkt utan att vänta på optik-IMU; rå SPI för hög ODR (recoil). *(Ej stel mot
  optiska axeln i prototypen — extrinsics blir grov; OK för skjut/spår-test.)*
- Komponenter enligt respektive BOM (NextPCB bestyckar; väst-patch verifiera 860 nm-LED).
- Litet 2S-batteri för bänktest.

## Verifiera vid bringup (mätpunkter)
1. **Skott-RX:** optik fyrar 940 nm 56 kHz → väst-patchens TSOP4856 ger DATA-puls (scope/MCU).
2. **Konstellation:** patchens 2× 860 nm syns i kamerabilden (frame-differencing) → PnP-bäring.
3. **Dagsljus-SNR @ avstånd** — den stora mätpunkten (LED-effekt/exponering).

## Noter
- Väst-patch v1 = **utan vibrator** (haptiken läggs till i nästa rev; ej nödvändig för skjut-testet).
- Väst-noden (ESP32-C5) behövs för full kedja, men för bänktestet räcker att läsa patchens
  DATA-linje direkt (scope eller valfri MCU).
