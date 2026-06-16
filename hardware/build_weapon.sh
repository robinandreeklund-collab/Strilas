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

echo "== 7-8) autoroute (Freerouting, headless) + applicera SES =="
# Freerouting är stokastisk: kör om tills ALLA signalnät (≠GND, fylls av plan) är routade.
cp "$PCB" /tmp/_placed.kicad_pcb
clean=0
for seed in 1 2 3 4 5 6 7 8; do
  xvfb-run -a java -jar /opt/freerouting.jar -de "$DSN" -do "$SES" -mp 200 >/dev/null 2>&1
  cp /tmp/_placed.kicad_pcb "$PCB"
  python3 hardware/ses_apply.py "$PCB" "$SES" >/dev/null
  u=$(python3 - "$PCB" <<'PY'
import pcbnew, math, sys
b=pcbnew.LoadBoard(sys.argv[1])
tr={}
for t in b.GetTracks(): tr.setdefault(t.GetNetCode(),[]).extend(
    [(t.GetStart().x/1e6,t.GetStart().y/1e6),(t.GetEnd().x/1e6,t.GetEnd().y/1e6)])
print(sum(1 for f in b.GetFootprints() for p in f.Pads()
    if p.GetNetname() not in ("","GND")
    and not any(math.hypot(p.GetPosition().x/1e6-ex,p.GetPosition().y/1e6-ey)<0.4
                for ex,ey in tr.get(p.GetNetCode(),[]))))
PY
)
  echo "   seed $seed: signal-oroutade paddar = $u"
  # 2 kvarvarande = J1.11(+3V3)/J1.14(VBAT) i boxade hörnet → handroutas i steg 8b
  # (VBAT når dessutom In2-VBAT-planet). Acceptera <=2; connectivity-grinden är steg 15.
  if [ "$u" -le 2 ]; then clean=1; break; fi
done
[ "$clean" = "1" ] || { echo "  !! routning gav >2 oroutade på 8 försök"; exit 1; }

echo "== 8b) handrouta de 2 boxade kraftstiften (+3V3/VBAT) =="
python3 hardware/weapon_stitch.py

echo "== 9) flippa kontakter (J1/J2/J3) till baksidan =="
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
