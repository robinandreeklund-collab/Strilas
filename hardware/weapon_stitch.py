#!/usr/bin/env python3
"""STRILAS — handrouta det enda nät på J1 (P4 edge B) som Freerouting inte når som SPÅR i
det täta optikkortet: IMU_INT (J1.11 ↔ U1.4), längst ned i vänstra hörnet (boxat av kamerahål
H10 + P4-standoff). Efter spegelvändningen av J1 (pad k = forna pad 15-k, för fysisk passning
mot P4-standoff-hålen) hamnar IMU_INT på J1.11 i det trånga hörnet medan +3V3/VBAT numera
routas av Freerouting i öppnare läge. B_Cu i vänsterkant-korridoren är verifierad fri.
Körs EFTER ses_apply, FÖRE flip_j1_back + weapon_finish (J1-paddar är THT → bevaras vid flip)."""
import math, pcbnew
b = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
OX, OY = 150.0, 120.0

# Hoppa över om Freerouting redan nått IMU_INT på J1.11 (placeringsberoende) — annars
# skulle ett dubbelt spår ge clearance-brott. Sök spår inom 0.4 mm från J1.11-paddens läge.
def imu_int_routed():
    pos = None
    for f in b.GetFootprints():
        if f.GetReference() == "J1":
            for pd in f.Pads():
                if pd.GetName() == "11":
                    pos = pd.GetPosition()
    if pos is None:
        return True
    for t in b.GetTracks():
        if t.GetNetname() != "IMU_INT":
            continue
        for end in (t.GetStart(), t.GetEnd()):
            if math.hypot(end.x - pos.x, end.y - pos.y) < int(0.4 * 1e6):
                return True
    return False

if imu_int_routed():
    print("  stitch: IMU_INT redan routad av Freerouting — hoppar over")
    raise SystemExit(0)

def V(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY - y))
def nc(n): return b.FindNet(n).GetNetCode()
def seg(net, layer, pts, w):
    code = nc(net)
    for i in range(len(pts) - 1):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*pts[i])); t.SetEnd(V(*pts[i + 1]))
        t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(layer); t.SetNetCode(code); b.Add(t)
def via(net, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(pcbnew.FromMM(0.6)); v.SetDrill(pcbnew.FromMM(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(nc(net)); b.Add(v)

# IMU_INT: B_Cu från J1.11 (@-25.28,-20.26) upp den fria vänsterkant-korridoren, via vid
# (-23.5,-2.0) upp till F_Cu, kort F_Cu-hopp (ovanför MISO/+3V3-spåren @y<=-3.75) in i U1.4
# (IMU INT-pad @-20.2,-2.25).
seg("IMU_INT", pcbnew.B_Cu, [(-25.28, -20.26), (-23.5, -20.26), (-23.5, -2.0)], 0.25)
via("IMU_INT", -23.5, -2.0)
seg("IMU_INT", pcbnew.F_Cu, [(-23.5, -2.0), (-20.2, -2.25)], 0.25)
pcbnew.SaveBoard("hardware/weapon-module.kicad_pcb", b)
print("  stitch: IMU_INT (J1.11->U1.4) handroutad pa B_Cu + via->F_Cu")
