#!/usr/bin/env python3
"""STRILAS — placera + nät-tilldela receiver-korten (väst + hjälm) ur netlistan (pcbnew).
Nyckeldelar placeras enligt receiver_boards_layout; smådelar grid-placeras i fri zon.
Ritar outline (+ hjälm-centrumhål). Sparar .kicad_pcb. (Routas sedan av freerouting.)
"""
import re, math, os, sys, pcbnew

FPDIR = "/usr/share/kicad/footprints"
LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strilas.pretty")
MM = pcbnew.FromMM


def fp_load(lib, fp):
    """Ladda footprint; 'strilas' = lokalt projektbibliotek, annars KiCad-standard."""
    path = LOCAL if lib == "strilas" else f"{FPDIR}/{lib}.pretty"
    return pcbnew.FootprintLoad(path, fp)


def parse_net(path):
    t = open(path).read()
    comps = {}
    for m in re.finditer(r'\(comp\s*\(ref "([^"]+)"\).*?\(footprint "([^"]+)"\)', t, re.S):
        comps[m.group(1)] = m.group(2)
    nets = {}
    ns = t[t.index("(nets"):]
    for blk in re.split(r'\(net\s*\(code', ns)[1:]:
        nm = re.search(r'\(name "([^"]+)"\)', blk)
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', blk)
        if nm and nodes:
            nets[nm.group(1)] = nodes
    return comps, nets


def place(netfile, pcbfile, positions, outline, layers=2, center_hole=None, free=(-20, 20, -15, 15), cutout=None, labels=None):
    comps, nets = parse_net(netfile)
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(layers)
    OX, OY = 150.0, 120.0
    def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
    fps = {}
    # grid-positioner för delar utan explicit position
    gx0, gx1, gy0, gy1 = free
    ylo, yhi = sorted([int(gy0), int(gy1)]); xlo, xhi = sorted([int(gx0), int(gx1)])
    grid = [(x, y) for y in range(yhi, ylo-1, -4) for x in range(xlo, xhi+1, 5)]
    gi = 0
    for ref, fpname in comps.items():
        lib, fp = fpname.split(":")
        f = fp_load(lib, fp)
        if f is None:
            print(f"  !! KAN EJ LADDA {fpname} ({ref})"); continue
        f.SetReference(ref)
        flip = False
        if ref in positions:
            p = positions[ref]; x, y, rot = p[0], p[1], p[2]; flip = len(p) > 3 and p[3] == "B"
        else:
            x, y = grid[gi % len(grid)]; rot = 0; gi += 1
        f.SetPosition(V(x, y))
        if rot: f.SetOrientationDegrees(rot)
        board.Add(f); fps[ref] = f
        if flip:
            try: f.Flip(f.GetPosition(), False)
            except Exception as e: print(f"  flip {ref} fail: {e}")
    # nät
    for name, nodes in nets.items():
        net = pcbnew.NETINFO_ITEM(board, name); board.Add(net)
        for ref, pad in nodes:
            f = fps.get(ref)
            if not f: continue
            for p in f.Pads():
                if p.GetName() == pad: p.SetNet(net)
    # outline
    if outline[0] == "rect":
        _, hw, hh = outline
        pts = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        for i in range(4):
            s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1) % 4]))
            s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); board.Add(s)
    else:  # circle
        _, r = outline
        c = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_CIRCLE)
        c.SetCenter(V(0, 0)); c.SetEnd(V(r, 0))
        c.SetLayer(pcbnew.Edge_Cuts); c.SetWidth(MM(0.15)); board.Add(c)
    if center_hole:
        ch = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_CIRCLE)
        ch.SetCenter(V(0, 0)); ch.SetEnd(V(center_hole, 0))
        ch.SetLayer(pcbnew.Edge_Cuts); ch.SetWidth(MM(0.15)); board.Add(ch)
    if cutout:                              # lins-hål (kamera bakom kortet)
        cx, cy, cr = cutout
        co = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_CIRCLE)
        co.SetCenter(V(cx, cy)); co.SetEnd(V(cx+cr, cy))
        co.SetLayer(pcbnew.Edge_Cuts); co.SetWidth(MM(0.15)); board.Add(co)
    # silkscreen-etiketter (t.ex. sikt-pilar för TSOP-böjning): (x, y, text, [size_mm])
    for lab in (labels or []):
        lx, ly, txt = lab[0], lab[1], lab[2]
        sz = lab[3] if len(lab) > 3 else 1.2
        t = pcbnew.PCB_TEXT(board); t.SetText(txt)
        t.SetPosition(V(lx, ly)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(MM(sz), MM(sz))); t.SetTextThickness(MM(sz * 0.15))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        board.Add(t)
    pcbnew.SaveBoard(pcbfile, board)
    print(f"  {pcbfile}: {len(fps)} komponenter, {len(nets)} nät")


