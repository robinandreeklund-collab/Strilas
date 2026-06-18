# STRILAS — Komplett systemguide

> **Ballistic Laser Tactical-Engagement Simulator.** Force-on-force trä­ning/spel där replika­vapen
> skjuter **kodat infrarött ljus** (inga projektiler), men med **simulerad ballistik** (kulfall +
> flygtid + lead) så att det blir **skicklighet, aldrig pek-och-skjut**. Träffar registreras av
> kropps-/hjälm­detektorer, posen löses optiskt av skyttens kamera, och allt loggas live.

Detta är **master-dokumentet** — den auktoritativa, kompletta referensen. Detaljanalyser ligger i
`vapen-stack/ritningar/` och länkas per avsnitt. Tillverknings­underlag i `vapen-stack/nextpcb/`.

> **Status (2026-06):** Alla 5 tillverkade kort routade rent (0 oanslutna / 0 clearance), system-
> simulering 28/28 PASS, order­paket klart. Se `vapen-stack/nextpcb/FORSTA-BATCH.md`.
> Äldre detaljdokument kan referera tidigare beslut (väst-nod "ESP32-C5", 3 TSOP/patch, 5+5 patchar);
> **gällande arkitektur är denna guide** (P4-WIFI6 överallt, 4-TSOP symmetrisk patch, rund hjälm).

---

## 1. Designfilosofi (varför systemet finns)

Vanlig laser-tag/MILES = pek-och-skjut: strålen träffar direkt, ingen ballistik. STRILAS bryter det:

- **Ljus faller inte → ballistik BERÄKNAS.** 940 nm-strålen går rakt, men firmware räknar kulfall
  och flygtid utifrån **avstånd R** och **vapenattityd**, och avgör i efterhand om "kulan" landat.
- **Kräver både hållover (drop) OCH lead (förhållning).** Spelaren måste själv sikta över och framför.
  Systemet auto-kompenserar **inget** → skicklighetsstyrt.
- **Ärlig adjudikering, inte trösklar.** Träff = den världsfasta, fall-korrigerade skottlinjen skär
  målets *verkliga* läge när kulan anländer (deferred hit). Inga gissningar.

Detaljer: [`ritningar/ballistik-analys.md`](vapen-stack/ritningar/ballistik-analys.md),
[`ritningar/rorligt-mal-analys.md`](vapen-stack/ritningar/rorligt-mal-analys.md).

---

## 2. Systemarkitektur — 3 noder, samma ESP

Allt kör **samma Waveshare ESP32-P4-WIFI6** (P4 SoC + onboard ESP32-C6 WiFi6/BLE) → en source, enkelt
underhåll, WiFi6-mesh genomgående (ESP-NOW/WiFi6). P4 självförsörjer via VSYS=VBAT (onboard MP1658-buck);
varje kort har dessutom en **carrier-buck (AP63203)** som ger 3,3 V till sensorer/last.

| Nod | Kort | Roll | Nyckelfunktioner |
|---|---|---|---|
| **Vapen** | optik + fire-control | "Sikte + domare" | OV9281-kamera (860 nm-pass) → PnP-pose; 940 nm-emitter (eye-safe CC); IMU; recoil; NFC-ammo; avtryck/laddhandtag |
| **Väst** | väst-mb + 10 patchar | Träff-RX torso 360° | 10 patch-DATA (skott-LOS); 20 konstellations-LED (pose); 10 zon-vibratorer (haptik) |
| **Hjälm** | hjälm-mb (rund) + 4 patchar | Huvud-RX + **RTK-position** + ljud | 360° huvud-TSOP; konstellation; **ZED-F9P RTK** + IMU (cm-position); högtalare+mik (spelljud/röst) |

Mesh: vapnets P4 löser posen och adjudikerar; väst/hjälm-noderna rapporterar DATA-träffar, RTK-position
och driver haptik/ljud lokalt. Detaljer: [`ritningar/system-struktur.md`](vapen-stack/ritningar/system-struktur.md).

---

## 3. Hur ett skott går till (end-to-end)

