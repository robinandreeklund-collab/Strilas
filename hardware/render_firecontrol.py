#!/usr/bin/env python3
"""STRILAS — placeringsgranskning av fire-control-kortet (50×42 mm).
Topp-vy: J1 = stel kantkontakt mot P4 edge A (vänster), JST-fan-out runt kanterna,
I²C-pullups + 3V3-avkoppling i centrum. Visar funktionsetiketter per kontakt."""
import pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

b = pcbnew.LoadBoard("hardware/firecontrol.kicad_pcb")
OX, OY = 150.0, 120.0
HW, HH = 25, 21
fig, ax = plt.subplots(figsize=(8.5, 7.2), facecolor="white")
ax.add_patch(FancyBboxPatch((-HW, -HH), 2*HW, 2*HH, boxstyle="round,pad=0,rounding_size=2.5",
             fc="#0b6b3a", ec="#06301a", lw=2, zorder=1))

LABEL = {"J1": "P4 EDGE A\n(1×12, stel)", "J2": "3V3-in\n(fr. edge B)", "J3": "TRIGGER",
         "J4": "RACK", "J5": "MAG-REL", "J6": "MAGWELL", "J7": "RECOIL\n(PWM/FAULT)",
         "J8": "NFC PN532\n(I²C)"}
def col(ref):
    if ref == "J1": return "#ffd040"
    if ref == "J2": return "#ff6060"
    if ref == "J8": return "#40c0ff"
    if ref == "J7": return "#ff9030"
    if ref.startswith("J"): return "#a0e0a0"
    if ref.startswith("H"): return "#dddddd"
    return "#ffe8b0"

for f in b.GetFootprints():
    ref = f.GetReference()
    fx = f.GetPosition().x/1e6-OX; fy = -(f.GetPosition().y/1e6-OY)
    pads = list(f.Pads())
    if ref.startswith("H") and len(pads) == 1:
        r = max(p.GetSize().x for p in pads)/2e6
        ax.add_patch(Circle((fx, fy), max(r, 1.0), fill=False, ec=col(ref), lw=1.6, zorder=8))
    else:
        xs = [p.GetPosition().x/1e6-OX for p in pads]; ys = [-(p.GetPosition().y/1e6-OY) for p in pads]
        pw = max(p.GetSize().x for p in pads)/1e6; ph = max(p.GetSize().y for p in pads)/1e6
        x0, x1 = min(xs)-pw/2, max(xs)+pw/2; y0, y1 = min(ys)-ph/2, max(ys)+ph/2
        ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False, ec=col(ref), lw=1.3, zorder=8))
    lab = LABEL.get(ref, ref)
    ax.text(fx, fy, lab, fontsize=5.6, ha="center", va="center", color="#fff", zorder=9, weight="bold")

ax.text(0, -HH+1.0, "gul=P4 edge A  röd=3V3-in  cyan=NFC  orange=recoil  grön=brytare(JST-PH)",
        fontsize=6, color="#fff", ha="center", zorder=10)
ax.set_aspect("equal"); ax.set_xlim(-HW-3, HW+3); ax.set_ylim(-HH-3, HH+3); ax.axis("off")
ax.set_title("STRILAS fire-control-kort (50×42) — matar P4 edge A stelt\n"
             "trigger · rack · mag-release · magwell · recoil-styrning · NFC",
             fontsize=9, weight="bold")
plt.tight_layout()
plt.savefig("hardware/firecontrol-placement.png", dpi=160, facecolor="white")
print("wrote hardware/firecontrol-placement.png")