# ---- väst-patch (täcknings-NOD 37×37, FYRFALDIGT SYMMETRISK, 4 monteringshål) — 4 ledade TSOP4856, kardborre/lim ----
# SIKTE (beräknat optimum, se vapen-stack/ritningar/patch-sikte.md): 4 mottagare jämnt 90° isär i
# DIAMANT (NÖ/NV/SV/SÖ), var och en böjd ~40° UTÅT från kortets normal (ben böjs; silk-pil visar).
# → 99,5 % av framåt-hemisfären, 100 % inom 60° zenit, ~2,3 mottagare ser ett frontalskott (redundans).
# Full 4-falds symmetri → patchen kan placeras i VALFRI vridning på västen och funkar lika bra.
# Dom-aim vs footprint-rot (verif.): rot0=NED rot90=HÖGER rot180=UPP rot270=VÄNSTER → aim_az=(rot+270)%360.
# Refs: U1-4=TSOP · varje TSOP har egen OR-diod (D1-4) + avkoppl-C (C2-5) BREDVID sig (4 identiska kluster).
#       D5,D6=OSLON 860nm konstellation (N/S, symmetriskt) · R3,R4=10R 2512 · delat: J1=1x5, Q1=FET,
#       R1=DATA-pull, R2=gate, C1=bulk — centrerat. (konstellations-LED ≠ per-TSOP; de är kamera-markörer.)
import math as _math
def _ring2(r, deg): return (round(r*_math.cos(_math.radians(deg)), 2), round(r*_math.sin(_math.radians(deg)), 2))
# RUND väst-patch (kompakt, för skydds-/dom-kåpa). Optiken på kanten, aim radiellt UT (TSOP-ben +
# LED-tabbar böjs 40° ut → ingen platt frontruta skuggar synvinkeln, funkar i valfri vridning).
# Centrum = driver + kontakt + 2 fasta OSLON. Speglar hjälm-halons verifierade ring-mönster, nedskalat
# till minsta Ø utan courtyard-krock (de 4 LEDADE TSOP-benens svep sätter undre gränsen).
# courtyard-mittpunkt ≠ origo för TSOP (2.54,1.31) & 1x5-header (0,5.07) → kompensera så att KROPPEN
# (ej origo) hamnar centrerad på ringen/positionen. _comp = origo som ger önskad courtyard-mitt.
def _comp(cx, cy, rot, off):
    # origo som ger courtyard-CENTRUM på (cx,cy) efter SetOrientationDegrees(rot). off = courtyard-mitt-
    # offset frå origo @rot0 i KiCad-footprint-koord (Y-ned). Board-offset (Y-upp) = standardrot(rot)·(ox,-oy).
    # (KALIBRERAT mot faktisk placerad board — tidigare formel hade Y-teckenfel → asymmetriska TSOP.)
    rad = _math.radians(rot); ox, oy = off
    dx = ox*_math.cos(rad) + oy*_math.sin(rad)
    dy = ox*_math.sin(rad) - oy*_math.cos(rad)
    return (round(cx - dx, 2), round(cy - dy, 2))
def _se(theta, r_pad, npin, opening="out", flip=False):
    """Side-entry JST (S-typ): pad-rad TANGENTIELLT centrerad @ (r_pad, theta), kropp/kabel-öppning
    RADIELLT. opening='out' → kabel ut mot kanten; 'in' → mot centrum. Kalibrerat: front opening=(rot+270)%360,
    flip opening=(90-rot)%360; padrow front=rot, flip=(-rot). Returnerar (origin_x, origin_y, rot[, 'B'])."""
    th = _math.radians(theta)
    pcx, pcy = r_pad*_math.cos(th), r_pad*_math.sin(th)     # pad-rad-centrum (board y-up)
    odir = theta % 360 if opening == "out" else (theta + 180) % 360
    rot = ((90 - odir) % 360) if flip else ((odir + 90) % 360)
    prang = (-rot) % 360 if flip else rot                  # pad-rad-riktning
    half = (npin - 1) * 2 / 2.0
    ox = pcx - half*_math.cos(_math.radians(prang)); oy = pcy - half*_math.sin(_math.radians(prang))
    return (round(ox, 2), round(oy, 2), rot) + (("B",) if flip else ())
_OFF_TSOP = (2.54, 1.31)                 # TSOP-courtyard-mitt-offset (courtyard centreras på ringen)
_PT, _PD, _PC = 16.0, 11.0, 8.5          # TSOP-courtyard / OR-diod / avkoppling — ALLA på TSOP-ekern (radiellt)
_PL, _PH = 16.0, 20.0                    # LED-tab-ring (kardinal) / monteringshål (yttre annulus, i luckorna)
_VEST_R = 22.5                            # kort-radie (Ø45) — rund, ryms i Ø46,5-dom (ren symmetri kräver annulus)
vest_pos = {}
# 4 TSOP @ DIAGONALER (45/135/225/315) — OR-diod (D1-4) + avkoppling (C2-5) RADIELLT INÅT på SAMMA
# eker (4 IDENTISKA kluster → full symmetri; ingen +11°-lutning längre).
for i, a in enumerate((45, 135, 225, 315)):
    rot = (a + 90) % 360
    cx, cy = _ring2(_PT, a)
    vest_pos[f"U{i+1}"] = (*_comp(cx, cy, rot, _OFF_TSOP), rot)   # TSOP-kropp centrerad på ringen
    vest_pos[f"D{i+1}"] = (*_ring2(_PD, a), rot)                  # OR-diod på ekern (radiellt inåt)
    vest_pos[f"C{i+2}"] = (*_ring2(_PC, a), rot)                  # avkoppling stackad innanför OR
# 4 LED-tabbar @ KARDINALER (0/90/180/270) — pad-rad TANGENTIELL (precis som TSOP) så tabben viks
# radiellt UT (böjs 40°, LED mot horisonten). rot=(a+180) → pad-axel tangentiell (a+90).
# _comp m. off=(0,1.27): centrera pad-MITTPUNKTEN (mellan de 2 hålen) + 3D-modellen på ring-punkten
# (footprint-origo=pad1 → annars hamnar de 2 hålen osymmetriskt utåt). → hål straddlar kardinalen symmetriskt.
for i, a in enumerate((0, 90, 180, 270)):
    rot = (a + 180) % 360
    cx, cy = _ring2(_PL, a)
    vest_pos[f"D{i+7}"] = (*_comp(cx, cy, rot, (0.0, 1.27)), rot)
# 4 monteringshål MITT i TSOP→tab-luckorna (67.5/157.5/247.5/337.5) → symmetriskt, EJ snett mot tab/TSOP
for i, a in enumerate((67.5, 157.5, 247.5, 337.5)):
    vest_pos[f"H{i+1}"] = (*_ring2(_PH, a), 0)
