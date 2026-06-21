#!/usr/bin/env python3
"""STRILAS — route vapen-HAT (70×58, 2-lager, HAT på CM5-carrierns 40-pin header).
Greenfield-routning (nytt kort, 0 spår) → freerouting är legitimt här. Samma flöde som
route_firecontrol.py: DSN → power-klass → freeroute-loop (GND utesluten) → ses_apply →
maze GND+rest → GND-fyll (F+B) → verifiera → Gerbers/STEP. Körs efter weapon_hat_place.py."""
import subprocess, sys, math, shutil, os, re, pcbnew
PCB = "hardware/weapon-hat.kicad_pcb"; DSN = "hardware/weapon-hat.dsn"; SES = "hardware/weapon-hat.ses"
MM = pcbnew.FromMM; OX, OY = 150.0, 120.0
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
PLANE_NETS = ("GND",); CU = [pcbnew.F_Cu, pcbnew.B_Cu]


def _conn(path, want_names=False):
    b = pcbnew.LoadBoard(path); items = []
    for i, t in enumerate(b.GetTracks()):
        net = t.GetNetname()
        if not net: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition(); items.append((net, ("v", i), [(p.x, p.y, None)]))
        else:
            s, e, L = t.GetStart(), t.GetEnd(), t.GetLayer(); items.append((net, ("t", i), [(s.x, s.y, L), (e.x, e.y, L)]))
    netpads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            net = p.GetNetname()
            if not net: continue
            pos = p.GetPosition(); lays = [L for L in CU if p.IsOnLayer(L)]
            key = ("p", f.GetReference() + "." + p.GetName())
            items.append((net, key, [(pos.x, pos.y, L) for L in lays] or [(pos.x, pos.y, None)]))
            netpads.setdefault(net, []).append(key)
    bynet = {}
    for net, key, pts in items: bynet.setdefault(net, []).append((key, pts))
    par = {}
    def find(x):
        par.setdefault(x, x)
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    bad, names = 0, []
    for net, pads in netpads.items():
        if net in PLANE_NETS or len(pads) < 2: continue
        el = bynet.get(net, [])
        for i in range(len(el)):
            for j in range(i + 1, len(el)):
                (ka, pa), (kb, pb) = el[i], el[j]
                if any((la is None or lb is None or la == lb) and math.hypot(xa - xb, ya - yb) < 60000
                       for xa, ya, la in pa for xb, yb, lb in pb): par[find(ka)] = find(kb)
        if len({find(k) for k in pads}) > 1: bad += 1; names.append(net)
    return names if want_names else bad


def finish(path):
    b = pcbnew.LoadBoard(path)
    for z in list(b.Zones()): b.Remove(z)
    def add_zone(layer):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(b.FindNet("GND").GetNetCode())
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2)); z.SetIsFilled(False)
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in [(-34.7,-28.7),(34.7,-28.7),(34.7,28.7),(-34.7,28.7)]: ch.Append(V(x, y))
        ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
    add_zone(pcbnew.F_Cu); add_zone(pcbnew.B_Cu)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path, b)


def verify(path):
    b = pcbnew.LoadBoard(path); items = []
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


b = pcbnew.LoadBoard(PCB)
for t in list(b.GetTracks()): b.Remove(t)
for z in list(b.Zones()): b.Remove(z)
pcbnew.SaveBoard(PCB, b)
pcbnew.ExportSpecctraDSN(b, DSN)
subprocess.run(["python3", "hardware/dsn_power_class.py", DSN])
d = open(DSN).read()
d = re.sub(r'\n\s*\(net GND\s*\(pins[^)]*\)\s*\)', '', d); d = d.replace(" GND ", " ")
open(DSN, "w").write(d)
shutil.copy(PCB, "/tmp/_hat_placed.kicad_pcb")
best = None
for seed in range(1, 11):
    if os.path.exists(SES): os.remove(SES)
    subprocess.run(["timeout", "-k", "5", "300", "xvfb-run", "-a", "java", "-jar", "/opt/freerouting.jar",
                    "-de", DSN, "-do", SES, "-mp", "100"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["bash", "-c", "pkill -9 -f freerouting.jar 2>/dev/null; pkill -9 Xvfb 2>/dev/null; true"])
    if not os.path.exists(SES) or os.path.getsize(SES) < 1000:
        print(f"  seed {seed}: timeout/ingen SES"); continue
    shutil.copy("/tmp/_hat_placed.kicad_pcb", PCB)
    subprocess.run(["python3", "hardware/ses_apply.py", PCB, SES], stdout=subprocess.DEVNULL)
    u = _conn(PCB); print(f"  seed {seed}: signal-oroutade = {u}")
    if best is None or u < best[0]:
        best = (u, seed); shutil.copy(PCB, "/tmp/_hat_best.kicad_pcb")
    if u == 0: break
shutil.copy("/tmp/_hat_best.kicad_pcb", PCB)
left = _conn(PCB, want_names=True)
print(f"  bästa seed {best[1]}: {best[0]} signal kvar ({left}) + GND → maze-router")
subprocess.run(["python3", "hardware/maze_route.py", PCB] + left + ["GND"])
if _conn(PCB) != 0: print("!! maze kunde ej stänga alla signaler"); sys.exit(1)
finish(PCB)
v, un = verify(PCB); print(f"clearance@0.2mm = {v}   oanslutna = {un}")
if v or un: print("!! DRC ej ren"); sys.exit(1)
print("REN board.")
os.system("rm -rf /tmp/gbhat && mkdir -p /tmp/gbhat")
subprocess.run(["kicad-cli","pcb","export","gerbers","-o","/tmp/gbhat/",PCB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["kicad-cli","pcb","export","drill","-o","/tmp/gbhat/",PCB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.makedirs("leverans/weapon-hat", exist_ok=True)
subprocess.run(["bash","-c","cd /tmp/gbhat && zip -q -r - . > /home/user/Strilas/leverans/weapon-hat/weapon-hat-gerbers.zip"])
subprocess.run(["kicad-cli","pcb","export","step","-f","--subst-models","-o","leverans/weapon-hat/weapon-hat.step",PCB],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Gerbers + STEP → leverans/weapon-hat/")
