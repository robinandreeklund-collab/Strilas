#!/usr/bin/env python3
"""Realistisk PCB-render av vapen-modulen (fram + bak), KiCad-liknande palett.
Grön lödmask, guld-paddar (ENIG), vit silk, koppar-spår, lins-urtag."""
import pcbnew, matplotlib, numpy as np
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Polygon
import matplotlib.transforms as mtrans

b = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
OX, OY = 150.0, 120.0
MASK = "#0b6b3a"; MASK_D = "#095c32"; COPPER = "#c87a3a"; GOLD = "#e6b84d"
SILK = "#eef2f0"; VIA = "#d9a441"; EDGE = "#06301a"


def P(v): return (v.x/1e6-OX, -(v.y/1e6-OY))


def draw(ax, side):
    front = side == "F"
    cu_layer = pcbnew.F_Cu if front else pcbnew.B_Cu
    silk_layer = pcbnew.F_SilkS if front else pcbnew.B_SilkS
    sgn = 1 if front else -1   # spegelvänd baksidan i X
    def X(x): return sgn*x
    # board (rundad grön platta)
    board = FancyBboxPatch((-26, -40), 52, 80, boxstyle="round,pad=0,rounding_size=2.5",
                           fc=MASK, ec=EDGE, lw=2, zorder=1)
    ax.add_patch(board)
    # svag plan-textur (mörkare grön fält)
    ax.add_patch(Rectangle((-25.7, -39.7), 51.4, 79.4, fc=MASK_D, ec="none", alpha=0.35, zorder=1.1))
    # spår (koppar, syns svagt under mask)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == cu_layer:
            (x1, y1), (x2, y2) = P(t.GetStart()), P(t.GetEnd())
            ax.plot([X(x1), X(x2)], [y1, y2], color=COPPER, alpha=0.55,
                    lw=max(0.8, t.GetWidth()/1e6*2.4), solid_capstyle="round", zorder=2)
    # vior (guld-ringar)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = P(t.GetPosition())
            ax.add_patch(Circle((X(x), y), t.GetWidth()/2e6, fc=GOLD, ec="#7a5a1a", lw=0.3, zorder=3))
    # paddar (guld, exponerade genom mask)
    for f in b.GetFootprints():
        for p in f.Pads():
            if not p.IsOnLayer(cu_layer):
                continue
            x, y = P(p.GetPosition())
            w, h = p.GetSize().x/1e6, p.GetSize().y/1e6
            ang = -p.GetOrientationDegrees() if front else p.GetOrientationDegrees()
            re = Rectangle((-w/2, -h/2), w, h, fc=GOLD, ec="#8a6a1f", lw=0.3, zorder=4)
            tr = (mtrans.Affine2D().rotate_deg(ang).translate(X(x), y) + ax.transData)
            re.set_transform(tr); ax.add_patch(re)
        # silk-referens
        if f.GetLayer() == (pcbnew.F_Cu if front else pcbnew.B_Cu) or True:
            fx, fy = P(f.GetPosition())
            ax.text(X(fx), fy, f.GetReference(), fontsize=5, ha="center", va="center",
                    color=SILK, zorder=6, weight="bold")
    # silk-grafik (emitter-ringar, outlines på rätt sida)
    for d in b.GetDrawings():
        if d.GetLayer() == silk_layer and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c = P(d.GetCenter()); r = (d.GetEnd().x-d.GetStart().x)/1e6
            ax.add_patch(Circle((X(c[0]), c[1]), abs(r), fill=False, ec=SILK, lw=0.6, zorder=5))
    # lins-urtag (genomgående hål)
    ax.add_patch(Circle((0, 2), 8, fc="#0a0a0a", ec="#d9d9d9", lw=1.0, zorder=7))
    ax.text(0, 2, "Ø16\nlins", fontsize=6, ha="center", va="center", color="#d9d9d9", zorder=8)
    ax.set_aspect("equal"); ax.set_xlim(-29, 29); ax.set_ylim(-43, 43)
    ax.axis("off")
    ax.set_title(("FRAM (F.Cu — emitter-driver, IMU, headers)" if front
                  else "BAK (B.Cu — GND-plan, termiska vior)"), fontsize=9, color="#222")


fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 9), facecolor="white")
draw(a1, "F"); draw(a2, "B")
fig.suptitle("STRILAS vapen-optikmodul  •  52 × 80 mm (stackad box: P4 bakom), 4-lager  •  940 nm-emitter + OV9281-lins (Ø16) + ICM-45686",
             fontsize=11, weight="bold")
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("hardware/weapon-module-render.png", dpi=170, facecolor="white")
print("wrote hardware/weapon-module-render.png")
