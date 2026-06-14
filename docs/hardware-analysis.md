# STRILAS — README-analys & hårdvaru-/dev-board-utredning

> Författad som teknisk underlagsrapport. Del 1 granskar nuvarande README/designspec. Del 2–8 är en researchdriven utredning (källor 2025–2026) av varje delsystem med konkreta komponenter, dev boards, priser och en rekommenderad uppgraderingsväg för att ta systemet till "next level". Del 9 samlar allt i en prioriterad roadmap + referens-BOM.

---

## Del 1 — Komplett analys av README

### 1.1 Vad README:n beskriver

STRILAS är en öppen DIY force-on-force-/MILES-liknande träningssimulator: replikvapen skjuter **kodat 905 nm IR** (inga projektiler), träffar registreras av kropps-/hjälmdetektorer, och en **central server avgör träff/miss** utifrån båda spelarnas position (UWB/GNSS), pipans attityd (IMU) och **simulerad ballistik med flygtid**. Systemet har fysisk rekyl (reciprocerande massa), NFC-baserad ammunitionslogistik, make-ready-tillståndsmaskin, live-telemetri och after-action review (AAR).

### 1.2 Styrkor i nuvarande spec

- **Säkerheten kommer först och är genuint genomtänkt.** De tre verkliga riskerna (IR-ögonsäkerhet, LiPo-laddning, högströmskontakter) är korrekt identifierade och rangordnade — och kravet att ögonsäkerheten ska upprätthållas **i hårdvara, inte firmware** är helt rätt.
- **Central, positionsbaserad adjudikation** är den arkitektoniska kärnan och rätt designval — rättvist för rörliga mål och grunden för analyslagret.
- **Två fysiskt separerade kraftskenor** (logik vs rekyl) och **cold-mate-sekvensering** av magasinskontakterna via make-ready-maskinen är välresonerat och säkerhetsdrivet.
- **NFC-ammunition med RAM-buffrad räknare** som bara skriver vid uttag/omladdning respekterar EEPROM-livslängd och är en smart detalj.
- README:n är genomarbetad, internt konsekvent i resonemanget och har realistisk power-budget.

### 1.3 Gap, inkonsekvenser och risker (åtgärdbara)

| # | Observation | Konsekvens | Förslag |
|---|---|---|---|
| 1 | **Repot innehåller bara `README.md`.** `docs/strilas-systemritning.html`, hela mappstrukturen (`firmware/`, `server/`, `hardware/`), `config/example.env` och per-modul-READMEs som länkas/refereras **finns inte ännu**. | Build-instruktionerna (`pio run`, `docker compose up`) går inte att följa; länkar är döda. | Markera README som designspec, eller börja bygga ut skelettet. Skapa minst `docs/` + stubbar. |
| 2 | **Vapen-MCU = en ensam ESP32** som ska göra mikrosekund-exakt IR-kodning, rekyl-PWM, triggerfångst, ballistik-FSM **och** radio på samma kärnor. | WiFi-stacken stjäl CPU-cykler → **timingjitter under nätverkslast**, just i den mest tidskritiska vägen. | Se Del 2: dela compute/radio (ESP32-P4+C6) eller lägg IR/rekyl på en deterministisk IO-coprocessor (RP2350 PIO). |
| 3 | **ESP-NOW** antyds som radioval. Hård gräns på **20 krypterade peers**, ingen QoS/garanterad retransmit. | Skalar inte rent till 16–32 spelare med dubbelriktad telemetri + video. | 5 GHz WiFi 6 (OFDMA/TWT) som backhaul + ev. 802.15.4/Thread-mesh som resilient hit-kanal. |
| 4 | **Tidssynk anges löst som "NTP/PTP".** Rättvis ballistik-adjudikation kräver gemensam tidsbas **snävare än engagemangets timingtolerans** (sub-ms). | Med ren NTP över WiFi (10-tals ms jitter) blir träffordningen mellan snabba skott tvetydig. | PTP/IEEE-1588 över backhaul + **hårdvarutidsstämpling av IR-ankomst** lokalt (PIO/PPI capture). |
| 5 | **IR-kodningsschema är ospecificerat.** | Egen kod är skör mot solljus och replay-/record-fusk. | Anta **MilesTag II / OpenLaserTag** (38–56 kHz modulerad bärvåg + pulslängd) och lägg **CRC + rullande nonce** ovanpå mot replay. |
| 6 | **IMU = BNO085 (eller BNO055).** BNO085 är i praktiken EOL/svåråtkomlig, har en känd "snap"-bugg vid snabba rörelser och **magnetometerfusion fungerar dåligt nära stål** (ett vapen = metall). | Pip-klättring är exakt en snabb, metallnära transient — BNO085:s svaghetszon. | **TDK ICM-45686** i 6DOF (mag av), gyro ≥1–2 kHz, host-side-fusion. |
| 7 | **UWB-metod (TWR vs TDoA) anges inte.** README säger "DW3000 + 4–8 ankare". | TWR skalar dåligt till många taggar; en tagg/ankare kan bara ranga i en slot åt gången. | **TDoA** (synkade ankare) för hög taggdensitet; se Del 3. |
| 8 | **905 nm "raw" laser i BOM.** README flaggar risken korrekt, men default bör vara den säkra vägen. | Ögonsäkerhet hänger helt på diffusion + strömgräns. | Default = diffuserad **860 nm IR-LED (SFH 4715AS)**; 905 nm-laser endast som verifierad Class 1-långdistansvariant. |
| 9 | **ESP32-CAM som vapenkamera.** Rolling shutter + 2.4 GHz + ingen HW H.264. | Smetar vid snabba panoreringar; trängs i 2.4 GHz; svårt att tidssynka frames för AAR. | Se Del 5: Pi Zero 2 W + Cam Module 3 (NoIR), global-shutter-variant för primärvapen. |
| 10 | **Spelarantal definieras aldrig.** Arkitekturen antyder "många". | Dimensionering av radio/server/anchors blir godtycklig. | Sätt ett designmål (t.ex. 16–32 noder) och dimensionera mot det. |

**Sammanfattning Del 1:** Designen är sund och säkerhetsmedveten. De största verkliga svagheterna är (a) en överbelastad ensam-MCU i den tidskritiska vägen, (b) odefinierad/underdimensionerad radio + tidssynk för rättvis adjudikation, och (c) några komponentval (BNO085, ESP32-CAM, raw 905 nm) som redan har bättre 2025–2026-alternativ. Resten av rapporten åtgärdar dessa konkret.

---

## Del 2 — Compute & nätverk (vapnets hjärna + radio)

Vapennoden behöver tre saker samtidigt: **hård realtids-IO** (µs-exakt IR-pulskodning, rekyl-PWM, triggerfångst), en **ballistik-FSM med headroom för sensorfusion**, och **lågfördröjd, deterministisk radio**. Nuvarande ensam-ESP32 tvingar allt på samma Xtensa-kärnor som delar tid med WiFi-stacken — där brister den.

