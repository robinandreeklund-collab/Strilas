# STRILAS Nivå 3 — Geometrisk ballistik-adjudikation (arkitektur)

> Resultatet av en fullständig omanalys (fem research-spår, 2024–2026-källor). Definierar hur STRILAS gör **riktig per-skott-ballistiksimulering** — inte laser-tag: en server integrerar kulans bana från siktvektor + positioner och avgör träff **geometriskt**, med IR-strålen som **pose-/siktlinje-ankare + träffzon**.
>
> Ersätter den tidigare "Fas 2 = valfri bonus"-framställningen. Nivå 3 *är* målet; nivå 1 (IR-kärnan) är byggsteget dit.

---

## 1. Vision & ärlig förankring (prior art)

STRILAS nivå 3 är i praktiken en **öppen DIY-version av det som primes just nu kapplöper om att fältsätta**:

| System | Vad det gör | Status |
|---|---|---|
| **US Army eBullet** | "true ballistic flight paths to within a seventeenth of a degree", penetrerar rök/löv som laser inte kan, "varje avtryck = ett dataevent" | Army-validering (ersätter MILES) |
| **Lockheed SIMRES / WOM** | geo-pairing + **digital tvilling i Unreal Engine 5**, "flyger ut den ballistiska banan med korrekt timing" | preferred vendor, US Army OTA (prototyp/down-select) |
| **BAE HITS** | vapenmonterad, **ingen laser**, pointing via dator­seende mot LIDAR-modell + GPS-RTK, **~2 mrad**, hög­fidelitetsballistik | ION GNSS+ 2020, prototyp |
| **Saab DISE / MILES / Cubic** | **laser** för direkteld, geometri bara för områdes-/indirekt eld | fältsatt standard |

**Ärlig slutsats:** konceptet är **inte nytt** (eBullet/SIMRES/HITS gör exakt detta), men det är **state-of-the-art, inte mainstream** — alla mass-fältsatta system laser:ar fortfarande direkteld. **Det nyskapande för STRILAS är den öppna DIY-instansieringen.** Och den verkliga ingenjörsrisken är **densamma som primes lägger mest pengar på: vapen-pose- och positionsnoggrannhet.**

---

## 2. Den avgörande upptäckten: ren geometri räcker inte — IR är ankaret

En fri IMU-siktvektor **driver** (yaw-drift 0,25–1°/min, obegränsad utan absolut referens). Siktfel → sidledsmiss = `räckvidd·tan(θ)`:

| Vinkelfel | 30 m | 75 m | 150 m |
|---|---|---|---|
| 0,5° | 0,26 m | 0,65 m | 1,31 m |
| 1,0° | 0,52 m | 1,31 m | 2,62 m |

Mål-tolerans (max siktfel för att landa på kroppen): torso ±0,48° @30 m, **±0,19° @75 m**, ±0,095° @150 m.

**Verdikt:** ren IMU+UWB-geometri träffar torso på ~30 m (med färsk ankring), **marginellt på 75 m**, **inte på 150 m**. Tilt (pitch/roll) är bra (~0,5–1°, gravitationsförankrad); **yaw/heading är problemet**. Alla fältsatta system som når sub-grad förankrar IMU:n mot en absolut referens (HITS: dator­seende-mot-LIDAR; ULTRA-Vis: vision+mag; TrackingPoint: optisk mållåsning).

→ **STRILAS:s billiga DIY-ankare är IR-strålen.** När målets TSOP avkodar strålen *vet* du att pipan pekade inom strålkonen mot just den spelaren — det **kollapsar heading-osäkerheten till strålens halvvinkel** (tight *bara* med smal stråle/kort håll — se **§3.2**) och ger en LOS-bekräftelse på köpet. IR:n är alltså **arkitektoniskt bärande, inte valfri.**

---

## 3. Hybridmodellen — vem gör vad

