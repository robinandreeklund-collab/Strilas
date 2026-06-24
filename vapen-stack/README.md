# STRILAS — vapen-stack (ren leveransmapp)

Allt för den kompletta vapen-stacken i **en mapp**: tre kort, hopsättnings-STEP,
verifiering och komplett BOM. Källkoden (generatorerna) ligger kvar i `../hardware/`.

## Stacken (uppifrån och ned)
```
FC-kort   (fire-control)  ── socket J1 → P4 edge A (12)  ·  J2 → P4 edge B (3V3-tapp)
ESP32-P4  (Waveshare)     ── edge A uppåt (FC) · edge B nedåt (optik)
Optik     (weapon-module) ── socket J1 → P4 edge B (14)  ·  lins Ø16 fram
```
Kraft: **batteri → optik J2 → VBAT → P4 VSYS → P4-regulator → 3V3 → alla kort**
(FC tar 3V3 direkt från edge B via J2 — ingen kabel/bygel).

## Filer

**Färdiga kort (beställ/tillverka):**
| Kort | PCB | 3D | Gerbers |
|---|---|---|---|
| Optik | `weapon-module.kicad_pcb` | `weapon-module.step` | `weapon-module-gerbers.zip` |
| P4-carrier* | `p4-board.kicad_pcb` | `p4-board.step` | — (köps, ej PCB) |
| Fire-control | `firecontrol.kicad_pcb` | `firecontrol.step` | `firecontrol-gerbers.zip` |

\* P4 = köpt **Waveshare ESP32-P4-WIFI6**. `p4-board.*` är mekanik-/headermodell.

**Hopsättning i Fusion (co-orienterade — droppa in vid origo, utan rotation):**
`weapon-module.step` (ankare) · `p4-board-stack.step` · `firecontrol-stack.step`
→ lyft P4 och FC i Z (~socket+header-höjd). USB-kabelpluggen i J_CAM kräver
clearance i P4↔optik-gapet.

**Färdig hop-assembly (allt i en fil):** `strilas-assembly.step` — alla tre korten
i en STEP, co-orienterade, **12 mm plan-till-plan** (optik z0 · P4 z12 · FC z24).
Standoffs läggs in av användaren. Regenereras med `python3 merge_assembly_step.py`
(kräver `pip install cadquery` — bygger en korrekt OCCT-assembly, stel Z-placering).

**BOM:** `BOM.csv` · `BOM.md` (komplett, alla kort + externa moduler). Regenereras
med `python3 gen_bom.py`.

**Verifiering:** `python3 system_sim.py` → ström-/signalflöde över kortgränserna
(0 typkrock · 0 utan ström · 0 dinglar). Bilder (regenereras ur live-netlista/-geometri):
- `port-matching.png` — varje stift etiketterat, mate-par med ✓ (`render_port_labels.py`)
- `edgeB-match-proof.png` — edge B↔optik: alla 14 stift + 4 hål, standoff-låst,
  speglad mate J1.k↔P4-stift(15-k), verifierad 0.000 mm (`render_edgeb_proof.py`)
- `system-flow.png` — kraft-/databuss-översikt

> **Mate (verifierat 0.000 mm mot _pads_z-geometrin):** P4 edge B är flippad till baksidan
> (J_B) → STACKAD/speglad mate, så optik **J1.k ↔ P4 edge B-stift (15-k)** (J1.1↔GPIO32 …
> J1.14↔VSYS). Edge A (FC) är på framsidan → RAK mate (FC J1.k ↔ edge A-stift k+5).
> De 5 IMU/SPI-näten ligger på J1-stift {1,2,4,6,7} = GPIO {32,27,26,23,22} och är
> permuterade för planär (korsningsfri, via-fri) routning IMU→J1 på F_Cu.

**Footprints:** `strilas.pretty/` (IR-emitter + ICM-456xx IMU).

**Design-noter:** `firecontrol.md` · `weapon-module-fab.md`

## Regenerera (källa i ../hardware/)
```
python3 hardware/weapon_module_netlist.py   &&  python3 hardware/receiver_place.py weapon
python3 hardware/make_p4_board.py
python3 hardware/firecontrol_netlist.py     &&  python3 hardware/receiver_place.py firecontrol
python3 hardware/export_stack_step.py        # co-orienterade STEP
```
