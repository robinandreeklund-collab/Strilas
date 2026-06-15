#!/usr/bin/env python3
"""Applicera en Freerouting-SES på valfri KiCad-board (generell). Användning:
    python ses_apply.py <board.kicad_pcb> <board.ses>
SES-enhet 0.1um=100nm, Y negeras, ingen offset (matchar ExportSpecctraDSN)."""
import re, sys, pcbnew
LAYER = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}


def toks(s): return re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s)


def parse(tk):
    out = []
    while tk:
        t = tk.pop(0)
        if t == "(": out.append(parse(tk))
        elif t == ")": return out
        else: out.append(t.strip('"'))
    return out


def walk(n, tag):
    if isinstance(n, list):
        if n and n[0] == tag: yield n
        for c in n: yield from walk(c, tag)


def main(pcb, ses):
    b = pcbnew.LoadBoard(pcb)
    tree = parse(toks(open(ses).read()))[0]
    xn = lambda v: round(float(v)*100); yn = lambda v: round(-float(v)*100)
    nt = nv = 0
    for net in walk(tree, "net"):
        ni = b.FindNet(net[1]); nc = ni.GetNetCode() if ni else 0
        for path in walk(net, "path"):
            ly = LAYER.get(path[1])
            if ly is None: continue
            w = round(float(path[2])*100)
            nums = [p for p in path[3:] if re.match(r'^-?\d', str(p))]
            pts = [(xn(nums[i]), yn(nums[i+1])) for i in range(0, len(nums)-1, 2)]
            for i in range(len(pts)-1):
                t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(*pts[i])); t.SetEnd(pcbnew.VECTOR2I(*pts[i+1]))
                t.SetWidth(w); t.SetLayer(ly); t.SetNetCode(nc); b.Add(t); nt += 1
        for via in walk(net, "via"):
            nums = [p for p in via[2:] if re.match(r'^-?\d', str(p))]
            if len(nums) < 2: continue
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(xn(nums[0]), yn(nums[1])))
            v.SetWidth(pcbnew.FromMM(0.6)); v.SetDrill(pcbnew.FromMM(0.3))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(nc); b.Add(v); nv += 1
    pcbnew.SaveBoard(pcb, b)
    b.BuildConnectivity()
    try: un = b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError: un = b.GetConnectivity().GetUnconnectedCount()
    print(f"  {pcb}: {nt} spår + {nv} vior, oroutade={un}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
