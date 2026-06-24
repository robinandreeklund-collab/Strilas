#!/usr/bin/env python3
"""STRILAS — placeringsgranskning av fire-control-kortet (71×21 mm, stackas ovanpå P4).
Topp-vy: J1 = FEMALE socket mot P4 edge A (pin6..17), stående JST-fan-out längs
nederhalvan, extra IMU (I²C) + pullups i mittbandet, 4 hål i linje med P4-standoffsen."""
import pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

b = pcbnew.LoadBoard("hardware/firecontrol.kicad_pcb")
OX, OY = 150.0, 120.0
HW, HH = 35.525, 10.5
fig, ax = plt.subplots(figsize=(13, 5), facecolor="white")
ax.add_patch(FancyBboxPatch((-HW, -HH), 2*HW, 2*HH, boxstyle="round,pad=0,rounding_size=2",
             fc="#0b6b3a", ec="#06301a", lw=2, zorder=1))

LABEL = {"J1": "P4 EDGE A socket (1×12)", "J2": "3V3-in", "J3": "TRIG", "J4": "RACK",
         "J5": "MAG-REL", "J6": "MAGWELL", "J7": "RECOIL", "J8": "NFC",
         "U1": "IMU\n0x69", "U2": "IMU\n0x68"}
def col(ref):
    if ref == "J1": return "#ffd040"
    if ref in ("U1", "U2"): return "#ff60ff"
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
        ax.add_patch(Circle((fx, fy), 1.1, fill=False, ec=col(ref), lw=1.6, zorder=8))
    else:
        xs = [p.GetPosition().x/1e6-OX for p in pads]; ys = [-(p.GetPosition().y/1e6-OY) for p in pads]
        pw = max(p.GetSize().x for p in pads)/1e6; ph = max(p.GetSize().y for p in pads)/1e6
        x0, x1 = min(xs)-pw/2, max(xs)+pw/2; y0, y1 = min(ys)-ph/2, max(ys)+ph/2
        ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False, ec=col(ref), lw=1.3, zorder=8))
    ax.text(fx, fy, LABEL.get(ref, ref), fontsize=6, ha="center", va="center", color="#fff", zorder=9, weight="bold")

ax.text(0, -HH+0.8, "gul=P4 edge A socket  magenta=extra IMU  röd=3V3-in  cyan=NFC  orange=recoil  grön=brytare (stående JST)",
        fontsize=6.5, color="#fff", ha="center", zorder=10)
ax.set_aspect("equal"); ax.set_xlim(-HW-2, HW+2); ax.set_ylim(-HH-3, HH+2); ax.axis("off")
ax.set_title("STRILAS fire-control-kort (71×21) — stackas ovanpå P4, möter edge A (USB-upp)\n"
             "trigger · rack · mag-release · magwell · recoil · NFC · 2× IMU (I²C 0x68/0x69)",
             fontsize=10, weight="bold")
plt.tight_layout()
plt.savefig("hardware/firecontrol-placement.png", dpi=160, facecolor="white")
print("wrote hardware/firecontrol-placement.png")
