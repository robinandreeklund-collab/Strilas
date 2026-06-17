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

- **Optik:** 54×74 mm, **4-lager**. **Väst-patch:** **37×37 mm täcknings-nod (4 monteringshål)** (4 ledade TSOP4856 i fyrfaldigt symmetrisk DIAMANT, var och en böjd ~40° utåt → 99,5 % hemisfär-täckning, se `../ritningar/patch-sikte.md`; lim/kardborre-fäst), **2-lager**. FR-4 1,6 mm, HASL/ENIG.
- Väst-patchen är **färdigroutad** (0 oroutade · 0 clearance · 0 oconnected). Ingen LDO och **4 monteringshål
  (M2.5) i hörnen** (skruv/standoff utöver lim/kardborre) — **3,3 V kommer från väst-moderkortet** via 5-pol J1 (VBAT·GND·DATA·LED_EN·3V3,
  matchar moderkortets zon-kontakt). TSOP4856 (abs-max 6 V) matas alltså av moderkortets buck-3V3,
  inte VBAT(2S). LED-grenar på VBAT, LED-spår 0,4 mm. *(Bänktest av lös patch: mata 3,3 V på J1.5.)*
- **Pre-produktionsgranskning gjord** (se `nextpcb/GRANSKNING.md`): P4-pinout 100 % verifierad mot
  Waveshares officiella datablad (båda kanter + kamera-USB), strömvägar simulerade, DRC ren.

## Kund-lödda TH-kontakter (NextPCB gör endast SMT)
- **Optik:** J1 (1×14 P4-socket) + J2 (JST-XH batteri) = **DNP** → du sourcar + lödder själv.
- **Väst-patch:** J1 (1×5) + 4× TSOP4856 (ledade, böjs/riktas för hand) = **DNP** → du sourcar + lödder själv; NextPCB monterar SMD (LED/dioder/R/C/FET).
- → NextPCB monterar bara ytmonterat (billigare, ingen selektiv-/handlödning); centroiderna
  utesluter dessa kontakter.

## Våglängdsplan (måste matcha)
- **Skott (optik D2/D3):** 940 nm — **SFH 4725CS** (efterträder discontinued SFH 4725S; samma OSLON Black-paket, kund-levererad). Drivs av **aktiv konstantströms-sänka** (OPA171 + DPAK-FET + 0R2 sense) → **stabil ~1 A oberoende av batterinivå** (HW-strömtak = eye-safety; 56 kHz-gatad).
- **Konstellation (väst D4/D5):** 860 nm — **SFH 4715AS** (OSLON Black, **Ie 780 mW/sr@1A** databl., högeffekt f. 150 m dagsljus). Kamerans IR-pass = **860 nm** → ser konstellationen, avvisar 940 nm-skottet. TSOP4856 tar emot 940 nm-skottet. Drivs ~0,4–0,5 A (max ~50 % duty — 2,5 W topp i 10R).
- **TSOP-matning:** **3,3 V från väst-moderkortet** (ingen LDO på patchen — mindre patch). TSOP tål EJ VBAT 2S (abs-max 6 V) → matas av moderkortets buck-3V3 via J1.5.
- **Dagsljus-SNR @150 m:** budget i `../ritningar/daylight-snr-budget.md` (SFH 4715AS @~0,4–0,5 A ≈ derat-SNR 7–35, marginal för verkliga förluster). Slutbekräftas på bänk.

## Köps separat (ej PCB)
- **ESP32-P4-WIFI6** (Waveshare) — kör optikkortet + kameran.
- **Arducam OV9281 USB-kamera** + **IR-pass-filter 860 nm** (matchar västens 860 nm SFH 4715AS-konstellation; avvisar 940 nm-skottet). Kör **50–60 fps @1280×800** över
  P4:ans **USB 2.0 OTG High-Speed** (4-pol: VBUS·D−·D+·GND). 120 fps kräver beskärning/MJPEG
  (>480 Mbps full ruta) — ej nödvändigt för prototypen.
- **GY-601N1 breakout-IMU** (välj **ICM-42688**-varianten = närmast vår familj) → P4 via **SPI**:
  `VCC=3V3 · GND · SCL=SCLK · SDA=SDI(MOSI) · SA0=SDO(MISO) · CS · INT` (3–5 V @8 mA).
  Ger IMU direkt utan att vänta på optik-IMU; rå SPI för hög ODR (recoil). *(Ej stel mot
  optiska axeln i prototypen — extrinsics blir grov; OK för skjut/spår-test.)*
- Komponenter enligt respektive BOM (NextPCB bestyckar; väst-patch verifiera 860 nm-LED).
- Litet 2S-batteri för bänktest.

## Verifiera vid bringup (mätpunkter)
1. **Väst 3V3-rail:** mata 3,3 V på patchens J1.5 (från moderkort el. bänkaggregat) innan TSOP-test.
2. **Skott-RX:** optik fyrar 940 nm 56 kHz → väst-patchens TSOP4856 ger DATA-puls (3,3 V-logik, scope/MCU).
3. **Konstellation:** patchens 2× 860 nm syns i kamerabilden (frame-differencing) → PnP-bäring.
4. **Dagsljus-SNR @ avstånd** — den stora mätpunkten (LED-effekt/exponering). Håll LED-duty ≤50 %.

## Noter
- Väst-patch v1 = **utan vibrator** (haptiken läggs till i nästa rev; ej nödvändig för skjut-testet).
- Väst-moderkortet (ESP32-P4-WIFI6, samma kort som vapnet) behövs för full kedja, men för bänktestet räcker att läsa patchens
  DATA-linje direkt (scope eller valfri MCU).
