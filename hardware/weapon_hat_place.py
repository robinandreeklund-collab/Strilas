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
    # KONTAKTER courtyard-balanserade: 6 djupa på botten fick EJ plats (46,9>46mm). Batteri-JST (XH,
    # 12,5mm DJUP) stannar botten; en GRUND PH (magwell) flyttas till TOPP-kant → båda får ~1mm gap.
    # Kant-kontakter hålls innanför ±22 (standoff-courtyard ~Ø7 vid ±25,5).
    if "MAGWELL" in v: return (-18, 18, 180)  # magwell-JST → TOPP-kant vänster (grund PH, klarar nedsänkt buck)
    if "ESP-brygga" in v: return (-7.5, 18, 180) # ESP-JST → extern modul
    if "optik" in v: return (4, 18, 180)      # emitter-JST (→optik)
    if "NFC" in v: return (15, 18, 180)       # NFC topp-kant höger
    if "AP63203" in v: return (-22.5, 10, 0)  # buck-IC (nedsänkt 1mm → topp-kontakter klarar kroppen)
    if "MD-5050" in (fp or ""): return (-16.5, 10, 0)  # buck-induktor intill IC
    if "2S batteri" in v: return (-17.5, -18, 0)  # batteri-JST botten-vänster
    if "TRIGGER" in v: return (-10, -18, 0)   # botten-kant: 5 kontakter, ~1mm gap
    if "RACK" in v: return (-3, -18, 0)
    if "MAGREL" in v: return (4, -18, 0)
    if "recoil" in v: return (14.5, -18, 0)   # recoil botten-kant höger
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
# ESP32-C6-sockeln ligger på FRAMSIDAN (i gapet mot optiken, USB-C nedåt) — ingen flip.

# --- EDGE-KONTAKT-SPRIDNING (courtyard-baserad, 1D): lägg kant-JST:er sida-vid-sida UTAN överlapp,
#     innanför ±22 (standoff-courtyard ~Ø6 vid ±25,5). Görs FÖRE SMT-relaxeringen → SMT packas runt
#     slutliga kontaktlägen. fixedpos-x sätter ORDNINGEN; här finjusteras x via uppmätta courtyards. ---
def _cyedge(ref):
    f = fps[ref]
    for L in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        cy = f.GetCourtyard(L)
        if cy and cy.OutlineCount() > 0:
            bb = cy.BBox(); return bb.GetLeft()/1e6 - OX, bb.GetRight()/1e6 - OX
    bb = f.GetBoundingBox(False, False); return bb.GetLeft()/1e6 - OX, bb.GetRight()/1e6 - OX
for _ey in (1, -1):
    _conns = [r for r in fps if r != "J1" and (comps[r][0] or "").startswith("Connector_JST")
              and (OY - fps[r].GetPosition().y/1e6) * _ey > 8]
    _conns.sort(key=lambda r: fps[r].GetPosition().x)
    _cur = -22.0
    for r in _conns:
        l, rt = _cyedge(r); c = fps[r].GetPosition().x/1e6 - OX
        yy = OY - fps[r].GetPosition().y/1e6
        fps[r].SetPosition(V(_cur - (l - c), yy))      # skift så vänster-courtyardkant = _cur
        _cur += (rt - l) + 0.8                          # nästa vänsterkant = denna högerkant + 0,8mm

