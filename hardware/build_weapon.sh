#!/usr/bin/env bash
# STRILAS — reproducerbar EDA-kedja för vapen-optikmodulen (netlista → routad board → Gerbers/STEP).
# Körs headless i container (KiCad 7 + Freerouting). Idempotent: kör om från noll varje gång.
set -euo pipefail
cd "$(dirname "$0")/.."           # repo-rot

PCB=hardware/weapon-module.kicad_pcb
DSN=hardware/weapon-module.dsn
SES=hardware/weapon-module.ses

echo "== 1) netlista (SKiDL) =="
python3 hardware/weapon_module_netlist.py

echo "== 2) footprints (emitter + IMU) =="
python3 hardware/make_footprints.py

echo "== 3) placering + nät + outline + linshål =="
python3 hardware/receiver_place.py weapon

echo "== 4) termiska vior under emittrarna (före routning) =="
python3 hardware/weapon_thermal_vias.py

echo "== 5) export Specctra-DSN =="
python3 - "$PCB" "$DSN" <<'PY'
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
pcbnew.ExportSpecctraDSN(b, sys.argv[2])
print("  wrote", sys.argv[2])
PY

echo "== 6) effektnät -> egen 0.4 mm-klass =="
python3 hardware/dsn_power_class.py "$DSN"

echo "== 7) autoroute (Freerouting, headless) =="
xvfb-run -a java -jar /opt/freerouting.jar -de "$DSN" -do "$SES" -mp 120

echo "== 8) applicera SES (spår/vior) =="
python3 hardware/ses_apply.py "$PCB" "$SES"

echo "== 9) brygga emitter-näten (om Freerouting missar) =="
python3 hardware/weapon_emitter_routes.py

echo "== 10) flippa kontakter (J1/J2/J3) till baksidan =="
python3 hardware/flip_j1_back.py

echo "== 11) kopparplan + fyllning =="
python3 hardware/weapon_finish.py

echo "== 12) Gerbers + drill =="
rm -rf /tmp/gbr && mkdir -p /tmp/gbr
kicad-cli pcb export gerbers -o /tmp/gbr/ "$PCB" >/dev/null
kicad-cli pcb export drill -o /tmp/gbr/ "$PCB" >/dev/null
( cd /tmp/gbr && zip -q -r - . ) > hardware/weapon-module-gerbers.zip
echo "  wrote hardware/weapon-module-gerbers.zip"

echo "== 13) STEP =="
kicad-cli pcb export step -f --subst-models -o hardware/weapon-module.step "$PCB" >/dev/null
echo "  wrote hardware/weapon-module.step"

echo "== 14) render =="
python3 hardware/render_weapon_realistic.py

echo "== 15) egenkontroll (clearance + connectivity) =="
# Freerouting är stokastisk i det täta emitter-området; denna grind fångar en dålig körning.
python3 - "$PCB" <<'PY'
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
items = []
for t in b.GetTracks():
    lays = CU if t.Type() == pcbnew.PCB_VIA_T else [t.GetLayer()]
    items.append((t.GetNetCode(), set(lays), t.GetEffectiveShape()))
for f in b.GetFootprints():
    for pd in f.Pads():
        items.append((pd.GetNetCode(), set(L for L in CU if pd.IsOnLayer(L)), pd.GetEffectiveShape()))
v = 0; n = len(items)
for i in range(n):
    for j in range(i + 1, n):
        if items[i][0] == items[j][0]: continue
        if not (items[i][1] & items[j][1]): continue
        if items[i][2].Collide(items[j][2], int(0.2 * 1e6)): v += 1
b.BuildConnectivity()
try: un = b.GetConnectivity().GetUnconnectedCount(True)
except TypeError: un = b.GetConnectivity().GetUnconnectedCount()
print(f"  clearance-brott @0.2mm = {v}   oroutade = {un}")
if v or un:
    print("  !! EJ REN — kör om (Freerouting-seed). Den låsta boarden byggs ren.")
    sys.exit(1)
print("  REN board.")
PY

echo "== KLART =="
