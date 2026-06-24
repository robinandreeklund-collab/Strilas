# STRILAS — egen ESP i hjälmen? (ja) + högtalare/kom

> Figur: [`spelare-topologi.png`](spelare-topologi.png)

## Svar: JA — ge hjälmen en egen ESP, trådlöst mot västen
Skäl (ärligt):
1. **Ingen kabel hjälm↔väst.** En kabel över nacken snor sig, går av och låser huvudrörelsen.
   Egen ESP + litet batteri i hjälmen → helt fristående, ren UX.
2. **Högtalare + mik hör hemma i hjälmen** (vid öron/mun). Med egen ESP drivs ljudet lokalt och
   skickas över radio → ingen ljudkabel ner till västen.
3. **GNSS sitter redan i hjälmen** (bäst sky-view) → läses lokalt och skickas vidare, inte rå-data
   genom en kabel.

## Vad hjälm-noden blir
ESP + litet LiPo · **8× TSOP4856** (360° huvud-träff) · **4× 860 nm**-konstellation (högt på ringen)
· **GNSS** · **I²S-ljud: liten förstärkare + högtalare + MEMS-mik** (spelljud + lagröst) · WiFi6/ESP-NOW.

## Frame-sync är INTE ett problem
Man kan tro att hjälmens och västens konstellation måste blinka exakt synkat. Det behövs inte:
**huvudet och torson är separata stela kroppar** (nacken rör sig) → skyttens kamera kör PnP på dem
**var för sig** ändå (torso-pose + huvud-pose). Varje grupp blinkar sitt eget ID-kodade mönster och
kameran frame-differensar dem oberoende. Hjälmen kan alltså vara helt självständig.

## ESP-val för hjälm-noden
- **ESP32-S3** — bäst för **ljud/röst** (dubbelkärna, beprövat audio-ekosystem, Opus-codec). WiFi4+BLE.
- **ESP32-C6** — om du vill hålla **WiFi6/BLE**-familjen genomgående och ljudet är lätt (enkel codec).
- Båda parar trådlöst med vapnets P4 och väst-C5 (samma Espressif-stack). **Rekommendation: S3** om
  röst-comms är en huvudfunktion; annars C6.

## Per-spelare-topologi (uppdaterad)
| Nod | MCU | Jobb | Länk |
|---|---|---|---|
| Vapenlåda | ESP32-P4-WIFI6 | kamera·IR·sikte/ballistik | WiFi6/ESP-NOW |
| Väst-nod | ESP32-C5 | 10 patchar·hit-zoner·konstellation | WiFi6/ESP-NOW |
| **Hjälm-nod** | **ESP32-S3/C6** | head-TSOP·GNSS·**högtalare+mik** | WiFi6/ESP-NOW |
| Magasin | (passiv) NFC + rekyl-batt | ammo + rekylström | magwell (fysiskt) |

## Pris att betala (ärligt)
- **Fler batterier att ladda:** huvud (vapen) + rekyl (magasin) + väst + hjälm = 4/spelare.
  Mildra med en **gemensam laddningsdocka** (håller alla fyra). Väst-/hjälm-batterierna är små
  (lågeffektsnoder) → lång drifttid.
- En radio till + en ljud-kedja → lite mer kostnad/komplexitet, men löser kabel + comms på köpet.

## TL;DR
Egen ESP i hjälmen = **rätt val**: slipper nack-kabeln och får högtalare/röst-comms trådlöst på köpet.
Frame-sync är inget hinder (huvud/torso är separata pose-kroppar ändå). Välj **S3** för seriöst ljud,
annars **C6**. Priset är ett extra litet batteri per spelare — lös med gemensam laddningsdocka.

---

## Byggt kort (2026-06): komplett hjälm-nod
Ø100 mm, **4-lager** (In1=GND-plan, In2=VBAT-plan), routad **rent** (0 oroutade · 0 clearance · 0 oconnected).
Netlista: `hardware/helmet_netlist.py` · placering: `hardware/receiver_place.py` (helmet) · route: `hardware/route_helmet.py`.

**Arkitektur (verifierad mot datablad):**
- **2S-batteri** (laddas i docka) → **AP63203** synk-buck (TSOT23-6, 3.8–32 V in, 2 A; FB-delare 31.6k/10k → 3.33 V).
  Buck-3V3 matar XIAO via dess 3V3-stift + alla sensorer/GNSS/mik/audio. Konstellations-LED:erna drivs DIREKT från 2S.
- **Stackad ESP: XIAO ESP32-S3** (2× 1×7 sockel, centrum) — matas från kortets 3V3, programmeras via egen USB-C.
  GPIO: D0=DATA, D1=LED_EN, D2/D3=I²S BCLK/LRCK, D4=I²S→amp, D5=I²S←mik, D6/D7=GNSS UART, D9=amp SD.
