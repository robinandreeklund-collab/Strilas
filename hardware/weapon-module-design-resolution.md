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

> Konsekvens: skott-LED = **940 nm OSLON Black-syskon** (samma paket som SFH 4715AS → Carclo
> 10195 passar; **verifiera P/N**). Konstellation = billiga 860 nm-LED på målet.

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
| 2.1 | "Rsense som strömgräns" är inte konstant ström | **Konstantströms-driver** (CC): FET + sense-resistor + reglering. Sense-resistorn sätter ett **hårt HW-tak**; firmware kan bara gå *lägre*. Det är "ögonsäkerhet i hårdvara" på riktigt. |
| 2.2 | Spänningsbudget för 2 LED i serie | 2× Vf(940 nm) ≈ 3–4 V + CC-headroom + sense → **VEMIT = boost till 9–12 V** (ren marginal vid 1–3 A). 2S (6,4–8,4 V) duger bara ≤~1,5 A. |
| 2.3 | Reservoarkondensator | 56 kHz-burst: cap levererar pulsen, batteriet snittet. **220–470 µF låg-ESR** + MLCC nära LED. |
| 2.4 | Inskydd | **Reverse-polarity P-FET (Q2)** + **TVS** + **PTC/säkring** på VEMIT-ingången. |

---

## 3. Ögonsäkerhet — riktig bedömning (inte gissning)

**Radiometrisk output (vår modell, 2× 940 nm, ±5° Carclo, 1 A):** Ie ≈ **~54 W/sr** kombinerat.
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

---

## 4. Termik

Vf(940 nm) ~2 V @ 3 A → ~6 W/LED *under puls*. Men **låg duty** (14 ms-paket @ ~10 Hz ≈ 14 %)
→ snitt ~0,8 W/LED. **Beslut:** kopparpour + **termiska vias** under varje LED:s thermal-pad;
FET (AO3400, låg Rds) klarar pulsat. Verifiera junction-temp vid värsta full-auto-duty.

---

## 5. IMU — 1–4 SPI-array (bestyckad 1)

- **Layout för 1–4× ICM-45686 på SPI** (egen CS/chip; I²C ger bara 2 adresser). **Bestycka 1.**
  Kameran (90 fps GS) re-ankrar attityden var ~11 ms → IMU:n fyller bara gapen → **1 räcker**;
  arrayen är zero-regret-reserv (redundans + renare gap-prediktion) om mätning visar behov.
- **Stel koppling** till optisk axel (samma styva kort) — kritiskt för kamera-IMU-extrinsics.
- 100 nF avkoppling/chip; SPI-linjer korta. **Extrinsisk kalibrering** (IMU↔kameraram) en gång.

---

## 6. Kameragränssnitt (löser MIPI-SI-problemet genom att undvika det)

**MIPI-CSI dras INTE på detta kort.** Kameramodulen sitter mekaniskt i centrum (standoffs
genom urtaget) men dess **FFC går direkt till P4:ans CSI-kontakt**. Detta kort bär bara:
emitter-driver (effekt), IMU (I²C), kontakt. → ingen höghastighets-differential-routing här.

**Vald kamera: ams-OSRAM MIRA220MINI (mono, global shutter, NIR).** Eftersom vi gör custom PCB
byts OV5640 ut direkt — **global shutter** är korrekt för ett rörligt vapen (rolling shutter
smetar/skevar under panorering → korrumperar blob-centroiderna → bäringsfel i rörelse). NIR →
ser 860 nm bättre. Optiskt format ~1/3" (aktiv ~4,46×3,91 mm) → M12-brännvidd för FOV 15–30°.

**Exakt footprint** från ams-OSRAM:s **öppna PCB-filer** (`github.com/ams-OSRAM/ams-Mira-Image-Sensors`)
→ urtag + standoff-hål direkt ur källan, ingen mätning. **Avvägning:** P4-drivrutin är exempel-grade
(mer integrationsjobb), högre kostnad/ledtid än gratis-OV5640.

---

## 7. Kontakt & signaler (J1, 2×4) + skydd

**J1 = 2×7:** `VBAT · EN · IR_MOD · SCK · MOSI · MISO · INT / GND · 3V3 · GND · CS1 · CS2 · CS3 · CS4`
(SPI för IMU-arrayen, 4 CS). Trigger går **direkt till P4-GPIO** (på greppet), ej via modulen.
**ESD:** serieresistor + TVS/ESD-diod på IR_MOD och SPI-linjerna.

---

## 8. Boresight & kalibrering (procedurer, en gång)

1. **Kamera-intrinsics** (brännvidd, distorsion) — schackrutemönster.
2. **Kamera-IMU-extrinsics** — relativ orientering.
3. **Boresight-zero** — kameran mäter var skotten landar vs retikel → lagra offset (emittrarna
   är monterade parallellt; firmware-zero tar resten).
4. **Konstellationsgeometri** mätt + lagrad (PnP-modell).

---

## 9. PCB-layoutregler

- **4-lager** (signal / GND / VEMIT-pour / signal): solid GND-plan, separat effekt-pour för
  pulsströmmen, stjärnjordning vid sense-resistorn.
- Pulsström-loopen (cap → LED → FET → sense) **kort & bred**; MLCC nära LED.
- Termiska vias under LED-pad till baksidans pour.

---

## 10. Kvarvarande MÄTPUNKTER (ärlig lista — inte olösta "problem", utan saker som *kräver* mätning)

| Mätpunkt | Hur |
|---|---|
| **Class 1-AE** | optisk effektmätare + IEC 60825-1-villkor, vid låst pulsformat |
| **Exakt kameramodul-mått** | mät kitets OV5640 → lås `CAM_W/H/HOLE` |
| **Konstellations-synlighet @150 m dag** | bringup-test, justera LED-effekt/modulering |
| **Junction-temp vid full-auto** | termisk mätning vid värsta duty |
| **Räckvidd vs ström** | fälttest, sätt CC-tak till lägsta som klarar 150 m |

Allt annat ovan är **beslutat och låst.**