> Flödesbild: [`vapen-stack/ritningar/skott-flode.png`](vapen-stack/ritningar/skott-flode.png).
> Konstellations-täckning (LED-riktning vs mottagar-vinkel): [`konstellation-tackning.md`](vapen-stack/ritningar/konstellation-tackning.md).

```
1. AVTRYCK → fire-control (edge A) signalerar P4. NFC-ammo > 0 + laddhandtag racked (make-ready).
2. EMITTER fyrar: 2× 940 nm OSLON i serie, aktiv konstantströms-sänka (OPA171+pass-FET+0R2 sense),
   ~1 A HW-tak (eye-safety), 56 kHz-gatad burst som bär skott-paket (skytte-ID, vapenprofil, dmg).
3. SKOTTLINJE LÅSES i världsram vid avtryck (riktning pipan pekar + ballistiskt fall). IMU håller
   linjen världsfast medan vapnet rör sig (recoil/svaj).
4. KAMERAN (860 nm-pass, global shutter, 120 fps) ser målets aktiva 860 nm-KONSTELLATION → frame-
   differencing → rena blobbar → PnP (≥4 LED i känt 3D-mönster) → mål-pose: avstånd R + bäring + orient.
5. BALLISTIK: R → kulfall (~14 cm @150 m) → hållpunkts-offset. Flygtid (~167 ms @150 m) → kameran
   spårar målet under hela flygtiden.
6. DEFERRED HIT: när kulan når R → träff OM den världsfasta fall-korrigerade linjen skär målets
   VERKLIGA läge då. Träffzon mappas på målets 3D-modell (anatomisk zon).
7. MÅLET: TSOP-patch (940 nm) ger LOS-gate/anti-fusk DATA-puls → väst/hjälm-nod → mesh. Vid
   ADJUDIKERAD träff fyras zon-VIBRATORN (haptik) + ljud/score. (Rå TSOP ≠ poäng; kameran avgör.)
```

---

## 4. Optik & våglängder (måste matcha)

| Funktion | Våglängd | Komponent (ams OSRAM, **samma leverantör**) | Mottagare |
|---|---|---|---|
| **Skott** (LOS/ID/anti-fusk) | **940 nm** | SFH 4725S OSLON Black (980 mW@1A), CC ~1 A, 56 kHz | TSOP4856 (56 kHz, ±45° lob) |
| **Konstellation** (pose) | **860 nm** | SFH 4715AS OSLON Black, Ie 780 mW/sr@1A | Kamera m. 860 nm bandpass |

> **Hjälm-konstellation:** OSLON på **LED-tab micro-PCB** (90°-vinklad right-angle fot) (`led-tab`) — NextPCB placerar OSLON:en,
> kund böjer benen radiellt ut mot horisonten (full effekt, syns i ögonhöjd @150 m). Se `konstellation-tackning.md`.
>
> **Sourcing-status:** 940 nm-emittern **SFH 4725S är utgående/EOL** (databl. 2023) men lagerförs ännu
> (last-time-buy) → OK för första batchen; verifiera aktuell 940 nm OSLON-ersättare inför produktion.
> 860 nm **SFH 4715AS = aktiv/tillgänglig**. **OSLON-emittrarna sitter under Carclo TIR-kollimatorlinser
> + hållare** som köps separat och monteras manuellt (sätter strålvinkeln; eye-safety ommäts med lins).

Kameran ser **860 nm** (konstellation) och **avvisar egna 940 nm-strålen** → ingen självbländning.
TSOP tar emot 940 nm-skottet. **Transparent IR-kupa** över korten: ser svart/mörkröd ut för ögat men
släpper nära-IR (T≈0,88), absorberar solglimt (bättre SNR). Specar: [`ritningar/fonster-spec.md`](vapen-stack/ritningar/fonster-spec.md).

---

## 5. Ballistik & räckvidd