# CENTRUM (spegelsymmetriskt vänster/höger): 2 fasta OSLON + driver + 3× 10R-grenR + DATA-pull/gate + bulk.
# J1 (5-pol JST-PH) är SIDOMONTERAD på BAKSIDAN (S-typ, låg bygghöjd, kabel ut i kant) → fronten helt fri.
vest_pos.update({
    "D5": (-2.4, 1.5, 0), "D6": (2.4, 1.5, 0),       # 2 fasta OSLON-konstellation (aim upp), center-par
    "Q1": (0.0, -3.0, 0),                            # LED-driver FET, center
    "R1": (-4.2, -3.0, 90), "R2": (4.2, -3.0, 90),   # DATA-pull 10k + gate 220R, flankerar FET (spegel)
    "R3": (0.0, 9.0, 0),                             # 10R gren-1 — N-kanal (radiellt, mellan center o tab)
    "R4": (9.0, 0.0, 90), "R5": (-9.0, 0.0, 90),     # 10R gren-2/3 — Ö/V-kanal (spegel)
    "C1": (0.0, -9.0, 90),                           # 10µF bulk (VBAT) — S-kanal
    "J1": _se(270, 14.0, 5, "out", flip=True),       # 5-pol JST-PH SIDOMONT. på BAKSIDAN, kabel ut nedkant
})
vest_labels = [(0.0, 5.5, "BOJ 40 UT", 0.5)]         # böj-instruktion (kort, center-fri yta)

# ---- hjälm-NOD (Ø100, komplett: buck+XIAO-S3+8TSOP+4LED+GNSS+I2S-audio) ----
# Ring (r=42) = 8× TSOP utåtriktade (360° huvud) + diod-OR + avkoppling strax innanför.
# 4× LED-konstellation (r=45) mellan TSOP-paren. Centrum = stackad XIAO + buck + modul-headers.
def _ring(r, deg): return (round(r*math.cos(math.radians(deg)), 1), round(r*math.sin(math.radians(deg)), 1))
helmet_pos = {}
for i in range(8):                                   # U2..U9 TSOP, D1..D8 BAT54, C4..C11 avkoppl (yttre ring)
    a = i*45
    helmet_pos[f"U{i+2}"] = (*_ring(41, a), (a+90) % 360)
    helmet_pos[f"D{i+1}"] = (*_ring(34, a), (a+90) % 360)
    helmet_pos[f"C{i+4}"] = (*_ring(26, a), (a+90) % 360)
for i in range(4):                                   # D9..D12 LED, R5..R8 10R-serieR (mellan TSOP-paren)
    a = 22.5 + i*90
    helmet_pos[f"D{i+9}"] = (*_ring(45, a), (a+90) % 360)
    helmet_pos[f"R{i+5}"] = (*_ring(36, a), (a+90) % 360)
helmet_pos.update({                                  # centrum-disk (r<27, innanför avkopplings-ringen)
    "J1": (-7.6, 0, 0), "J2": (7.6, 0, 0),           # XIAO ESP32-S3 (2× 1x7 sockel, lodräta rader)
    "U1": (-4, 17, 0), "L1": (4, 17, 0),             # buck + induktor (ovan XIAO)
    "C1": (-10, 14, 0), "C2": (-10, 20, 0), "C3": (12, 19, 0),  # Cbst / Cin / Cout
    "R1": (-1, 22, 90), "R2": (-1, 13, 90),          # FB-delare
    "R3": (-12, 9, 0),                               # DATA-pullup (nära XIAO D0)
    "J3": (0, -21.5, 0),                             # ZED-F9P 8-pol JST GH (nedan XIAO; puck i centrum, kabel)
    "J4": (21, 2, 0), "J5": (-22, 0, 0),             # amp 1x7 (höger) / mik 1x6 (vänster)
    "Q1": (13, 13, 0), "R4": (17, 12, 90),           # LED-driver + gate
    "J6": (35, -7, 0),                               # 2S-batteri JST (tom yttre-ring-lucka, mellan U9/U2)
    "H1": _ring(47, 45) + (0,), "H2": _ring(47, 135) + (0,),
    "H3": _ring(47, 225) + (0,), "H4": _ring(47, 315) + (0,),
})

