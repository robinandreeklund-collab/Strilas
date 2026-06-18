#!/usr/bin/env python3
"""STRILAS — FC post-route-fix: koppla U2.1 (IMU2 AD0=GND) + reparera +3V3 till C5.

BAKGRUND: freerouting kör med GND UTESLUTET (maze-routas separat). U2 (IIM-42653, LGA-14,
0,5 mm pitch) har sin AD0/SDO-pad (pin 1 = GND, ger I²C-adress 0x68) inne i LGA-fotavtrycket.
Den enda flykt-vägen söderut blockeras av en kort +3V3-stump (y≈122,08) som matar U2.5 +
avkopplaren C5 — så GND-planet når aldrig U2.1 och maze-routern hittar ingen väg (LGA-pitchen
lämnar < 0,6 mm för en via mellan +3V3 (F.Cu) och NFC_SCL (B.Cu)).

FIX (deterministisk, körs EN gång på det freeroutade kortet):
  1. Ta bort +3V3-väggen  (167.78,122.08)->(170.32,122.08) på F.Cu  → U2.1:s södra ficka öppnas.
  2. Lägg en egen GND-flykt för U2.1: F.Cu-diagonal U2.1(169.80,121.25)->(169.55,121.95)
     + via där ned till B.Cu + kort B.Cu-stump till befintligt GND-spår (169.43,122.07)->(171.72,122.07).
     (via @169.55 klarar 0,2 mm mot C6/U2.5-matningen vid (170.32,122.08).)
  3. C5.1 (+3V3) blir nu föräldralös (matades genom väggen) → routa om med maze, MEN med
     DRC-minsta keepout (MAZE_KEEP=0.30 / MAZE_VIAKEEP=0.52); default-0,4 mm är för konservativ
     för det trånga U2-hörnet. Maze drar C5.1 -> U2.5 runt GND-flykten.
  4. Fyll GND-plan (F+B) och verifiera 0 clearance / 0 oroutade.

OBS: koordinaterna i steg 1 hör till DEN routning som ligger i hardware/firecontrol.kicad_pcb.
Routas kortet om från grunden (route_firecontrol.py, icke-deterministiskt) hamnar +3V3-väggen
på annat ställe → härled om vägg-segmentet (det +3V3-spår på F.Cu som passerar strax söder om
U2.1 ≈ y 121,9–122,2, x 168–170) innan du kör om.
"""
import os, sys, math, subprocess, pcbnew

PCB = sys.argv[1] if len(sys.argv) > 1 else "hardware/firecontrol.kicad_pcb"
MM = pcbnew.FromMM; OX, OY = 150.0, 120.0
HERE = os.path.dirname(os.path.abspath(__file__))