| Delsystem | Ansvar | Varför just den |
|---|---|---|
| **IR-stråle (SFH 4715AS + TSOP4856, kodad)** | (a) **förankrar sikte/heading** (pip pekade inom konen mot spelaren), (b) **LOS-grind** (skymd av skydd = ingen träff), (c) **exakt kroppszon**, (d) skytt-ID + rullande nonce | IMU-heading driver; UWB är för grov för kroppsdelar; bara IR vet om skydd skymde |
| **IMU (ICM-45686)** | **tilt** (bra), **postur** (stå/huk/ligg), kort-tids-aim mellan ankringar, pip-attityd | gravitationsförankrad tilt är pålitlig |
| **UWB (DW3000) + GNSS** | **positioner & räckvidd** (~10–30 cm), delad klocka (HW-tidsstämpel) | cm-räckvidd; men för grov för kroppsdel |
| **Ballistikmotor (server)** | **kulans bana**: flygtid, drop, lead mot rörligt mål, anslagsfart, räckviddsskada | riktig fysik ovanpå det IR-förankrade siktet |

**Kärnan:** geometrin avgör *anländer kulan till kroppsvolymen, från vilket håll, hur hårt*; **IR-zonen avgör *var på kroppen*** (huvud/bröst/…). Ingen av dem ensam räcker.

### 3.1 Pose-stack (BESLUTAD: fuserad)

Vapnets siktriktning (systemets nyckelgräns) byggs i lager — billigt och robust nu, optisk precision som uppgradering:

| Lager | Roll | Status |
|---|---|---|
| **IR-stråle** | LOS-grind + heading-ankare (kollapsar yaw till strålkonen) + zon + ID | **nu** (robust i allt ljus) |
| **ICM-45686 (array 2–4)** | hög-rate tilt + kort-tids-attityd, √N-brusreduktion | **nu** |
| **GNSS dubbelantenn-heading (ZED-X20D, ~0,1°)** | absolut yaw-referens som binder IMU-driften | **nu** (utomhus) |
| **Sikteskamera + AI + ArUco/AprilTag-fiducials** | optisk bäring (~2 mrad) + zon + ID + LOS ur bild | **uppgradering** (kräver Jetson-klass på/nära vapen + thermal i mörker) |

Motivering: detta är vägen primes (BAE HITS) landar på — IR/inertial/GNSS ger robust bas i alla förhållanden, kameran/AI lyfter pose-precisionen där compute/ljus tillåter. IR behålls oavsett (LOS-sanning + mörker-robusthet). Avstånd: UWB/GNSS nu, ev. LiDAR (Benewake TF02-Pro) som komplement.

### 3.2 Precision ≠ IR-strålbredd — kamera/GNSS-heading KRÄVS på avstånd

Vanligt missförstånd: att en smalare IR-stråle = bättre precision. Fel. **IR-strålbredden är länkbudget/täckning, inte hitbox.** En räckviddsoptimerad LED-stråle är bred — spot-diameter = 2·R·tan(halvvinkel):

| Strålvinkel | Spot @100 m | Spot @150 m |
|---|---|---|
| ±7,5° (medium spot) | 26 m | **40 m** |
| ±5° (narrow spot) | 17 m | 26 m |
| ±0,5° (i praktiken laser) | 1,7 m | **2,6 m** |

Även ±0,5° ger en 2,6 m spot på 150 m — bredare än en människa. En personstor IR-spot @150 m kräver ~0,1° = laser. **Alltså: ingen LED-stråle kan vara hitboxen på avstånd.**

Precisionen (träff ja/nej + zon) kommer från **siktvektorn (pose) + ballistik + målets hitbox-geometri**, avgjort på servern. IR ger grov LOS + skott-ID + "ett mål belystes"; servern reder ut vem/var. Krav för att upplösa mål @150 m:

| Vill upplösa | Krävd pose-precision | Vad ger det |
|---|---|---|
| Torso (0,5 m) | **0,19°** | kamera/AI (0,11°) ✅ · GNSS-heading (0,1°) ✅ |
| Huvud (0,2 m) | **0,076°** | kamera/AI marginellt ✅ |
| (skakig IMU/drift 1–3°) | → 2,6–7,9 m miss | ❌ kan inte ens upplösa en person |