# ---- vapen-optikmodul (42×62, P4-carrier) ----
# Lins-hål Ø16 i mitten (kamera bakom kortet): keepout x[-8,8] y[-12,4].
# Pulsloop hålls kort: C2(reservoar)→D2→D3→Q2(CC pass-FET)→R2(sense)→GND uppe.
# IMU + avkoppling i höger remsa; inmatningsskydd nere till vänster; headers nederst.
# Kamerafäste (B0332 38×38): 4× M2-hål i 28×28-mönster runt linsaxeln (0,-4).
#   H4(-14,10) H5(14,10) H6(-14,-18) H7(14,-18). Komponenter flyttade ut till kanterna
#   så dessa hål + standoffs är fria. Kameran skruvas fast bakom kortet, lins genom Ø16.
# P4-VÄNSTERLÄGE (enligt användarens Fusion-modell): P4 (71×21) ligger bakom kortet,
# huggande VÄNSTERKANTEN (centrum x≈-16, längd längs y, USB-C-änden UPP/ESP-änden ned).
# Edge B (VBUS/VSYS/3V3-sidan) ytterst (vänster) → optik-J1. Edge A (GPIO-sidan) inåt → FC-stack.
# Kamerans B4B-ZR-kontakt riktad +x (höger) → fri från P4. J1 (P4-kantkontakt) flyttad
# till vänsterkanten (P4:ans yttre signalrad). Kraft/skydd-remsa flyttad till HÖGERkanten;
# AKTIV KONSTANTSTRÖMS-SÄNKA (ersätter Rset): op-amp U2 + DPAK pass-FET Q2 + sense R2 +
# referensdelare R3/R4 + gate-R R5 + komp C7 + op-amp-avkoppl C6. Klustret i fria zonen
# x[-10,10] y[4,13] (mellan kamerahål H8/H9 @±14, under Carclo-ben @y15.2, ovan lins-keepout @y2).
# Funktioner (skidl-ref): U2=OPA171, Q2=AOD4184A(DPAK), R2=0R2 sense, R3=15k, R4=1k, R5=100R gate,
#   C2=Cbulk 100µF, C6=op-amp-avkoppl, C7=komp 100pF, F1=PTC, Q1=PFET(rev-pol), D1=TVS,
#   R1=100k-pulldown, C1=Cin 10µF, U1=IMU, C3/C4/C5=IMU-avkoppl.
weapon_box = {   # 54×74 mm: 2× Ø20-lins+kamera fram; P4 (15mm-standoff) bakom VÄNSTER; centrum-kort-hål
    "D2": (-12, 23, 0), "D3": (12, 23, 180),
    # 8 Carclo-ben (H12-H19): D2 H12-H15, D3 H16-H19 — 9.0×15.60 rektangel/lins, Ø2.1
    "H12": (-16.5, 30.8, 0), "H13": (-7.5, 30.8, 0), "H14": (-16.5, 15.2, 0), "H15": (-7.5, 15.2, 0),
    "H16": (7.5, 30.8, 0), "H17": (16.5, 30.8, 0), "H18": (7.5, 15.2, 0), "H19": (16.5, 15.2, 0),
    # konstantströms-sänka i centrum-fria zonen (kort LED_CATH→Q2 + gate-loop)
    "Q2": (8.5, 9, 90), "R2": (-2, 5, 0),                # DPAK pass-FET (höger) + 0R2 sense (källa→GND)
    "U2": (-9, 11, 0), "C7": (-9, 7.5, 0), "C6": (-9, 4.5, 0),  # op-amp + komp + avkoppl (vänsterkolumn)
    "R3": (-5, 11, 0), "R4": (-1, 11, 0), "R5": (3, 11, 0),  # delare 15k/1k + gate-R (toppraden)
    "C2": (18, 18, 0),                                   # bulk 100µF nära LED-anod/VBAT (topp-höger)
    # inmatningsskydd på HÖGERkanten (frigör vänsterkanten för P4 + J1)
    "F1": (24, 9, 90), "Q1": (24, 3, 0), "D1": (24, -3, 90), "R1": (24, -9, 90), "C1": (24, -15, 0),
    # batteri-in (JST-XH) längs NEDERKANTEN. OBS: flip_j1_back speglar kroppen topp-botten,
    # så för att kabelöppningen ska peka NEDÅT (mot nederkanten) EFTER flippen placeras den
    # rot180 (öppning uppåt FÖRE flip → nedåt EFTER). y=-25.3 ger ~2 mm marginal till kanten.
    # (trigger m.fl. fire-control-I/O ligger på separat kort mot P4 edge A — ej här.)
    "J2": (8, -25.3, 180),
    # J1 = 1x14 P4-kantkontakt på VÄNSTERKANTEN (P4 vänd så signalkanten edge B ligger ytterst).
    # P4-pin (make_p4_board-index) m @ optikkort-y = -31 + (m-1)*2.54. Edge B (ESP→USB):
    #   VSYS=P4-pin19 (y=+14.71) ... GPIO32=P4-pin6 (y=-18.31). Origo=J1-pin1 (VSYS), går nedåt.
    "J1": (-25.28, 5.14, 0),   # FLYTTAD -9.57mm i Y: J1 möter P4 edge B när standoff-hålen linjeras
    # kamerafäste H8-H11 (B0332 28×28 om lins (0,-6)); B4B-ZR-kontakt riktad +x (höger)
    "H8": (-14, 8, 0), "H9": (14, 8, 0), "H10": (-14, -20, 0), "H11": (14, -20, 0),
    # IMU + avkoppling vänster-centrum (under P4, NÄRA J1) → korta SPI-escapes till J1
    "U1": (-19, -3, 0), "C3": (-22, -7, 90), "C4": (-19, -8, 0), "C5": (-15, -1, 90),  # IMU tätt intill J1; C3 upp till matn.-sidan → fri nCS-escape ned-vänster
    # kort-monteringshål: alla x>-5.5 (ej under P4) — H1 topp-höger, H2 botten-höger,
    # H3 höger-kant (mellan kraftremsan och H2), H4 centrum-topp (mellan linserna)
    "H1": (24, 34, 0), "H2": (24, -34, 0), "H3": (24, -22, 0),
    "H4": (0, 28, 0),
    # 4 P4-standoff: synkade mot P4:ans hål, sammanfaller i stacken. RÖRS EJ (korrekta).
    "H5": (-25.15, -33.48, 0), "H6": (-6.85, -33.48, 0),
    "H7": (-6.85, 20.31, 0), "H20": (-25.15, 20.31, 0),
}

weapon_pos = {
    # topp: emittrar + pulsreservoar + Rset (caps ut i hörnen, fria från H4/H5)
    "D2": (-9, 22, 0),  "D3": (9, 22, 0),          # 940 nm emittrar (skottstråle)
    "C2": (-8, 15, 0), "R2": (0, 15, 90), "C1": (8, 15, 0),    # 100µF MLCC / Rset / 10µF
    # höger: driver längst ut (x≈19, fritt från H5/H7) + IMU i mittkolumnen (x≈10-14)
    "Q1": (19, 9, 0),   "R3": (19, 3, 90),         # N-FET + gate-R (far-right)
    "U1": (14, -3, 0),                             # IMU (mellan H5/H7, fri från lins)
    "C3": (14, -9, 0), "C4": (10, -8, 0), "C5": (10, 1, 0),  # IMU-avkoppling
    # vänster remsa: inmatningsskydd (x≈-18, fritt från H4/H6)
    "F1": (-18, 8, 90), "Q2": (-18, 1, 0), "D1": (-18, -6, 90), "R1": (-18, -12, 90),
    # kamerafäste (M2, 28×28 om lins (0,-4))
    "H4": (-14, 10, 0), "H5": (14, 10, 0), "H6": (-14, -18, 0), "H7": (14, -18, 0),
    # nederkant: kontakter + kort-monteringshål
    "J2": (-15, -27, 90), "J1": (-1, -27, 90), "H3": (18, -27, 0),
    "H1": (-18, 28, 0), "H2": (18, 28, 0),
}

