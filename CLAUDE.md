# STRILAS — projektanteckningar för Claude

IR-vapen/laser-tag-system. PCB:er i `hardware/` (KiCad 7, `kicad-cli` 7.0.11), färdigt
tillverkningsunderlag per kort i `leverans/`. Kretsar definieras i kod (SKiDL `*_netlist.py`
→ `*.net`) och placeras/routas via pcbnew-skript i `hardware/`.

## ⚠️ REGEL: ändrar du ett PCB → uppdatera `leverans/`

`leverans/<kort>/` är det FÄRDIGA underlaget som skickas till tillverkning. **Varje gång ett
`hardware/*.kicad_pcb` ändras (placering, routning, footprints, hål, outline, …) MÅSTE
motsvarande artefakter regenereras och kopieras till `leverans/<kort>/`** — annars speglar
gerbers/STEP/BOM/centroid ett gammalt kort. Håll även `leverans/LÄS-MIG.md` (kort-dimensioner
m.m.) i synk.

### Kort → leverans-mapp
| `hardware/*.kicad_pcb` | `leverans/` | noter |
|---|---|---|
| `weapon-module` | `optik/` | OBS namnbyte; har även `optik-PROTOTYP-*` (IMU obestyckad) |
| `firecontrol` | `firecontrol/` | |
| `vest-patch` | `vest-patch/` | |
| `helmet-mb` | `helmet-mb/` | |
| `vest-mb` | `vest-mb/` | |
| `led-tab` | `led-tab/` | micro-PCB (genereras av `hardware/led_tab.py`) |

### Artefakter per kort (alla ska uppdateras)
`<kort>-gerbers.zip`, `<kort>-bom.xls`, `<kort>-centroid.csv` + `.xls`, `<kort>.step`.

### Regenerera (utan att förstöra befintlig routning)
- **BOM + centroid** (alla kort på en gång): `cd hardware && python3 ../vapen-stack/gen_nextpcb.py`
  → skriver `hardware/nextpcb/*`. Kopiera sedan rätt filer till `leverans/<kort>/`.
- **Gerbers + STEP UTAN omroutning** (bevarar spåren):
  ```sh
  python3 hardware/strip_fab_silk.py hardware/<kort>.kicad_pcb   # dölj ref-des/titel på silk (NextPCB monterar från centroid/BOM; texter hamnar annars över pads)
  kicad-cli pcb export gerbers -o /tmp/gb/ hardware/<kort>.kicad_pcb
  kicad-cli pcb export drill   -o /tmp/gb/ hardware/<kort>.kicad_pcb
  (cd /tmp/gb && zip -r - .) > leverans/<kort>/<kort>-gerbers.zip
  kicad-cli pcb export step -f --subst-models -o leverans/<kort>/<kort>.step hardware/<kort>.kicad_pcb
  ```
- **Omroutning** behövs bara om kortet är OROUTAT (0 segment). Då: `python3 hardware/route_<kort>.py`
  (freerouting, icke-deterministiskt; exporterar gerbers + STEP själv). Kör ALDRIG `route_*.py` på ett
  redan routat kort om du vill behålla spåren — det nollställer och routar om från grunden.
- **Byta footprint på plats utan att tappa routning**: följ mönstret i `hardware/swap_led_tab.py`
  (ladda board, ersätt FOOTPRINT på samma läge/vridning/nät; ETT kort per process pga pcbnew-SWIG
  ger otypat board-objekt vid andra `LoadBoard()` i samma process).

### Verifiera innan commit
- **DRC**: 0 unconnected + 0 clearance (samma kontroll som i `route_patch.py` / `route_helmet_mb.py`).
- **STEP är INTE byte-deterministisk** (tidsstämpel + entitets-ordning skiljer mellan körningar).
  Jämför ALDRIG `.step` med `diff` — verifiera currency via bounding-box + masscentrum med cadquery
  (`importStep(p).val().BoundingBox()` / `.Center()`); matchar de mot en färsk export på < 0,01 mm är
  STEP-filen aktuell. BOM (`xlwt`-`.xls`) + centroid (`.csv`/`.xls`) ÄR deterministiska → byte-jämförbara.
- **Gerber-jämförelse**: strippa datum-/kommentarrader (`CreationDate`, `TF.`, `G04`, Excellon `;`)
  innan `diff`, annars ser allt ut att ha ändrats.

## Netlistor (SKiDL)
`*_netlist.py` → `*.net`. SKiDL genererar nya slumptaggar/tstamps varje körning → stora men
icke-substantiella diffar. Verifiera att bara den avsedda ändringen skedde genom att jämföra
KONNEKTIVITETEN (`{netnamn: sorterade (ref,pin)}`) mot HEAD, inte råa diffen.

## Footprint-bibliotek
Projektets egna footprints ligger i `hardware/strilas.pretty/` och refereras som `strilas:<namn>`.
3D-modeller som hör till dem (t.ex. `hardware/led-tab-3d.step`) refereras via `${KIPRJMOD}/…` och
löses relativt `.kicad_pcb`-filens katalog vid STEP-export.