- **Designräckvidd: 150 m.**
- **Mynningshastighet v₀ ≈ 900 m/s** (profil-beroende).
- **Kulfall @150 m:** `½·g·(R/v₀)² ≈ 14 cm` → hållpunkt **~0,9 mrad (~3 MOA)** över målet.
- **Flygtid @150 m:** `R/v₀ ≈ 167 ms` = **~20 frames @120 fps** (deferred-hit-fönstret).
- **Avstånds-okänslighet:** `d(fall)/dR ≈ 1,8 mm/m` → även ±0,9 m R-fel ger bara **±1,6 mm** hållpunktsfel (försumbart).

Hållpunkts-retikel sjunker med avståndet; spelaren lägger konstellationen på den. Bildmitten får peka
**över** målet — det är poängen. [`ritningar/ballistik-analys.md`](vapen-stack/ritningar/ballistik-analys.md).

---

## 6. Rörliga mål — lead (förhållning)

Lead-vinkel = **v_mål / v₀** (oberoende av avstånd). Litet → alltid inom kamerans ±6,85° FOV:

| Målfart | lead-vinkel | lead @150 m |
|---|---|---|
| 3 m/s | 0,19° | 0,50 m |
| 5 m/s | 0,32° | 0,83 m |
| 10 m/s | 0,64° | 1,67 m |
| 15 m/s | 0,95° | 2,50 m |

Sikta **där målet är** (ingen lead) → kulan anländer dit målet **var** → miss på korsande mål. Sikta
**framför** → träff. Mål som tvärbromsar efter avtryck hinner undan (realistiskt). [`rorligt-mal-analys.md`](vapen-stack/ritningar/rorligt-mal-analys.md).

---

## 7. Optik & algoritm (kamera = sikte)

- **Kamera:** Arducam OV9281 (1280×800, 3 µm px, **global shutter** → ingen rörelsesmet), USB till P4.
- **Lins:** 16 mm M12 low-distortion → **~13,7° HFOV**, **0,0107 °/px**, skala **1° = 2 618 mm @150 m**.
- **PnP (Perspective-n-Point)** på ≥4 icke-koplanära konstellations-LED → 6-DOF mål-pose (R + bäring +
  orientering) i ett svep. Robustare än 2-punkts-stadiametri.
- **Frame-differencing + 860 nm-bandpass + modulerade LED** → rena blobbar även i dagsljus; subpixel-
  centroidering (~0,1 px) → ~24 px konstellations-baslinje @150 m.
- **IMU re-ankrar attityden varje frame** (8,3 ms @120 fps) → låg inter-frame-drift.
- **Deferred adjudication:** skottlinje låst i världsram vid avtryck; träff bedöms när kulan når R.
- **Latens-budget** (sensor→beslut ~8–16 ms) måste kompenseras (annars lead-bias) — mjukvaru-jobb.

Algoritm-roller: konstellations-centroider = "beräkningspunkterna" (ger bäring + R). 940 nm = skott-ID/LOS
(ej geometri). Kamera = ser 860 nm, avvisar 940 nm. IMU = stel mot optiska axeln.

---

## 8. Precision (felbudget @150 m)

RSS av oberoende felkällor (IIM-42653 + 120 fps + low-distortion-lins):

| Felkälla | 1σ @150 m |
|---|---|
| Centroid-brus (0,1 px) | 2,8 mm |
| Intrinsisk kalibrerings-rest | 3,9 mm |
| IMU mellan-frame-brygga (120 fps) | 1,2 mm |
| Avstånd→hållpunkt (±0,9 m) | 1,6 mm |
| **RSS (bäring/träffläge)** | **≈ 5,2 mm 1σ** |
| **Avstånd R (PnP)** | **±0,3–0,9 m** |

Sensorbruset (~5 mm) är **~27× mindre** än hållpunkten (140 mm) → systemet är **inte** begränsningen;
spelarens sikte är det. Svagheter: smalt FOV (mål ur bild vid recoil), dagsljus-SNR (omätt), latens.
[`ritningar/precision-iim42653.md`](vapen-stack/ritningar/precision-iim42653.md), [`precision-analys.md`](vapen-stack/ritningar/precision-analys.md).

---

## 9. Hitbox / zoner

