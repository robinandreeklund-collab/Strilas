#!/usr/bin/env python3
"""STRILAS — VAPEN-HAT placering: bygg board ur weapon-hat.net (parse → kluster → radpacka → nät).
kinet2pcb saknas → bygg direkt via pcbnew: ladda footprints, klustra per funktion, radpacka utan
överlapp (storlek per footprint-typ, ej silk-bbox), tilldela nät. Sedan route_weapon_hat.py (freerouting).
Kör:  python3 hardware/weapon_hat_place.py  → hardware/weapon-hat.kicad_pcb
"""
import re, pcbnew
from collections import defaultdict
OX, OY = 150.0, 120.0; MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
F = "/usr/share/kicad/footprints"; LOC = "/home/user/Strilas"
NET = "hardware/weapon-hat.net"

# ---- parse netlist (flerradat KiCad-format) ----
txt = open(NET).read()
comps = {}
for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)\s+\(value "([^"]*)"\)(.*?)(?=\(comp\s+\(ref|\(libparts|\Z)', txt, re.S):
    ref, val, rest = m.groups()
    fm = re.search(r'\(footprint "([^"]+)"', rest)
    comps[ref] = (fm.group(1) if fm else None, val)
padnet = {}
for blk in re.split(r'\(net\s', txt)[1:]:
    nm = re.search(r'\(name "([^"]+)"', blk)
    if not nm: continue
    net = nm.group(1).lstrip('/')
    for nd in re.finditer(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', blk):
        padnet[(nd.group(1), nd.group(2))] = net

# ---- kluster ur nät-medlemskap ----
CC   = {"IDRV_REF","IDRV_SENSE","DRV_GATE","LED_CATH","VBAT_E"}
PWR  = {"VBAT","VBAT_IN","VBAT_F","+5V"}
IMUN = {"SCK","MOSI","MISO","nCS","IMU_INT"}
FCN  = {"TRIG","RACK","MAGREL","MAGWELL","RECOIL_PWM","RECOIL_FAULT","MODE0","MODE1","PTT"}
ref_nets = defaultdict(set)
for (r, p), n in padnet.items(): ref_nets[r].add(n)
def cluster(ref):
    if ref == "J1": return "HDR"
    if (comps[ref][0] or "").startswith(("Connector_JST","Connector_PinHeader")): return "CONN"
    nets = ref_nets[ref]
    if nets & CC:  return "CC"
    if nets & FCN: return "FC"
    if nets & IMUN: return "IMU"
    if "VBAT_SENSE" in nets: return "ADC"
    if nets & PWR: return "PWR"
    return "MISC"

# ---- cellstorlek per footprint-typ (mm, utan silk-text) ----
SIZES = [("TO-263",16,10),("TO-252",7.5,7),("SOT-23-5",4,4),("SOT-23",3.6,3.4),
         ("S4B-PH",11,7),("S2B-PH",8,6.5),("S2B-XH",9,7),("TSSOP",4.5,4),("LGA-14",4,4),
         ("R_2512",7,4),("C_1210",4,3.6),("C_1206",4,2.6),("D_SMB",5.5,4.2),("Fuse_1812",6,4.5),
         ("R_0805",2.8,2),("C_0805",2.8,2),("C_0402",1.8,1.5)]
def cell(fp):
    for k, w, h in SIZES:
        if k in (fp or ""): return w, h
    return 3.5, 3.5

# ---- regioner (radpacka vänster→höger, nedåt): xL, xR, yTop — TIGHT för 56×41 ----
REG = {"CC":(-27,-15,11), "IMU":(-14,-5,11), "ADC":(-3,7,11),
       "PWR":(-26,-2,-2), "FC":(-1,22,-2), "MISC":(8,22,11)}
# fasta kontakt-lägen — mappas via VÄRDE-sträng (robust mot SKiDL-ref-numrering J3..J9)
def fixedpos(ref):
    fp, v = comps[ref]; v = v or ""
    if ref == "J1": return (0, 16, 90)       # 40-pin header topp (48 mm i 56-bredden)
    if "TO-263" in (fp or ""): return (-21, 2, 90)   # buck (stor, roterad) vänster, klar av kant
    if "XT30" in v: return (-23, -17, 0)      # batteri nedre-vänster
    if "optik" in v: return (24, 6, 90)       # emitter-JST (→optik) höger kant
    if "TRIGGER" in v: return (-11, -17.5, 0)
    if "RACK" in v: return (-4, -17.5, 0)
    if "MAGREL" in v: return (3, -17.5, 0)
    if "MAGWELL" in v: return (10, -17.5, 0)
    if "recoil" in v: return (24, -14, 90)
    if "NFC" in v: return (24, -6, 90)
    return None

b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)
nets_obj = {}
def get_net(n):
    if n not in nets_obj:
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets_obj[n] = ni
    return nets_obj[n]

