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
IMU2N = {"IMU2_INT","IMU3_INT"}                # de 2 nya I²C-IMU:erna
IDN  = {"ID_SD","ID_SC"}                       # HAT-ID-EEPROM-buss
BUCKN = {"SW_n","BST_n","FB_n"}                # buck-switchstegets noder
def cluster(ref):
    if ref == "J1": return "HDR"
    if (comps[ref][0] or "").startswith(("Connector_JST","Connector_PinHeader")): return "CONN"
    nets = ref_nets[ref]
    if nets & BUCKN: return "BUCK"
    if nets & IDN: return "EEPROM"
    if nets & CC:  return "CC"
    if nets & IMU2N: return "IMU2"
    if nets & FCN: return "FC"
    if nets & IMUN: return "IMU"
    if "VBAT_SENSE" in nets: return "ADC"
    if nets & PWR: return "PWR"
    return "MISC"

# ---- cellstorlek per footprint-typ (mm, utan silk-text) ----
SIZES = [("TO-263",16,10),("TO-252",7.5,7),("SOT-23-5",4,4),("SOT-23",3.6,3.4),
         ("S4B-PH",11,7),("S2B-PH",8,6.5),("S2B-XH",9,7),("TSSOP",4.5,4),("LGA-14",4,4),
         ("SOIC-8",5.2,4.0),("R_2512",7,4),("C_1210",4,3.6),("C_1206",4,2.6),("D_SMB",5.5,4.2),("D_SMA",4.3,2.8),("Fuse_1812",6,4.5),
         ("R_0805",2.8,2),("C_0805",2.8,2),("C_0402",1.8,1.5)]
def cell(fp):
    for k, w, h in SIZES:
        if k in (fp or ""): return w, h
    return 3.5, 3.5

# 40-pin honan sitter i CENTRUM på BAKSIDAN (pad-rektangel x±25, y±2,1). En fri mittremsa
# |y|<CTR krävs på FRAMSIDAN (genompläterade hål). ALLA kontakter ligger på TOPP-/BOTTEN-KANTEN
# (rot 0 → låga i y, kabel ut ur kanten); SMT packas i de två banden mellan header och kant.
CTR = 3.6                                   # halv mittremsa (header-pad ±2,1 + marginal)
TOPCL = {"PWR", "IMU", "CC", "BUCK"}        # dessa SMT-kluster → toppbandet; övriga → bottenbandet
# ---- regioner (radpacka vänster→höger, nedåt): xL, xR, yTop ----
# SMT i icke-överlappande x-banor (höger om bucken upptill; ovanför kant-kontakterna nedtill).
# BOTTEN-bandet rymmer nu även de 2 nya I²C-IMU:erna (IMU2) + deras avkopplingscaps (MISC).
REG = {"BUCK":(-27,-12,13), "PWR":(-12,18,13), "IMU":(18,27,13), "CC":(-26,-20,13),   # TOPP-band
       "ADC":(-27,-17,-6), "IMU2":(-17,-9,-6), "FC":(-9,3,-6),                  # BOTTEN-band
       "EEPROM":(3,11,-6), "MISC":(11,27,-6)}                                   # MISC = avkopplingscaps, bred lane
# fasta kontakt-lägen — ALLA på topp/botten-kant (kabel ut ur kant), klara av mittremsan
def fixedpos(ref):
    fp, v = comps[ref]; v = v or ""
    if ref == "J1": return (0, 0, 90)         # 40-pin HONA centrum (flippas till baksidan nedan)
    if "AP63203" in v: return (-23, 11, 0)    # buck-IC topp-vänster
    if "MD-5050" in (fp or ""): return (-17.5, 11, 0)  # buck-induktor intill IC → kort SW-nod
    if "optik" in v: return (6, 18, 180)      # emitter-JST (→optik) topp-kant (pad-rad klar av NFC)
    if "NFC" in v: return (15, 18, 180)       # NFC topp-kant höger (klar av standoff-hål)
    if "2S batteri" in v: return (-20, -18, 0)       # batteri JST-XH botten-vänster kant (klar av standoff-hål)
    if "TRIGGER" in v: return (-13, -18, 0)
    if "RACK" in v: return (-6.5, -18, 0)
    if "MAGREL" in v: return (0, -18, 0)
    if "MAGWELL" in v: return (6.5, -18, 0)
    if "recoil" in v: return (16, -18, 0)     # recoil botten-kant höger
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

