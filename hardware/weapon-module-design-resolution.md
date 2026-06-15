# STRILAS — Vapen-optikmodul: full designupplösning (inga genvägar)

> Mål: ta modulen från placerings-sketch → **korrekt, byggbar spec**. Varje känt
> problem listas med **beslut + konkreta värden + motivering**. Det som *måste mätas*
> (ögonsäkerhet, exakt kameramodul) är utpekat som mätpunkter — det är rätt process,
> inte en genväg.

---

## 0. Den avgörande låsningen: två våglängder (löser självbländning + optimerar båda vägar)

| Funktion | Väg | **Våglängd** | Filter |
|---|---|---|---|
| **SKOTT** (vapen-emitter → måls TSOP) | D1/D2 | **940 nm** | måls-TSOP + **940 nm** bandpass |
| **POSE-konstellation** (måls LED → vapnets sikteskamera) | mål-LED | **860 nm** | sikteskamera NoIR + **860 nm** bandpass |

**Varför detta löser allt:** sikteskamerans 860 nm-bandpass **avvisar vapnets egna 940 nm-
skott** → **ingen självbländning** (inget beroende av timing/baffel). Dessutom optimalt per
väg: **940 nm = TSOP-känslighetstopp** (~950 nm), **860 nm = bättre kisel-QE** i kameran →
konstellationen syns på avstånd. 56 kHz-bärvågen är *modulation*, oberoende av våglängd.

> Konsekvens (LÅST): skott-LED = **Vishay VSMA1094750X02 (äkta 940 nm, 945 nm topp)**, 1,5 A DC /
> 5 A pulsat, AEC-Q102 — datablad + footprint klara. *(Tidigare "OSLON Black 940 nm SFH 4715AS"
> var fel: OSLON "AS" är 850/860 nm.)* TIR-kollimator för 3,4 mm-källa. Konstellation = billiga
> 860 nm-LED på målet.

---

## 1. Optik

| # | Problem | Beslut |
|---|---|---|
| 1.1 | Självbländning | **Löst** via våglängdssplit (§0). Baffel = defense-in-depth, ej bärande. |
| 1.2 | FOV-val (telefoto kontra bred) | **FOV är en avvägning, inte ett fast tal.** Det tidigare "telefoto krävs" gällde *passiva ArUco* (avkoda mönster → ~20–30 px på markören → smal FOV @150 m). Vi bytte till **aktiv IR-konstellation** (lokalisera ljuspunkter → få px + subpixel räcker) → **bäringsprecisionen är trivial vid vilken FOV som helst** (30° → 0,013°/px, subpixel ~0,001° ≪ kravet 0,19°). **MEN** smalare FOV/längre brännvidd ger bättre **dagsljus-SNR @150 m** (större bländare, mer signal mot sol). → Sätt FOV av §1.3-testet; trolig landning **15–30°** (smalare = mer räckviddsmarginal; bredare = lättare målfångst, ±7,5° @15° är ändå lätt med grovsikte). |
| 1.3 | Syns konstellationen @150 m i dagsljus? (= det som egentligen sätter FOV) | Konstellations-LED **modulerade** (frame-differencing) + 860 nm-bandpass + tillräcklig **strålstyrka** (~0,5–1 W/sr/LED, ev. lätt kollimerade) + vald **brännvidd**. **Mätpunkt** vid bringup → bestämmer både LED-effekt och FOV. |
| 1.4 | Carclo-linsmontering | 3 **pins** per lins ner i PCB-hål (Carclo-footprint) + lim; LED i optiskt centrum; montera **efter** reflow. |
| 1.5 | Baffel | Svart shroud-ring mellan emittrar och linsbarrel (blockerar sidoljus/scatter). |
| 1.6 | Fokus | M12 fast-fokus satt på **hyperfokal** för engagemangsavstånd (konstellationen är ändå punktkällor → tolerant). |

---

## 2. Emitter-driver (skottet)

| # | Problem | Beslut |
|---|---|---|
| 2.1 | "Rsense som strömgräns" är inte konstant ström | **Hårt HW-strömtak (Rset = R2, 3R3 2W)** sätter Imax oberoende av firmware → "ögonsäkerhet i hårdvara". Det här är vad som är **byggt på kortet** (enkelt, robust, få komponenter). |
| 2.2 | Topologi — **BYGGD v1 = Rset-tak + N-FET-gate** | VBAT 2S (6,4–8,4 V) → **R2 (Rset)** → LED-sträng 2× Vf(940 nm) → **Q1 (N-FET)** mot GND. C2 (220 µF) levererar pulsen. *Buck-CC (nedan) är en **effektivitetsuppgradering**, ej i v1-netlistan.* |
| 2.2b | (Framtida) Buck-CC-uppgradering | VBAT > LED-sträng → steg **ner**; kräver **L1** + **Cin** + freewheel-diod + Rsense. Ger högre verkningsgrad än Rset men fler delar. **Inte** i det routade kortet. |
| 2.4 | 56 kHz-modulering | **Q1 (AO3400) i serie** gatar bärvågen mot GND (RMT från P4 driver gaten via R3). |
| 2.5 | Inskydd | **Reverse P-FET (Q2)** + **TVS** + **PTC (F1)** på VBAT — PTC:s **håll-ström > pulsens medel** (annars nuisance-trip). |

