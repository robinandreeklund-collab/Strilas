#!/usr/bin/env python3
"""STRILAS — route väst-patch-kortet (71×21, 2-lager, stack ovanpå P4 edge A).
DSN → power-klass (0,4 mm) → freeroute (loop) → ses_apply → GND-fyll (F+B) → verifiera → Gerbers/STEP.
Körs efter receiver_place.py firecontrol + firecontrol_flip.py (J1/J2-socklar → undersidan).
P4-socklarna sitter på DXF-exakta rader ±8.89 → samma router-flöde som moderkorten, 2-lager."""
import subprocess, sys, math, shutil, os, pcbnew
PCB = "hardware/vest-patch.kicad_pcb"; DSN = "hardware/vest-patch.dsn"; SES = "hardware/vest-patch.ses"
MM = pcbnew.FromMM; OX, OY = 150.0, 120.0
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

PLANE_NETS = ("GND",)          # GND fylls som plan på BÅDA lagren; signaler + kraft routas som spår
CU = [pcbnew.F_Cu, pcbnew.B_Cu]


def unrouted(path):
    b = pcbnew.LoadBoard(path)
    items = []
    for i, t in enumerate(b.GetTracks()):
        net = t.GetNetname()
        if not net: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition(); items.append((net, ("v", i), [(p.x, p.y, None)]))
        else:
            s, e, L = t.GetStart(), t.GetEnd(), t.GetLayer()
            items.append((net, ("t", i), [(s.x, s.y, L), (e.x, e.y, L)]))
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
    bad = 0
    for net, pads in netpads.items():
        if net in PLANE_NETS or len(pads) < 2: continue
        elems = bynet.get(net, [])
        for i in range(len(elems)):
            for j in range(i + 1, len(elems)):
                (ka, pa), (kb, pb) = elems[i], elems[j]
                touch = any((la is None or lb is None or la == lb)
                            and math.hypot(xa - xb, ya - yb) < 60000
                            for xa, ya, la in pa for xb, yb, lb in pb)
                if touch: par[find(ka)] = find(kb)
        if len({find(k) for k in pads}) > 1: bad += 1
    return bad


def leftover_nets(path):
    """Signal-nät som ej är helt sammankopplade (samma union-find som unrouted, men returnerar namn)."""
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
    out = []
    for net, pads in netpads.items():
        if net in PLANE_NETS or len(pads) < 2: continue
        el = bynet.get(net, [])
        for i in range(len(el)):
            for j in range(i + 1, len(el)):
                (ka, pa), (kb, pb) = el[i], el[j]
                if any((la is None or lb is None or la == lb) and math.hypot(xa - xb, ya - yb) < 60000
                       for xa, ya, la in pa for xb, yb, lb in pb): par[find(ka)] = find(kb)
        if len({find(k) for k in pads}) > 1: out.append(net)
    return out


def finish(path):
    b = pcbnew.LoadBoard(path)
    for z in list(b.Zones()): b.Remove(z)
    def add_zone(layer):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(b.FindNet("GND").GetNetCode())
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2)); z.SetIsFilled(False)
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for k in range(72):                            # cirkulär gjutning (rund Ø45, inset r=22)
            a = math.radians(k * 5); ch.Append(V(22.0 * math.cos(a), 22.0 * math.sin(a)))
        ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
    add_zone(pcbnew.F_Cu); add_zone(pcbnew.B_Cu)   # GND-fyll båda lagren (2-lager)
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
_tr = list(b.GetTracks()); _zo = list(b.Zones())
for t in _tr: b.Remove(t)
for z in _zo: b.Remove(z)
pcbnew.SaveBoard(PCB, b)
pcbnew.ExportSpecctraDSN(b, DSN)
subprocess.run(["python3", "hardware/dsn_power_class.py", DSN])
# 2-lager: uteslut GND ur freerouting-nätlistan → båda lagren fria för signaler (annars proppar
# 74 GND-spår igen → fler signaler misslyckas). GND maze-routas separat efteråt (som originalet).
import re as _re
_d = open(DSN).read()
_d = _re.sub(r'\n\s*\(net GND\s*\(pins[^)]*\)\s*\)', '', _d)
_d = _d.replace(" GND ", " ")
open(DSN, "w").write(_d)
shutil.copy(PCB, "/tmp/_vp_placed.kicad_pcb")
clean = False; best = None
for seed in range(1, 13):
    if os.path.exists(SES): os.remove(SES)
    subprocess.run(["timeout", "-k", "5", "240", "xvfb-run", "-a",
                    "java", "-jar", "/opt/freerouting.jar", "-de", DSN, "-do", SES, "-mp", "100"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["bash", "-c", "pkill -9 -f freerouting.jar 2>/dev/null; pkill -9 Xvfb 2>/dev/null; true"])
    if not os.path.exists(SES) or os.path.getsize(SES) < 1000:
        print(f"  seed {seed}: freerouting timeout/ingen SES — nästa seed"); continue
    shutil.copy("/tmp/_vp_placed.kicad_pcb", PCB)
    subprocess.run(["python3", "hardware/ses_apply.py", PCB, SES], stdout=subprocess.DEVNULL)
    u = unrouted(PCB); print(f"  seed {seed}: signal-oroutade = {u}")
    if best is None or u < best[0]:
        best = (u, seed); shutil.copy(PCB, "/tmp/_vp_best.kicad_pcb")
    if u == 0: clean = True; break
# bästa seed (GND routas av freerouting → inga instängda GND-paddar). Stäng ev. kvar-signaler med maze.
shutil.copy("/tmp/_vp_best.kicad_pcb", PCB)
# maze-routa ev. kvar-signaler + HELA GND-nätet (GND uteslöts ur freerouting → måste dras nu)
left = leftover_nets(PCB)
print(f"  bästa seed {best[1]}: {best[0]} signal kvar ({left}) + GND → maze-router")
subprocess.run(["python3", "hardware/maze_route.py", PCB] + left + ["GND"])
if unrouted(PCB) != 0: print("!! maze kunde ej stänga alla signaler"); sys.exit(1)
finish(PCB)
v, un = verify(PCB); print(f"clearance@0.2mm = {v}   oconnected = {un}")
if v or un: print("!! DRC ej ren"); sys.exit(1)
print("REN board.")
os.system("rm -rf /tmp/gbvp && mkdir -p /tmp/gbvp")
subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "-o", "/tmp/gbvp/", PCB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["kicad-cli", "pcb", "export", "drill", "-o", "/tmp/gbvp/", PCB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["bash", "-c", "cd /tmp/gbvp && zip -q -r - . > /home/user/Strilas/hardware/vest-patch-gerbers.zip"])
subprocess.run(["kicad-cli", "pcb", "export", "step", "-f", "--subst-models", "-o", "hardware/vest-patch.step", PCB],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Gerbers + STEP exporterade.")