### 2.1 MCU-kandidater

| MCU / board | Kärna / klocka | RAM / flash | Tidskritisk IO | Radio | Determinism | ~Pris (board) |
|---|---|---|---|---|---|---|
| ESP32-S3 (nuvarande klass) | Xtensa LX7 ×2 @240 MHz | 512 KB +8 MB PSRAM | RMT (HW IR-modulering), MCPWM, LEDC | WiFi4 + BLE5 | Medel — radio stjäl cykler | ~$15 |
| **ESP32-P4 (+C6)** Waveshare ESP32-P4-WIFI6 | RISC-V ×2 @400 MHz + LP-kärna | 768 KB L2 + upp till 32 MB PSRAM | RMT, MCPWM; pinna IR/ballistik på en kärna | **C6-kompanjon** (WiFi6 + BLE5 + 802.15.4) via SDIO | Bra — radio avlastad | ~$14–26 |
| **RP2350** (Pico 2 / 2 W) | Cortex-M33 ×2 @150 MHz | 520 KB / 4 MB ext | **12 PIO-state machines** = jitter-fri kodad pulståg + HW IR-ankomststämpling | Ingen (2 W = CYW43 WiFi4/BLE) | **Utmärkt** (bare-metal) | $5 / ~$7 |
| Teensy 4.1 | Cortex-M7 @600 MHz | 1 MB / 8 MB | HW IR-modulator, FlexIO, DMA | Ingen | Utmärkt | ~$32 |
| STM32H7 (H743/H723) | Cortex-M7 @480–550 MHz | upp till 1 MB | Avancerade timers, **on-chip 1588 PTP** | Ingen | Utmärkt (brantast toolchain) | ~$25–30 |
| **nRF54L15** DK | Cortex-M33 @128 MHz + RISC-V | 256 KB / 1.5 MB | PPI/GPIOTE (zero-jitter HW-eventrouting), NFC | **BLE6 + 802.15.4/Thread + 2.4G** | Utmärkt | ~$22–39 |

**Om IR-timing:** renast är RP2350 PIO (12 oberoende state machines = dedikerad HW för 905 nm-pulståg, rekyl-PWM och IR-ankomststämpling med noll CPU-jitter), Teensy 4.1:s HW IR-modulator, och nRF54L:s PPI/GPIOTE. ESP32 RMT fungerar bra för IR men konkurrerar med RF-stacken på samma kärnor.

### 2.2 Nätverk för många noder, låg latens

| Alternativ | Latens | Nodantal | Determinism | Not |
|---|---|---|---|---|
| ESP-NOW (nuvarande) | 1–10 ms | **20 krypterade peers** (hård) | Dålig (CSMA, ingen QoS) | Bryts vid 32 noder med dubbelriktad telemetri |
| **5 GHz WiFi 6 (OFDMA/TWT)** | sub-ms–få ms | 30+ via AP | Bättre (RU-schemaläggning) | Flyr trängseln i 2.4 GHz; bär även video |
| Thread / 802.15.4 | få ms/hopp, mesh | hundratals, självläkande | Bra för telemetri | Klarar inte video; bra som resilient hit-/status-mesh |
| LoRa | 100-tals ms | många | n/a realtid | Endast långdistans-muster/säkerhetsbeacons |

### 2.3 Tidssynk (rättvis adjudikation)

- **NTP/SNTP:** 10-tals ms över WiFi — otillräckligt.
- **PTP / IEEE-1588 (gPTP 802.1AS):** sub-µs trådbundet, sub-ms över WiFi med PHY-tidsstämpling. Öppen `ESP1588`-klient finns för ESP32; STM32H7 har 1588-HW.
- **Praktik:** kör PTP över backhaul **och** tidsstämpla optisk IR-ankomst i HW (PIO/PPI capture) lokalt, försonat mot serverns grandmaster. Det tar bort OS/stack-jitter ur den känsligaste händelsen.

### 2.4 Rekommendation — Compute & nätverk

> **Primärt:** **ESP32-P4 + ESP32-C6** (t.ex. Waveshare ESP32-P4-WIFI6, ~$14–26). Pinna ballistik-FSM + IR/rekyl/trigger på en P4-kärna, låt C6 sköta all radio över SDIO — löser ensam-ESP32:ns kontentionsproblem direkt och ger WiFi6 + BLE + 802.15.4 för dual-radio-split. Behåller Espressif-ekosystemet.
>
> **För hårdaste IR-determinism:** lägg en **RP2350 (Pico 2, $5) som dedikerad IO-coprocessor** (12 PIO state machines → jitter-fritt pulståg + HW IR-tidsstämpling) bredvid radio-SoC:n.
>
> **Radio:** 5 GHz WiFi 6 OFDMA-backhaul till server + valfri Thread-mesh för hit/status. **Tidssynk:** PTP över backhaul + HW-tidsstämplad IR-ankomst.

---

## Del 3 — Positionering & lokalisering (mest noggrannhetskritiska delsystemet)

Rättvis träffadjudikation står och faller med positionsnoggrannheten. Mål: kontinuerlig sub-30 cm-pose ute och inne.

### 3.1 UWB — kärnan

| Modul / kit | Chip | Noggrannhet | AoA | ~Pris | Not |
|---|---|---|---|---|---|
| **Qorvo DWM3000** modul | DW3110/DW3000 | ~10 cm | nej (modul) | **$23.62** (1), EVB **$29.50** | Brett ekosystem, billigast |
| DW3220 (chip) | DW3000-familj | <5 cm, AoA | **5°** | — | AoA-kapabel variant |
| **Makerfabs MaUWB_ESP32S3** | DW3000 | ~10 cm | nej | **$46.58** | ESP32-S3 + UWB + WiFi/BLE, "unlimited anchors + 64 tags", Multi-PAN — DIY-vänligast |
| NXP SR150 (Murata Type2BP EVK) | SR150 | ~10 cm | **<3° (dual-RX), 3D med 3 antenner** | **~$148** (1) | FiRa, interop med Apple U1/Android UWB |
| NXP SR040 (Murata Type2DK EVK) | SR040 | ~10 cm | nej (tagg) | **~$100** (1) | Lågeffekttagg |

**TWR vs TDoA — avgörande för många taggar:** med klassisk **TWR** kan en tagg/ankare bara ranga i en slot åt gången → skalar dåligt. **TDoA** (envägs-blink, synkade ankare) ger teoretiskt tusentals taggar/cell, lägre tagg-effekt och latens. Priset är att **alla ankare måste vara sub-ns-synkade** (1 ns klockfel ≈ 30 cm) — den svåraste infra-biten.

