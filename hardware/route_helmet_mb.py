#!/usr/bin/env python3
"""STRILAS — route hjälm-moderkort (80×62, 4-lager): DSN → power-klass (0,4 mm) → freeroute (loop) →
ses_apply → kopparplan (In1=GND, In2=VBAT, F/B=GND-fyll) → verifiera → Gerbers/STEP.
Körs efter receiver_place.py vest_mb. (1-nods-NC/reserv-nät ignoreras i routnings-grinden.)"""
import subprocess, sys, math, shutil, os, pcbnew
PCB = "hardware/helmet-mb.kicad_pcb"; DSN = "hardware/helmet-mb.dsn"; SES = "hardware/helmet-mb.ses"
MM = pcbnew.FromMM; OX, OY = 150.0, 120.0
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))


def unrouted(path):
    b = pcbnew.LoadBoard(path); tr = {}; pc = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname(): pc[p.GetNetname()] = pc.get(p.GetNetname(), 0) + 1
    for t in b.GetTracks():
        tr.setdefault(t.GetNetCode(), []).extend(
            [(t.GetStart().x/1e6, t.GetStart().y/1e6), (t.GetEnd().x/1e6, t.GetEnd().y/1e6)])
    return sum(1 for f in b.GetFootprints() for p in f.Pads()
               if p.GetNetname() not in ("", "GND") and pc.get(p.GetNetname(), 0) >= 2
               and not any(math.hypot(p.GetPosition().x/1e6-ex, p.GetPosition().y/1e6-ey) < 0.4
                           for ex, ey in tr.get(p.GetNetCode(), [])))


def finish(path):
    b = pcbnew.LoadBoard(path)
    for z in list(b.Zones()): b.Remove(z)
    def add_zone(layer, net):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(b.FindNet(net).GetNetCode())
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2)); z.SetIsFilled(False)
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in [(-47.5, -37.5), (47.5, -37.5), (47.5, 37.5), (-47.5, 37.5)]: ch.Append(V(x, y))
        ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
    add_zone(pcbnew.In1_Cu, "GND"); add_zone(pcbnew.In2_Cu, "VBAT")
    add_zone(pcbnew.B_Cu, "GND"); add_zone(pcbnew.F_Cu, "GND")
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path, b)


def verify(path):
    b = pcbnew.LoadBoard(path); CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]; items = []
    for t in b.GetTracks():
        lays = CU if t.Type() == pcbnew.PCB_VIA_T else [t.GetLayer()]
        items.append((t.GetNetCode(), set(lays), t.GetEffectiveShape()))
    for f in b.GetFootprints():
        for pd in f.Pads(): items.append((pd.GetNetCode(), set(L for L in CU if pd.IsOnLayer(L)), pd.GetEffectiveShape()))
    v = sum(1 for i in range(len(items)) for j in range(i+1, len(items))
            if items[i][0] != items[j][0] and (items[i][1] & items[j][1]) and items[i][2].Collide(items[j][2], int(0.2e6)))
    b.BuildConnectivity()
    try: un = b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError: un = b.GetConnectivity().GetUnconnectedCount()
    return v, un


b = pcbnew.LoadBoard(PCB); pcbnew.ExportSpecctraDSN(b, DSN)
subprocess.run(["python3", "hardware/dsn_power_class.py", DSN])
shutil.copy(PCB, "/tmp/_hmb_placed.kicad_pcb")
clean = False
for seed in range(1, 13):
    subprocess.run(["xvfb-run", "-a", "java", "-jar", "/opt/freerouting.jar", "-de", DSN, "-do", SES, "-mp", "150"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy("/tmp/_hmb_placed.kicad_pcb", PCB)
    subprocess.run(["python3", "hardware/ses_apply.py", PCB, SES], stdout=subprocess.DEVNULL)
    u = unrouted(PCB); print(f"  seed {seed}: signal-oroutade = {u}")
    if u == 0: clean = True; break
if not clean: print("!! ingen ren routning"); sys.exit(1)
finish(PCB)
v, un = verify(PCB); print(f"clearance@0.2mm = {v}   oconnected = {un}")
if v or un: print("!! DRC ej ren"); sys.exit(1)
print("REN board.")
os.system("rm -rf /tmp/gbhmb && mkdir -p /tmp/gbhmb")
subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "-o", "/tmp/gbhmb/", PCB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["kicad-cli", "pcb", "export", "drill", "-o", "/tmp/gbhmb/", PCB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["bash", "-c", "cd /tmp/gbhmb && zip -q -r - . > /home/user/Strilas/hardware/helmet-mb-gerbers.zip"])
subprocess.run(["kicad-cli", "pcb", "export", "step", "-f", "--subst-models", "-o", "hardware/helmet-mb.step", PCB],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Gerbers + STEP exporterade.")