# ---- fire-control-kort (71×21, STACKAS ovanpå P4, samma format) ----
# FC-frame = P4-frame (lång axel = x). J1 = FEMALE socket mot P4 edge A pin6..20 (15-pin)
# @ (x=-18.3..+17.25, y=+8.89) — samma fysiska läge som P4-stiften (rak stack).
# Stående JST (kabel upp) längs undervaktsiden; extra IMU + I²C-pullups i mittbandet;
# 4 monteringshål i linje med P4-standoffsen (-34.10/+20.07, ±9.125, Ø1.7) → genomgående stack.
# OBS: pinrader ±8.89 (DXF-exakt, spann 17.78=7×2.54) — INTE 9.28.
# OBS: koordinater är PRE-MIRROR (receiver_place.py-frame). Verkliga board-koords efter spegling:
#   board_x = 150 + x_pm,  board_y = 120 + y_pm
# Speglingen utförs separat (fc_add_ports_v2.py / fc_mirror.py) efter placering + flip.
firecontrol_pos = {
    "J1": (-18.31, 8.89, 90),                                  # socket mot edge A (pin6..20, 15-pin) — EXAKT på P4 J_A pad1
    "J2": (-25.92, -8.89, 90),                                 # edge-B kraft-tapp (3V3+GND), bortre långsida
    "J3": (-16, -6, 0), "J4": (-9, -6, 0), "J5": (-2, -6, 0), "J6": (5, -6, 0),  # switchar (botten), -1mm v. för J10-luckan
    "J7": (-27, 6, 0), "J8": (27, -6, 0),                      # J7 recoil (övre vänster), J8 NFC (höger om H4)
    "J9": (26.5, 7, 0),                                        # OLED I²C JST-PH 4-pin [GND/3V3/SCL/SDA] — nedre h. hörnet
    "J10": (12.2, -6, 0),                                      # lägesväljare JST-PH 3-pin [MODE_A/MODE_B/GND] — luckan J6→H4
    "U1": (8, 0.5, 0), "U2": (21, 0.5, 0),                     # 2× extra IMU (I²C 0x69/0x68)
    "C3": (4, 3.5, 0), "C4": (12, 3.5, 0),                     # U1-avkoppling
    "C5": (17, 3.5, 0), "C6": (25, 3.5, 0),                    # U2-avkoppling
    "R1": (-1, 4, 0), "R2": (-5, 4, 0),                        # I²C-pullups (SDA/SCL)
    "R3": (8, 3.5, 0), "R4": (21, 3.5, 0),                     # MODE_A/MODE_B pull-ups 4k7 (cap-radens luckor C3-C4 / C5-C6)
    "C1": (-9, 3.5, 0), "C2": (-13, 3.5, 0),                   # 3V3-rail/NFC-avkoppling
    "H1": (-34.10, 9.125, 0), "H2": (-34.10, -9.125, 0),
    "H3": (20.07, 9.125, 0), "H4": (20.07, -9.125, 0),
}

# ---- väst-moderkort v2 (100×60, väst-nod) — 10 zon-kontakter + ESP32-C6-devkit + 2×TPIC + buck ----
vest_mb_pos = {}
# 10 zon-kontakter = S6B JST-PH SIDE-ENTRY. Övre rad: öppning UPP (kabel ut toppkant); nedre: öppning NED.
# rot180→öppning=90 (upp), pad-rad längs -x → origo = mitt+(5,0). rot0→öppning=270 (ned), origo = mitt-(5,0).
for i, xc in enumerate([-36, -18, 0, 18, 36]):
    vest_mb_pos[f"J{i+1}"] = (xc + 5.0, 21.0, 180)   # övre zon-rad J1-J5 (öppning upp, kabel ut toppkant)
    vest_mb_pos[f"J{i+6}"] = (xc - 5.0, -21.0, 0)    # nedre zon-rad J6-J10 (öppning ned, kabel ut nederkant)
vest_mb_pos.update({
    "J11": (-25.4, 8.89, 90), "J12": (-25.4, -8.89, 90),  # ESP32-P4-WIFI6 (2× 1x20 kant-sockel; rader 17.78mm=7×2.54 DXF-exakt, origin -25.4 centrerar)
    "U2": (-41, 11, 0), "C5": (-33, 11, 0),      # TPIC6B595 #1 (VIB-driver) + avkoppl (vänster)
    "U3": (41, 11, 0), "C6": (33, 11, 0),        # TPIC6B595 #2 + avkoppl (höger)
    # buck-kluster i fria bandet y[-13..-21] (under P4 edge-A-raden @y-8.89, ovan nedre zon-rad @y-24)
    "U1": (-10, -16, 0), "L1": (-3, -16, 0),     # buck + induktor (nedre-centrum)
    "C1": (-17, -16, 0), "C2": (-17, -13, 0), "C3": (4, -16, 0), "C4": (11, -16, 0),  # Cin/.. + Cbulk
    "R1": (-7, -13, 90), "R2": (1, -13, 90),     # FB-delare
    "J13": (42, -5, 90),                         # 2S-batteri XT30PW (höger kant, mellan TPIC o nedre zon-rad; ≥15A)
    "H1": (-48, 28, 0), "H2": (48, 28, 0), "H3": (-48, -28, 0), "H4": (48, -28, 0),
})