**Pragmatisk nyans (viktig):** **DS-TWR (double-sided two-way ranging) + CFO-korrektion** self-cancelar klockoffset (residual ~ps), vilket **eliminerar behovet av nätverksvid sub-ns-synk**. Rekommenderad väg: börja med DS-TWR + TDMA-schemaläggning för 16–32 spelare (klarar ~10 Hz aggregerat, fördelat per tagg), och gå till uplink-TDoA endast om du behöver passiv höghastighetstracking av många taggar — och bygg då PTP/UWB-trådlös 1588-synk (~10 ns) på ankarna. Notera att Makerfabs stock-bibliotek är demo-grade single-tag — **MAC/TDMA/TDoA-lagret skriver du själv**.

### 3.2 GNSS RTK (utomhus)

- **u-blox ZED-F9P:** dubbelband (L1/L2) RTK, **0.01 m + 1 ppm CEP**, upp till 20 Hz, <10 s konvergens, Moving Base. Kräver korrektionsdata (egen bas eller NTRIP). Boards: ArduSimple simpleRTK2B ~€172 (~$185), SparkFun GPS-RTK2 **$259.95**.
- **ZED-F9R:** RTK + on-chip IMU dead-reckoning (ADR) — håller position i GNSS-skugga (urban canyon, under tak), upp till 30 Hz. SparkFun-board **$299.95**. Bra för fält med blandad täckning.
- **Heading:** ZED-F9H eller F9P-par i moving-baseline → **~0.4° heading @1 m baslinje** (förbättras med längre baslinje) — GNSS-härlett, kräver ingen magnetometer.
- Integration: GNSS ger absolut utomhusankare, UWB tar över inomhus/under tak, IMU broar glappen.

### 3.3 Sensorfusion

2025-forskning (arXiv 2512.10480, GNSS/UWB/IMU, jämför EKF/FGO/PF) ger tydligt svar: **error-state EKF (ESKF)** är mest konsekvent — bäst median/RMSE (horisontellt fel **0.44–1.73 m** i blandade scenarier; tightly-coupled ESKF når **~8–10 cm** under bra geometri), snabb, stabil kovarians. **Factor Graph Optimization (FGO)** är tyngre men vinner i NLOS-tunga miljöer (träd, byggnader, spelare som skymmer varandra) tack vare robusta loss-kärnor (Huber/Barron) — upp till ~41 % felreduktion. Kör **chest-mounted IMU-PDR som rörelse-backbone** + absoluta UWB/GNSS-uppdateringar.

**Arkitektur (rekommenderad hybrid):** kör hög-rate AHRS (x-io Fusion eller VQF, magnetometer-fritt — magnetometer är opålitlig nära vapen) + ESKF-prediktion **på noden**, skicka filtrerad pose + kovarians **och** råa UWB-ranges till servern som kör **FGO-backend (GTSAM) + ballistik/adjudikation** med global världsram. Skicka inte rå IMU (bandbredd); lös inte allt på noden (förlorar global konsistens). Survey:a varje UWB-ankare in i samma globala ram (WGS84/UTM) vid installation → ingen runtime-transform vid handoff. Hysteres-handoff (två fix-kvalitetströsklar + överlappszon) förhindrar "flapping" i dörröppningar.

### 3.4 Rekommendation — Positionering

> **Inomhus/arena:** UWB i **TDoA-läge** med synkade ankare. DIY-snabbast: **Makerfabs MaUWB_ESP32S3 ($46.58/nod)**. För vinkeldata/färre ankare: **NXP SR150-ankare ($148) + SR040-taggar ($100)** (bonus: telefoner kan agera taggar). Renaste low-cost-byggblock: **Qorvo DWM3000 ($24/modul)**.
> **Utomhus:** **u-blox ZED-F9P** (RTK-rover) + NTRIP/egen bas; **ZED-F9R** där täckningen är skuggig.
> **Fusion:** **ESKF** på servern, IMU-PDR backbone + UWB(inne)/GNSS(ute), med OSM-/banbaserad feasibility-constraint vid övergångar. Sikta sub-30 cm inne, cm-RTK ute.

---

## Del 4 — IR-engagement, IMU & optik

### 4.1 IR-emitter, kodning & räckvidd

| Väg | Del | Uteffekt | Stråle | Ögonsäkerhet | Not |
|---|---|---|---|---|---|
| **Diffuserad IR-LED (default)** | ams-OSRAM **SFH 4715AS** (860 nm) | 780 mW/sr @1A | 45–90° | **Trivialt Class 1** (inkoherent, stor källa) | ~$1; kiseldetektorer något känsligare @860 nm; ~15–40 m |
| IR-LED (bred) | SFH 4170S (860 nm) | 280 mW/sr | 130° | Class 1 | Bättre som IFF-beacon än skott |
| Pulsad 905 nm-laser | ams-OSRAM **SPL PL90 / DP90_3** | 25–65 W peak | 10–25° | **Kräver diffusor + HW-strömgräns** för Class 1 | Riktig MILES använder detta; 50–150 m+, men MÅSTE diffuseras + mätas |

**Ögonsäkerhet (icke förhandlingsbar):** riktig MILES når Class 1 via korta pulser + låg pulsenergi + **divergens/diffusion** (Army-utvärdering bekräftar att sändare modifierades och om-testades). Per IEC 60825-1 måste pulsad tillgänglig energi respektera ~514 nJ/puls skalad av C5=N^(-1/4). **Designregel: HW-strömgräns (fast resistorstak, inte bara firmware) + diffusor + uppmätt AE vid aperturen.**

**Kodning — anta MilesTag II / OpenLaserTag:** 38–56 kHz modulerad bärvåg (solljus-/sabotageförsvar), pulslängdskodning (header 2400 µs + 600 µs paus; "1"=1.2 ms, "0"=0.6 ms), paket = typ + spelar-ID + team + **4-bit damage** + extended ID. **Lägg CRC + rullande nonce** ovanpå mot replay (stock MilesTag saknar krypto). Fork: `LZRTag` (ESP32) och `milesTag`-Arduino-libbet.

### 4.2 IR-detektor

| Ansats | Solljusavvisning | Hit-zon | Latens | Dom |
|---|---|---|---|---|
| **TSOP-mottagarmoduler** (Vishay TSOP382xx/48xx/75xxx, ~$1) | Utmärkt (AGC + bärvågs-bandpass) | placera många → zoner | få ms (golv ~180–260 µs) | **Bästa DIY-default** — demodulerar i kapsel |
| Rå PIN-fotodiod (BPW34, SFH 213 FA) + TIA + bandpass | Du bygger filter/AGC själv | hög (om array) | lägst | Mer jobb; bara för custom bärvåg/finare timing |