→ **På 100–150 m är kamera/AI-bäring + GNSS-heading inte en "uppgradering" — de ÄR precisionsmekanismen.** Enbart IMU+IR ger bara "rikta åt rätt håll". Emittern kollimeras därför **enbart för räckvidd** (länkbudget); strålen får vara bred eftersom geometrin gör precisionen.

---

## 4. Exteriörballistik-motor

**Modell:** 3-DOF point-mass + **G7-drag** (custom Doppler-tabell möjlig per vapenprofil) + **vektorvind** + **lufttäthet (temp/tryck)**. Spin-drift & Coriolis är sub-tum på 300 m → valfria analytiska efterkorrektioner. (MPM/STANAG 4355 pluggbart senare.)

**5.56 M855 sanity (G7 BC ≈ 0,151, ~930 m/s):** 100 yd zero → drop 0 @100 yd, −5,5 cm @200 yd, ~−32 cm @300 m; flygtid ~0,1 s @100 yd, ~0,35 s @300 yd.

**Miljöeffekter (rangordnade för 0–300 m):** vind (STOR, måste med) → lufttäthet via temp/tryck (måttlig) → spin-drift (~0,5–1 tum @300 m, valfri) → Coriolis (försumbar). README-roadmapens vind+temp täcks.

**Integration:** RK4, ~1 ms fast steg (~350 steg till 300 m = mikrosekunder CPU/skott). Integrera en gång → lagra `(t→pos, vel)` → bygg **interpolant** → servern frågar position vid valfri t för träffskärning utan om-integration.

**Återanvänd:** **js-ballistics (ISC)** för JS-server eller **py-ballisticcalc (LGPL)** för Python — båda har 3-DOF+G7+custom drag+RK4+atmosfär+vind. Seeda drag-tabeller från standard **JBM G7-tabellen**.

---

## 5. Geometrisk träffdetektering & kroppsmodell

**Kropp = ~10–15 posturvalda kapslar** (ANSUR-mått): huvud-sfär Ø15–20 cm, torso-kapsel ~40 cm bred × ~24 cm djup, mage ~34 cm, lår/underben/armar som kapslar. NATO E-silhuett ≈ 1,0×0,5 m; CRISAT hukande frontalarea 0,37 m².

**Skärning:** kulan = stråle/svept kapsel; kropp = kapslar som **rör sig under flygtiden**. **Continuous collision detection** i en **delad tidsdomän** → leadet sköts automatiskt (testa kulsegmentet mot kroppens *interpolerade pose vid samma tidsstämpel*). <15 kapslar/kropp + AABB broad-phase → försumbar kostnad.

**Postur från IMU:** jaga **inte** full skelett-pose (driftrisk). 1 torso-IMU → klassificera **stå/huk/ligg + kroppsriktning**, driv ett litet bibliotek av förformade kapseluppsättningar. Lägg limb-IMU:er bara om limb-träff senare krävs.

**Precisionskonflikten (ärlig):** UWB ~10–30 cm ≈ ett huvud (~17 cm). → **Avgör ALDRIG kroppsdel ur positionsgeometrin.** Geometrin = *anländer + räckvidd/vinkel/fart*; **IR-zonen = var på kroppen.**

**Fusionsregel:**
- **HIT** = geometri ("anlände + LOS-rimligt + inom dödlig räckvidd/fart") **OCH** IR-zon inom synkfönster → registrera på **IR-zonen**, skada skalad av ballistiken.
- Geometri men ingen IR → skymning/rikoschett → **miss/near-miss**.
- IR men geometri säger "nådde aldrig fram" → förkasta (multipath/reflex). Korskollen är hela poängen.

---

## 6. Systemarkitektur — dataflöde & server-loop

> 📊 **Visuellt:** se [`system-flowchart.md`](system-flowchart.md) för komponentkarta, skottsekvens (trigger→träffad), pose-fusionslager och emitter-ring-detaljen.

