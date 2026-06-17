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

**Hur (fysik):** en platt SMD-LED på ett liggande kort lyser uppåt; inget rent-PCB-sätt ger horisontell
stråle. Lösning utan att offra räckvidden: behåll **högeffekt-OSLON** (maskinplacerad vid kanten r48.5,
radiellt orienterad) + en **45°-omriktningshållare/optik per LED** (köps separat, monteras manuellt —
som Carclo-linshållaren på skott-emittern) som viker strålen 90° ut mot horisonten.
- Fallback om 45°-IR-optik ej finns: vinklad hållare som lutar LED:n ut, eller **ledad IR-emitter böjd
  utåt** som TSOP:erna (matchar mottagaren bokstavligt, enklare — men lägre effekt → verifiera 150 m).
  OSLON-vägen bevarar dagsljus-budgeten; ledad-vägen måste bänk-verifieras.

De **4 hjälm-patcharna** (skalet, utåtvända) bidrar fortsatt. Systemnivå: disc-LED (sido, horisont) +
patchar → från vilken skyttvinkel som helst ser kameran flera face-on punkter → robust PnP.

## Att bekräfta på bänk
- Sourcing: 45° omriktnings-optik/hållare för 860 nm OSLON (köps separat, manuell montering).
- Blob-SNR vid sneda vinklar @150 m dagsljus efter omriktning (LED-lobens kant).