**Täckning (kopiera MILES):** hjälm-"halo" med **6–8 mottagare** utåtvinklade (360°), torso-sele med **~8–16 mottagare** grupperade i zoner (huvud/bröst/rygg/vä/hö). ±45°-delar med ≥90° mellanrum (≥4/ring); ±75° (TSOP753) minskar antal men suddar zongränser. Kill/near-miss kodas i själva paketet. Standardisera **en bärvågsfrekvens** (38/40/56 kHz) i hela systemet, emitter+mottagare matchade. Utomhushärdning: billigt 905 nm glas-bandpass (10–30 nm FWHM) eller SFH 213 FA (inbyggt dagsljusfilter) — bara värt om emittern verkligen är 905 nm.

### 4.3 IMU-uppgradering

Per SlimeVR:s publika drift-dataset: **BNO085/086** har bekväm onboard-fusion men en "snap"-bugg vid snabb rörelse och magnetometerberoende som **fallerar nära stål** — fel verktyg intill en pipa. **ICM-42688-P** har låg gyrobrus men driver. **Rekommendation: TDK ICM-45686** (~$5 chip) i **6DOF (mag av)**, gyro-ODR **≥1–2 kHz** för att fånga sub-100 ms pip-klättringsimpuls, med egen complementary/Madgwick-fusion på host → deterministisk, tunbar rekyl-loop. Dev: TDK ICM-45686 EVAL (~$99), SlimeVR Mumo-breakout (ICM-45686+QMC6309), eller generisk breakout. BNO086 (Adafruit/SparkFun Qwiic ~$25–30) endast som snabb prototyp-stopgap.

### 4.4 AR-HUD / optik (roadmap-funktion)

Riktigt genomförbart: en **micro-OLED reflekterad in i optiken** är den beprövade vägen (Revic Radikl-smartscope ~$3995, Maztech X4-FCS ~$3495 gör exakt detta). DIY-vägar:

- **Billigaste prototyp:** Sony **micro-OLED HDMI-kit (~$185, 640×400, 2400 nit)** + 45° plattstrålsplittare i 3D-printad sikteshus; rendera reticle/ammo/träffar vit-på-svart (svart = transparent genom combiner). Funkar inomhus, marginellt i starkt dagsljus.
- **Dagsljusljusstyrka utan optik-R&D:** köp **Vuzix Z100 ($499/$799 dev)** — JBD **microLED + waveguide**, genomskinlig monokrom grön HUD läsbar ute, SDK; mata reticle/ammo över BLE.
- **Öppet/hackbart:** **Brilliant Labs Frame ($349)**, öppen HW+SW, ~3000 nit micro-OLED-prisma.
- **2026+ produktionsoptik:** färg-microLED-waveguide (Vuzix/TCL CSOT) för äkta dagsljus.

**Designtips:** monokrom grön/vit-på-svart, glanceable HUD (reticle + 2–3 siffror), 640×400 räcker (billigare/ljusare). Montera display+combiner som en "fire-control"-modul klampad över optiken (Maztech-stil) snarare än att bygga om ett kikarsikte.

### 4.5 Rekommendation — IR/IMU/optik

> **Emitter:** default **SFH 4715AS (860 nm)** + diffusor (~30 m). 905 nm-laser (SPL PL90) endast som långdistansvariant **bakom HW-strömgräns + diffusor + bänkverifierad Class 1-AE**. Firmware är aldrig ögonsäkerhetsvakt.
> **Kodning:** MilesTag II/OpenLaserTag + CRC/nonce.
> **Detektor:** zonade Vishay TSOP-moduler, hjälm-halo + torso-zoner, en bärvåg systemvitt.
> **IMU:** **ICM-45686** 6DOF, gyro ≥1–2 kHz, host-side-fusion.
> **HUD:** micro-OLED-waveguide nu → färg-microLED-waveguide 2026+.

---

## Del 5 — Kamera, edge-AI & server

### 5.1 Vapenkamera

ESP32-CAM duger för PoC men brister: **rolling shutter smetar vid snabba panoreringar**, ingen HW H.264 (bandbreddstung MJPEG), endast 2.4 GHz, ingen lågljus/IR-cut, svag per-frame-tidsstämpling.

| Alternativ | Sensor/slutare | Encode | Lågljus | Latens | Not |
|---|---|---|---|---|---|
| ESP32-CAM (nuv.) | OV2640 rolling | MJPEG (SW) | dålig | 50–80 ms @VGA | ~$8, 2.4 GHz, smetar |
| **Pi Zero 2 W + Cam Module 3 (NoIR)** | IMX708 rolling, AF | HW H.264 | bra | ~100–150 ms | ~$15 + $25–35; bäst $/funktion |
| Pi Zero 2 W/CM5 + **GS-kamera** | IMX296 **global shutter** | HW H.264 | IR-cut | ~100 ms | $50; eliminerar pan-smet — idealt för AAR |
| RunCam analog 5.8 GHz | rolling, NTSC | analog | varierar | <30 ms | lägst latens, låg uppl., ingen frame-tidsstämpel |

### 5.2 Video-backhaul (16–32 cams)

- **Analog 5.8 GHz:** lägst latens men bara ~8 rena kanaler — kan inte bära 32 strömmar; endast som enstaka live-feed.
- **Digital FPV (HDZero/Walksnail/DJI O4):** punkt-till-punkt-goggle-ekosystem, dyrt/nod, ej byggt för 32 strömmar in i en server.
- **WiFi 6/6E (rekommenderas):** standard-IP, inspelningsbart, tidsstämplat. Budget H.264: 720p30 ≈ 2–4 Mbps/cam → 32 cams ≈ 64–128 Mbps. Praktik: **flera 4×4 WiFi 6/6E-APs (OFDMA/MU-MIMO), ~8–10 cams/AP**, dedikerad video-VLAN på 5/6 GHz (håll 2.4 GHz fritt). Plana ~3–4 APs för 32 noder.

### 5.3 Edge-AI

Auto-taggning av engagemangsklipp, mål-ID, lågljusförbättring är värdefullt — men gör **inferens på servern, inte på vapnet**. Behåll bara en billig rörelse-/skott-trigger på noden för att bokmärka klipp.

| Board | TOPS | Pris | Roll |
|---|---|---|---|
| Pi 5 + AI HAT (Hailo-8L/8) | 13/26 | $70–110 | per-cam edge om det nånsin behövs |
| **NVIDIA Jetson Orin Nano Super** | upp till 67 | **$249** | bäst edge-AI-värde, CUDA |
| Google Coral | 4 | ~$60 | svagare/äldre |

### 5.4 Server & telemetristack