# ---- hjälm-MODERKORT v4 (RUND Ø~104, "holo") — ESP32-P4-WIFI6 + buck + F9P + IMU + 4 TSOP + 2 LED + ljud + 4 patch ----
# RUND skiva (F9P-puck monteras ovanpå centrum). P4 central horisontell; 4 TSOP radiellt utåt på ringen
# (NÖ/NV/SV/SÖ, dom ut för 360° huvudtäckning); 2 konstellations-LED N/S; kringdelar i krans/crescents.
# Genererad av cirkulär bbox-center-layout (se commit-historik). Domer riktas radiellt ut.
helmet_mb_pos = {
    "J8": (-25.4, 8.89, 90),
    "J9": (-25.4, -8.89, 90),
    "U4": (29.86, 26.27, 135),
    "D2": (24.51, 20.57, 45),
    "C7": (19.51, 24.09, 45),
    "U3": (-26.27, 29.86, 225),
    "D1": (-20.57, 24.51, 135),
    "C6": (-24.09, 19.51, 135),
    "U5": (-29.86, -26.27, 315),
    "D3": (-24.51, -20.57, 45),
    "C8": (-19.51, -24.09, 45),
    "U6": (26.27, -29.86, 45),
    "D4": (20.57, -24.51, 135),
    "C9": (24.09, -19.51, 135),
    "D5": (13.17, 39.9, 70),
    "D6": (-1.28, 42.0, 90),
    "D7": (-15.56, 39.03, 110),
    "D8": (-37.68, 18.59, 152),
    "D9": (-37.53, -18.91, 205),
    "D10": (15.56, -39.03, 290),
    "R5": (11.29, 31.01, 70),
    "R6": (-11.29, 31.01, 20),
    "R7": (10.0, -2.0, 0),
    # RTK-puck-kontakter (GH, horisontella SMD): J1=8-pol ZED-F9P, J12=6-pol alt-puck — botten, kabel mot puck (centrum)
    "J1": (-0.0, -39.0, 0),
    "J10": (-22.0, -34.0, 0),                        # 2S-batteri (XH), nedre vänster
    # 4 patch-portar = S5B side-entry på BAKSIDAN (fronten = optik-ring, för trång) — öppning radiellt UT,
    # spridda runt bak-kanten, kabel ut. (Front-kanten reserverad för obligatorisk TSOP/LED-optik.)
    "J2": _se(0, 41, 5, "out", flip=True), "J3": _se(52, 41, 5, "out", flip=True),
    "J4": _se(108, 41, 5, "out", flip=True), "J5": _se(150, 41, 5, "out", flip=True),
    # --- ES8388 headset-kluster: codec (U7) VÄNSTER om P4 (korta I²S/I²C/mik-nät) m. fanout-halo;
    #     PAM8302A-amp (U8) i HÖGER korridor (mellan patch-J2/J3). ---
    "U7": (-31.0, 0.0, 0),                          # ES8388 codec (QFN-28 0,5mm) — fri halo runt
    "C10": (-35.0, 5.5, 0), "C11": (-31.0, 6.0, 0), "C12": (-27.0, 5.5, 0),   # codec-avkoppl (N)
    "C13": (-35.0, -5.5, 0), "C14": (-31.0, -6.0, 0), "C15": (-27.0, -5.5, 0),# codec-ref/avkoppl (S)
    "C16": (-38.0, 2.5, 0), "C17": (-38.0, -2.5, 0),                          # VREF/VMID-filter (W)
    "C18": (-41.5, 4.0, 90), "C19": (-41.5, 0.0, 90),                          # mik AC-koppl (Cmic/Crin)
    "R8": (-41.5, -4.0, 90),                        # mik-bias 2k2
    "J6": _se(205, 42, 2, "out", flip=True),        # MIC_BOOM (S2B side-entry, BAKSIDAN)
    "U8": (40.0, 0.0, 0),                           # PAM8302A amp (SOIC-8) — höger korridor
    "C20": (33.0, 3.0, 0), "C21": (33.0, -3.0, 0),                            # amp ingång/VDD (klar U8-courtyard 7,4 mm)
    # I²C-pullups 4k7 — DIREKT över P4:s I²C-pinnar (U2.13 SCL / U2.14 SDA @ y≈14.9). Bussen
    # spände annars hela kortet (codec x=-31 ↔ pull-ups x=+45) → freerouting strandade pull-up-
    # paddarna i höger-korridoren (amp U8); nära mastern blir anslutningen en ~2 mm-stubbe.
    # Orientering: I²C-padden mot bussen (rot vald) → spåret korsar ej egna +3V3-padden.
    # (Slutförs deterministiskt av finish_helmet_pullups.py — INTE freerouting-roulette.)
    "R10": (2.2, 16.7, 180), "R9": (-2.2, 16.7, 0),                          # R10=SCL-pull, R9=SDA-pull
    "J7": _se(240, 42, 2, "out", flip=True),        # SPEAKER (S2B side-entry, BAKSIDAN)
    "J11": _se(295, 42, 2, "out", flip=True),       # PTT-knapp (S2B side-entry, BAKSIDAN)
    "U2": (0.16, 13.5, 0),
    "C4": (-3.7, 13.5, 90),
    "C5": (3.7, 13.5, 90),
    "Q1": (0.0, 19.91, 0),
    "R4": (5.0, 20.0, 90),
    "L1": (-3.5, -15.0, 0),
    "U1": (3.0, -15.09, 0),
    "C2": (0.0, -19.5, 0),
    "C1": (-15.0, -14.5, 0),
    "C3": (-16.5, -19.5, 0),
    "R1": (14.5, -14.0, 90),
    "R2": (14.5, -17.5, 90),
    "R3": (14.5, -21.0, 90),
    # puck-fästhål: MEDELMÖNSTER (±10.2 × ±17.0) → passar BÅDE ZED-F9P (20.80×33.90) och
    # alt-puck (~20.0×34.1). Skillnad ~0,2 mm/håll absorberas av M2.5-hål (verifiera mot fysisk puck).
    "H5": (10.2, 17.0, 0),
    "H6": (-10.2, 17.0, 0),
    "H7": (-10.2, -17.0, 0),
    "H8": (10.2, -17.0, 0),
    "J12": (13.0, -34.0, 0),                         # alt-puck 6-pol GH (nära 8-pol J1 + puck, samma nät)
    "H1": (39.73, 21.13, 0),
    "H2": (6.26, 44.56, 0),
    "H3": (-10.89, -43.66, 0),
    "H4": (39.73, -21.13, 0),
}