**Server-auktoritativ** (som tävlings-FPS-netcode): vapen/väst skickar *signerade bevis*; **servern ensam avgör**.

**FireEvent (vapen→server, vid sear/trigger break):** `shooter_id, seq (anti-replay), t_fire (ns), muzzle_pos + kovarians, aim_vec + aim_quat, weapon_profile_id, raw UWB-ranges, ir_code (rullande), hmac`.

**IRHit (väst→server, bara om TSOP ser kodad stråle):** `target_id, t_ir_rx (HW-tidsstämpel), ir_code (matchar live FireEvent), shooter_id_decoded, zone, rssi, target_pos, body_quat, seq, hmac`.

Plus låg-rate **PlayerState** (UWB-pos + kropps-IMU-pose + tid, ~50–100 Hz) för positionshistorik/rewind.

**Adjudikations-loop (Ryzen mini-PC, tick 120–250 Hz):**
1. Ordna FireEvents på `t_fire`.
2. **Rewind** varje mål till `t_fire` (lag-kompensation à la Valve — håll ~1 s historik).
3. **Integrera ballistiken** från `muzzle_pos` längs `aim_vec`.
4. **Placera rörliga hitboxes** vid målets pose, framskjutet till kulans *ankomsttid* (5.56 @300 yd ≈ 0,4 s → springande mål hinner ~2–3 m).
5. **Skär** svept bana mot kapslar → geometrisk kandidat + zon + konfidens (ur kovarianser).
6. **Kombinera med IR LOS+zon-grind** (matchande `ir_code` inom tids-/zonfönster), annars cover/penetrations-modell.
7. **Utdata:** hit/miss + zon + skada (profil × zon × räckviddsavfall) → skytt, mål, AAR.

**Latensbudget (16–32 spelare):** banintegration <1 ms/skott; aggregerad full-auto ~500 skott/s = några ms/tick. WiFi6 upp (~2–5 ms) + tick (≤8 ms) + adjudikation (<1 ms) + ner (~2–5 ms) ≈ **15–25 ms** till "du är träffad".

---

## 7. Tidssynk (två nivåer)

| Nivå | Krav | Teknik |
|---|---|---|
| **Grov (event/rewind)** | ≤ några µs (1 ms skew × 5 m/s = 5 mm) | **PTP/IEEE-1588 över WiFi6** (HW-tidsstämpel sub-µs) — tidsstämplar `t_fire`, `t_ir_rx`, PlayerState |
| **Fin (räckvidd, 1 ns ≈ 30 cm)** | ns | **UWB DS-TWR/CFO** self-cancelar drift internt → ~10 cm utan nätverksklocka; IR-ankomst **HW-tidsstämplas** i TSOP-capture |

Kulans flygtid (100-tals ms) **modelleras**, mäts inte → inget synk-krav, bara djup på positionshistoriken.

---

## 8. Anti-fusk & rättvisa

- **Rullande nonce/CRC på IR-koden** per skott (bunden till `seq`) → inspelad strålpuls kan inte spelas upp (nonce matchar ingen *live* FireEvent).
- **Signerade rapporter** (HMAC/Ed25519 + monoton `seq`) → servern droppar dubbletter/gamla.
- **Korsvalidering:** giltig träff kräver (signerad FireEvent) ∧ (signerad IRHit med matchande nonce i fönstret) ∧ (geometrisk rimlighet). Förfalska en → faller.
- **Rå-UWB re-solve:** vapnet skickar råa ankar-ranges → servern räknar om `muzzle_pos` själv (fångar positions-spoofing).
- **Feedback:** omedelbar lågkonfidens-cue (ljud/haptik) vid lokal IR-detektering → serverns auktoritativa verdikt bekräftar. Valfritt **fördröj "du är träffad" med simulerad flygtid** (realism, servern har ändå ToF).

---

## 9. Ärliga begränsningar & ingenjörsrisker

