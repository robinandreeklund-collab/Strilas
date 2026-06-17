# STRILAS — konstellations-täckning (LED-riktning vs mottagar-vinkel)

> Figur: [`skott-flode.png`](skott-flode.png)

## Frågan (bra observation)
Konstellations-LED:erna är SMD och lyser **vinkelrätt ut ur kortet** ("rakt upp"), medan TSOP-
mottagarna sitter böjda ~40–90°. Hur ger LED:erna en tydlig ljusbild då?

## Svar: LED:ens "mottagare" är skyttens KAMERA — inte TSOP:erna
Två **separata** optiska vägar:
- **TSOP (940 nm):** tar emot *skottet* från vapnet. Böjs utåt för bred skott-/LOS-täckning.
- **LED (860 nm):** ses av **skyttens kamera** långt borta. Kameran är "mottagaren". LED:ens
  riktning behöver alltså **inte** matcha TSOP:ens böjning.

## Konstellationen läses som en HELHET (därför spelar per-patch-mismatch ingen roll)
Kameran löser spelarens **6-DOF-pose ur alla LED-punkter den ser samtidigt** (patcharna som är
vända mot skytten) och mappar sedan träffen på 3D-modellen. Den behöver **inte** se just den
träffade patchens egna LED. Per-patch har LED:en ~±60° (OSLON 4715AS) medan TSOP:erna täcker
bredare — men det är ofarligt eftersom posen kommer från **alla synliga patchar** ihop.

## "Rakt upp" beror på monteringsytan
- **Patch (lim på utåtvänd yta — bröst/axel/hjälmsida):** "rakt upp ur kortet" = **rakt ut mot
  hotriktningen**, där skyttarna/kamerorna är. OSLON ~±60° → ~120° kon framåt. Rätt.
- **Hjälm-DISCEN (plant ovanpå hjälmen, F9P-puck uppåt):** dess 6 LED pekar **uppåt** → bidrar mest
  för förhöjda/ovanifrån-vinklar, knappt horisontellt.

## Beslutad arkitektur — SIDO-EMITTERANDE disc-LED (uppdaterad)
En LED som lyser rakt upp ur den liggande discen syns knappt för en kamera i ögonhöjd @150 m → dålig
PnP. Därför görs discens 6 konstellations-LED **sido-emitterande, riktade RADIELLT UT mot horisonten**
så de matchar de utåt-böjda TSOP-mottagarna och faktiskt syns för skytten.

**Hur (fysik + vald lösning):** en platt SMD-LED på ett liggande kort lyser uppåt; inget rent-PCB-sätt
ger horisontell stråle. Research visade dessutom: högeffekt-IR (krävs @150 m dagsljus) finns BARA som
topp-emitterande (OSLON-dom/chip-on-star) — högeffekt SIDO-emit-SMD existerar inte (right-angle IR =
20–50 mA, för svaga). **Lösning (`hardware/led_tab.py`): LED-TAB micro-PCB.** En liten egen PCB (~6×11 mm)
med EN högeffekt-OSLON SFH4715AS + 2-håls fot. NextPCB SMT-placerar OSLON:en (löser den svåra handlödningen),
kund löder en **RIGHT-ANGLE (90°) stiftlist** i foten (samma 2-håls mönster som en rak list) → den håller taben
**STELT LODRÄT** mot discen — ingen handböjning, samma vinkel varje exemplar. OSLON:en strålar då vågrät radiellt
ut mot horisonten, precis som de utåt-böjda TSOP-mottagarna.
→ Full OSLON-effekt (dagsljus-budgeten intakt) + rätt aim utan handarbete + ingen exotisk optik. Discen (D5–D10) har
6 tab-socklar (2 hål) där den vinklade fotens stift löds in (3 serie-par via disc-spår + 3 serieR 2512 på discen).
Konstellations-LED behöver ingen precis position (PnP kalibrerar grov vinkel) — bara optikens
skott-emitter (under Carclo-linsen) kräver precisionsplacering.

De **4 hjälm-patcharna** (skalet, utåtvända) bidrar fortsatt. Systemnivå: disc-LED (sido, horisont) +
patchar → från vilken skyttvinkel som helst ser kameran flera face-on punkter → robust PnP.

## Att bekräfta på bänk
- Sourcing: right-angle (90°) 1×2 2.54 mm stiftlist (standarddel) som tab-fot — håller OSLON:en lodrät.
- Blob-SNR vid sneda vinklar @150 m dagsljus (OSLON-lobens kant; ingen omriktningsoptik behövs — vågrät stråle direkt).