Två zonsystem som gör olika saker:

**A) Kamera/PnP-zoner (fina, mjukvara) — i praktiken obegränsat.** P4 mappar träffpunkten på målets
3D-modell. Gräns = bäringsprecision:

| Avstånd | bäring 1σ | minsta säkra zon (~3σ) |
|---|---|---|
| 25 m | 0,9 mm | ~3 mm |
| 75 m | 2,6 mm | ~8 mm |
| 150 m | 5,2 mm | ~16 mm |

→ **8–16 anatomiska zoner** (huvud, vä/hö bröst, vä/hö mage, armar, ben) glasklart särskiljbara ända till 150 m.

**B) Fysiska TSOP-patch-zoner (LOS-gate + fallback).** Varje patch = 1 DATA-linje. Bekräftar att strålen
*nådde fram* (anti-fusk, ej genom vägg) + grov-zon om kameran tappar konstellationen. [`vest-zonschema.md`](vapen-stack/ritningar/vest-zonschema.md).

---

## 10. Patch-design (täcknings-nod)

Identisk patch på väst och hjälm — **rund Ø45 mm, 4-falds symmetrisk (4× M2-hål)**, lim/kardborre +
ev. rökfärgad polykarbonat-dom (Ø46,5 inner) som skydd över de böjda benen. **Kontakt = JST-PH 5-pol
SIDE-ENTRY (S-typ) på BAKSIDAN** → låg bygghöjd, kabel ut i kant, domen täcker fronten obehindrat.
Fronten = ren optik (4 identiska TSOP-kluster + 4 LED-tabbar i kardinalriktning + 2 fasta LED), driver/kraft i centrum:

- **4× TSOP4856** (ledade) i **diamant**, var och en böjd **~40° utåt** från kortets normal.
  Beräknat optimum: **99,5 % av framåt-hemisfären** täckt, **100 % inom 60° zenit**, ~2,3 mottagare
  ser ett frontalskott (redundans). Full symmetri → funkar i **valfri vridning** på kroppen.
- Varje TSOP: egen OR-diod (BAT54) + avkopplings-C → 4 identiska kluster; alla OR:as till **1 DATA-linje**.
- **Konstellation: 2 fasta 860 nm OSLON + 4 böjbara LED-tabbar = 6 LED**, kopplade i **3 seriepar-grenar**
  (2 LED + 10R 2512/gren); N-FET (AO3400, LED_EN) modulerar. ~0,2–0,28 A/gren → ~0,5–0,8 A/patch på VBAT.
- TSOP matas **3,3 V från moderkortet** (abs-max 6 V → tål ej 2S direkt); LED-konstellationen på **VBAT**.
- Baksida (mot kroppen): **ERM-vibrator** för lokal träff-känsla.
- Beräkning: [`ritningar/patch-sikte.md`](vapen-stack/ritningar/patch-sikte.md).

---

## 11. Haptik (väst)

- **ERM coin-motor bakom varje zon**, mot kroppen → lokal buzz där du träffas.
- Drivs av **2× TPIC6B595** power-shift-register (open-drain 150 mA/kanal, inbyggd flyback), styrt med
  3 GPIO (SER/SRCK/RCK) → 16 kanaler täcker 10 zoner. PWM = intensitet/mönster.
- **Fyras på ADJUDIKERAD träff** (kamera/spellogik bekräftar) ~tiotal ms efter skott = känns direkt —
  inte på rå TSOP (bred kon kan nudda flera patchar på en miss).
- Effekt: ERM ~80 mA @3 V, 200–400 ms/träff → försumbart medel. [`ritningar/vest-haptik.md`](vapen-stack/ritningar/vest-haptik.md).

---

## 12. RTK-positionering & IMU (hjälm)

- **ZED-F9P RTK-puck** (BDLX, rund Ø55 mm × 55 mm, inbyggd antenn + **IST8310-kompass**) monterad
  **direkt på hjälm-kortets centrum** via korta standoffs: 4 puck-fästhål (M2.5) i puckens exakta
  mönster **20,80 × 33,90 mm**, centrerat, ovanför den stackade P4-modulen. GH-kontakt (8-pol, 1,25 mm)
  i syd, öppning mot centrum. **cm-noggrann** position, matas VBAT (3–9 V), UART + I²C till hjälm-P4.