- **Host:** en modern **Ryzen mini-PC** (32 GB, NVMe) kör fusion + adjudikation + DB + dashboard i realtid. N100/N150 räcker om AI offloadas. Undvik moln i den heta loopen.
- **Ingest:** MQTT (Mosquitto/EMQX).
- **TSDB:** **TimescaleDB** (Postgres-extension) för blandad snabb-telemetri + relationell sessionsdata; InfluxDB 3 om rå ingest-rate dominerar.
- **Dashboard:** Grafana för analys + custom websocket-app för live-karta/adjudikationsoverlay.
- **Klocksynk:** PTP på trådbunden backbone, chrony/NTP till vapen-Pis; tidsstämpla varje frame + hit.

### 5.5 Rekommendation — Kamera/AI/server

> **Cam:** Pi Zero 2 W + Cam Module 3 NoIR (standard); GS IMX296-variant för primärvapen. ESP32 kvar som skott/hit/trigger-sensor.
> **Backhaul:** dedikerad WiFi 6E video-VLAN, 3–4×4×4-APs.
> **AI:** centralt på servern + **Jetson Orin Nano Super ($249)** som AI-coprocessor.
> **Server:** Ryzen mini-PC; MQTT → TimescaleDB → Grafana + websocket-karta; PTP+chrony.

---

## Del 6 — Rekyl, kraft & NFC

### 6.1 Rekylaktuator

- **Beprövad DIY-väg:** airsoft **reciprocerande massa** (Tokyo Marui Next Gen Recoil Shock-stil) ger realistisk muzzle-flip via en elektriskt cyklad vikt — kommersiellt mogen och hackbar.
- **Alternativ:** solenoid (enkel, hård "smäll", hög toppström, dålig termisk uthållighet vid 12 Hz), **voice-coil** (rätt fysik men off-the-shelf VCA med 30 mm slag + nog kraft för 0.12 kg är stora/dyra → opraktiskt för DIY), BLDC-svänghjul/kam med **FOC-driver** för programmerbar felt-recoil-skalning per vapenprofil.
- **Bästa DIY-praktiska valet enligt research: BLDC + vev/kam-reciprokation driven av en ODrive S1 (~$149, 12–48 V, 40 A kont., closed-loop FOC).** 12 Hz = 720 RPM är trivialt; vevradien sätter 30 mm-slaget, intensiteten tunas i firmware (RPM/acceleration/vridmomentstak). Budgetvariant: SimpleFOC Mini eller ST B-G431B-ESC1 (~$20–30). **Snabb prototyp/fallback:** hobby push-pull-solenoid (~$15–25) + MOSFET för att validera känslan på en helg. **Genväg:** skörda en Tokyo Marui NGRS-rekylmotor (~$400–550 donator) — färdig reciprocerande massa, men borstad motor utan FOC-tuning.

### 6.2 Högströmsväxling (rekylskenan, ~20 A peak)

- **Integrerad eFuse (rekommenderat): TI TPS25983** (2.7–26 V, **20 A**, 2.7 mΩ) — soft-start/inrush, OC/SC, termisk avstängning och omvänd-ström-blockering i ett chip. Sätt strömgräns + fault-timer **över** 20 A-toppen så legitima pulser inte nuisance-trippar. Alternativ: Infineon PROFET high-side för fordonsklassat omvänt-polskydd.
- **Diskret variant:** modern sub-mΩ logic-level-MOSFET (Infineon OptiMOS, t.ex. IAUA250N04S6N005 ~0.55 mΩ — IRLZ44N:s 22 mΩ ger ~9 W vid 20 A) + **snabb Schottky-flyback (SS54-klass, hellre 10–20 A)** eller TVS-clamp (SMBJ15A) för snappare ankarretur + low-ESR cap-bank (READMEns 2×2200 µF, gärna 3–6×1000 µF låg-ESR Panasonic FR + MLCC nära lasten). Driv ev. via hot-swap-controller **TPS24700/24701** för cold-mate-kontakten.
- Behåll READMEns princip: skenan på **endast mellan "rack" och "mag release"** → kontakterna bryts aldrig under last.

### 6.3 Batteri & BMS

- **Cell:** gå från löst "≥25C LiPo" till definierade högdräneringsceller: **Molicel P45B** (21700, 4500 mAh) eller **P42A** (4200 mAh), båda ~45 A — 20 A är bara ~0.5C, stor termisk marginal. Cylindriska är robustare/utbytbara/dock-laddbara vs mjuka LiPo-pouchar (LiPo vinner dock på spänningsstyvhet under burst). 2S–4S sätter spänning; gå 2P för mindre per-cell-stress.
- **Fuel gauge:** för pack-SOC (2S–4S) är **TI BQ34110** (till 65 V/32 A) den enda multicell-gaugen; för enkelcellsövervakning är **MAX17260** (ModelGauge m5, noll-config) bäst — undvik BQ27427 (integrerad 7 mΩ shunt → ~2.8 W vid 20 A).
- **BMS:** **TI BQ76952** (3–16S, hög-side-FET-drive, programmerbara OCD/SCD-delays som rider ut pulsade 20 A, autonom balansering) eller billigare **BQ76920** (3–5S). Undvik billiga DW01-protect-only-kort (underdimensionerade FET, ingen balansering/telemetri, nuisance-trippar på pulser). **Ammo-räkning och laddning är separata storheter** (README:n har rätt) — dockan = långsam BMS-cykel, NFC-omskrivning = snabb; rotera en pool av magasin.
- **Laddningsdocka:** per-bay charger-IC (**BQ25887** ger 2S med inbyggd cellbalansering; **BQ25731** för 3–4S + extern AFE), NTC på charger-TS-pin (JEITA hård-cutoff) + digital **TMP1075** (32 I²C-adresser, ~$0.46) per bay för telemetri, brandsäker zon (README:ns största brandrisk).

### 6.4 NFC / RFID

| Del | Roll | Not |
|---|---|---|
| NTAG215 (nuv.) | passiv tagg | billig men **klonbar** — svag mot fusk |
| **NTAG424 DNA** | passiv tagg + **AES-128 SUN** | dynamisk autentisering/anti-klon i HW; uppgradering mot fusk |
| PN532 (nuv. läsare) | I²C/SPI | enkel, Arduino-vänlig, kort räckvidd |
| **PN5180 / ST25R3916** | läsare | längre räckvidd, bredare tagg-stöd — snabbare/säkrare mag-detektering |

### 6.5 Rekommendation — Rekyl/kraft/NFC

> **Rekyl:** reciprocerande massa (airsoft-stil) + PWM-skalning nu; voice-coil/BLDC-FOC som per-profil-uppgradering.
> **Växling:** integrerad **eFuse/smart high-side-switch** med soft-start, behåll cold-mate-sekvensering.
> **Batteri:** **Molicel P42A/P45B** + **BQ27**-fuel-gauge + balanserande BMS; brandsäker laddningsdocka.
> **NFC:** uppgradera tagg till **NTAG424 DNA (AES/SUN)** mot klon/fusk, läsare till **PN5180/ST25R3916**; behåll HMAC + server-side-spegling.

