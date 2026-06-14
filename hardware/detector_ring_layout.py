#!/usr/bin/env python3
"""
STRILAS — PCB-placeringsritning: detektor-ring med 8x TSOP4856 + central kamera.

Genererar en mattsatt topvy (top view) av en rund detektormodul:
  - 8 st Vishay TSOP4856 (56 kHz IR-mottagare) jamnt fordelade i en ring (45 grader)
  - central oppning + monteringshal for en P4-kompatibel kameramodul (t.ex. OV5640)
  - monteringshal, kontakt mot ESP32-P4 (8x OUT + 3V3 + GND)

Det ar en placerings-/mekanikritning for iteration, inte fab-fardiga Gerbers.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, RegularPolygon, FancyArrowPatch
import matplotlib.transforms as mtransforms

mm = 1.0
BOARD_R   = 38.0      # kort-radie (Ø76 mm)
BOLT_R    = 27.0      # TSOP bult-cirkel-radie
LENS_R    = 8.0       # central linsoppning (Ø16 mm)
CAM_SQ    = 24.0      # kameramodul keepout (24x24 mm) - matcha din modul
CAM_HOLE  = 20.0      # kamera-monteringshal centrum-avstand (20 mm fyrkant)

GREEN     = "#0e5a2a"
GREEN_ED  = "#0a7d39"
COPPER    = "#c98a3a"
PAD       = "#d9b25a"
SILK      = "#e8f0e8"
CUT       = "#0b0e12"

fig, ax = plt.subplots(figsize=(11, 11))
ax.set_aspect("equal")
ax.set_facecolor("#0b0e12")
fig.patch.set_facecolor("#0b0e12")

# ---- kort-outline ----
board = Circle((0, 0), BOARD_R, facecolor=GREEN, edgecolor=GREEN_ED, lw=2.5, zorder=1)
ax.add_patch(board)

# ---- central kamera-oppning + keepout + monteringshal ----
ax.add_patch(Circle((0, 0), LENS_R, facecolor=CUT, edgecolor=SILK, lw=1.5, zorder=4))
ax.text(0, 0, "KAMERA\nlins-\noppning\nØ16", ha="center", va="center",
        color=SILK, fontsize=8, zorder=5)
ax.add_patch(Rectangle((-CAM_SQ/2, -CAM_SQ/2), CAM_SQ, CAM_SQ, fill=False,
                        edgecolor=SILK, lw=1.0, ls=(0, (5, 4)), zorder=3))
for sx in (-1, 1):
    for sy in (-1, 1):
        ax.add_patch(Circle((sx*CAM_HOLE/2, sy*CAM_HOLE/2), 1.0,
                            facecolor=CUT, edgecolor=COPPER, lw=1.2, zorder=4))
# FFC-slits for kamerakabel (ut mot kontaktsidan)
ax.add_patch(Rectangle((-7, -CAM_SQ/2 - 3.2), 14, 2.0, facecolor=CUT,
                        edgecolor=SILK, lw=0.8, zorder=3))
ax.text(0, -CAM_SQ/2 - 5.4, "FFC-slits (MIPI-CSI)", ha="center", va="top",
        color=SILK, fontsize=7, zorder=5)

# ---- en TSOP4856-footprint (topvy), placerad/roterad radiellt ----
def draw_tsop(ax, angle_deg, idx):
    """Rita en TSOP4856: kropp + IR-dome (riktad framat/ut) + 3 pads (2.54 mm)."""
    th = np.deg2rad(angle_deg)
    cx, cy = BOLT_R*np.cos(th), BOLT_R*np.sin(th)
    t = (mtransforms.Affine2D()
         .rotate_deg(angle_deg - 90)     # leder inat, dome utat
         .translate(cx, cy) + ax.transData)
    # kropp ~5.8 (tangentiell) x 6.0 (radiell)
    body = Rectangle((-2.9, -3.0), 5.8, 6.0, facecolor="#15171c",
                     edgecolor=SILK, lw=1.0, transform=t, zorder=5)
    ax.add_patch(body)
    # IR-dome (halvklot) mot ytterkant
    dome = Circle((0, 1.7), 1.7, facecolor="#2b2f36", edgecolor=SILK,
                  lw=0.8, transform=t, zorder=6)
    ax.add_patch(dome)
    # 3 pads (OUT, GND, VS) pa innerkanten, 2.54 mm pitch
    for k, lbl in zip((-1, 0, 1), ("O", "G", "V")):
        p = Rectangle((k*2.54 - 0.6, -3.6), 1.2, 1.6, facecolor=PAD,
                      edgecolor="#7a5a1e", lw=0.6, transform=t, zorder=6)
        ax.add_patch(p)
    # etikett
    lt = (mtransforms.Affine2D().rotate_deg(angle_deg - 90).translate(cx, cy)
          + ax.transData)
    ax.text(0, 0.0, f"T{idx}", ha="center", va="center", color=SILK,
            fontsize=8, fontweight="bold", transform=lt, zorder=7)

for i in range(8):
    draw_tsop(ax, i*45.0, i+1)

# ---- monteringshal M2.5 (mellan TSOP-arna, r=34) ----
for a in (22.5, 112.5, 202.5, 292.5):
    th = np.deg2rad(a)
    ax.add_patch(Circle((34*np.cos(th), 34*np.sin(th)), 1.4,
                        facecolor=CUT, edgecolor=COPPER, lw=1.2, zorder=4))

# ---- kontakt mot P4 (2x5 = 8x OUT + 3V3 + GND), nere ----
hx, hy = -11.43, -33.0
ax.add_patch(Rectangle((hx-2, hy-2.2), 25.4, 7.0, facecolor="#15171c",
                       edgecolor=SILK, lw=1.0, zorder=5))
for r in range(2):
    for c in range(5):
        ax.add_patch(Circle((hx + c*2.54, hy + r*2.54), 0.7, facecolor=PAD,
                            edgecolor="#7a5a1e", lw=0.5, zorder=6))
ax.text(0, hy - 4.8, "→ ESP32-P4:  8× OUT  +  3V3  +  GND  (2×5, 2.54 mm)",
        ha="center", va="top", color=SILK, fontsize=8, zorder=7)

# ---- mattlinjer / annoteringar ----
def dim_radius(ax, r, label, ang=60):
    th = np.deg2rad(ang)
    ax.annotate("", xy=(r*np.cos(th), r*np.sin(th)), xytext=(0, 0),
                arrowprops=dict(arrowstyle="<->", color="#6fb3ff", lw=1.0), zorder=8)
    ax.text(r*0.55*np.cos(th)+1.5, r*0.55*np.sin(th)+1.5, label,
            color="#6fb3ff", fontsize=8, zorder=8)

dim_radius(ax, BOARD_R, "Ø76 mm", ang=68)
dim_radius(ax, BOLT_R, "bult-Ø54", ang=15)

# 45-graders markor
for i in range(8):
    th = np.deg2rad(i*45)
    ax.plot([0, BOARD_R*np.cos(th)], [0, BOARD_R*np.sin(th)],
            color="#243044", lw=0.6, ls=":", zorder=1)
ax.text(BOARD_R*np.cos(np.deg2rad(22.5))*0.62,
        BOARD_R*np.sin(np.deg2rad(22.5))*0.62, "45°", color="#8b949e", fontsize=8)

# ---- titel + notruta ----
ax.set_title("STRILAS — Detektor-ring: 8× TSOP4856 + central P4-kamera (topvy)",
             color="#e6edf3", fontsize=13, pad=16)
notes = (
    "NOTER\n"
    "• 8× TSOP4856 (56 kHz) i ring, 45° isär → tät framåttäckning + redundans + grov träffposition\n"
    "• Domerna pekar FRAMÅT (ut ur kortet), samma riktning som kameran. För 360°: vinklade facetter (separat mekanik)\n"
    "• Per TSOP: 100 nF avkoppling nära VS + 100 Ω serie + 0.1–1 µF (Vishay app-note) mot störning\n"
    "• 8 separata OUT → 8 P4-GPIO (behåller zon/riktning). OR:a ihop bara om du nöjer dig med ren ja/nej-träff\n"
    "• Central öppning Ø16 + 20 mm hålbild: MATCHA din P4-kamera (OV5640). FFC-slits för MIPI-CSI-kabeln\n"
    "• 860/940 nm bandpass-glas över domerna för utomhus-räckvidd (matcha emitterns våglängd)"
)
ax.text(-BOARD_R-2, -BOARD_R-9, notes, ha="left", va="top", color="#aeb7c2",
        fontsize=8.2, family="monospace", zorder=9,
        bbox=dict(boxstyle="round,pad=0.6", fc="#11151b", ec="#30363d"))

lim = BOARD_R + 6
ax.set_xlim(-lim, lim); ax.set_ylim(-lim - 14, lim)
ax.axis("off")
plt.tight_layout()
out = "hardware/detector-ring-8x-tsop4856.png"
plt.savefig(out, dpi=150, facecolor=fig.get_facecolor())
print("wrote", out)