- **IIM-42653 IMU** (I²C, delar F9P-bussen + INT) → **GNSS/INS-fusion**: överbryggar multipath/skugga,
  ger lokal huvud-attityd, förbättrar RTK-fix. Samma IMU som vapnet/fire-control.
- Hjälm-noden skickar cm-position + huvud-pose i meshen → live-spårning + after-action.
- Kompletterar (ute) den optiska posen; ger absolut världsposition som vapnets relativa pose saknar.

IMU används även i vapnet för **recoil→sikte-loopen** (mynningsklättring matas in i nästa skotts bana;
okontrollerade serier vandrar av målet). IIM-42653: ±4000 dps, RNSD 0,005 °/s/√Hz, ZRO ±0,04 °/s/°C.

---

## 13. Korten (5 tillverkade PCB)

| Kort | Storlek | Lager | Innehåll | Routning |
|---|---|---|---|---|
| **Optik/vapen** | 54×74 mm | 4 | P4-stack, OV9281-USB, 940 nm-emitter + CC-driver, IMU, lins-hål Ø16 | 0/0/0 |
| **Fire-control** | 71×21 mm | 2 | Stackas på P4 edge A; avtryck/laddhandtag/mag-switchar, recoil-ctrl, NFC, 2× extra IMU | 0/0/0 |
| **Väst-patch** | **rund Ø45 mm** | 2 | 4 TSOP diamant + 6 LED (2 fasta + 4 tab) i 3 grenar + FET + JST-PH 5-pol side-entry (baksida) | 0/0/0 |
| **Hjälm-mb** | **rund Ø97 mm** | 4 | P4, F9P-puck (centrum), IMU, 4 TSOP + 6 LED-tab, ljud (amp+mik), 4 patch-kontakter | 0/0/0 |
| **Väst-mb** | 100×60 mm | 4 | P4, 10 zon-kontakter JST-PH 6-pol side-entry (patch+vibrator), 2× TPIC6B595, buck, **XT30-batteri** (In2=VBAT-plan) | 0/0/0 |

**Strömplan:** alla 4-lagerskort In1=GND, F/B=GND-fyll. In2 = **VBAT** (väst-mb + hjälm-mb + optik —
bär LED-konstellationsström + patchar). P4-pinout **byte-identisk** över alla kort, verifierad mot Waveshares
dok (I²C SCL=GPIO8/SDA=GPIO7). Carrier-buck matar 3,3 V-last; P4 självförsörjer via VSYS=VBAT.

---

## 14. Kraft & batteritid (uppskattning — bekräfta på bänk)

2S LiPo per nod. Buck-verkningsgrad ~90 %. Recoil-aktuatorn (~20 A-toppar) matas från **separat
magasins-batteri**, ej nodbatteriet. **Konstellations-LED:erna är den dominerande lasten** och därmed
den primära batteritids-drivaren — deras **medel-duty** är designparametern att optimera (synka blink/
ID till lågt duty mot kamerans exponering).

Grov medeleffekt per nod (aktivt spel):

| Last | Vapen | Väst | Hjälm |
|---|---|---|---|
| P4 + WiFi6 (kamera/PnP tyngst på vapen) | ~2,5 W | ~1,5 W | ~1,8 W |
| Sensorer (IMU/F9P/kamera) | ~0,2 W | — | ~0,5 W (F9P) |
| Emitter 940 nm (pulsad, skott-takt) | ~0,1–0,3 W | — | — |
| Konstellation 860 nm (se duty) | — | **se nedan** | ~0,3 W (2 LED) |
| Haptik/ljud (pulsad) | — | ~0,1 W | ~0,3 W |

**Konstellations-LED, väst (10 patchar × 6 LED = 60 LED i 30 seriepar-grenar, drivs på VBAT):**