---

## Del 7 — Säkerhet & "fairness/anti-cheat" (tvärgående)

Eftersom adjudikationen är central och spelet kompetitivt är detta ett eget spår:

- **Ögonsäkerhet i HW** (Del 4) — strömstak i resistor, inte firmware.
- **IR anti-replay** — CRC + rullande nonce/sekvens ovanpå MilesTag (Del 4.1).
- **NFC anti-klon** — NTAG424 DNA SUN + HMAC + server-side-mirror per mag-ID (Del 6.4).
- **Tidsintegritet** — PTP + HW-tidsstämplad IR-ankomst (Del 2.3) så träffordning inte kan manipuleras via nätverksjitter.
- **LiPo-säkerhet** — BMS, balansering, termisk övervakning, brandsäker docka (Del 6.3).

---

## Del 8 — Vad som saknas i repot (konkreta nästa steg)

1. Skapa `docs/strilas-systemritning.html` (eller byt referensen) — länkas men finns inte.
2. Lägg upp mappskelettet (`firmware/`, `server/`, `hardware/`, `profiles/`, `config/example.env`) så build-instruktionerna stämmer.
3. Definiera designmål för **spelarantal** (t.ex. 16–32) — dimensionerar radio/server/anchors.
4. Specificera **IR-kodningsprotokollet** explicit (MilesTag II-derivat + CRC/nonce).
5. Specificera **UWB-läge** (TDoA) och **tidssynk-budget** (sub-ms).

---

## Del 9 — Prioriterad uppgraderingsroadmap & referens-BOM

### 9.1 Roadmap (effekt vs insats)

| Prio | Uppgradering | Varför | Insats |
|---|---|---|---|
| **1** | Dela compute/radio: **ESP32-P4+C6** (ev. + RP2350 IO-coprocessor) | Tar bort timingjitter i den tidskritiska vägen | Medel |
| **1** | **PTP + HW-tidsstämplad IR-ankomst** | Rättvis, manipuleringssäker adjudikation | Medel |
| **2** | IMU **BNO085 → ICM-45686** (6DOF, ≥1 kHz) | BNO085 är EOL + fallerar på snabba metallnära transienter | Låg |
| **2** | Radio **ESP-NOW → 5 GHz WiFi 6 (OFDMA)** + Thread-mesh | Skalar till 32 noder + videobackhaul | Medel |
| **2** | UWB i **TDoA** (Makerfabs MaUWB / Qorvo DWM3000 / NXP SR150) | Skalar till många taggar, sub-30 cm | Medel–hög |
| **3** | IR-kodning **MilesTag II + CRC/nonce**; emitter **860 nm SFH 4715AS** default | Solljus-/sabotagerobust + säkrare default | Låg–medel |
| **3** | Kamera **ESP32-CAM → Pi Zero 2 W + Cam Module 3** | Tidsstämplad HW-H.264, lågljus, ingen pan-smet | Medel |
| **3** | Server: **Ryzen mini-PC** + MQTT + TimescaleDB + Grafana/websocket | Realtidsfusion/adjudikation/DB/karta för 32 noder | Medel |
| **4** | NFC **NTAG215 → NTAG424 DNA**, läsare **PN5180/ST25R3916** | Anti-klon/fusk, snabbare detektering | Låg |
| **4** | Kraft: **eFuse smart-switch** + **Molicel P42A/P45B** + BQ27/BMS | Robustare högströmsväxling + batterimarginal | Medel |
| **5** | AR-HUD: micro-OLED-waveguide → microLED 2026+ | Roadmap-funktion, reticle/ammo i optiken | Hög |
| **5** | Edge-AI: **Jetson Orin Nano Super** för auto-tagg/mål-ID | AAR-automation | Medel |

### 9.2 State-of-the-art Nivå-3-BOM (2025–2026)

Uppdaterad för **nivå 3** (geometrisk ballistik-adjudikation): UWB/GNSS/kropps-IMU/server/tidssynk är nu **kärna**, inte bonus. Senaste 2025–2026-delar.

**Vapennod**

| Subsystem | **State-of-the-art** | ~Pris | Not |
|---|---|---|---|
| Hjärna | **ESP32-P4 PICO** (P4 + C6) | ~$24 | dual-core, MIPI-CSI/DSI, H.264, ljud, WiFi6 ombord |
| Radio-uplink | **ESP32-C5** (dual-band **5 GHz** WiFi 6) där 5 GHz krävs | ~$15 | C6 (2.4 GHz) räcker annars |
| IMU (pose) | **TDK ICM-45686** (ev. **2–4 i array** → √N-brus) | ~$5/st | array = billig pose-vinst; tactical: ADIS16470 ($300–400) |
| UWB | **Qorvo DWM3001CDK / QM33110W** (tagg, TWR/TDoA) | ~$32 | AoA-ankare separat (infra) |
| IR-emitter (**samboresiktad ring**) | **ams-OSRAM SFH 4715AS (860 nm)** **×4 i kvadrat runt sikteskameran**, lensad, 3 A puls | ~$3/st | samaxlig med kameran → "det kameran siktar på = dit IR går"; dubblar som **aktiv fiducial-konstellation** (känd kvadrat → 6DoF-PnP för observerande kameror, funkar i mörker); större apparent källa → **lättare Class 1** |
| **Sikteskamera + edge-AI** (fuserad pose-väg, uppgradering, se ⓥ) | **P4 MIPI-CSI** (dag) / **thermal** (mörker) + ArUco-läsning, **centrerad i emitter-ringen** | $25–200 | bäring + zon + ID optiskt (HITS/TrackingPoint-vägen) |
| Avståndsmätare (valfri) | **Benewake TF02-Pro LiDAR** | ~$45 | metrisk räckvidd lokalt (kamera ger bäring, ej räckvidd) |
| NFC | **NTAG424 DNA** + **ST25R3916** | ~$1 + $20 | anti-klon/fusk |
| Rekyl | **BLDC + vev + ODrive S1** FOC | ~$149 | per-profil-kraft |
| Rekylväxling | **TI TPS25985** (80 A stapelbar eFuse) + SS54 + cap-bank | ~$5 | nyare/kraftigare än TPS25983 |
| HUD | micro-OLED-waveguide → **microLED-waveguide** 2026 | $185+ | reticle/avstånd i optiken |

**Väst/hjälm-nod**

