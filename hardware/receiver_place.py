#!/usr/bin/env python3
"""STRILAS — placera + nät-tilldela receiver-korten (väst + hjälm) ur netlistan (pcbnew).
Nyckeldelar placeras enligt receiver_boards_layout; smådelar grid-placeras i fri zon.
Ritar outline (+ hjälm-centrumhål). Sparar .kicad_pcb. (Routas sedan av freerouting.)
"""
import re, math, pcbnew

FPDIR = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM


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


def place(netfile, pcbfile, positions, outline, layers=2, center_hole=None, free=(-20, 20, -15, 15)):
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
        f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", fp)
        if f is None:
            print(f"  !! {fpname} ({ref})"); continue
        f.SetReference(ref)
        if ref in positions:
            x, y, rot = positions[ref]
        else:
            x, y = grid[gi % len(grid)]; rot = 0; gi += 1
        f.SetPosition(V(x, y))
        if rot: f.SetOrientationDegrees(rot)
        board.Add(f); fps[ref] = f
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

if __name__ == "__main__":
    place("hardware/vest-patch.net", "hardware/vest-patch.kicad_pcb",
          vest_pos, ("rect", 29, 21), layers=2, free=(-24, 24, -18, 0))
    place("hardware/helmet-halo.net", "hardware/helmet-halo.kicad_pcb",
          helmet_pos, ("circle", 50), layers=4, center_hole=10, free=(-30, 30, 28, 12))