Topp (alla patchar blinkar synkront) ≈ **0,2–0,28 A/gren × 30 = 5–8 A** på VBAT (8,3 A @ fulladdat 8,4 V).
LED:erna går **direkt på batteriet via In2=VBAT-plan** (INTE bucken) → batteri + **XT30-kontakt (≥15 A)** +
VBAT-plan bär toppen med marginal. Medelströmmen sätts av blink-duty:

| Medel-duty | I_LED medel | Effekt | + P4 ⇒ nod-medel | Drifttid 2S 2200 mAh (16,3 Wh) |
|---|---|---|---|---|
| 2 % (synkad/optimerad) | ~0,15 A | ~1,1 W | ~2,8 W | **~5,8 h** |
| 5 % | ~0,35 A | ~2,7 W | ~4,5 W | **~3,6 h** |
| 10 % | ~0,7 A | ~5,3 W | ~7 W | **~2,3 h** |

→ **Rekommendation:** håll konstellations-duty lågt (≤5 %) via blink-synk → 3–6 h speltid på en 2S
2200 mAh. (Vill man ändå ha hög samtidig ljusstyrka klarar VBAT-planet + XT30 toppen; det är
**batteritiden**, inte kopparen/kontakten, som då blir gränsen.) Vapen-noden (ingen konstellation)
≈ 0,4 A → **~5 h**; hjälm ≈ 0,5–0,7 A → **~3–4 h**. *(Estimat — mät faktisk P4-vision-effekt + vald
LED-duty på bänk; ladd-dock balanserar alla pack.)*

---

## 15. Eye-safety (säkerhet före allt)

- 940 nm är **osynligt** → farligast nära mynningen. **Strömtaket sätts i HÅRDVARA** (CC-sänka:
  I = Vref/Rsense ≈ 1 A, op-amp + sense-resistor), inte bara firmware. Skalning till högre ström kräver
  avsiktligt Rsense-byte **+ IEC 60825-1-ommätning**. Mål: **Klass 1 (eye-safe)**; vid tvekan, använd
  divergerad IR-LED (det vi gör — OSLON-emitter, ej kollimerad laserdiod).
- **LiPo-laddning** (dock) = projektets största brandrisk: per-cell-balansering, riktig BMS, termik, brandsäker plats.
- **Recoil-skena** ~20 A: kontakter >25 A, gör/bryt **kallt** (skenan av vid mag-byte, make-ready-statemaskin).
- Skyddsglasögon för alla; definierade spelgränser; "weapons safe"-procedur. (Se root-`README.md`.)

---

## 16. Comms / mesh

Alla noder = ESP32-P4-WIFI6 (P4 + C6) → **WiFi6/ESP-NOW-mesh**, gemensam tidsstämpling. Vapnets P4
adjudikerar; väst/hjälm rapporterar DATA-träffar + RTK-position; allt loggas för live-spårning + AAR.

---

## 17. Tillverkning & beställning

Order­paket: **`vapen-stack/nextpcb/`** — per kort `<kort>-gerbers.zip` + `-bom.xls` + `-centroid.csv/.xls`.
3D: `hardware/<kort>.step`. Beredskaps­rapport: **`nextpcb/FORSTA-BATCH.md`**.

- **NextPCB monterar endast SMT.** P4-socklar samt alla JST-PH-kontakter (patch/zon/headset, nu **side-entry**)
  + batteri-JST/XT30 **kund-löds** — markerade **DNP i BOM** (NextPCB monterar EJ) men kvar som beställnings-
  rader, ute ur centroid. ZED-F9P GH (SMD) monteras av NextPCB. FC:s 2 extra IMU = **prototyp-DNP** (breakout först).
- **OSLON-emittrar/LED (ams OSRAM) sourcas + placeras nu av NextPCB** (ej längre consignment "C" — verifiera
  lager/EOL inför produktion, t.ex. 940 nm SFH4725AS bin13). Matcha kamerans 860/940 nm IR-pass.