- **8× TSOP4856** (940 nm skott-RX, utåt på ringen, 360°) → 8× BAT54 diod-OR → DATA (3,3 V-logik, 10k pullup).
- **4× SFH4715AS** 860 nm-konstellation (mellan TSOP-paren) + AO3400-driver (10R 2512, blink-modulerad) ← LED_EN.
- **GNSS:** ATGM336H-5N-modul (egen antenn) på 1×5-header → XIAO-UART.
- **I²S-ljud:** MAX98357A-amp-breakout (1×7 + högtalare) + I²S-MEMS-mik-breakout (1×6) → röst/spelljud.

**Köps separat (pluggas på header):** XIAO ESP32-S3, ATGM336H-GNSS-modul, MAX98357A-amp-breakout + högtalare,
I²S-MEMS-mik-breakout, 2S-LiPo. **NextPCB monterar** allt ytmonterat (buck, TSOP, LED, BAT54, NFET, R/C/L);
TH-headers/sockets (J1–J6) löder du själv. Underlag: `nextpcb/helmet-bom.xls` + `helmet-centroid.xls` + `helmet-halo-gerbers.zip`.

**Kvarstår (bänk):** buck-utgång 3,3 V verifieras innan ESP plugg; I²S audio + GNSS-fix bekräftas; konstellations-duty ≤50 %.

---

## v2 (2026-06): hjälm-MODERKORT + distribuerade patchar (ersätter platta ringen)
Den platta hjälm-ringen är **pensionerad**. Hjälmen blir nu som västen: **4 lösa dubbel-aim-patchar**
(front/bak/vä/hö, kardborre, samma patch som västen) + ett **centralt hjälm-moderkort** ("holo"-kortet).

**Hjälm-moderkort** (`hardware/helmet_mb_netlist.py`, 80×62 mm 4-lager, routat rent 0/0/0):
- **XIAO ESP32-S3** (Seeed, samma som väst-moderkortet → enkel sourcing), matas från kortets 3V3.
- **2S → AP63203-buck → 3,3 V** (XIAO + 165 + IMU + TSOP). LED-konstellation på VBAT.
- **ZED-F9P RTK-puck** (8-pol JST GH): cm-RTK + IST8310-kompass + antenn, matas VBAT (3–9 V), UART+I²C.
- **IIM-42653 IMU** (I²C, delar F9P-bussen + 1 INT) → **GNSS/INS-fusion** (bättre RTK, överbryggar
  multipath/skugga) + **lokal huvud-attityd**. Samma IMU som optik/fire-control.
- **4 egna TSOP4856** (ledade, ben böjs/sprids i diagonal-vinklar som kompletterar de 4 patcharna)
  → diod-OR → 1 DATA. Plus 4 patch-DATA → alla 5 läses via **74HC165** (SPI, sparar GPIO).
- **2 topp-konstellations-LED** (860 nm) + driver (LED_EN broadcast → patchar + topp-LED).
- 4 patch-kontakter (1x5: VBAT·GND·DATA·LED_EN·3V3) + 2S-batteri-JST.
- GPIO (XIAO 11): UART2 + I²C2 + IMU_INT1 + LED_EN1 + 165(SCK/MISO/LD)3 = **9 (2 reserv)**.

**Ljud (talcomms):** ryms INTE på XIAO:n samtidigt med F9P+IMU+9 mottagare (I²S = 4 GPIO till). Utelämnat
i v2; vill man ha tal-comms i hjälmen krävs en större ESP eller att man offrar nåt — separat beslut.

**Köps separat / kund-lödda:** XIAO-S3, ZED-F9P-puck, 4 patchar, 2S-LiPo. NextPCB monterar all SMD
(buck, 165, IMU, F9P-GH-kontakt, BAT54, LED, R/C/L); ledade TSOP + 2.54-kontakter/sockets löder du själv.
Underlag: `nextpcb/helmet-mb-bom.xls` + `helmet-mb-centroid.xls` + `helmet-mb-gerbers.zip`.

**Kvarstår (bänk):** buck-3,3 V innan XIAO · F9P UART+I²C + IST8310 + IIM-42653 på samma I²C (adresser:
IST8310 0x0E, IIM-42653 0x68 — ingen krock) · GNSS/INS-fusion-firmware · 165-läsning · LED_EN-broadcast.

---

## v3 (2026-06): ESP32-C6-devkit + HÖGTALARE/MIK (ersätter XIAO-versionen)
Bytte nod-ESP **XIAO-S3 → ESP32-C6-DevKitC-1** (Waveshare N16, electrokit) på hjälm-moderkortet —
samma byte görs på väst-moderkortet (enkel sourcing, WiFi6 genomgående).

**Varför C6:** WiFi 6 (matchar vapnets ESP32-P4-WIFI6 → bättre mesh/latens) + **23 GPIO** → nu ryms
**ljud (högtalare + mik)** för träff-feedback, OCH vi slopar 74HC165:an (alla 5 DATA läses direkt på GPIO).
Avvägning: större kort (96×76 mm) och C6 single-HP-core (räcker för feedback-ljud + enkel röst; tung
voice-codec skulle föredra S3). Mik+högtalare ENBART på hjälmen; västen = vibratorer (haptik).

