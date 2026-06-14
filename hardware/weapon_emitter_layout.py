#!/usr/bin/env python3
"""
STRILAS — VAPNETS optikmodul v1 (KOMPAKT, 2 emittrar).
Precis sikteskamera + IR-skottemitter + IMU + driver pa ETT kort.

Krympt fran 4-emitter-ringen (Ø80) till en kompakt ~42x62 mm modul UTAN att tappa
prestanda:
  - PRECISION oforandrad: sikteskameran (OV5640 NoIR + 860 nm IR-pass + TELEFOTO M12)
    ser malets IR-konstellation -> solvePnP -> baring sub-0.1 grader.
  - RACKVIDD bibehallen: 2x SFH 4715AS (860 nm) + Carclo-kollimator delar effektlasten
    -> 100-150 m. Symmetriska ovanfor kameran => samboresikt (parallax ~0.01 grader @150 m).
  - 2 (inte 1) emittrar => effekten sprids => lattare Class 1 an en hardkord enskild kalla.
  - Tappar bara: framtida aktiv-fiducial-beacon (4-punkt) + lite redundans. Ej v1-krav.
  - IMU ICM-45686 + emitter-driver (N-FET + Rsense HW-stromgrans + cap + flyback) ombord.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch

BW, BH    = 42.0, 62.0      # kort 42 x 62 mm
EMIT_X, EMIT_Y = 10.0, 20.0 # 2 emittrar: (+/-10, +20)
LENS_R    = 10.0            # Carclo 10195 ~Ø20
CAM_W, CAM_H = 25.0, 24.0   # OV5640-modul (mat din egen!)
CAM_CY    = -4.0            # kamera-centrum y
CAM_BARREL = 9.0

GREEN, GREEN_ED = "#0e5a2a", "#0a7d39"
PAD, SILK, CUT  = "#d9b25a", "#e8f0e8", "#0b0e12"
IRC, LENSC, CAMC = "#7a1f1f", "#3a6ea5", "#00bcd4"

fig, ax = plt.subplots(figsize=(9.5, 12.6))
ax.set_aspect("equal"); ax.set_facecolor("#0b0e12"); fig.patch.set_facecolor("#0b0e12")

# ---- kort-outline (rundad rektangel) + samboresikt-axel ----
ax.add_patch(FancyBboxPatch((-BW/2+3, -BH/2+3), BW-6, BH-6,
             boxstyle="round,pad=3,rounding_size=4", facecolor=GREEN, edgecolor=GREEN_ED, lw=2.5, zorder=1))
ax.plot([0, 0], [-BH/2, BH/2], color="#243044", lw=0.7, ls=":", zorder=1)

# ---- central sikteskamera (telefoto) ----
ax.add_patch(Rectangle((-CAM_W/2, CAM_CY-CAM_H/2), CAM_W, CAM_H, facecolor="#10212a", edgecolor=SILK, lw=1.3, zorder=3))
ax.add_patch(Circle((0, CAM_CY), CAM_BARREL+1.4, facecolor="#0c1418", edgecolor=CAMC, lw=1.4, zorder=4))
ax.add_patch(Circle((0, CAM_CY), CAM_BARREL, facecolor=CUT, edgecolor=SILK, lw=1.3, zorder=5))
ax.text(0, CAM_CY+1.4, "SIKTESKAMERA", ha="center", va="center", color=CAMC, fontsize=6.4, fontweight="bold", zorder=6)
ax.text(0, CAM_CY-2.2, "OV5640 NoIR\n860nm IR-pass\nTELEFOTO M12", ha="center", va="center", color=SILK, fontsize=5.6, zorder=6)
for sx in (-1, 1):
    for sy in (-1, 1):
        ax.add_patch(Circle((sx*10.5, CAM_CY+sy*9.5), 1.0, facecolor=CUT, edgecolor="#c98a3a", lw=1.0, zorder=6))
ax.add_patch(Rectangle((-6, CAM_CY-CAM_H/2-1.9), 12, 1.9, facecolor="#1c1c22", edgecolor=SILK, lw=0.8, zorder=4))
ax.text(0, CAM_CY-CAM_H/2-2.4, "FFC → P4 MIPI-CSI", ha="center", va="top", color=SILK, fontsize=6.0, zorder=6)

# ---- 2x SFH 4715AS (860 nm) + Carclo-kollimator, symmetriskt ovanfor kameran ----
def draw_emitter(ax, x, y, idx):
    ax.add_patch(Circle((x, y), LENS_R, facecolor="none", edgecolor=LENSC, lw=1.8, zorder=5))
    ax.add_patch(Circle((x, y), LENS_R-2.0, facecolor="none", edgecolor=LENSC, lw=0.8, ls=":", zorder=5))
    for ba in (90, 210, 330):
        bx, by = x + (LENS_R-0.8)*np.cos(np.deg2rad(ba)), y + (LENS_R-0.8)*np.sin(np.deg2rad(ba))
        ax.add_patch(Circle((bx, by), 0.7, facecolor=CUT, edgecolor=LENSC, lw=0.8, zorder=6))
    ax.add_patch(Rectangle((x-1.9, y-1.9), 3.8, 3.8, facecolor=IRC, edgecolor=SILK, lw=1.0, zorder=6))
    ax.add_patch(Rectangle((x-3.3, y-0.8), 1.4, 1.6, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.add_patch(Rectangle((x+1.9, y-0.8), 1.4, 1.6, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.text(x, y+LENS_R+0.3, f"D{idx}", ha="center", va="bottom", color=SILK, fontsize=6.6, fontweight="bold", zorder=6)

draw_emitter(ax, -EMIT_X, EMIT_Y, 1)
draw_emitter(ax,  EMIT_X, EMIT_Y, 2)
ax.text(0, EMIT_Y, "SFH4715AS\n+Carclo", ha="center", va="center", color="#9bbfe0", fontsize=5.6, zorder=6)

# ---- IMU + driver i sidoremsorna (vid sidan av kameran) ----
def part(ax, x, y, w, h, ref, val, vy="top"):
    ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor="#15171c", edgecolor=SILK, lw=0.9, zorder=5))
    ax.text(x, y+0.2, ref, ha="center", va="center", color=SILK, fontsize=6.0, fontweight="bold", zorder=6)
    yy = y-h/2-0.5 if vy == "top" else y+h/2+0.5
    ax.text(x, yy, val, ha="center", va=vy, color="#aeb7c2", fontsize=5.2, zorder=6)
# vänster remsa: IMU + Q1 + Rg
ax.add_patch(Rectangle((-16.5-3, 1.5-2.5), 6, 5, facecolor="#1d2530", edgecolor=SILK, lw=1.0, zorder=5))
ax.text(-16.5, 3.0, "U2", ha="center", va="center", color=SILK, fontsize=6.0, fontweight="bold", zorder=6)
ax.text(-16.5, -1.6, "IMU", ha="center", va="top", color="#aeb7c2", fontsize=5.2, zorder=6)
part(ax, -16.5, -7.5, 4.2, 3.0, "Q1", "AO3400")
part(ax, -16.5, -13.0, 3.2, 2.2, "Rg", "220Ω")
# höger remsa: C1 + R1 + D5
part(ax, 16.5, 2.5, 4.6, 4.4, "C1", "220µF")
part(ax, 16.5, -6.0, 4.0, 2.8, "R1", "Rsense")
part(ax, 16.5, -12.0, 3.4, 2.4, "D5", "SS54")

# ---- kontakt mot P4 (2x4), botten ----
hy = -25.5; hx0 = -1.5*2.54
ax.add_patch(Rectangle((hx0-2, hy-1.4), 2.54*3+4, 2.54+3.0, facecolor="#15171c", edgecolor=SILK, lw=1.0, zorder=5))
for c in range(4):
    ax.add_patch(Circle((hx0 + c*2.54, hy+2.54), 0.65, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.add_patch(Circle((hx0 + c*2.54, hy), 0.65, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
ax.text(0, hy-2.3, "J1: IR_MOD·VEMIT·EN·GND / 3V3·SDA·SCL·GND", ha="center", va="top", color=SILK, fontsize=5.6, zorder=6)

# ---- monteringshal ----
for x, y in [(0, 27.5), (-17.5, -27), (17.5, -27)]:
    ax.add_patch(Circle((x, y), 1.3, facecolor=CUT, edgecolor="#c98a3a", lw=1.0, zorder=4))

# ---- mattlinjer ----
ax.annotate("", xy=(BW/2-3, BH/2+1.5), xytext=(-BW/2+3, BH/2+1.5),
            arrowprops=dict(arrowstyle="<->", color="#6fb3ff", lw=1.0), zorder=8)
ax.text(0, BH/2+2.0, "42 mm", ha="center", color="#6fb3ff", fontsize=8, zorder=8)
ax.annotate("", xy=(BW/2+1.5, BH/2-3), xytext=(BW/2+1.5, -BH/2+3),
            arrowprops=dict(arrowstyle="<->", color="#6fb3ff", lw=1.0), zorder=8)
ax.text(BW/2+2.2, 0, "62 mm", ha="left", va="center", color="#6fb3ff", fontsize=8, rotation=90, zorder=8)

ax.set_title("STRILAS — VAPNETS optikmodul v1 (KOMPAKT): kamera + 2× IR-emitter + IMU + driver",
             color="#e6edf3", fontsize=11.5, pad=10)
notes = (
    "NOTER — krympt Ø80 → 42×62 mm UTAN prestandaförlust\n"
    "• PRECISION oförändrad = sikteskameran (telefoto + IR-pass) → solvePnP-bäring sub-0.1° (emitterantal påverkar EJ precision)\n"
    "• RÄCKVIDD bibehållen = 2× SFH4715AS + Carclo delar lasten → 100–150 m; symmetriska → samboresikt (parallax ~0.01° @150 m)\n"
    "• 2 (ej 1) emittrar: effekten sprids → lättare Class 1. Tappar bara framtida aktiv-fiducial-beacon (ej v1-krav)\n"
    "• ⚠️ kameran ser egna 860 nm-emittrar → baffel + avfyra bara vid trigger, ELLER emitter 940 nm / kamerafilter 860 nm\n"
    "• R1 = HW-strömgräns (mät Class 1). Kamera = P4-stödd (OV5640/Mira220, EJ IMX296). Mät modul → CAM_W/H"
)
ax.text(-BW/2-1, -BH/2-2, notes, ha="left", va="top", color="#aeb7c2", fontsize=7.2,
        family="monospace", zorder=9, bbox=dict(boxstyle="round,pad=0.6", fc="#11151b", ec="#30363d"))

ax.set_xlim(-BW/2-8, BW/2+10); ax.set_ylim(-BH/2-16, BH/2+6); ax.axis("off")
plt.tight_layout()
out = "hardware/weapon-emitter-camera-860nm.png"
plt.savefig(out, dpi=150, facecolor=fig.get_facecolor())
print("wrote", out)