# ===== Ø108-OMLÄGGNING (max Ø108) — RTK-puck Ø86 monteras på BAKSIDAN (sky-side); P4/optik på FRONTEN
#   (mot hjälmen). Front-optiken (TSOP/OR-diod/LED/avkoppl) skalas UT till kanten (+7 mm radie; rotation =
#   aim radiellt ut, behålls). ALLA kabel-kontakter → BAKSIDANS yttre ring (utanför Ø86-puck r43, innanför
#   kort-r54), öppning radiellt UT. Centrum-el (P4/codec U7/amp U8/buck/IMU/const-R) stannar på fronten. =====
for _ref in ("U3", "U4", "U5", "U6", "D1", "D2", "D3", "D4", "C6", "C7", "C8", "C9"):
    _x, _y, _rt = helmet_mb_pos[_ref][:3]; _r = _math.hypot(_x, _y)
    _sc = (_r + 10.0) / _r
    helmet_mb_pos[_ref] = (round(_x * _sc, 2), round(_y * _sc, 2), _rt)
# 6 LED-tabbar (D5-D10) JÄMNT runt om (60° isär, mirror-symmetriskt: 30/90/.../330) på r=49, pad-rad
# TANGENTIELL (viks radiellt ut) + pad-mittpunkt/3D-modell CENTRERAD på ringpunkten (som patchen).
for _i, _a in enumerate((30, 90, 150, 210, 270, 330)):
    _rot = (_a + 180) % 360
    _cx, _cy = _ring2(51.0, _a)
    helmet_mb_pos[f"D{_i+5}"] = (*_comp(_cx, _cy, _rot, (0.0, 1.27)), _rot)
def _ghr(theta, r):                                  # GH-kontakt (SM0xB-GHS) på baksidan: öppning radiellt UT
    th = _math.radians(theta)                        # (GH-footprint-ram ≈ +90° vs PH → rot=(180-theta))
    return (round(r * _math.cos(th), 2), round(r * _math.sin(th), 2), (180 - theta) % 360, "B")
helmet_mb_pos.update({
    # Bak-ring (r46-47): HEADSET (mik J6/högt J7/PTT J11) GRUPPERADE i toppen (samma headset → en
    # kabelknippa, sitter ihop). 4 patch-portar (S5B) spridda runt om. Allt side-entry, öppning radiellt ut.
    "J6": _se(75, 46, 2, "out", flip=True), "J7": _se(90, 46, 2, "out", flip=True),     # headset mik + högtalare
    "J11": _se(105, 46, 2, "out", flip=True),                                           #   + PTT (grupperade, topp)
    "J2": _se(0, 46, 5, "out", flip=True), "J3": _se(180, 46, 5, "out", flip=True),     # 4 patch-portar (S5B)
    "J4": _se(230, 46, 5, "out", flip=True), "J5": _se(310, 46, 5, "out", flip=True),
    "J1": (-9.0, -30.0, 0, "B"), "J12": (9.0, -30.0, 0, "B"),                            # RTK-puck-GH 8+6-pol → BAK INRE (under Ø86-pucken)
    "J10": (0.0, -31.0, 0),                                                             # 2S-batteri XH → FRONT (innanför tab-ringen; öppning ut nedkant)
    "H1": (*_ring2(51, 58), 0), "H2": (*_ring2(51, 165), 0),                             # kort-fästhål i fria vinklar (mellan tab/TSOP/kontakt)
    "H3": (*_ring2(51, 250), 0), "H4": (*_ring2(51, 345), 0),
})

