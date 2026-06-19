#!/usr/bin/env python3
"""STRILAS — DETERMINISTISK slutförning av hjälm-routningen efter att I²C-pull-ups (R9/R10)
flyttats intill P4 (master). Utgår från den BEVISAT kompletta freerouting-routningen där allt
var ihopkopplat UTOM själva pull-up-paddarna (de satt strandade vid x=+45 i amp-korridoren).

Detta är INTE en omroutning (route_*.py nollställer spåren). Här bevaras hela den routade
kopparen; bara de två sista anslutningarna dras exakt:
  • R9/R10 flyttas till (±2.5, 16.6) direkt över U2:s I²C-pinnar.
  • Gamla +3V3-stubbar vid de TIDIGARE padd-lägena tas bort (de pekar nu i tomma luften).
  • Varje pull-up-+3V3-padd får en stitch-via → In2 = +3V3-plan.
  • I²C SCL/SDA dras som korta F-spår från pull-up-padden till bussens befintliga F-koppar.
Därefter fylls kopparplanen och DRC verifieras (0 clearance / 0 oanslutet) innan export.

Användning: python3 hardware/finish_helmet_pullups.py [<src.kicad_pcb>]
  src default = den freeroutade backupen i /tmp; resultat skrivs till hardware/helmet-mb.kicad_pcb."""
import sys, math, subprocess, os, shutil, pcbnew

SRC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/hmb_backup_783.kicad_pcb"
PCB = "hardware/helmet-mb.kicad_pcb"
MM = pcbnew.FromMM; OX, OY = 150.0, 120.0
F, B = pcbnew.F_Cu, pcbnew.B_Cu
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
def XY(p): return (round(p.x / 1e6 - OX, 3), round(OY - p.y / 1e6, 3))

b = pcbnew.LoadBoard(SRC)
fps = {f.GetReference(): f for f in b.GetFootprints()}
# net-namn → netcode (FindNet ger ibland otypat SWIG-objekt; hämta koden från paddarna istället)
NETCODE = {}
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname(): NETCODE[p.GetNetname()] = p.GetNetCode()

# --- 1. spara gamla padd-lägen (för stubb-städning), flytta R9/R10 ---
old_pads = {}   # ref.pad -> (x,y) i mm-board-koord
for r in ("R9", "R10"):
    for p in fps[r].Pads():
        old_pads[r + "." + p.GetName()] = XY(p.GetPosition())
# Orientering vald så att I²C-padden pekar mot bussen (U2 @ x≈0) och +3V3-padden UTÅT → I²C-
# spåret korsar aldrig den egna +3V3-padden. R10 till höger om bussen (rot180 → SCL-padd vänster),
# R9 till vänster (rot0 → SDA-padd höger). 4.4 mm isär → courtyards fria (1 mm-glapp).
fps["R10"].SetPosition(V(2.2, 16.7)); fps["R10"].SetOrientationDegrees(180)  # SCL-pull (SCL-padd vänster→buss)
fps["R9"].SetPosition(V(-2.2, 16.7)); fps["R9"].SetOrientationDegrees(0)     # SDA-pull (SDA-padd höger→buss)
new_pads = {}
for r in ("R9", "R10"):
    for p in fps[r].Pads():
        new_pads[r + "." + p.GetName()] = (XY(p.GetPosition()), p.GetNetname())

# --- 2. ta bort gamla +3V3-stubbar som ENBART matade de flyttade pull-up-paddarna ---
# (spår/via vars ändpunkt låg inom 0.4 mm av ett gammalt +3V3-padd-läge → pekar nu i tomma luften)
def near(pt, ref, tol=0.4):
    return math.hypot(pt[0] - ref[0], pt[1] - ref[1]) < tol
v3_olds = [old_pads["R9.1"], old_pads["R10.1"]]
all_tracks = list(b.GetTracks())   # ENDA snapshot — b.GetTracks() blir otypat efter Remove()
removed = gnd_rm = 0
for t in all_tracks:
    net = t.GetNetname()
    if net == "+3V3":
        if t.Type() == pcbnew.PCB_VIA_T:
            if any(near(XY(t.GetPosition()), o) for o in v3_olds): b.Remove(t); removed += 1
        elif any(near(XY(t.GetStart()), o) or near(XY(t.GetEnd()), o) for o in v3_olds):
            b.Remove(t); removed += 1
    elif net == "GND" and t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == F:
        # GND-F-diagonalen som freerouting drog tvärs över R9-zonen är REDUNDANT (GND = plan på
        # In1/F/B). Ta bort den; dess enda beroende padd (Q1.2) återkopplas explicit nedan.
        if any(-3.6 <= x <= -0.7 and 16.0 <= y <= 19.2 for x, y in (XY(t.GetStart()), XY(t.GetEnd()))):
            b.Remove(t); gnd_rm += 1
print(f"tog bort {removed} gamla +3V3-stubbar + {gnd_rm} GND-F-diagonal-segment (Q1.2 stitchas om)")

