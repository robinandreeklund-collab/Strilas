#!/usr/bin/env python3
"""STRILAS — snabb placerings-render (PNG) för visuell kontroll av footprint-layout/orientering.
Ritar: Edge.Cuts-outline, varje footprints courtyard (fram=blå, bak=röd streckad), ref-etikett,
pad-rad, samt en PIL för footprintens +Y-lokala riktning (= JST side-entry kabel-öppning).
Användning: python3 hardware/render_place.py <board.kicad_pcb> <out.png> [titel]"""
import sys, math, pcbnew
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly

def poly_pts(sps):
    out = []
    for oi in range(sps.OutlineCount()):
        ol = sps.Outline(oi); pts = [(ol.CPoint(i).x/1e6, ol.CPoint(i).y/1e6) for i in range(ol.PointCount())]
        out.append(pts)
    return out

def main():
    pcb, out = sys.argv[1], sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else pcb
    b = pcbnew.LoadBoard(pcb)
    fig, ax = plt.subplots(figsize=(13, 13))
    # outline (Edge.Cuts)
    for d in b.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts: continue
        if d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c = d.GetCenter(); r = d.GetRadius()/1e6
            ax.add_artist(plt.Circle((c.x/1e6, -c.y/1e6), r, fill=False, color="k", lw=1.5))
        elif d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = d.GetStart(), d.GetEnd()
            ax.plot([s.x/1e6, e.x/1e6], [-s.y/1e6, -e.y/1e6], "k-", lw=1.5)
    for f in b.GetFootprints():
        ref = f.GetReference(); flip = f.IsFlipped()
        col = "crimson" if flip else "royalblue"
        cy = f.GetCourtyard(pcbnew.B_CrtYd if flip else pcbnew.F_CrtYd)
        drew = False
        for pts in poly_pts(cy):
            ax.add_patch(MplPoly([(x, -y) for x, y in pts], closed=True, fill=False,
                                 ec=col, lw=1.0, ls="--" if flip else "-")); drew = True
        p = f.GetPosition(); px, py = p.x/1e6, -p.y/1e6
        if not drew:  # fallback: bbox
            bb = f.GetBoundingBox(False, False)
            ax.add_patch(MplPoly([(bb.GetLeft()/1e6, -bb.GetTop()/1e6), (bb.GetRight()/1e6, -bb.GetTop()/1e6),
                                  (bb.GetRight()/1e6, -bb.GetBottom()/1e6), (bb.GetLeft()/1e6, -bb.GetBottom()/1e6)],
                                 closed=True, fill=False, ec=col, lw=1.0))
        ax.text(px, py, ref, fontsize=6, ha="center", va="center", color=col)
        # pads
        for pad in f.Pads():
            pp = pad.GetPosition(); ax.plot(pp.x/1e6, -pp.y/1e6, ".", color=col, ms=2)
        # +Y local arrow (JST side-entry: cable opening faces footprint +Y)
        if ref.startswith("J"):
            ang = math.radians(f.GetOrientationDegrees())
            # footprint local +Y in board coords (KiCad: orientation CCW, Y-down internal).
            # local +Y after rotation (board, Y-down): dx=sin(ang)*L? — derive via two transformed pts
            L = 3.0
            # transform local (0,L)[Y-down] by KiCad orientation; flip mirrors X
            lx, ly = 0.0, L
            rx = lx*math.cos(ang) - ly*math.sin(ang)
            ry = lx*math.sin(ang) + ly*math.cos(ang)
            if flip: rx = -rx
            ax.annotate("", xy=(px+rx, py-ry), xytext=(px, py),
                        arrowprops=dict(arrowstyle="->", color="green", lw=1.3))
    ax.set_aspect("equal"); ax.set_title(title); ax.grid(True, alpha=0.3)
    ax.relim(); ax.autoscale_view()
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print("wrote", out)

if __name__ == "__main__":
    main()