# 40-pin honan: FLIPPA till baksidan FÖRST (Flip speglar runt pin1-origo), centrera SEDAN
# kortets geometriska CENTRUM via PAD-centroid (ej bbox; silk/ref snedvrider).
j1 = fps["J1"]
j1.Flip(j1.GetPosition(), False)            # → BAKSIDAN (trycks ner på carrierns centrum-stiftlist)
px = [p.GetPosition().x for p in j1.Pads()]; py = [p.GetPosition().y for p in j1.Pads()]
cxp = (min(px)+max(px))//2; cyp = (min(py)+max(py))//2
j1.Move(pcbnew.VECTOR2I(int(OX*1e6) - cxp, int(OY*1e6) - cyp))

# --- relaxering: nudga ev. överlappande (icke-fasta) footprints isär tills 0 clearance ---
# BAND-MEDVETEN: varje rörlig del klampas i SITT band (topp y≥+CTR / botten y≤-CTR) så att
# mittremsan för centrum-honan ALLTID hålls fri på framsidan.
import math
movable = [r for r in fps if fixedpos(r) is None]
band = {r: (1 if cluster(r) in TOPCL else -1) for r in movable}   # +1 topp, -1 botten
def hits(ra, rb):
    return any(pa.GetEffectiveShape().Collide(pb.GetEffectiveShape(), int(0.2e6))
               for pa in fps[ra].Pads() for pb in fps[rb].Pads())
XMIN, XMAX = int((OX-25)*1e6), int((OX+25)*1e6)
INNER = CTR + 2.2                                        # håll del-CENTRUM så att även pads klarar remsan
YTOP_LO, YTOP_HI = int((OY-14.5)*1e6), int((OY-INNER)*1e6) # toppband (mellan header och topp-kontakter)
YBOT_LO, YBOT_HI = int((OY+INNER)*1e6), int((OY+14.5)*1e6) # bottenband (mellan header och kant-JST)
def clampy(r, y):
    return (min(YTOP_HI, max(YTOP_LO, y)) if band[r] > 0 else min(YBOT_HI, max(YBOT_LO, y)))
# hård FÖR-klamp: tvinga ALLA rörliga in i sitt band + på kortet (packaren kan spilla över kant);
# liten unik x-spridning bryter exakt-staplade lägen så relaxeringen säkert konvergerar
for i, r in enumerate(sorted(movable)):
    p = fps[r].GetPosition()
    fps[r].SetPosition(pcbnew.VECTOR2I(min(XMAX, max(XMIN, p.x + (i % 7 - 3) * 200000)), clampy(r, p.y)))
for _ in range(250):
    moved = False
    for ra in movable:
        for rb in fps:
            if ra == rb or not hits(ra, rb): continue
            pa, pb = fps[ra].GetPosition(), fps[rb].GetPosition()
            dx, dy = pa.x - pb.x, pa.y - pb.y
            if dx == 0 and dy == 0: dy = 1
            L = math.hypot(dx, dy) or 1; st = 0.8e6
            nx = min(XMAX, max(XMIN, pa.x + int(dx/L*st))); ny = clampy(ra, pa.y + int(dy/L*st))
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

# 4 standoff-monteringshål (M2.5) i hörnen → 20 mm-standoffs upp till optik-PCB:n.
# Lägen matchar optikens hörnhål (±18,±25,5) när optiken sitter 90°-vriden på stacken.
for i,(hx,hy) in enumerate([(25.5,18),(25.5,-18),(-25.5,18),(-25.5,-18)]):
    mh = pcbnew.FootprintLoad(f"{F}/MountingHole.pretty", "MountingHole_2.7mm_M2.5")
    mh.SetReference(f"MH{i+1}"); mh.SetPosition(V(hx,hy)); b.Add(mh)

pcbnew.SaveBoard("hardware/weapon-hat.kicad_pcb", b)
print(f"placerade {len(fps)} komponenter → hardware/weapon-hat.kicad_pcb (70×58 mm, 2-lager)")