- **Köps separat:** 3× ESP32-P4-WIFI6, RTK-puck (ZED-F9P 8-pol GH **eller** alt all-in-one UM980/F9P Ø86 6-pol GH),
  OV9281 + IR-pass-filter, headset (mik/högtalare/PTT), 10× ERM-vibrator, 2S-batterier, IR-kupa (mörk-IR-akryl).
- **Optik-linser + hållare (köps separat, MONTERAS MANUELLT):** Carclo TIR-kollimatorlins för OSLON Black
  (Carclo 10003-serien — välj spridning för räckvidd) + Carclo-lenshållare per emitter, klistras/snäpps
  över emittrarna efter SMT (fästben finns på optikkortet). NextPCB SMT-placerar OSLON-emittrarna med
  precision; linsen monteras sen manuellt ovanpå.
- FR-4 1,6 mm, HASL/ENIG. Alla MPN ifyllda (passiva = representativa, verifiera mot NextPCB-bibliotek).

---

## 18. Verifiering (maskinkontrollerat)

- **Per kort** (`hardware/verify_board.py`): footprints matchar netlist, alla net-noder har pad,
  **0 oanslutna + 0 clearance@0,2 mm** på alla 5 kort. 0 courtyard-krockar; rund hjälm radiellt OK.
- **P4-pinout:** byte-identisk över alla möte-kort; I²C bekräftad mot Waveshares dok.
- **System-simulering** (`hardware/sim_system.py`): korten "uppkopplade" via kabel-bryggor →
  **28/28 PASS** (skott-RX, konstellation, kraft, I²C, GNSS-UART, vibrator, ljud, vapen-CC-emitter,
  IC-kraftintegritet) — allt flödar end-to-end.

**Bänk-bekräftas (ej fångbart i layout):** dagsljus-SNR @150 m (störst), kontinuerlig spårning +
latenskompensation i 167 ms, recoil-hantering, TSOP-räckvidd @150 m, buck-3,3 V, IMU LGA-pad mot IIM-42653.

---

## 19. Repo-karta (för framtida referens / minne)

```
hardware/
  *_netlist.py / receiver_netlists.py   — SKiDL kretsdefinitioner → .net
  make_p4_board.py                      — KANONISK P4-WIFI6 mekanik/pinout (källa)
  receiver_place.py                     — placering (vest_pos/helmet_mb_pos/vest_mb_pos) + outline
  route_*.py                            — DSN→freerouting(loop, timeout-skydd)→ses_apply→kopparplan→DRC→gerber/STEP
  dsn_power_class.py / ses_apply.py     — power-net-breddning / SES-import
  verify_board.py                       — pad/footprint/anslutnings-verifiering
  sim_system.py                         — system-signalflödes-simulering (kabel-bryggor)
  strilas.pretty/                       — custom footprints (OSLON, InvenSense LGA-14, Vishay)
  <kort>.kicad_pcb / .net / .step / -gerbers.zip
vapen-stack/
  gen_nextpcb.py                        — BOM + centroid (MPN-dict, grupperar på värde+footprint)
  ritningar/*.md + *.png                — alla analyser (ballistik, precision, SNR, zoner, haptik, sikte…)
  nextpcb/                              — ORDERPAKET: gerbers/bom/centroid per kort + FORSTA-BATCH.md
README.md                               — högnivå-intro + säkerhet
STRILAS-SYSTEM-GUIDE.md                 — DETTA dokument (master-referens)
```

**Verktygskedja:** KiCad 7 (kicad-cli 7.0.11) + pcbnew Python API · SKiDL (netlistor) · freerouting v1.9.0
(java, körs headless via xvfb-run; analytics av + spår-rensning före DSN-export = undvik dialog-hängning).

**Centrala designval (låsta):** P4-WIFI6 överallt · 940 nm skott / 860 nm konstellation (ams OSRAM OSLON) ·
kamera = sikte (PnP, ej stadiametri) · 16 mm-lins · deferred hit · eye-safety i HW · 4-TSOP-diamant 40° patch ·
rund hjälm med F9P-puck i centrum · haptik på adjudikerad träff.