---

## 3. Ögonsäkerhet — riktig bedömning (inte gissning)

**Radiometrisk output (vår modell, 2× 940 nm Vishay, ±5° TIR, 1 A):** Ie ≈ **~54 W/sr** kombinerat.
Irradians vid ögat: `E = Ie / d²`. Värsta fall (någon **1 m** från mynningen): E ≈ 54 W/m² →
genom 7 mm-pupill (3,85·10⁻⁵ m²) ≈ **2,1 mW in i ögat** (pulsat, låg duty).

**Detta är inte trivialt Class 1.** Bedömning per **IEC 60825-1** krävs, med:
- **Definierat pulsformat:** 56 kHz-bärvåg, paket ~14 ms, max repetition (semi: få Hz; full-auto: ~10–15 Hz). Lås detta i firmware (oöverstigligt).
- **Mätvillkor:** radiant effekt genom 7 mm apertur vid 100 mm & 14 mm, inom acceptansvinkeln, för det verkliga pulståget — jämför mot AEL (worst-of: enkelpuls / medel / pulståg).
- **Extended-source-lättnad:** LED (inkoherent, utsträckt) ger högre tillåten exponering än laser — vår fördel.

**Beslut/regel:**
1. CC-driverns sense-resistor sätter **absolut HW-tak**; **börja på 1 A**.
2. Köp räckvidd med **mottagar-bandpass** före mer ström.
3. **MÄT AE vid aperturen** (optisk effektmätare) och få Class 1-utlåtande **innan** modulen pekas mot människor.

> Detta är en **mätpunkt**, inte en genväg: ögonsäkerhet får aldrig härledas ur minnet.
>
> **Kalkyl gjord:** se [`eye-safety-budget.md`](eye-safety-budget.md) + [`eye_safety_budget.py`](eye_safety_budget.py).
> Konservativ punktkälla → max **~0,1 A full-auto / ~0,67 A semi**; men utsträckt-källa-relaxation
> (C6 upp till ~67×) gör **1–3 A Class 1 *om* skenbar källa ≥ α_max** — **måste mätas**.

---

## 4. Termik

Vf(940 nm) ~2 V @ 3 A → ~6 W/LED *under puls*. Men **låg duty** (14 ms-paket @ ~10 Hz ≈ 14 %)
→ snitt ~0,8 W/LED. **Beslut:** kopparpour + **termiska vias** under varje LED:s thermal-pad;
FET (AO3400, låg Rds) klarar pulsat. Verifiera junction-temp vid värsta full-auto-duty.

---

## 5. IMU — 1× ICM-45686 (SPI) — array BORTTAGEN

- **1 IMU på SPI** (SPI för hög ODR vid rekyl-transienten). **Arrayen borttagen** efter
  fysik-verifieringen: kameran re-ankrar attityden varje frame → inter-frame-drift **0,0005°**
  (@60 fps) ≪ krav. 4 chip gav försumbar vinst → onödig yta/komplexitet.
- **Stel koppling** till optisk axel (samma styva kort) — kritiskt för kamera-IMU-extrinsics.
- 100 nF avkoppling; SPI-linjer korta. **Extrinsisk kalibrering** (IMU↔kameraram) en gång.

---

## 6. Kameragränssnitt (löser MIPI-SI-problemet genom att undvika det)

**Ingen kamera-elektrik på detta kort.** Kameramodulen sitter mekaniskt **bakom** kortet (lins
genom Ø16-urtaget) och ansluts till P4 via **USB-kabel** — inte via detta kort. Kortet bär bara:
emitter-driver (effekt), IMU (SPI), P4-carrier-header, batteri-in. → ingen kamera- eller
höghastighets-differential-routing här.

