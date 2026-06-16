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


def place(netfile, pcbfile, positions, outline, layers=2, center_hole=None, free=(-20, 20, -15, 15), cutout=None):
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
    pcbnew.SaveBoard(pcbfile, board)
    print(f"  {pcbfile}: {len(fps)} komponenter, {len(nets)} nät")


# ---- väst-patch (58×42) ----
vest_pos = {   # 58×42 (±29,±21). FULL explicit placering (inga grid-delar) — OSLON-LED + 2512 R är stora.
    # refs (netlist-ordning): U1-3=TSOP · D1-3=OR-dioder · D4,D5=OSLON-konstellation 860nm
    # R1=DATA-pullup · R2=gate · R3,R4=LED-serieR(2512 10R) · C1=bulk · C2-4=TSOP-avkoppl · Q1=driver
    "U1": (-17, 16, 0), "U2": (0, 16, 0), "U3": (17, 16, 0),       # TSOP4856 (top, mot skytt)
    "D1": (-17, 9.5, 0), "D2": (0, 9.5, 0), "D3": (17, 9.5, 0),    # OR-dioder (under varje TSOP)
    "C2": (-17, 4.5, 0), "C3": (0, 4.5, 0), "C4": (17, 4.5, 0),    # TSOP-avkoppling
    "D4": (-21, -2, 0), "D5": (21, -2, 0),                          # OSLON 860nm konstellation (spridda)
    "R3": (-12, -2, 90),"R4": (12, -2, 90),                         # LED-serieR 10R 2512 (inboard)
    "Q1": (0, -8, 0),   "R2": (7, -8, 90),                          # N-FET-driver + gate-R
    "C1": (-20, -10, 0),"R1": (-12, -10, 0),                        # bulk 10µF (VBAT) / DATA-pullup (3V3)
    "U4": (-4, -14, 0), "C5": (-11, -14, 90), "C6": (4, -14, 0),    # 3V3-LDO (HT7333-A SOT-89) + Cin/Cout
    "J1": (14, -9, 0),                                              # 1x4 — pin1 origo; pin4 @ rel -16,6 (innanför -21)
    "H1": (-26, 18, 0), "H2": (26, 18, 0), "H3": (-26, -18, 0), "H4": (26, -18, 0),
}
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
    "J3": (-7, -19, 0),                              # GNSS-modul 1x5 (vänster-botten, klar av 270°-eker)
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
# FC-frame = P4-frame (lång axel = x). J1 = FEMALE socket mot P4 edge A pin6..17
# @ (x=-18.3..+9.64, y=+9.28) — samma fysiska läge som P4-stiften (rak stack).
# Stående JST (kabel upp) längs nederhalvan; extra IMU + I²C-pullups i mittbandet;
# 4 monteringshål i linje med P4-standoffsen (-34.06/+19.73, ±9.15) → genomgående stack.
firecontrol_pos = {
    "J1": (-18.3, 9.28, 90),                                   # socket mot edge A (pin6..17)
    "J2": (-25.92, -9.28, 90),                                 # edge-B kraft-tapp (3V3+GND), bortre långsida
    "J3": (-15, -6, 0), "J4": (-8, -6, 0), "J5": (-1, -6, 0), "J6": (6, -6, 0),  # switchar (botten)
    "J7": (-27, 6, 0), "J8": (27, -6, 0),                      # J7 recoil (övre vänster), J8 NFC (höger om H4)
    "U1": (8, 0.5, 0), "U2": (21, 0.5, 0),                     # 2× extra IMU (I²C 0x69/0x68)
    "C3": (4, 3.5, 0), "C4": (12, 3.5, 0),                     # U1-avkoppling
    "C5": (17, 3.5, 0), "C6": (25, 3.5, 0),                    # U2-avkoppling
    "R1": (-1, 4, 0), "R2": (-5, 4, 0),                        # I²C-pullups
    "C1": (-9, 3.5, 0), "C2": (-13, 3.5, 0),                   # 3V3-rail/NFC-avkoppling
    "H1": (-34.06, 9.15, 0), "H2": (-34.06, -9.15, 0),
    "H3": (19.73, 9.15, 0), "H4": (19.73, -9.15, 0),
}

# ---- väst-moderkort (90×60, väst-nod) — 10 zon-kontakter + XIAO-S3 + 165/TPIC + buck ----
vest_mb_pos = {}
for i, xc in enumerate([-38, -19, 0, 19, 38]):  # xc = önskad mitt; origo = xc-6.35 (1x6 sträcker +x vid rot90)
    vest_mb_pos[f"J{i+1}"] = (xc - 6.35, 24, 90)  # övre zon-rad J1-J5 (1x6, rot90, centrerad)
    vest_mb_pos[f"J{i+6}"] = (xc - 6.35, -24, 90)  # nedre zon-rad J6-J10
vest_mb_pos.update({
    "J11": (-7.6, 0, 0), "J12": (7.6, 0, 0),     # XIAO ESP32-S3 (2× 1x7 sockel), centrum
    "U2": (-32, 8, 0), "U3": (-32, -8, 0),       # 2× 74HC165 (DATA-läsning), vänster
    "C5": (-37, 8, 90), "C6": (-37, -8, 90),     # 165-avkoppling
    "U4": (32, 9, 0), "U5": (32, -9, 0),         # 2× TPIC6B595 (VIB-driver), höger
    "C7": (40, 4, 90), "C8": (40, -4, 90),       # TPIC-avkoppling
    "U1": (-22, 12, 0), "L1": (-15, 12, 0),      # buck + induktor (övre-vänster mittband)
    "C1": (-26, 8, 0), "C2": (-28, 15, 0), "C3": (-9, 13, 0), "C4": (-9, 8, 0),  # Cbst/Cin/Cout/Cbulk
    "R1": (-19, 7, 90), "R2": (-15, 7, 90),      # FB-delare
    "J13": (18, -10, 0),                         # 2S-batteri JST (höger mittband)
    "H1": (-46, 27, 0), "H2": (46, 27, 0), "H3": (-46, -27, 0), "H4": (46, -27, 0),
})

BOARDS = {
    "vest": lambda: place("hardware/vest-patch.net", "hardware/vest-patch.kicad_pcb",
                          vest_pos, ("rect", 29, 21), layers=2, free=(-24, 24, -18, 0)),
    "vest_mb": lambda: place("hardware/vest-mb.net", "hardware/vest-mb.kicad_pcb",
                             vest_mb_pos, ("rect", 50, 30), layers=4, free=(-3, 3, -3, 3)),
    "helmet": lambda: place("hardware/helmet-halo.net", "hardware/helmet-halo.kicad_pcb",
                            helmet_pos, ("circle", 50), layers=4, free=(-3, 3, -3, 3)),
    # vapnet: alla delar placeras explicit -> tom fri-zon (säker, ingen krock med lins)
    "weapon": lambda: place("hardware/weapon-module.net", "hardware/weapon-module.kicad_pcb",
                            weapon_box, ("rect", 27, 37), layers=4, free=(26, 27, 36, 37), cutout=(0, -6, 8)),
    # fire-control breakout: matar P4 edge A stelt (1x12), fan-out till greppets I/O
    "firecontrol": lambda: place("hardware/firecontrol.net", "hardware/firecontrol.kicad_pcb",
                                 firecontrol_pos, ("rect", 35.525, 10.5), layers=2, free=(33, 35, 9, 10)),
}

if __name__ == "__main__":
    sel = sys.argv[1:] or list(BOARDS)   # ange t.ex. 'weapon' för att bara bygga om vapnet
    for name in sel:
        BOARDS[name]()