# ===== KRYMPNING till vald diameter (HELMET_R = kort-radie; default 50 = Ø100, kompromiss med
#   luft för symmetriska patch-kontakter + puck/batteri-clearance; 48 = Ø96 (maxpackat), 54 = Ø108).
#   Ø108-blocket ovan bygger nominal-layouten; här dras den ihop: rigida kluster (4 optik-block,
#   codec, amp) translateras radiellt inåt (intern geometri bevaras), kant-ringen (tabbar/kontakter/
#   hål) räknas OM via samma hjälpare på skalade radier. Kant-kontakterna sitter i tab-LUCKORNA
#   (LED-tabbar fixa var 60° @28/88/148/208/268/328°), patchar symmetriskt. =====
_HR = float(os.environ.get("HELMET_R", "50.0"))
if abs(_HR - 54.0) > 0.05:
    _R0, _RC = 54.0, 30.0
    _kk = (_HR - _RC) / (_R0 - _RC)
    def _shrink_r(r): return _RC + (r - _RC) * _kk if r > _RC else r
    for _blk in (("U3", "D1", "C6"), ("U4", "D2", "C7"), ("U5", "D3", "C8"), ("U6", "D4", "C9")):
        _om = max(_math.hypot(*helmet_mb_pos[r][:2]) for r in _blk) + 3.6   # optik-block ytterkant
        _cx = sum(helmet_mb_pos[r][0] for r in _blk) / 3.0; _cy = sum(helmet_mb_pos[r][1] for r in _blk) / 3.0
        _cr = _math.hypot(_cx, _cy); _s = (_cr - (_om - (_HR - 0.6))) / _cr
        _dx, _dy = _cx * _s - _cx, _cy * _s - _cy                          # RIGID translation (ej skalning)
        for r in _blk:
            _p = helmet_mb_pos[r]; helmet_mb_pos[r] = (round(_p[0] + _dx, 2), round(_p[1] + _dy, 2), _p[2])
    for _blk in (("U7", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "R8"),
                 ("U8", "C20", "C21")):
        _cx = sum(helmet_mb_pos[r][0] for r in _blk) / len(_blk); _cy = sum(helmet_mb_pos[r][1] for r in _blk) / len(_blk)
        _cr = _math.hypot(_cx, _cy); _s = _shrink_r(_cr) / _cr
        _dx, _dy = _cx * _s - _cx, _cy * _s - _cy                          # RIGID translation
        for r in _blk:
            _p = helmet_mb_pos[r]; helmet_mb_pos[r] = (round(_p[0] + _dx, 2), round(_p[1] + _dy, 2), _p[2])
    for _i, _a in enumerate((30, 90, 150, 210, 270, 330)):       # 6 LED-tabbar (pad-mitt centrerad)
        _rot = (_a + 180) % 360; _cx, _cy = _ring2(_HR - 1.8, _a)
        helmet_mb_pos[f"D{_i+5}"] = (*_comp(_cx, _cy, _rot, (0.0, 1.27)), _rot)
    _rc = _HR - 5.8                                              # kontakt-pad-radie (kropp/öppning når kanten)
    # ALLA kant-kontakter i tab-LUCKORNA (mellan LED-tabbarna @28/88/148/208/268/328°), fria från
    # optik (41/131/221/311°). 4 patchar SYMMETRISKT: två motstående par (118↔298, 178↔358).
    helmet_mb_pos["J2"] = _se(115, _rc, 5, "out", flip=True); helmet_mb_pos["J3"] = _se(178, _rc, 5, "out", flip=True)
    helmet_mb_pos["J4"] = _se(295, _rc, 5, "out", flip=True); helmet_mb_pos["J5"] = _se(358, _rc, 5, "out", flip=True)
    # headset (mik/högt/PTT) GRUPPERAT i luckan 49-85° (bort från tab D6@88° + optik U4@41°; 11°-pitch)
    helmet_mb_pos["J6"] = _se(55, _rc, 2, "out", flip=True); helmet_mb_pos["J7"] = _se(66, _rc, 2, "out", flip=True)
    helmet_mb_pos["J11"] = _se(77, _rc, 2, "out", flip=True)
    for _h, _a in zip(("H1", "H2", "H3", "H4"), (100, 195, 255, 342)):  # kort-fästhål i fria vinkel-luckor
        helmet_mb_pos[_h] = (*_ring2(_HR - 2.6, _a), 0)
    for _r in ("J1", "J12"):                                     # inre bak puck-GH (ZED-F9P 8-pol / alt 6-pol)
        _p = helmet_mb_pos[_r]; _rr = _math.hypot(_p[0], _p[1]); _s = _shrink_r(_rr) / _rr if _rr else 1
        _side = (_p[3],) if len(_p) > 3 else ()
        helmet_mb_pos[_r] = (round(_p[0] * _s, 2), round(_p[1] * _s, 2), _p[2]) + _side
    helmet_mb_pos["J10"] = (*_ring2(_HR - 4.0, 238), 0)          # batteri ut i kant-luckan 238° (FRI från puck-GH inne)
    # AMP intill HÖGTALAR-kontakten: PAM8302A (U8) matar J7 (högtalare, topp). På Ø108 fick SPK_P/N
    # plats trots amp@höger, men på det täta Ø96 spänner de halva kortet → orienterbart. Flytta amp +
    # in/avkoppl-C till den fria top-center-luckan (mellan R5@x≥8 och R6@x≤-7), direkt under J7 →
    # SPK blir korta genomborrade stubbar (high-current/EMI-kritiska nätet kort; codec-line-in får vara längre).
    helmet_mb_pos["U8"] = (0.0, 33.0, 0)
    helmet_mb_pos["C20"] = (-2.5, 28.5, 0); helmet_mb_pos["C21"] = (2.5, 28.5, 0)  # under U8 (7,4 mm-courtyard ryms ej flankerat)

BOARDS = {
    "helmet_mb": lambda: place("hardware/helmet-mb.net", "hardware/helmet-mb.kicad_pcb",
                               helmet_mb_pos, ("circle", _HR), layers=4, free=(-3, 3, -3, 3)),
    "vest": lambda: place("hardware/vest-patch.net", "hardware/vest-patch.kicad_pcb",
                          vest_pos, ("circle", _VEST_R), layers=2, free=(-2, 2, -2, 2), labels=vest_labels),
    "vest_mb": lambda: place("hardware/vest-mb.net", "hardware/vest-mb.kicad_pcb",
                             vest_mb_pos, ("rect", 50, 30), layers=4, free=(-3, 3, -3, 3)),
    # vapnet: alla delar placeras explicit -> tom fri-zon (säker, ingen krock med lins)
    "weapon": lambda: place("hardware/weapon-module.net", "hardware/weapon-module.kicad_pcb",
                            weapon_box, ("rect", 27, 37), layers=4, free=(26, 27, 36, 37), cutout=(0, -6, 8)),
    # fire-control breakout: matar P4 edge A stelt (1x12), fan-out till greppets I/O
    "firecontrol": lambda: place("hardware/firecontrol.net", "hardware/firecontrol.kicad_pcb",
                                 firecontrol_pos, ("rect", 35.5, 10.5), layers=2, free=(33, 35, 9, 10)),
}

if __name__ == "__main__":
    sel = sys.argv[1:] or list(BOARDS)   # ange t.ex. 'weapon' för att bara bygga om vapnet
    for name in sel:
        BOARDS[name]()