1. **Pose/position-noggrannhet är den hårda nöten** (samma som primes) → därför är IR-ankaret obligatoriskt; rena långdistans-headshots på geometri är ute.
2. **CQB-clustering:** UWB-fel (m i NLOS) kan göra det tvetydigt *vilken* av två närstående spelare som träffades → IR-zonen + LOS löser det optiskt (IR:ns styrka i trängsel).
3. **Räckvidd/precision begränsas** av IR-länkbudget (sol) + strålkon-vinkel (ankrings-noggrannhet) — se `phase1-feasibility-sim.md`.
4. **NLOS-UWB måste detekteras & förkastas** (annars meter-fel i positionerna).

---

## 10. Fasning (uppdaterad, ärlig)

| | Fas 1 (byggsteg) | Nivå 3 (målet) |
|---|---|---|
| Träff | IR-stråle + zon (lokalt) — bevisar IR/rekyl/feedback/FSM | **server: ballistik-bana + geometri + IR-grind/zon** |
| Kräver | ESP32-P4, SFH4715AS, TSOP4856, ICM-45686 | + **UWB (DW3000) + GNSS + body-IMU + server + tidssynk** |
| Ballistik | vapenprofil lokalt | **3-DOF G7 + vind + density, RK4, server** |

Fas 1 bygger nervsystemet (IR/rekyl/feedback). **Nivå 3 är destinationen och kräver positioner + IMU + server — inte valfri bonus.**

---

## Källor (urval)
- [Breaking Defense — eBullet ersätter MILES](https://breakingdefense.com/2020/11/ebullet-brings-richer-realism-to-army-training-no-more-laser-tag/) · [Lockheed SIMRES](https://www.lockheedmartin.com/en-us/products/simres.html) · [Janes — geo-pairing SIMRES](https://www.janes.com/osint-insights/defence-news/c4isr/lockheed-martin-reveals-geo-pairing-simres-tactical-engagement-simulation-system) · [BAE HITS (ION 2020)](https://www.ion.org/publications/abstract.cfm?articleID=17741) · [Shephard — "No more lasers?"](https://plus.shephardmedia.com/analysis/decisive-edge-no-more-lasers-rethinking-live-infantry-training-with-realistic-ballistics/)
- [TDK ICM-45686 datasheet](https://invensense.tdk.com/download-pdf/icm-45686-datasheet/) · [ULTRA-Vis <10 mrad](https://www.researchgate.net/publication/258716091_Soldier-worn_augmented_reality_system_for_tactical_icon_visualization) · [TrackingPoint](https://en.wikipedia.org/wiki/TrackingPoint)
- [py-ballisticcalc](https://github.com/o-murphy/py-ballisticcalc) · [js-ballistics](https://github.com/o-murphy/js-ballistics) · [G1 vs G7 vs CDM](https://precisionrifleblog.com/2019/06/09/g1-vs-g7-vs-custom-drag-models/) · [STANAG 4355](https://en.wikipedia.org/wiki/STANAG_4355) · [JBM Ballistics](https://jbmballistics.com/ballistics/calculators/calculators.shtml)
- [Valve — Lag Compensation](https://developer.valvesoftware.com/wiki/Lag_Compensation) · [DW3000 datasheet](https://www.mouser.com/pdfDocs/DW3000DataSheet5.pdf) · [UWB-baserad IEEE-1588 (~ns)](https://real.mtak.hu/170222/1/InfocomJournal_2023_2_4.pdf) · [PTP sub-µs (Cho)](https://www.cs.utexas.edu/~mok/cs386C/papers/PTP1588_Cho.pdf)
- [ANSUR antropometri](https://mreed.umtri.umich.edu/mreed/downloads/anthro/ansur/ADAS-Dimension_Definitions.pdf) · [Deep Inertial Poser (6 IMU)](https://arxiv.org/pdf/1810.04703) · [CRISAT/STANAG 4512](https://en.wikipedia.org/wiki/Collaborative_Research_into_Small_Arms_Technology) · [MILES kodord (GlobalSecurity)](https://www.globalsecurity.org/military/systems/ground/miles.htm)
