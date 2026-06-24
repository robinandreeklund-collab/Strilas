#!/usr/bin/env bash
# STRILAS — färdigställ väst-patch (2-lager): strip → freeroute → SES → GND-pour → Gerbers/STEP.
set -euo pipefail
cd "$(dirname "$0")/.."
PCB=hardware/vest-patch.kicad_pcb
DSN=hardware/vest-patch.dsn
SES=hardware/vest-patch.ses

echo "== 1) strip tracks/zoner, spara placerad board =="
python3 - "$PCB" <<'PY'
import sys, pcbnew
b=pcbnew.LoadBoard(sys.argv[1])
for t in [x for x in b.GetTracks()]: b.Remove(t)
for z in [x for x in b.Zones()]: b.Remove(z)
pcbnew.SaveBoard(sys.argv[1], b)
print("  strippad")
PY
cp "$PCB" /tmp/_vest_placed.kicad_pcb

echo "== 2) export DSN =="
python3 - "$PCB" "$DSN" <<'PY'
import sys, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); pcbnew.ExportSpecctraDSN(b, sys.argv[2]); print("  wrote", sys.argv[2])
PY

echo "== 3) freeroute (headless) tills rent =="
clean=0
for seed in 1 2 3 4 5; do
  xvfb-run -a java -jar /opt/freerouting.jar -de "$DSN" -do "$SES" -mp 100 >/dev/null 2>&1 || true
  cp /tmp/_vest_placed.kicad_pcb "$PCB"
  python3 hardware/ses_apply.py "$PCB" "$SES" >/dev/null
  u=$(python3 - "$PCB" <<'PY'
import pcbnew, math, sys
b=pcbnew.LoadBoard(sys.argv[1]); tr={}
for t in b.GetTracks(): tr.setdefault(t.GetNetCode(),[]).extend([(t.GetStart().x/1e6,t.GetStart().y/1e6),(t.GetEnd().x/1e6,t.GetEnd().y/1e6)])
print(sum(1 for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() not in ("","GND")
    and not any(math.hypot(p.GetPosition().x/1e6-ex,p.GetPosition().y/1e6-ey)<0.4 for ex,ey in tr.get(p.GetNetCode(),[]))))
PY
)
  echo "   seed $seed: signal-oroutade = $u"
  [ "$u" = "0" ] && { clean=1; break; }
done
[ "$clean" = "1" ] || { echo "  !! ingen ren routning"; exit 1; }

echo "== 4) GND-pour (F + B) =="
python3 - "$PCB" <<'PY'
import sys, pcbnew
b=pcbnew.LoadBoard(sys.argv[1])
bb=b.GetBoardEdgesBoundingBox()
gnd=b.FindNet("GND").GetNetCode()
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z=pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(gnd)
    z.SetLocalClearance(pcbnew.FromMM(0.25)); z.SetMinThickness(pcbnew.FromMM(0.2)); z.SetIsFilled(False)
    ch=pcbnew.SHAPE_LINE_CHAIN()
    m=pcbnew.FromMM(0.3)
    for x,y in [(bb.GetLeft()+m,bb.GetTop()+m),(bb.GetRight()-m,bb.GetTop()+m),
                (bb.GetRight()-m,bb.GetBottom()-m),(bb.GetLeft()+m,bb.GetBottom()-m)]:
        ch.Append(x,y)
    ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
b.BuildConnectivity()
try: un=b.GetConnectivity().GetUnconnectedCount(True)
except TypeError: un=b.GetConnectivity().GetUnconnectedCount()
print(f"  2 GND-zoner fyllda, oconnected={un}")
PY

echo "== 5) Gerbers + STEP =="
rm -rf /tmp/gbv && mkdir -p /tmp/gbv
kicad-cli pcb export gerbers -o /tmp/gbv/ "$PCB" >/dev/null
kicad-cli pcb export drill -o /tmp/gbv/ "$PCB" >/dev/null
( cd /tmp/gbv && zip -q -r - . ) > hardware/vest-patch-gerbers.zip
kicad-cli pcb export step -f --subst-models -o hardware/vest-patch.step "$PCB" >/dev/null
echo "  wrote vest-patch-gerbers.zip + vest-patch.step"
echo "== KLART =="