| Subsystem | **State-of-the-art** | ~Pris |
|---|---|---|
| MCU | **ESP32-C5** (5 GHz WiFi6 + BLE + 802.15.4/Thread) | ~$15 |
| Detektorer | **Vishay TSOP4856** (56 kHz) ×16–24, zonade | ~$1/st |
| Kropps-IMU (pose) | **TDK ICM-45686** (postur stå/huk/ligg) | ~$5 |
| UWB-tagg | **DWM3001CDK / QM33110W** | ~$32 |
| **Fiducial (för kamera-pose)** | ArUco/AprilTag-mönster på väst+hjälm | ~$0 | ger ID + 6DoF-pose till sikteskameran |
| Feedback | WS2812 + haptik + I²S-ljud | ~$12 |

**Magasin:** **Molicel P50B** (21700, 5000 mAh, ~45–60 A — nyaste/bästa) + **BQ76952**-BMS + **BQ34110**-gauge + NTAG424. ~$10–14/st.

**Infrastruktur**

| Del | **State-of-the-art** | ~Pris |
|---|---|---|
| UWB-ankare (AoA) | **Qorvo QM35825** (4-antenn AoA, ±5 cm/±2°, IEEE 802.15.4-2024) ×4–8 | DK ~$599 |
| GNSS-rover (ute) | **u-blox ZED-X20P** (all-band L1/L2/L5/L6) | ~$281 |
| GNSS-heading-ankare | **u-blox ZED-X20D** dubbelantenn (**~0,1° yaw**) — *vapen-pose-ankaret* | board-pris |
| GNSS-bas (anti-jam) | **Septentrio mosaic-X5** (OSNMA/AIM+) | ~$500+ |
| Server | **Jetson Orin NX 16GB** (100 TOPS, NVDEC/NVENC 16–32 strömmar) | ~$599 |
| Server (budget) | **Jetson Orin Nano Super** (67 TOPS) | $249 |
| Nätverk | **WiFi 7-AP** (MLO 5/6 GHz) + ESP32-C5-noder på 5 GHz | $300–600 |
| Laddningsdocka | **BQ25756** (snabb) / **BQ25798** (MPPT-sol/USB-PD) per bay | — |

> **ⓥ Vapen-pose — systemets nyckelgräns (BESLUT: fuserad, alla lager samverkar):**
> 1. **ICM-45686-array** — hög-rate tilt/attityd (√N-brus).
> 2. **GNSS-dubbelantenn-heading (ZED-X20D, ~0,1°)** — absolut yaw som binder IMU-driften (ute).
> 3. **IR-stråle** — LOS-grind + heading-ankare + zon + ID, robust i allt ljus (behålls oavsett).
> 4. **Sikteskamera + edge-AI + fiducials (HITS/TrackingPoint-vägen)** — optisk bäring (~2 mrad), zon & ID ur bilden; vassast, kräver compute på/nära vapnet + degraderar i mörker (→ thermal). **Uppgradering.**
> *Tactical IMU ADIS16470 (8°/hr, $300–400) = dyrt high-end-alternativ till lager 1.*
>
> **Emitter-ring-knepet:** de 4 IR-emittrarna sitter i en kvadrat **runt kameralinsen** → fire-strålen blir *samaxlig* med kamerans optiska axel (siktbäring = IR-bäring), och samma 4 emittrar utgör en **aktiv fiducial-konstellation** som andra kameror kan PnP-pose:a på i mörker. Se [`system-flowchart.md`](system-flowchart.md) §emitter-ring.

---

## Del 10 — Valda dev boards (projektbeslut)

**Strategibeslut:** bygg Fas 1 direkt på Fas 2/nivå-3-plattformen — slipp firmware-port och få nivå-3-gränssnitten "vilande" från dag ett.

| Kort | Roll | Senaste-teknik-not |
|---|---|---|
| **ESP32-P4 PICO** (P4 + C6) | **Vapenhjärna** | MIPI-CSI-kamera + H.264 + DSI + ljud + WiFi6 ombord; ~$24 |
| **ESP32-C5** | **Väst/hjälm + 5 GHz-uplink** | dual-band WiFi6 (2025) — slår C6 för uplink; behåller Thread |
| **Qorvo QM35825** (DK) | **UWB-ankare (AoA)** | 4-antenn ±2°/±5 cm, IEEE 802.15.4-2024, integrerad M33 |
| **Qorvo DWM3001CDK** | **UWB-tagg** | billig FiRa TWR/TDoA-nod (~$32) |
| **u-blox ZED-X20P + ZED-X20D** | **GNSS-rover + heading-ankare** | all-band; X20D ger ~0,1° pose-yaw |
| **TDK ICM-45686** | **Pose-IMU** | fortf. klassledande (2025–26); array för √N-vinst |
| **Jetson Orin NX 16GB** | **Server/adjudikation/AI** | 100 TOPS + NVDEC/NVENC för 16–32 cam-strömmar |
| **ESP32-P4-NANO** | **Bas-dock / gateway** | RJ45/PoE/USB-host |
| **WitMotion IWT603** | **IMU-prototyp** → ICM-45686 | snabb bänkvalidering |

**Avvägning:** den verkliga risken (och kostnaden) ligger i **vapen-pose- & positionsnoggrannhet** — samma som primes. Därför är GNSS-heading-ankaret (X20D) + IMU-array (eller kamera/AI) den viktigaste state-of-the-art-investeringen, inte en snabbare MCU.

---

## Källor (urval)

