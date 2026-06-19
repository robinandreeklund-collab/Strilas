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

## Efter lager-kollen — så standardiserar vi
- Uppdatera `*_netlist.py` så 100nF/1uF använder det valda paketet överallt, och byt ev. värden
  till in-stock-MPN. Regenerera `.net`.
- Uppdatera MPN-tabellen i `vapen-stack/gen_nextpcb.py` med de valda MPN:erna.
- Footprint-byte (0402↔0805) på de berörda korten kräver omplacering+routning av just de C:na —
  liten ändring; säg till så kör jag när du valt paket.