**Vald kamera (LÅST): USB OV9281 mono GLOBAL SHUTTER NoIR** (1 MP 1280×800, 3 µm, 1/4″, USB-UVC →
P4:ans USB OTG 2.0 HS). **⚠️ Måste vara NoIR** (inget IR-cut), annars syns ingen 860 nm-konstellation.
**Lins: 12 mm M12 (~18° FOV)** — fysiken kräver det för 150 m (1 MP @ 6mm/35,5° upplöser bara ~9 px
konstellation → LED:erna smälter ihop; 12 mm ger ~8 px separation + 18 px baslinje → SNR ≈ 87, robust PnP).
Global shutter (OV9281) → ingen pan-smet i grunden; kort exponering + modulerade LED ger ren blob-
detektion i dagsljus. (En 6 mm-lins kan behållas om man nöjer sig med robust räckvidd ~80 m.)

**Avstånd:** kommer ur **PnP** (konstellationens kända bas + vinkelutbredning); i v1 mäts målets
position med måttband. **Ingen LiDAR behövs** (superseder av PnP; kan återkomma endast för markörlöst avstånd).

---

## 7. Kontakt & signaler (J1, 2×4) + skydd

**J1 = 2×5:** `VBAT · EN · IR_MOD · SCK · MOSI / GND · 3V3 · GND · MISO · CS`
(SPI för 1 IMU). Trigger går **direkt till P4-GPIO** (på greppet), ej via modulen.
**ESD:** serieresistor + TVS/ESD-diod på IR_MOD och SPI-linjerna.
*(VBAT/GND ev. dubblerade pinnar för pulsström — se §9.5.)*

---

## 8. Boresight & kalibrering (procedurer, en gång)

1. **Kamera-intrinsics** (brännvidd, distorsion) — schackrutemönster.
2. **Kamera-IMU-extrinsics** — relativ orientering.
3. **Boresight-zero** — kameran mäter var skotten landar vs retikel → lagra offset (emittrarna
   är monterade parallellt; firmware-zero tar resten).
4. **Konstellationsgeometri** mätt + lagrad (PnP-modell).

---

## 9. PCB-layoutregler

- **4-lager** (signal / GND / VBAT-pour / signal): solid GND-plan, separat effekt-pour för
  pulsströmmen, stjärnjordning vid sense-resistorn.
- Pulsström-loopen (Cin → buck → L1 → LED → FET → sense) **kort & bred**; MLCC nära LED.
- Termiska vias under LED-pad till baksidans pour.

---

## 9.5 Designgranskning — fynd & optimering

**Funktionellt (åtgärdat):**
- ✅ **Buck-switchens passiva tillagda** (L1 + Cin + D5 freewheel + Cout) — saknades; boost→buck rättat (§2).
- **Per-IC-avkoppling explicit:** 100 nF/IMU, U6 in/ut-caps, 3V3-buss-MLCC. (Schema-detalj, måste ritas.)

**Elektrisk optimering:**
- **EMI:** buck-switchern (U6) är störkälla mot kamera-MIPI/IMU. Placera bort från kamera, skärma,
  och kör helst drivern **bara under skott** (pulsad ändå). Switchfrekvens bort från känsliga band.
- **Pulsström på J1:** VBAT/GND vid 1–3 A puls → **dubbla pinnar / separat effektkontakt**; stjärnjord vid Rsense.

**Mekaniskt / miljö (rekylerande vapen, utomhus):**
- **Låsande + dragavlastade kontakter** (FFC + J1) mot rekylvibration.
- **Kamerafokus-lås** (gänglås/lim på M12) + lins-/filter-retention.
- **Conformal coating** (fukt/damm); stel IMU-montering (redan §5).

**Bekräftat (ingen åtgärd):**
- Kamerans matning + SCCB (I²C-styrning) kommer från **P4:ans CSI-kontakt** → inga kamerarails på detta kort.
- Trigger → direkt P4-GPIO (greppet), ej via modulen.
- ⚠️ **Välj/verifiera TIR-kollimator** för Vishay VSMA1094750 (3,4 mm-källa) → strålvinkel ≤ ±7,5°.

---

## 10. Kvarvarande MÄTPUNKTER (ärlig lista — inte olösta "problem", utan saker som *kräver* mätning)

| Mätpunkt | Hur |
|---|---|
| **Class 1-AE** | optisk effektmätare + IEC 60825-1-villkor, vid låst pulsformat |
| **Exakt kameramodul-mått** | mät OV9281 USB-modulen → lås `CAM_W/H/HOLE` (lins genom Ø16) |
| **Konstellations-synlighet @150 m dag** | bringup-test, justera LED-effekt/modulering |
| **Junction-temp vid full-auto** | termisk mätning vid värsta duty |
| **Räckvidd vs ström** | fälttest, sätt CC-tak till lägsta som klarar 150 m |

Allt annat ovan är **beslutat och låst.**
