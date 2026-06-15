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

**BOM:** `BOM.csv` · `BOM.md` (komplett, alla kort + externa moduler). Regenereras
med `python3 gen_bom.py`.

**Verifiering:** `python3 system_sim.py` → ström-/signalflöde över kortgränserna
(0 typkrock · 0 utan ström · 0 dinglar). Bilder:
- `port-matching.png` — varje stift etiketterat, mate-par med ✓
- `edgeB-match-proof.png` — edge B↔optik: alla 14 stift + 4 hål, standoff-låst
- `system-flow.png` — kraft-/databuss-översikt

**Footprints:** `strilas.pretty/` (IR-emitter + ICM-456xx IMU).

**Design-noter:** `firecontrol.md` · `weapon-module-fab.md`

## Regenerera (källa i ../hardware/)
```
python3 hardware/weapon_module_netlist.py   &&  python3 hardware/receiver_place.py weapon
python3 hardware/make_p4_board.py
python3 hardware/firecontrol_netlist.py     &&  python3 hardware/receiver_place.py firecontrol
python3 hardware/export_stack_step.py        # co-orienterade STEP
```
