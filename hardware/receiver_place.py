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
vest_pos = {
    "U1": (-17, 4, 0), "U2": (0, 4, 0), "U3": (17, 4, 0),         # TSOP
    "D1": (-22, 15, 0), "D2": (22, -13, 0),                       # LED (konstellation) – obs: refs from netlist order
    "J1": (14, -17, 0),
}
# ---- hjälm-halo (Ø100) ----
helmet_pos = {f"U{i+1}": (38*math.cos(math.radians(i*45)), 38*math.sin(math.radians(i*45)), i*45-90) for i in range(8)}
helmet_pos.update({"J2": (0, 0, 0), "J1": (0, -44, 0)})

# ---- vapen-optikmodul (42×62, P4-carrier) ----
# Lins-hål Ø16 i mitten (kamera bakom kortet): keepout x[-8,8] y[-12,4].
# Pulsloop hålls kort: C2(reservoar)→R2(Rset)→D2→D3→Q1→GND uppe.
# IMU + avkoppling i höger remsa; inmatningsskydd nere till vänster; headers nederst.
# Kamerafäste (B0332 38×38): 4× M2-hål i 28×28-mönster runt linsaxeln (0,-4).
#   H4(-14,10) H5(14,10) H6(-14,-18) H7(14,-18). Komponenter flyttade ut till kanterna
#   så dessa hål + standoffs är fria. Kameran skruvas fast bakom kortet, lins genom Ø16.
weapon_box = {   # 54×68 mm: 2× Ø20-lins+kamera fram; INGET under linserna; P4 längs höger 68 mm-kant
    "D2": (-12, 23, 0), "D3": (12, 23, 180),
    # Carclo 10734 4-bens-hållare (ritn. 60575): 4 hål/lins Ø2.1 i 9.0×15.60 rektangel, LED centralt
    "H8": (-16.5, 30.8, 0), "H9": (-7.5, 30.8, 0), "H10": (-16.5, 15.2, 0), "H11": (-7.5, 15.2, 0),   # D2
    "H12": (7.5, 30.8, 0), "H13": (16.5, 30.8, 0), "H14": (7.5, 15.2, 0), "H15": (16.5, 15.2, 0),     # D3
    # driver i CENTRUM-gapet mellan linserna (fritt från Ø20): N-FET + gate-R
    "Q2": (0, 19, 90), "R3": (0, 14, 90),
    # vänster kant (fritt från linsernas x=-22): Rset + inmatningsskydd
    "R2": (-24, 18, 90), "F1": (-24, 10, 90), "Q1": (-24, 3, 0), "D1": (-24, -4, 90),
    "R1": (-24, -11, 90), "C2": (-24, -18, 0),
    # höger kant: RIGID P4-kantkontakt (1×13, längs 68 mm)
    "J1": (24, 15, 0),   # placeras fram för routning, flippas till baksidan efteråt
    # kamerafäste (B0332 28×28 om lins (0,-6))
    "H4": (-14, 8, 0), "H5": (14, 8, 0), "H6": (-14, -20, 0), "H7": (14, -20, 0),
    # nederkant: ingångskond + IMU-kluster + batteri/trigger
    "C1": (-17, -30, 0), "U1": (-8, -30, 0), "C3": (-2, -31, 90), "C4": (3, -31, 90), "C5": (9, -30, 0),
    "J2": (-24, -25, 90), "J3": (16, -30, 90),
    "H1": (-24, 31, 0), "H2": (24, 31, 0), "H3": (24, -22, 0),
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

BOARDS = {
    "vest": lambda: place("hardware/vest-patch.net", "hardware/vest-patch.kicad_pcb",
                          vest_pos, ("rect", 29, 21), layers=2, free=(-24, 24, -18, 0)),
    "helmet": lambda: place("hardware/helmet-halo.net", "hardware/helmet-halo.kicad_pcb",
                            helmet_pos, ("circle", 50), layers=4, center_hole=10, free=(-30, 30, 28, 12)),
    # vapnet: alla delar placeras explicit -> tom fri-zon (säker, ingen krock med lins)
    "weapon": lambda: place("hardware/weapon-module.net", "hardware/weapon-module.kicad_pcb",
                            weapon_box, ("rect", 27, 35), layers=4, free=(26, 27, 34, 35), cutout=(0, -6, 8)),
}

if __name__ == "__main__":
    sel = sys.argv[1:] or list(BOARDS)   # ange t.ex. 'weapon' för att bara bygga om vapnet
    for name in sel:
        BOARDS[name]()
