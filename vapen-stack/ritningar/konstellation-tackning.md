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

## Beslutad arkitektur (rekommendation, vald)
- **Horisontell huvud-konstellation = de 4 hjälm-PATCHARNA** (på skalet, utåtvända — som kroppspatcharna).
- **Hjälm-discens 6 LED = bonus uppåt/förhöjt.**
- 360°-täckning på systemnivå: distribuerade patchar (kropp fram/bak/sidor + hjälmsidor) → från
  vilken skyttvinkel som helst är flera patchar face-on → tillräckligt med punkter för robust PnP.

## Att bekräfta på bänk
Verklig blob-SNR vid sneda vinklar @150 m dagsljus (LED-lobens kant). Om sido-synlighet blir knapp:
fler patchar hellre än smal lins; ev. sido-emitterande/vinklade LED på discen som senare steg.