def Vm(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def near(a, c, t=0.02):
    return abs(a - c) < t


# U2.1 (IMU2 AD0=GND) ligger i ~(169.80,121.25). "Väggen" = +3V3-spår på F.Cu som passerar
# strax söder om paddan och stänger ute GND-planet. Sök segment vars bbox skär denna ruta:
WALL_BOX = (168.3, 170.7, 121.65, 122.65)   # x0,x1,y0,y1 (mm) söder om U2.1


def _seg_hits_box(sx, sy, ex, ey, box):
    x0, x1, y0, y1 = box
    # grov bbox-överlapp räcker (spåren är korta, axelnära)
    return not (max(sx, ex) < x0 or min(sx, ex) > x1 or max(sy, ey) < y0 or min(sy, ey) > y1)


def prepare():
    b = pcbnew.LoadBoard(PCB)
    # --- samla allt FÖRE mutering (pcbnew-SWIG korrumperar collection-iteratorn efter Remove) ---
    gnd_nc = None
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == "GND":
                gnd_nc = p.GetNetCode(); break
        if gnd_nc:
            break
    # U2.1-pad (GND) position
    u21 = None
    for f in b.GetFootprints():
        if f.GetReference() == "U2":
            for p in f.Pads():
                if p.GetName() == "1":
                    pp = p.GetPosition(); u21 = (pp.x/1e6, pp.y/1e6)
    if u21 is None:
        print("!! hittar ej U2.1 — avbryter."); sys.exit(1)

    # TRIGGER: agera BARA om U2.1 saknar GND-spår/via som rör paddan (= instängd). Når maze/plan
    # redan paddan (vanligt när J9/J10 ligger borta från U2) finns ett GND-spår vid U2.1 → no-op.
    # (Tidigare version triggade på +3V3 i en ruta → falsk träff på legitim +3V3-routning.)
    have_escape = False
    walls = []
    for t in b.GetTracks():
        net = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            if net == "GND" and math.hypot(p.x/1e6 - u21[0], p.y/1e6 - u21[1]) < 0.35:
                have_escape = True
            continue
        s, e = t.GetStart(), t.GetEnd()
        if net == "GND":
            if min(math.hypot(s.x/1e6 - u21[0], s.y/1e6 - u21[1]),
                   math.hypot(e.x/1e6 - u21[0], e.y/1e6 - u21[1])) < 0.35:
                have_escape = True
        elif net == "+3V3" and t.GetLayer() == pcbnew.F_Cu:
            if _seg_hits_box(s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6, WALL_BOX):
                walls.append(t)
    if have_escape:
        print("U2.1 har redan GND-spår/via — instängning saknas, fixup behövs ej."); return False
    if not walls:
        print(f"U2.1 oansluten men ingen +3V3-vägg i {WALL_BOX} — kan ej auto-fixa, kolla manuellt."); sys.exit(1)
    print(f"steg 1: U2.1 instängd → tar bort {len(walls)} +3V3-vägg-segment söder om paddan.")

    # --- mutera ---
    for wall in walls:
        b.Remove(wall)
    tr = pcbnew.PCB_TRACK(b); tr.SetStart(Vm(169.80, 121.25)); tr.SetEnd(Vm(169.55, 121.95))
    tr.SetWidth(MM(0.2)); tr.SetLayer(pcbnew.F_Cu); tr.SetNetCode(gnd_nc); b.Add(tr)
    v = pcbnew.PCB_VIA(b); v.SetPosition(Vm(169.55, 121.95)); v.SetDrill(MM(0.3)); v.SetWidth(MM(0.6))
    v.SetNetCode(gnd_nc); b.Add(v)
    tr2 = pcbnew.PCB_TRACK(b); tr2.SetStart(Vm(169.55, 121.95)); tr2.SetEnd(Vm(169.55, 122.07))
    tr2.SetWidth(MM(0.2)); tr2.SetLayer(pcbnew.B_Cu); tr2.SetNetCode(gnd_nc); b.Add(tr2)
    pcbnew.SaveBoard(PCB, b)
    print("steg 1–2: +3V3-vägg borttagen, U2.1 GND-flykt (via@169.55,121.95) tillagd.")
    return True


def route_3v3():
    env = dict(os.environ, MAZE_KEEP="0.30", MAZE_VIAKEEP="0.52")
    r = subprocess.run([sys.executable, os.path.join(HERE, "maze_route.py"), PCB, "+3V3"], env=env)
    if r.returncode != 0:
        print("!! maze +3V3 misslyckades"); sys.exit(1)
    print("steg 3: +3V3 (C5.1) omroutad med DRC-min keepout.")


def fill_and_verify():
    b = pcbnew.LoadBoard(PCB)
    gnd_nc = None
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == "GND":
                gnd_nc = p.GetNetCode(); break
        if gnd_nc:
            break
    for z in list(b.Zones()):
        b.Remove(z)

    def V(x, y):
        return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

    def add_zone(layer):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(gnd_nc)
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2)); z.SetIsFilled(False)
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in [(-35.0, -10.3), (35.0, -10.3), (35.0, 10.3), (-35.0, 10.3)]:
            ch.Append(V(x, y))
        ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
    add_zone(pcbnew.F_Cu); add_zone(pcbnew.B_Cu)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)

    b = pcbnew.LoadBoard(PCB)
    CU = [pcbnew.F_Cu, pcbnew.B_Cu]
    items = []
    for t in b.GetTracks():
        lays = CU if t.Type() == pcbnew.PCB_VIA_T else [t.GetLayer()]
        items.append((t.GetNetCode(), set(lays), t.GetEffectiveShape()))
    for f in b.GetFootprints():
        for pd in f.Pads():
            items.append((pd.GetNetCode(), set(L for L in CU if pd.IsOnLayer(L)), pd.GetEffectiveShape()))
    v = sum(1 for i in range(len(items)) for j in range(i + 1, len(items))
            if items[i][0] != items[j][0] and (items[i][1] & items[j][1]) and items[i][2].Collide(items[j][2], int(0.2e6)))
    b.BuildConnectivity()
    try:
        un = b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError:
        un = b.GetConnectivity().GetUnconnectedCount()
    print(f"steg 4: clearance@0.2mm = {v}   oroutade = {un}")
    if v or un:
        print("!! DRC EJ ren"); sys.exit(1)
    print("REN board.")


if __name__ == "__main__":
    if prepare():          # bara om en vägg faktiskt togs bort (U2.1 var instängd)
        route_3v3()        # C5:s +3V3 blev föräldralös → routa om
        fill_and_verify()
    else:
        print("Inget att göra (U2.1 redan kopplad).")
