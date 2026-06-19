# STRILAS — GEMENSAM-KOMPONENT-SAMPLER (DEMO · EJ FÖR TILLVERKNING)

Samma idé som IMU-samplern, fast för **de återkommande passiva/diskreta/regulator-delarna**. Ladda
upp `common-sampler-bom.xls` till NextPCB → se vilka som finns i **basic-biblioteket / lager** → välj
in-stock-varianter och **standardisera ALLA kort på samma delar** (ett paket per värde, inga one-offs,
inga extra-setup-avgifter). Tillverkas inte.

## Filer
`common-sampler-gerbers.zip` · `common-sampler-bom.xls` (28 delar) · `common-sampler-centroid.csv`.

## Komponent-inventering (alla 5 tillverkade kort)

| Del | Paket idag | Kort som använder | Antal | Status |
|---|---|---|---|---|
| **C 100nF** | **0402 OCH 0805** | weapon, firecontrol, helmet, vest | 9× 0402 + 16× 0805 | ⚠ **två paket — standardisera** |
| **C 1uF** | **0402 OCH 0805** | firecontrol(0402), weapon+helmet(0805) | 1× 0402 + 8× 0805 | ⚠ **två paket — standardisera** |
| C 10uF | 1206 | weapon, helmet, vest | 6 | ★ gemensam, konsekvent |
| C 22uF | 1206 | helmet, vest | 2 | ok |
| C 100uF | 1210 | weapon, vest | 2 | ok |
| C 100pF | 0805 | weapon | 1 | ok (C0G) |
| R 10k | 0805 | helmet, vest | 4 | ★ gemensam |
| R 4k7 | 0805 | firecontrol, helmet | 6 | I²C-pullup |
| R 220R / 31.6k | 0805 | helmet, vest | 2+2 | ok |
| R 100R/1k/2.2k/15k/100k | 0805 | weapon/helmet | 1 ea | ok (alla 0805 ✓) |
| R 10R | 2512 | helmet, vest | 6 | effekt (LED-serie) |
| R 0R2 | 2512 | weapon | 1 | CC-sense |
| BAT54 | SOD-123 | helmet, vest | 8 | ok |
| AO3400 | SOT-23 | helmet, vest | 2 | ok |
| AO3401 / AOD4184A / SMBJ12A | SOT-23 / TO-252 / SMB | weapon | 1 ea | optik-specifika |
| L 4.7uH | FNR5040 | helmet, vest | 2 | buck |
| AP63203 / HT7333 / OPA171 | TSOT23-6 / SOT-89 / SOT23-5 | helmet+vest / vest-patch / weapon | — | regulator/op-amp |

## Konsoliderings-rekommendation (efter lager-koll)
1. **Motstånd:** redan nästan helt **0805** → behåll 0805 som standard, **2512** endast för effekt
   (10R LED-serie, 0R2 CC-sense). Inget att ändra utom att bekräfta in-stock.
2. **100nF:** välj **ETT** paket för hela projektet. Förslag: **0805** (mest använt, lättast handlöda,
   basic-lib) — om hjälm-kortet behöver tätare packning kan 0402 väljas istället, men då för ALLA.
3. **1uF:** standardisera till **0805** (firecontrols enda 0402:a byts).
4. Bekräfta de mindre vanliga (31.6k, 0R2, 100pF C0G, AOD4184A, OPA171, HT7333) finns i lager;
   annars välj närmaste in-stock-ekvivalent och uppdatera netlistorna.

## LAGER-KOLL RESULTAT (NextPCB) + valda MPN
24/28 auto-matchade (18 **In Stock**, 6 kort lead 4–7 d); 4 manuellt offererade. Valda MPN (nu i
`gen_nextpcb.py`, paket-medvetet → samma MPN per (värde,paket) på ALLA kort):

| Del | Vald MPN | Status |
|---|---|---|
| 100nF **0805** | CL21B104KBCNNNC | ✅ In Stock — **projekt-standard** |
| 100nF 0402 | CL05B104KO5NNNC | 4–7 d (kvar där footprint är 0402) |
| 1uF **0805** | GRM21BR61E105KA99L (Murata) | bytt fr ej-matchad CL21A105KAFNNNG |
| 1uF 0402 | CL05A105KP5NNNC | ✅ In Stock |
| 100pF / 10uF / 22uF | CL21C101JBANNNC / CL31A106KBHNNNE / CL31A226KAHNNNE | ✅ In Stock |
| 100uF 1210 | CL32A107MQVNNNE (Samsung) | bytt fr ej-matchad GRM32ER61E107ME20L |
| R 4k7/220R/15k/31.6k/100k 0805 | RC0805FR-… | ✅ In Stock |
| R 10k/100R/1k/2.2k 0805 | RC0805FR-… | 4–7 d (jellybean, alltid sourcbar) |
| BAT54 / SMBJ12A / AO3400 / AO3401 / AOD4184A | BAT54-7-F / SMBJ12A / AO3400A / AO3401A / AOD4184A | ✅ In Stock |
| AP63203 / HT7333 / OPA171 | AP63203WU-7 / HT7333-A / OPA171AIDBVR | ✅ In Stock |
| R 0R2 2512 (CC-sense) | PE2512FKE070R200L | ⚠ manuell offert (footprint-specifik) |
| L 4.7uH FNR5040 | FNR5040320R47M | ⚠ manuell offert (footprint-specifik) |

## Status — vad som är gjort vs kvar
**KLART (utan kort-ändring):** `gen_nextpcb.py` använder nu paket-medvetna in-stock-MPN ovan,
samma per (värde,paket) på ALLA kort. Alla board-BOM:er regenererade. Korten är beställbara som de är
(0805-delar in-stock, 0402/jellybean kort lead, 2 footprint-specifika manuellt offererade).

**KVAR (valfritt, kräver omroutning):** äkta *en-paket-per-värde*-konsekvens. 100nF används fysiskt i
både 0402 (optik 2, firecontrol 5, helmet 2) och 0805; 1uF i både. Att tvinga ett paket kräver
footprint-byte → omplacering+routning av just de C:na på optik/firecontrol/helmet (firecontrol är
litet/tätt, helmet tätt → 0402→0805 = större, viss risk; 0805→0402 = mindre, säkrare). **Rekommendation:**
behåll båda paketen för prototypen (alla varianter sourcbara) — gör en-paket-unifieringen inför
produktion. Säg till vilket paket (förslag 100nF→0805 in-stock, 1uF→0402 in-stock) så kör jag omroutningen.