**Hjälm-mb v3** (`hardware/helmet_mb_netlist.py`, 96×76 4-lager, routat rent 0/0/0):
- ESP32-C6-DevKitC-1 (2× 1x16-sockel), matas 3V3, WiFi6. GPIO: UART2 + I²C2 + IMU_INT1 + LED_EN1 +
  5 DATA + I²S4 + amp_SD1 = 16 av 23 (reserv kvar). Strapping GPIO8/9/15 + USB GPIO12/13 undvikna.
- 2S → AP63203-buck 3,3V. ZED-F9P RTK-puck (8-pol GH, UART+I²C). IIM-42653 IMU (I²C delad + INT).
- 4 egna TSOP4856 (ledade, diagonal-aim) → diod-OR. 4 patch-DATA. 2 topp-LED + driver.
- **LJUD:** MAX98357A-amp-breakout (1x7 + högtalare) + I²S-MEMS-mik-breakout (1x6).
- 4 patch-kontakter (1x5) + 2S-batteri. Deliverables: `nextpcb/helmet-mb-bom/centroid/gerbers/STEP`.

## v4 (2026-06): ESP32-P4-WIFI6 — SAMMA kort överallt (ersätter C6-devkiten)
Användaren: *"varför kan jag inte bara köra samma som på vapnet? p4 c6? … mycket lättare att
underhålla med samma kort överallt."* → båda moderkorten kör nu **exakt samma ESP32-P4-WIFI6**
(Waveshare) som vapnets optikmodul. En enda ESP-source genom hela systemet, WiFi6 genomgående.

**Hjälm-mb v4** (`hardware/helmet_mb_netlist.py`, **RUND Ø97 mm** 4-lager, routat rent 0/0/0):
- **Rund skiva** (önskemål): P4 central horisontell; 4 TSOP radiellt utåt på ringen (NÖ/NV/SV/SÖ,
  360° huvudtäckning); **6 sido-emitterande konstellations-LED på 90°-vinklade LED-tab-micro-PCB (right-angle fot)** (D5–D10,
  fria azimut-gluggar i kransen); 8 kontakter + 4 monteringshål i de glesaste gluggarna runt kransen;
  buck/IMU/LED-driver i crescents (serie-R R5–R7 SMD, R7 i den fria kanalen mellan P4-socklarna).
- **F9P-puck monteras DIREKT på kortets centrum** (BDLX ZED-F9P, rund Ø55, höjd 55 mm, IST8310-kompass,
  inbyggd antenn). 4 puck-fästhål (H5–H8, M2.5) i puckens exakta mönster **20,80 × 33,90 mm rektangel**,
  centrerat → skruvas på korta standoffs ovanför P4-modulen. GH-kontakten (J1) sitter i SYD med
  öppningen mot centrum (mot puckens syd-kontakt) — kort kabel rakt ner.
- **ESP32-P4-WIFI6**, 2× 1×20 kant-sockel (edge A=signaler, edge B=kraft-tapp). Pinout verifierad
  mot Waveshares datablad. P4 självförsörjer via VSYS=VBAT; carrier-buck (AP63203) ger 3,3 V för
  laster (sensorer/F9P/IMU/ljud/patch-rail). ~40 GPIO → gott om marginal.
- Edge A: I²C (F9P+IMU) · UART (F9P) · IMU_INT · LED_EN · 5 DATA direkt · I²S (BCLK/LRCK/DOUT/DIN) ·
  amp_SD = 14 av 16 signalstift.
- Oförändrat i övrigt: ZED-F9P RTK-puck, IIM-42653 IMU, 4 egna TSOP4856 (diagonal-aim) → diod-OR,
  6 LED-tab-konstellation + driver, MAX98357A-amp + I²S-MEMS-mik, 4 patch-kontakter, 2S-batteri.
- **Strömplan:** In1=GND, **In2=VBAT** (bär konstellations-LED-ström + patch-rail; korsar P4-sockel-
  "väggen"), F/B=GND-fyll. +3V3 routas som spår. (Rim-LED-lasten flyttade höga strömmen till VBAT → planas.)
- Deliverables: `hardware/helmet-mb-gerbers.zip` + `.step`.

## Konstellations-arkitektur (disc vs patch) — 2026-06
Hjälm-discen ligger plant ovanpå hjälmen (F9P-puck uppåt) → dess 6 konstellations-LED sitter på **LED-TAB micro-PCB** (egen liten PCB med OSLON + 2 ben) som löds in
i discens tab-socklar (D5–D10) och **böjs radiellt ut mot horisonten** (som de ledade TSOP:erna) → full
effekt, kameran ser dem i ögonhöjd @150 m. De **4 hjälm-patcharna** på skalet bidrar också (utåtvända, som kroppspatcharna). Kameran löser huvud-posen ur de
patchar som är face-on. Konstellations-LED har ingen kollimator (bred lob). Se
[`konstellation-tackning.md`](konstellation-tackning.md) + [`skott-flode.png`](skott-flode.png).