**Compute/nätverk:** [ESP32-P4 vs S3 (Elecrow)](https://www.elecrow.com/blog/who-is-the-true-performance-king-esp32-p4-vs-esp32-s3.html) · [ESP32-P4-WIFI6 (Waveshare)](https://www.waveshare.com/wiki/ESP32-P4-WIFI6) · [ESP32-C5 dual-band $15 (CNX)](https://www.cnx-software.com/2025/04/30/esp32-c5-mass-production-esp32-c5-devkitc-1-board/) · [RP2350 PIO (Geerling)](https://www.jeffgeerling.com/blog/2024/raspberry-pi-pico-2-rp2350-adds-more-pio-risc-v-cores/) · [Teensy 4.1 (PJRC)](https://www.pjrc.com/store/teensy41.html) · [nRF54L15 (CNX)](https://www.cnx-software.com/2025/09/03/nrf54l15-connect-kit-a-compact-bluetooth-6-0-le-802-15-4-and-nfc-development-board/) · [ESP-NOW (Espressif)](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/network/esp_now.html) · [ESP1588 PTP](https://github.com/leifclaesson/ESP1588)

**Positionering:** [Qorvo DWM3000 (store)](https://store.qorvo.com/products/detail/dwm3000-qorvo/681949/) · [Makerfabs MaUWB_ESP32S3](https://www.makerfabs.com/mauwb-esp32s3-uwb-module.html) · [NXP SR150](https://www.nxp.com/products/SR150) · [NXP SR040](https://www.nxp.com/products/wireless-connectivity/trimension-uwb/trimension-sr040-reliable-uwb-solution-for-iot:SR040) · [Murata Type2BP EVK (Mouser)](https://www.mouser.com/ProductDetail/Murata-Electronics/LBUA0VG2BP-EVK-P) · [TDoA vs TWR (Inpixon)](https://www.inpixon.com/blog/uwb-localization-tdoa-vs-twr) · [u-blox ZED-F9P](https://www.u-blox.com/en/product/zed-f9p-module) · [ZED-F9R](https://www.u-blox.com/en/product/zed-f9r-module) · [GNSS/UWB/IMU fusion EKF/FGO/PF (arXiv 2512.10480)](https://www.arxiv.org/abs/2512.10480)

**IR/IMU/optik:** [ams-OSRAM SFH 4715AS](https://look.ams-osram.com/m/3a147ddac0391319/original/SFH-4715AS.pdf) · [SPL DP90_3 905 nm](https://ams-osram.com/products/lasers/ir-lasers-eel/osram-ir-laser-diode-spl-dp90-3) · [IEC 60825-1](https://webstore.iec.ch/en/publication/3587) · [Army MILES laser-safety (OSTI)](https://osti.gov/biblio/793320-laser-safety-evaluation-miles-mini-miles-laser-emitting-components) · [OpenLaserTag protokoll](https://openlasertag.org/language/en/openlasertag-ir-communication-protocol/) · [MilesTag II spec](https://wiki.cuvoodoo.info/lib/exe/fetch.php?media=ir-cock-grenade:mt2proto.pdf) · [LZRTag](https://hackaday.io/project/160804-lzrtag-flexible-diy-lasertag) · [Vishay TSOP382](https://www.vishay.com/docs/82491/tsop382.pdf) · [SlimeVR IMU-jämförelse](https://docs.slimevr.dev/diy/imu-comparison.html) · [TDK ICM-45686 (DigiKey)](https://www.digikey.com/en/products/detail/tdk-invensense/ICM-45686/24374985)

**Kamera/AI/server:** [Pi-kameraguide](https://thinkrobotics.com/blogs/learn/raspberry-pi-camera-module-comparison-complete-2025-guide) · [GS-kamera (Geerling)](https://www.jeffgeerling.com/blog/2023/testing-raspberry-pis-new-global-shutter-camera/) · [Jetson Orin Nano $249](https://videocardz.com/newz/nvidia-launches-jetson-orin-nano-developer-kit-at-249-mini-pc-for-developers) · [TSDB-jämförelse](https://www.tigerdata.com/blog/timescaledb-vs-influxdb-for-time-series-data-timescale-influx-sql-nosql-36489299877) · [PTP (Teledyne)](https://www.teledynevisionsolutions.com/learn/learning-center/machine-vision/precision-system-synchronization-with-the-ieee-1588-precision-time-protocol-ptp/)

**Rekyl/kraft/NFC:** [TI smart eFuse](https://www.ti.com/product-category/power-management/high-side-switches-controllers/smart-efuse/overview.html) · [Infineon eFuses](https://infineon.com/products/power/smart-power-switches/efuses) · [Molicel P42A](https://www.18650batterystore.com/products/molicel-p42a) · [Molicel P45B](https://imrbatteries.com/products/molicel-p45b-21700-4500mah-45a-battery) · [NXP NTAG424 DNA](https://www.nxp.com/products/rfid-nfc/nfc-hf/ntag-for-tags-and-labels/ntag-424-dna-424-dna-tagtamper-advanced-security-and-privacy-for-trusted-iot-applications:NTAG424DNA) · [ST25R3916 (Elechouse)](https://www.elechouse.com/product/st25r3916_nfc_reader/) · [Tokyo Marui NGRS (Evike)](https://www.evike.com/products/56862/)

**Senaste teknik (2025–2026):** [Qorvo QM35825 (4-antenn AoA)](https://www.qorvo.com/products/p/QM35825) · [QM35825DK-05 (DigiKey ~$599)](https://www.digikey.com/en/products/detail/qorvo/QM35825DK-05/26742402) · [Qorvo DWM3001CDK](https://www.digikey.com/en/products/detail/qorvo/DWM3001CDK/24367348) · [NXP SR250 (UWB-radar+AoA)](https://www.cnx-software.com/2024/09/20/nxp-trimension-sr250-short-range-uwb-radar-supports-secure-ranging-for-smart-homes-and-industrial-iot/) · [u-blox ZED-X20P](https://www.u-blox.com/en/zed-x20p) · [ZED-X20D heading (Inside GNSS)](https://insidegnss.com/u-blox-introduces-zed-x20d-gnss-heading-module-for-mass-market-high-precision-applications/) · [Quectel LG290P quad-band](https://www.cnx-software.com/2024/07/30/quectel-lg290p-world-first-quad-band-gnss-module-l1-l2-l5-and-e6/) · [Septentrio mosaic-X5](https://www.septentrio.com/en/products/gnss-receivers/gnss-receiver-modules/mosaic-x5) · [ADI ADIS16470 (tactical IMU)](https://www.analog.com/en/products/adis16470.html) · [Jetson Orin NX / AGX Orin](https://www.hackster.io/news/nvidia-launches-275-tops-jetson-agx-orin-developer-s-kit-at-1-999-bbb5ff80e050) · [Jetson Thor T5000](https://nvidianews.nvidia.com/news/nvidia-blackwell-powered-jetson-thor-now-available-accelerating-the-age-of-general-robotics) · [ESP32-C5 (5 GHz WiFi6)](https://www.cnx-software.com/2025/04/30/esp32-c5-mass-production-esp32-c5-devkitc-1-board/) · [WiFi 7 / MLO (Meraki)](https://documentation.meraki.com/Wireless/Design_and_Configure/Architecture_and_Best_Practices/Wi-Fi_7_(802.11be)_Technical_Guide) · [Molicel P50B vs P45B](https://www.aboutenergy.io/post/molicel-p50b-vs-p45b-key-differences-specifications) · [TI TPS25985 (80 A eFuse)](https://www.ti.com/product/TPS25985) · [TI BQ25798 (MPPT-sol)](https://www.ti.com/product/BQ25798)

**Kamera/AI-pose (HITS/TrackingPoint-vägen):** [BAE HITS (ION 2020)](https://www.ion.org/publications/abstract.cfm?articleID=17741) · [TrackingPoint](https://en.wikipedia.org/wiki/TrackingPoint) · [Lockheed SIMRES](https://www.lockheedmartin.com/en-us/products/simres.html) · [ArUco-markörer (OpenCV)](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html) · [Benewake TF02-Pro LiDAR](https://en.benewake.com/TF02Pro/)

---

*Underlagsrapport för STRILAS. Säkerhetsbegränsningarna (IR Class 1 i HW, cold-mate-kontakter, BMS-laddning) är icke förhandlingsbara i varje hårdvaruändring — i linje med README:ns bidragsregler.*