# --- relaxering: nudga ev. överlappande (icke-fasta) footprints isär tills 0 clearance ---
# BAND-MEDVETEN: varje rörlig del klampas i SITT band (topp y≥+CTR / botten y≤-CTR) så att
# mittremsan för centrum-honan ALLTID hålls fri på framsidan.
import math
movable = [r for r in fps if fixedpos(r) is None]
band = {r: (1 if cluster(r) in TOPCL else -1) for r in movable}   # +1 topp, -1 botten
# COURTYARD-medveten kollision: använd komponentens KROPP (courtyard-bbox), ej bara pads → inga
# kroppar ovanpå varandra. Cacha half-extent + centrum-offset (translations-invariant i relaxeringen).
def cyinfo(f):
    bb = None
    for L in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        cy = f.GetCourtyard(L)
        if cy and cy.OutlineCount() > 0: bb = cy.BBox(); break
    if bb is None: bb = f.GetBoundingBox(False, False)
    p = f.GetPosition(); c = bb.GetCenter()
    return (bb.GetWidth()//2, bb.GetHeight()//2, c.x - p.x, c.y - p.y)
CY = {r: cyinfo(fps[r]) for r in fps}
GAP = int(0.15e6)
def cxy(ref):
    p = fps[ref].GetPosition(); hw, hh, ox, oy = CY[ref]
    return p.x + ox, p.y + oy, hw, hh
def hits(ra, rb):
    xa, ya, hwa, hha = cxy(ra); xb, yb, hwb, hhb = cxy(rb)
    return abs(xa - xb) < hwa + hwb + GAP and abs(ya - yb) < hha + hhb + GAP
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

# --- AVKOPPLING: snäpp 2-poliga caps INTILL rätt IC/pin (kort loop → bra PI/EMI) ---
# Auto-placeringen klustrar caps på nät → de hamnar långt från sina IC. Här flyttas varje
# avkopplingscap till närmaste lediga läge runt sitt mål: buck-in/ut/BST vid bucken,
# +3V3-caps fördelas till närmaste 3V3-IC, sense-cap vid ADC.
def padpos(ref, net):
    for p in fps[ref].Pads():
        if padnet.get((ref, p.GetName())) == net: q = p.GetPosition(); return (q.x, q.y)
    q = fps[ref].GetPosition(); return (q.x, q.y)
def collide(ref, x, y):
    fps[ref].SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
    hw, hh, ox, oy = CY[ref]; cx, cyy = int(x) + ox, int(y) + oy
    for o in fps:
        if o == ref: continue
        xo, yo, hwo, hho = cxy(o)
        if abs(cx - xo) < hw + hwo + GAP and abs(cyy - yo) < hh + hho + GAP: return True
    return False
buck = next((r for r in fps if "AP63203" in (comps[r][1] or "")), None)
ind  = next((r for r in fps if "MD-5050" in (comps[r][0] or "")), None)
adc  = next((r for r in fps if "ADS1115" in (comps[r][1] or "")), None)
ics3 = [r for r in fps if r[0] == "U" and "+3V3" in ref_nets[r]]
deco = [r for r in fps if r[0] == "C" and fixedpos(r) is None]
tgt = {}
rr = 0
for c in deco:
    n = ref_nets[c]
    if "BST_n" in n and buck: tgt[c] = padpos(buck, "BST_n")
    elif "VBAT" in n and buck: tgt[c] = padpos(buck, "VBAT")          # buck-input-caps
    elif "+5V" in n and ind:  tgt[c] = padpos(ind, "+5V")            # buck-output-caps
    elif "VBAT_SENSE" in n and adc: tgt[c] = padpos(adc, "VBAT_SENSE")
    elif "+3V3" in n and ics3:
        ic = ics3[rr % len(ics3)]; rr += 1; q = fps[ic].GetPosition(); tgt[c] = (q.x, q.y)
MH_POS = [(25.5,18),(25.5,-18),(-25.5,18),(-25.5,-18)]               # standoff-hål (skapas senare)
def cval(c):  # HF/små först (närmast IC), bulk sist
    v = (comps[c][1] or "")
    return {"100nF":0,"1uF":1,"22pF":0,"10uF":2,"22uF":3,"100uF":4}.get(v, 1)
for c in sorted(tgt, key=cval):
    tx, ty = tgt[c]; orig = fps[c].GetPosition(); done = False
    for rad in (1.5, 2.0, 2.5, 3.0, 3.6, 4.3, 5.2, 6.2):
        for a in range(0, 360, 20):
            x = min(XMAX, max(XMIN, tx + rad*1e6*math.cos(math.radians(a))))
            y = ty + rad*1e6*math.sin(math.radians(a))
            xb, yb = x/1e6 - OX, OY - y/1e6
            if abs(yb) < CTR + 1 or abs(yb) > 19: continue          # ut ur mittremsa + på kort
            if any(math.hypot(xb-mx, yb-my) < 2.8 for mx, my in MH_POS): continue  # klar av standoff-hål
            if not collide(c, x, y): done = True; break
        if done: break
    if not done: fps[c].SetPosition(orig)                            # ingen plats → behåll relaxat läge (ej krock)

# outline 56×41 mm (alla kort samma storlek — C6-sockeln på framsidan kräver ingen tillväxt)
W, H, CH = 28.0, 20.5, 2.0
# TOPP-VÄNSTRA hörnet FASAT (2 mm, 45°) = orienterings-nyckel → kortet kan ej monteras 180°-fel.
pts = [(-W,-H),(W,-H),(W,H),(-W+CH,H),(-W,H-CH)]
for i in range(len(pts)):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1)%len(pts)])); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
tt = pcbnew.PCB_TEXT(b); tt.SetText("STRILAS VAPEN-HAT (CM5)"); tt.SetPosition(V(0, 16)); tt.SetLayer(pcbnew.F_SilkS)
tt.SetTextSize(pcbnew.VECTOR2I(MM(1.2),MM(1.2))); tt.SetTextThickness(MM(0.2)); tt.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(tt)

