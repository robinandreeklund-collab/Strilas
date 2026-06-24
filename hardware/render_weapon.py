#!/usr/bin/env python3
"""Rendera vapen-kortet (spår/vior/paddar/zoner/outline) till PNG för översikt."""
import pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon

b = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
OX, OY = 150.0, 120.0
def P(v): return (v.x/1e6-OX, v.y/1e6-OY)
COL = {pcbnew.F_Cu: "#c0392b", pcbnew.In1_Cu: "#27ae60", pcbnew.In2_Cu: "#8e44ad", pcbnew.B_Cu: "#2980b9"}
fig, ax = plt.subplots(figsize=(7, 10))

# zoner (svagt)
for z in b.Zones():
    ly = z.GetLayer()
    poly = z.GetFilledPolysList(ly)
    for i in range(poly.OutlineCount()):
        ol = poly.Outline(i)
        pts = [(ol.CPoint(k).x/1e6-OX, ol.CPoint(k).y/1e6-OY) for k in range(ol.PointCount())]
        ax.add_patch(Polygon(pts, closed=True, color=COL.get(ly, "#999"), alpha=0.10, lw=0))

# spår
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T:
        (x1, y1), (x2, y2) = P(t.GetStart()), P(t.GetEnd())
        ax.plot([x1, x2], [y1, y2], color=COL.get(t.GetLayer(), "#555"),
                lw=max(0.6, t.GetWidth()/1e6*2.0), solid_capstyle="round", alpha=0.9)
    else:  # via
        x, y = P(t.GetPosition())
        ax.add_patch(Circle((x, y), t.GetWidth()/2e6, color="#f1c40f", ec="#7f6000", lw=0.3, zorder=5))

# paddar + ref
for f in b.GetFootprints():
    for p in f.Pads():
        x, y = P(p.GetPosition())
        w, h = p.GetSize().x/1e6, p.GetSize().y/1e6
        ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, angle=0, color="#e67e22", alpha=0.85, zorder=4))
    fx, fy = P(f.GetPosition())
    ax.text(fx, fy-1.6, f.GetReference(), fontsize=5.5, ha="center", color="black", zorder=6)

# outline + lins
ax.add_patch(Rectangle((-21, -31), 42, 62, fill=False, ec="black", lw=1.5))
ax.add_patch(Circle((0, 4), 8, fill=False, ec="black", lw=1.2, ls="--"))  # lins-hål (y inverterad)
ax.text(0, 4, "lins Ø16", fontsize=6, ha="center", va="center")
ax.set_aspect("equal"); ax.set_xlim(-24, 24); ax.set_ylim(34, -34)
ax.set_title("STRILAS vapen-optikmodul — routad (F=röd In1=GND-grön In2=VBAT-lila B=blå)", fontsize=8)
ax.axis("off")
plt.tight_layout(); plt.savefig("hardware/weapon-module-routed.png", dpi=150)
print("wrote hardware/weapon-module-routed.png")