# ladda alla footprints + tilldela nät
fps = {}
for ref, (fp, val) in comps.items():
    lib, mod = fp.split(":", 1); base = F if lib != "strilas" else LOC + "/hardware"
    f = pcbnew.FootprintLoad(f"{base}/{lib}.pretty", mod)
    if f is None: print("FAIL load", fp); continue
    f.SetReference(ref); f.SetValue(val); b.Add(f); fps[ref] = f
    for pd in f.Pads():
        n = padnet.get((ref, pd.GetName()))
        if n: pd.SetNet(get_net(n))
# fasta lägen (kontakter, via värde-mappning)
for ref in fps:
    fp = fixedpos(ref)
    if fp: fps[ref].SetOrientationDegrees(fp[2]); fps[ref].SetPosition(V(fp[0], fp[1]))
# radpacka övriga per kluster
groups = defaultdict(list)
for ref in comps:
    if fixedpos(ref) is None: groups[cluster(ref)].append(ref)
MARG = 1.5
for cl, refs in groups.items():
    xL, xR, yTop = REG.get(cl, REG["MISC"])
    refs.sort(key=lambda r: -cell(comps[r][0])[0])     # stora först → tätare
    cx, cy, rowh = xL, yTop, 0.0
    for ref in refs:
        w, h = cell(comps[ref][0])
        if cx + w > xR: cx = xL; cy -= rowh + MARG; rowh = 0.0
        fps[ref].SetOrientationDegrees(0); fps[ref].SetPosition(V(cx + w/2, cy - h/2))
        cx += w + MARG; rowh = max(rowh, h)

# centrera 40-pin headern via bbox (origo = pin1)
j1 = fps["J1"]; bb = j1.GetBoundingBox()
j1.Move(pcbnew.VECTOR2I(int(OX*1e6) - (bb.GetLeft()+bb.GetRight())//2, int((OY-16.5)*1e6) - (bb.GetTop()+bb.GetBottom())//2))

# --- relaxering: nudga ev. överlappande (icke-fasta) footprints isär tills 0 clearance ---
import math
movable = [r for r in fps if fixedpos(r) is None]
def hits(ra, rb):
    return any(pa.GetEffectiveShape().Collide(pb.GetEffectiveShape(), int(0.2e6))
               for pa in fps[ra].Pads() for pb in fps[rb].Pads())
XMIN, XMAX = int((OX-24)*1e6), int((OX+24)*1e6); YMIN, YMAX = int((OY-18)*1e6), int((OY+18)*1e6)
for _ in range(80):
    moved = False
    for ra in movable:
        for rb in fps:
            if ra == rb or not hits(ra, rb): continue
            pa, pb = fps[ra].GetPosition(), fps[rb].GetPosition()
            dx, dy = pa.x - pb.x, pa.y - pb.y
            if dx == 0 and dy == 0: dy = 1
            L = math.hypot(dx, dy) or 1; st = 0.8e6
            nx = min(XMAX, max(XMIN, pa.x + int(dx/L*st))); ny = min(YMAX, max(YMIN, pa.y + int(dy/L*st)))
            fps[ra].SetPosition(pcbnew.VECTOR2I(nx, ny)); moved = True
    if not moved: break

# outline 70×58 mm
W, H = 28.0, 20.5
pts = [(-W,-H),(W,-H),(W,H),(-W,H)]
for i in range(4):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1)%4])); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
tt = pcbnew.PCB_TEXT(b); tt.SetText("STRILAS VAPEN-HAT (CM5)"); tt.SetPosition(V(0, 16)); tt.SetLayer(pcbnew.F_SilkS)
tt.SetTextSize(pcbnew.VECTOR2I(MM(1.2),MM(1.2))); tt.SetTextThickness(MM(0.2)); tt.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(tt)

pcbnew.SaveBoard("hardware/weapon-hat.kicad_pcb", b)
print(f"placerade {len(fps)} komponenter → hardware/weapon-hat.kicad_pcb (70×58 mm, 2-lager)")