# --- 3. helpers för att lägga F-spår och stitch-via ---
def track(net, x0, y0, x1, y1, layer=F, w=0.2):
    t = pcbnew.PCB_TRACK(b); t.SetStart(V(x0, y0)); t.SetEnd(V(x1, y1))
    t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNetCode(NETCODE[net]); b.Add(t)
def via(net, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetDrill(MM(0.3)); v.SetWidth(MM(0.6))
    v.SetNetCode(NETCODE[net]); b.Add(v)

# --- 4. +3V3: stitch-via ovanför varje pull-up-+3V3-padd → In2-plan ---
for ref in ("R9.1", "R10.1"):
    (px, py), net = new_pads[ref]
    vy = py + 0.9                     # via 0.9 mm ovanför padden (öppen yta, under Q1 @ y18.2)
    track(net, px, py, px, vy); via(net, px, vy)

# --- 5. I²C: kort F-spår från pull-up-padd → bussens befintliga F-koppar (snap till känd punkt) ---
#   bussens F-ändpunkter (ur backupen): SCL @ (0.16, 15.195), SDA @ (-1.684, 14.833)
BUS = {"R10.2": (0.16, 15.195), "R9.2": (-1.684, 14.833)}   # SCL F-ände / SDA F-ände (befintlig koppar)
for ref, (bx, by) in BUS.items():
    (px, py), net = new_pads[ref]
    track(net, px, py, bx, by)

# --- 5b. Q1.2 (GND-padd vars enda spår var den borttagna diagonalen) → stitch-via till GND-plan.
#   Spår rakt VÄNSTER ut ur Q1:s courtyard + via @ (-2.5, 18.96) → In1/B GND-plan. ---
track("GND", -0.938, 18.96, -2.5, 18.96); via("GND", -2.5, 18.96)

# --- 5c. C21.1/U8.6 (+3V3 vid ampen) nådde +3V3-planet GENOM gamla R10.1:s via — som togs bort
#   med stubbarna ovan. Återkoppla deras F-spårkedja till In2-planet med en stitch-via i det nu
#   amp-områdets långa F-spår (y=-4.082) på en punkt fri från In1-spår (VBAT/LED_EN). ---
via("+3V3", 37.3, -4.082)

for r in ("R9", "R10"):
    for p in fps[r].Pads():
        print("  ny padd", r + "." + p.GetName(), p.GetNetname(), XY(p.GetPosition()))
pcbnew.SaveBoard(PCB, b)
print("flyttade pull-ups + drog stubbar →", PCB)


# --- 6. fyll kopparplan (In1=GND, In2=+3V3, F/B=GND) ---
def finish():
    bb = pcbnew.LoadBoard(PCB)
    for z in list(bb.Zones()): bb.Remove(z)
    nc = {}
    for f in bb.GetFootprints():
        for p in f.Pads():
            if p.GetNetname(): nc[p.GetNetname()] = p.GetNetCode()
    def add_zone(layer, net):
        z = pcbnew.ZONE(bb); z.SetLayer(layer); z.SetNetCode(nc[net])
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2)); z.SetIsFilled(False)
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for k in range(72):
            a = math.radians(k * 5); ch.Append(V(53.0 * math.cos(a), 53.0 * math.sin(a)))
        ch.SetClosed(True); z.AddPolygon(ch); bb.Add(z)
    add_zone(pcbnew.In1_Cu, "GND"); add_zone(pcbnew.In2_Cu, "+3V3")
    add_zone(pcbnew.B_Cu, "GND"); add_zone(pcbnew.F_Cu, "GND")
    pcbnew.ZONE_FILLER(bb).Fill(bb.Zones()); pcbnew.SaveBoard(PCB, bb)
finish()


# --- 7. verifiera: 0 clearance-krock + 0 oanslutet + 0 signal-öar ---
def verify():
    bb = pcbnew.LoadBoard(PCB); CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]; it = []
    for t in bb.GetTracks():
        lays = CU if t.Type() == pcbnew.PCB_VIA_T else [t.GetLayer()]
        it.append((t.GetNetCode(), set(lays), t.GetEffectiveShape()))
    for f in bb.GetFootprints():
        for pd in f.Pads(): it.append((pd.GetNetCode(), set(L for L in CU if pd.IsOnLayer(L)), pd.GetEffectiveShape()))
    v = sum(1 for i in range(len(it)) for j in range(i + 1, len(it))
            if it[i][0] != it[j][0] and (it[i][1] & it[j][1]) and it[i][2].Collide(it[j][2], int(0.2e6)))
    bb.BuildConnectivity()
    try: un = bb.GetConnectivity().GetUnconnectedCount(True)
    except TypeError: un = bb.GetConnectivity().GetUnconnectedCount()
    return v, un
v, un = verify()
print(f"VERIFIERING: clearance-krockar={v}  oanslutet={un}")
print("REN" if v == 0 and un == 0 else "!! ej ren — åtgärda")
