#!/usr/bin/env python3
"""Lägg P4-monterings-silk på ETT kort (ett kort per process pga pcbnew-SWIG).
Kör: python3 hardware/add_p4_silk.py <weapon-module|helmet-mb|vest-mb>
Placerar etiketter (edge A/B + USB-änd) i VERIFIERAT padd-fria lägen (riktig bbox-koll)."""
import sys, pcbnew
MM = pcbnew.FromMM
OX, OY = 150.0, 120.0


def V(x, y):
    return pcbnew.VECTOR2I(int((OX + x) * 1e6), int((OY - y) * 1e6))


def main(board):
    path = f"hardware/{board}.kicad_pcb"
    b = pcbnew.LoadBoard(path)
    foots = list(b.GetFootprints())     # FÖRSTA board-access (undviker pcbnew-SWIG otypning)
    padboxes = []                       # ur GetPosition+GetSize (ej GetBoundingBox = flakigt i SWIG)
    for f in foots:
        for p in f.Pads():
            c = p.GetPosition(); sz = p.GetSize()
            r = max(sz.x, sz.y) / 2e6   # konservativ kvadrat (täcker roterade paddar)
            cx, cy = c.x / 1e6 - OX, OY - c.y / 1e6
            padboxes.append((cx - r, cy - r, cx + r, cy + r))
    # rensa ev. tidigare P4-monteringssilk (idempotent)
    for d in list(b.GetDrawings()):
        if d.GetClass() == "PCB_TEXT" and any(k in d.GetText() for k in ("EDGE", "USB", "P4-WIFI6", "P4 EDGE", "P4 ")):
            b.Remove(d)

    def mk(layer, x, y, txt, h, mir, ang):
        t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetLayer(layer); t.SetPosition(V(x, y))
        t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); t.SetTextThickness(MM(0.15))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        if mir:
            t.SetMirrored(True)
        if ang:
            t.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
        return t

    def tbox(x, y, txt, h, ang):
        """analytisk text-bbox (KiCad stroke-font ~h bred/tecken) + 0.3 mm marginal."""
        w = len(txt) * h * 0.95 + 0.6; ht = h * 1.1 + 0.6
        if abs(ang) == 90:
            w, ht = ht, w
        return (x - w / 2, y - ht / 2, x + w / 2, y + ht / 2)

    def clear(x, y, txt, h, ang):
        tx0, ty0, tx1, ty1 = tbox(x, y, txt, h, ang)
        for px0, py0, px1, py1 in padboxes:
            if min(tx1, px1) - max(tx0, px0) > 0.05 and min(ty1, py1) - max(ty0, py0) > 0.05:
                return False
        return True

    def place(layer, txt, h, mir, ang, xr, yr):
        """skanna rutnät i [xr]×[yr], placera i första padd-fria läge (närmast region-mitt)."""
        cx = sum(xr) / 2; cy = sum(yr) / 2
        cand = [(x, y) for x in [xr[0] + i * 0.5 for i in range(int((xr[1] - xr[0]) / 0.5) + 1)]
                for y in [yr[0] + i * 0.5 for i in range(int((yr[1] - yr[0]) / 0.5) + 1)]]
        cand.sort(key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
        for x, y in cand:
            if clear(x, y, txt, h, ang):
                b.Add(mk(layer, x, y, txt, h, mir, ang)); return (round(x, 1), round(y, 1))
        return None

    F, B = pcbnew.F_SilkS, pcbnew.B_SilkS
    placed = {}
    if board in ("helmet-mb", "vest-mb"):
        # J8/J11 = edge B @ y+8.9 (övre); J9/J12 = edge A @ y-8.9 (undre); USB/VBUS-änd @ x-25 (vänster)
        placed["EDGE B"] = place(F, "P4 EDGE B", 1.3, False, 0, (-12, 12), (10.5, 20))
        placed["EDGE A"] = place(F, "P4 EDGE A", 1.3, False, 0, (-12, 12), (-20, -10.5))
        placed["USB"] = place(F, "USB-AND", 1.3, False, 90, (-45, -27), (-8, 8))
    elif board == "weapon-module":
        # J1 = edge B, BAKSIDA, vertikal kolumn x~25 (pad1=VSYS/USB topp). edge A → fire-control ovan.
        placed["EDGE B"] = place(B, "P4 EDGE B", 1.1, True, 90, (8, 20), (-20, -2))
        placed["USB"] = place(B, "USB-AND UPP", 0.9, True, 90, (8, 22), (0, 10))
    pcbnew.SaveBoard(path, b)
    ok = all(v for v in placed.values())
    print(f"{board}: " + ", ".join(f"'{k}'@{v}" for k, v in placed.items()) + ("  ✓ alla padd-fria" if ok else "  ✗ NÅGON EJ PLACERAD"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
