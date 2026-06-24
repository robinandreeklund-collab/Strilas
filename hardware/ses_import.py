#!/usr/bin/env python3
"""STRILAS — applicera Freerouting-SES (rutter) på KiCad-boarden via pcbnew-API.
(KiCad 7 standalone saknar board-medveten ImportSpecctraSES → vi parsar SES själva.)
SES-enhet = 0.1 um = 100 nm; Y negeras; ingen offset (matchar ExportSpecctraDSN-transformen).
"""
import re
import pcbnew

PCB = "hardware/weapon-module.kicad_pcb"
SES = "hardware/weapon-module.ses"
LAYER = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu,
         "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}


def toks(s):
    return re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s)


def parse(tokens):
    """S-expr → nästlade listor."""
    out = []
    while tokens:
        t = tokens.pop(0)
        if t == "(":
            out.append(parse(tokens))
        elif t == ")":
            return out
        else:
            out.append(t.strip('"'))
    return out


def walk(node, tag):
    """Yield alla subnoder vars första element == tag."""
    if isinstance(node, list):
        if node and node[0] == tag:
            yield node
        for c in node:
            yield from walk(c, tag)


def x_nm(v): return round(float(v) * 100)
def y_nm(v): return round(-float(v) * 100)


def main():
    board = pcbnew.LoadBoard(PCB)
    tree = parse(toks(open(SES).read()))[0]

    ntrack = nvia = 0
    for net in walk(tree, "net"):
        name = net[1]
        ni = board.FindNet(name)
        nc = ni.GetNetCode() if ni else 0
        for wire in walk(net, "wire"):
            for path in walk(wire, "path"):
                layer = LAYER.get(path[1])
                if layer is None:
                    continue
                w = round(float(path[2]) * 100)
                nums = [p for p in path[3:] if re.match(r'^-?\d', str(p))]
                pts = [(x_nm(nums[i]), y_nm(nums[i+1])) for i in range(0, len(nums)-1, 2)]
                for i in range(len(pts)-1):
                    tr = pcbnew.PCB_TRACK(board)
                    tr.SetStart(pcbnew.VECTOR2I(*pts[i]))
                    tr.SetEnd(pcbnew.VECTOR2I(*pts[i+1]))
                    tr.SetWidth(w); tr.SetLayer(layer); tr.SetNetCode(nc)
                    board.Add(tr); ntrack += 1
        for via in walk(net, "via"):
            nums = [p for p in via[2:] if re.match(r'^-?\d', str(p))]
            if len(nums) < 2:
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(x_nm(nums[0]), y_nm(nums[1])))
            v.SetWidth(pcbnew.FromMM(0.6)); v.SetDrill(pcbnew.FromMM(0.3))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(nc)
            board.Add(v); nvia += 1

    pcbnew.SaveBoard(PCB, board)
    print(f"  applicerade {ntrack} spårsegment + {nvia} vior")


if __name__ == "__main__":
    main()
