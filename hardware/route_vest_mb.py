#!/usr/bin/env python3
"""STRILAS — route väst-moderkort (100×60, 4-lager): DSN → power-klass (0,4 mm) → freeroute (loop) →
ses_apply → kopparplan (In1=GND, In2=VBAT, F/B=GND-fyll; +3V3 routat — lågström) → verifiera → Gerbers/STEP.
Körs efter receiver_place.py vest_mb. (1-nods-NC/reserv-nät ignoreras i routnings-grinden.)

KRAFTPLAN: In2 = VBAT-plan (hög LED-ström: 10 patchar × 3 grenar ≈ 5–8 A topp på VBAT, drivs
direkt från batteriet — INTE bucken). +3V3 är lågström (TSOP/logik <1 A) → routas som spår.
(Tidigare hade In2=+3V3 och VBAT som 0,4 mm-spår → underdimensionerat för LED-toppen; bytt.)"""
import subprocess, sys, math, shutil, os, pcbnew
PCB = "hardware/vest-mb.kicad_pcb"; DSN = "hardware/vest-mb.dsn"; SES = "hardware/vest-mb.ses"
MM = pcbnew.FromMM; OX, OY = 150.0, 120.0
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))


PLANE_NETS = ("GND", "VBAT")   # får kopparplan i finish() → behöver ej full spår-routning


def unrouted(path):
    """Antal signal-nät som EJ är helt sammankopplade (union-find över spår/via/pad, utan plan).
    Plan-näten (GND/VBAT) hoppas över; de fylls som plan senare. Fångar nät-öar (delade nät)."""
    b = pcbnew.LoadBoard(path)
    CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
    items = []   # (net, key, [(x,y,layer-or-None-for-via)])
    for i, t in enumerate(b.GetTracks()):
        net = t.GetNetname()
        if not net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition(); items.append((net, ("v", i), [(p.x, p.y, None)]))
        else:
            s, e, L = t.GetStart(), t.GetEnd(), t.GetLayer()
            items.append((net, ("t", i), [(s.x, s.y, L), (e.x, e.y, L)]))
    netpads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            net = p.GetNetname()
            if not net:
                continue
            pos = p.GetPosition(); lays = [L for L in CU if p.IsOnLayer(L)]
            key = ("p", f.GetReference() + "." + p.GetName())
            items.append((net, key, [(pos.x, pos.y, L) for L in lays] or [(pos.x, pos.y, None)]))
            netpads.setdefault(net, []).append(key)
    bynet = {}
    for net, key, pts in items:
        bynet.setdefault(net, []).append((key, pts))
    par = {}
    def find(x):
        par.setdefault(x, x)
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    bad = 0
    for net, pads in netpads.items():
        if net in PLANE_NETS or len(pads) < 2:
            continue
        elems = bynet.get(net, [])
        for i in range(len(elems)):
            for j in range(i + 1, len(elems)):
                (ka, pa), (kb, pb) = elems[i], elems[j]
                touch = any((la is None or lb is None or la == lb)
                            and math.hypot(xa - xb, ya - yb) < 60000   # 0.06 mm
                            for xa, ya, la in pa for xb, yb, lb in pb)
                if touch: par[find(ka)] = find(kb)
        if len({find(k) for k in pads}) > 1:
            bad += 1
    return bad


def finish(path):
    b = pcbnew.LoadBoard(path)
    for z in list(b.Zones()): b.Remove(z)
    def add_zone(layer, net):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(b.FindNet(net).GetNetCode())
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2)); z.SetIsFilled(False)
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in [(-49.5, -29.5), (49.5, -29.5), (49.5, 29.5), (-49.5, 29.5)]: ch.Append(V(x, y))
        ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
    add_zone(pcbnew.In1_Cu, "GND"); add_zone(pcbnew.In2_Cu, "VBAT")   # In2=VBAT-plan (hög LED-ström → helt innerplan)
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


b = pcbnew.LoadBoard(PCB)
_tr = list(b.GetTracks()); _zo = list(b.Zones())  # samla FÖRST (mutering ogiltigförklarar iteratorn)
for t in _tr: b.Remove(t)                          # rensa ev. spår/via från tidigare routning
for z in _zo: b.Remove(z)                          # rensa ev. kopparplan → ren DSN (inga "multiple vias skipped")
pcbnew.SaveBoard(PCB, b)                            # spara ren placerad board (placerings-utgångsläge)
pcbnew.ExportSpecctraDSN(b, DSN)
subprocess.run(["python3", "hardware/dsn_power_class.py", DSN])
shutil.copy(PCB, "/tmp/_vmb_placed.kicad_pcb")
clean = False
for seed in range(1, 13):
    if os.path.exists(SES): os.remove(SES)   # tvinga ny SES → ingen stale-återanvändning
    # hård per-seed-timeout: headless-freerouting hänger ibland @1% CPU → döda + nästa seed
    subprocess.run(["timeout", "-k", "5", "240", "xvfb-run", "-a",
                    "java", "-jar", "/opt/freerouting.jar", "-de", DSN, "-do", SES, "-mp", "100"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["bash", "-c", "pkill -9 -f freerouting.jar 2>/dev/null; pkill -9 Xvfb 2>/dev/null; true"])
    if not os.path.exists(SES) or os.path.getsize(SES) < 1000:
        print(f"  seed {seed}: freerouting timeout/ingen SES — nästa seed"); continue
    shutil.copy("/tmp/_vmb_placed.kicad_pcb", PCB)
    subprocess.run(["python3", "hardware/ses_apply.py", PCB, SES], stdout=subprocess.DEVNULL)
    u = unrouted(PCB); print(f"  seed {seed}: signal-oroutade = {u}")
    if u == 0: clean = True; break
if not clean: print("!! ingen ren routning"); sys.exit(1)
finish(PCB)
v, un = verify(PCB); print(f"clearance@0.2mm = {v}   oconnected = {un}")
if v or un: print("!! DRC ej ren"); sys.exit(1)
print("REN board.")
os.system("rm -rf /tmp/gbv2 && mkdir -p /tmp/gbv2")
subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "-o", "/tmp/gbv2/", PCB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["kicad-cli", "pcb", "export", "drill", "-o", "/tmp/gbv2/", PCB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["bash", "-c", "cd /tmp/gbv2 && zip -q -r - . > /home/user/Strilas/hardware/vest-mb-gerbers.zip"])
subprocess.run(["kicad-cli", "pcb", "export", "step", "-f", "--subst-models", "-o", "hardware/vest-mb.step", PCB],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Gerbers + STEP exporterade.")