# 4 standoff-monteringshål (M2.5) i hörnen → 20 mm-standoffs upp till optik-PCB:n.
# Lägen matchar optikens hörnhål (±18,±25,5) när optiken sitter 90°-vriden på stacken.
for i,(hx,hy) in enumerate([(25.5,18),(25.5,-18),(-25.5,18),(-25.5,-18)]):
    mh = pcbnew.FootprintLoad(f"{F}/MountingHole.pretty", "MountingHole_2.7mm_M2.5")
    mh.SetReference(f"MH{i+1}"); mh.SetPosition(V(hx,hy)); b.Add(mh)

# PIN1-MARKÖR: Ø1,2 mm NPTH-hål intill 40-pin-headerns pin1 (-24,1,-1,3) → SYNS I STEP-modellen
# (silk syns ej i STEP). Läge (-22,6,-3,3) clear-skannat (≥0,9 mm koppar). + B.Silk-triangel mot pin1.
_pf = pcbnew.FOOTPRINT(b); _pf.SetReference("PIN1"); _pf.SetValue("40-pin pin1"); _pf.SetPosition(V(-22.6,-3.3))
_pp = pcbnew.PAD(_pf); _pp.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); _pp.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
_pp.SetSize(pcbnew.VECTOR2I(MM(1.2),MM(1.2))); _pp.SetDrillSize(pcbnew.VECTOR2I(MM(1.2),MM(1.2)))
_pp.SetLayerSet(_pp.UnplatedHoleMask()); _pp.SetPosition(V(-22.6,-3.3)); _pf.Add(_pp)
_pf.Reference().SetVisible(False); _pf.Value().SetVisible(False); b.Add(_pf)
_tri = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_POLY); _ch = pcbnew.SHAPE_LINE_CHAIN()
for _p in [V(-23.5,-4.2),V(-21.7,-4.2),V(-22.6,-2.3)]: _ch.Append(_p)
_ch.SetClosed(True); _ps = pcbnew.SHAPE_POLY_SET(); _ps.AddOutline(_ch); _tri.SetPolyShape(_ps)
_tri.SetLayer(pcbnew.B_SilkS); _tri.SetFilled(True); _tri.SetWidth(MM(0.15)); b.Add(_tri)

pcbnew.SaveBoard("hardware/weapon-hat.kicad_pcb", b)
print(f"placerade {len(fps)} komponenter → hardware/weapon-hat.kicad_pcb (70×58 mm, 2-lager)")
