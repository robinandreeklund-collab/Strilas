#!/usr/bin/env python3
"""
STRILAS — PCB-placeringsritning: VAPNETS optikmodul.
IR-emitter (860 nm) + sikteskamera + driver/strömgräns på ETT kort.

Topvy (top view) av en rund modul som klampas på vapnet:
  - 4x ams-OSRAM SFH 4715AS (860 nm) i kvadrat runt kameran (SAMBORESIKTAD ring)
    -> siktaxel = IR-axel, och de 4 utgor en aktiv fiducial-konstellation
  - central oppning + monteringshal for P4-kamera (OV5640, MIPI-CSI)
  - emitter-driver ombord: N-FET + stromsattnings-/sense-resistor (HW-stromgrans
    = ogonsakerhet) + reservoarkondensator + gate-resistor + flyback/TVS
  - kollimator-lins (~+/-5 grader) over varje LED -> 100-150 m rackvidd
  - kontakt mot ESP32-P4: IR_MOD (56 kHz fran RMT), VEMIT, 3V3, GND, EN

Placerings-/mekanikritning for iteration, inte fab-fardiga Gerbers.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import matplotlib.transforms as mtransforms

BOARD_R   = 30.0      # Ø60 mm
EMIT_OFF  = 15.0      # emitter-position (x,y) = (+/-15, +/-15)
LENS_R    = 5.5       # kollimator-lins-radie (Ø11)
CAM_LENS  = 7.0       # central kamera-linsoppning (Ø14)
CAM_SQ    = 20.0      # kameramodul keepout
CAM_HOLE  = 16.0      # kamera-monteringshal (16 mm fyrkant)

GREEN, GREEN_ED = "#0e5a2a", "#0a7d39"
PAD, SILK, CUT  = "#d9b25a", "#e8f0e8", "#0b0e12"
IRC             = "#7a1f1f"   # IR-emitter-rod
LENSC           = "#3a6ea5"

fig, ax = plt.subplots(figsize=(11, 11.5))
ax.set_aspect("equal"); ax.set_facecolor("#0b0e12"); fig.patch.set_facecolor("#0b0e12")

# ---- kort-outline ----
ax.add_patch(Circle((0, 0), BOARD_R, facecolor=GREEN, edgecolor=GREEN_ED, lw=2.5, zorder=1))

# ---- samboresikt-kors (kameraxel = emitter-centroid-axel) ----
ax.plot([-BOARD_R, BOARD_R], [0, 0], color="#243044", lw=0.7, ls=":", zorder=1)
ax.plot([0, 0], [-BOARD_R, BOARD_R], color="#243044", lw=0.7, ls=":", zorder=1)

# ---- central kamera ----
ax.add_patch(Circle((0, 0), CAM_LENS, facecolor=CUT, edgecolor=SILK, lw=1.5, zorder=5))
ax.text(0, 0, "KAMERA\nOV5640\nØ14", ha="center", va="center", color=SILK, fontsize=7.5, zorder=6)
ax.add_patch(Rectangle((-CAM_SQ/2, -CAM_SQ/2), CAM_SQ, CAM_SQ, fill=False,
                       edgecolor=SILK, lw=1.0, ls=(0, (5, 4)), zorder=3))
for sx in (-1, 1):
    for sy in (-1, 1):
        ax.add_patch(Circle((sx*CAM_HOLE/2, sy*CAM_HOLE/2), 1.0, facecolor=CUT,
                            edgecolor="#c98a3a", lw=1.0, zorder=4))
ax.add_patch(Rectangle((-7, CAM_SQ/2 + 1.5), 14, 2.0, facecolor=CUT, edgecolor=SILK, lw=0.8, zorder=3))
ax.text(0, CAM_SQ/2 + 4.0, "FFC → P4 MIPI-CSI", ha="center", va="bottom", color=SILK, fontsize=7, zorder=6)

# ---- 4x SFH 4715AS (860 nm) + kollimator i kvadrat runt kameran ----
def draw_emitter(ax, x, y, idx):
    # kollimator-lins
    ax.add_patch(Circle((x, y), LENS_R, facecolor="none", edgecolor=LENSC, lw=1.6, zorder=5))
    ax.add_patch(Circle((x, y), LENS_R-1.4, facecolor="none", edgecolor=LENSC, lw=0.8, ls=":", zorder=5))
    # LED-footprint (OSLON Black ~3.85x3.85) i fokus
    ax.add_patch(Rectangle((x-1.9, y-1.9), 3.8, 3.8, facecolor=IRC, edgecolor=SILK, lw=1.0, zorder=6))
    # 2 pads (anod/katod)
    ax.add_patch(Rectangle((x-1.9-1.4, y-0.8), 1.4, 1.6, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.add_patch(Rectangle((x+1.9, y-0.8), 1.4, 1.6, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.text(x, y-LENS_R-1.6, f"D{idx}\nSFH4715AS", ha="center", va="top", color=SILK, fontsize=6.8, zorder=6)

corners = [(-EMIT_OFF, EMIT_OFF), (EMIT_OFF, EMIT_OFF), (-EMIT_OFF, -EMIT_OFF), (EMIT_OFF, -EMIT_OFF)]
for i, (x, y) in enumerate(corners):
    draw_emitter(ax, x, y, i+1)

# ---- emitter-driver (nere mellan de tva nedre emittrarna) ----
def part(ax, x, y, w, h, ref, val, fc="#15171c"):
    ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor=fc, edgecolor=SILK, lw=0.9, zorder=5))
    ax.text(x, y+0.2, ref, ha="center", va="center", color=SILK, fontsize=6.6, fontweight="bold", zorder=6)
    ax.text(x, y-h/2-0.6, val, ha="center", va="top", color="#aeb7c2", fontsize=6.0, zorder=6)

part(ax, -7.5, -8.5, 4.5, 3.2, "Q1", "AO3400\nN-FET")
part(ax,  0.0, -8.5, 4.0, 3.0, "R1", "Rsense\n~1–3 Ω 2W")
part(ax,  7.5, -8.5, 4.5, 4.5, "C1", "220 µF\nreservoar")
part(ax, -3.8, -12.5, 3.0, 2.4, "Rg", "220 Ω")
part(ax,  3.8, -12.5, 3.4, 2.4, "D5", "flyback\nSS54")

# ---- kontakt mot P4 (1x5) ----
hy = -25.0; hx0 = -2*2.54
ax.add_patch(Rectangle((hx0-2, hy-2), 2.54*4+4, 4.4, facecolor="#15171c", edgecolor=SILK, lw=1.0, zorder=5))
labels = ["IR_MOD", "VEMIT", "3V3", "GND", "EN"]
for c, lbl in enumerate(labels):
    ax.add_patch(Circle((hx0 + c*2.54, hy), 0.7, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.text(hx0 + c*2.54, hy-2.6, lbl, ha="center", va="top", color=SILK, fontsize=5.8, rotation=90, zorder=6)
ax.text(0, hy+3.0, "→ ESP32-P4 (1×5, 2.54 mm)", ha="center", va="bottom", color=SILK, fontsize=7.5, zorder=6)

# ---- monteringshal M2.5 (4 st pa axlarna, r=27) ----
for a in (0, 90, 180, 270):
    th = np.deg2rad(a)
    ax.add_patch(Circle((27*np.cos(th), 27*np.sin(th)), 1.4, facecolor=CUT, edgecolor="#c98a3a", lw=1.0, zorder=4))

# ---- mattlinjer ----
def dim(r, label, ang):
    th = np.deg2rad(ang)
    ax.annotate("", xy=(r*np.cos(th), r*np.sin(th)), xytext=(0, 0),
                arrowprops=dict(arrowstyle="<->", color="#6fb3ff", lw=1.0), zorder=8)
    ax.text(r*0.55*np.cos(th)+1.2, r*0.55*np.sin(th)+1.2, label, color="#6fb3ff", fontsize=8, zorder=8)
dim(BOARD_R, "Ø60 mm", 57)
ax.annotate("", xy=(EMIT_OFF, EMIT_OFF), xytext=(-EMIT_OFF, EMIT_OFF),
            arrowprops=dict(arrowstyle="<->", color="#6fb3ff", lw=0.9), zorder=8)
ax.text(0, EMIT_OFF+1.0, "emitter-kvadrat 30 mm", ha="center", color="#6fb3ff", fontsize=7.5, zorder=8)

# ---- titel + noter ----
ax.set_title("STRILAS — VAPNETS optikmodul: 4× SFH 4715AS (860 nm) + kamera + driver (topvy)",
             color="#e6edf3", fontsize=12.5, pad=14)
notes = (
    "NOTER\n"
    "• 4× SFH 4715AS (860 nm) i kvadrat runt kameran = SAMBORESIKTAD → siktaxel = IR-axel; de 4 = aktiv fiducial-konstellation\n"
    "• Varje LED i fokus på en kollimator (~±5°) → strålen koncentreras → 100–150 m räckvidd\n"
    "• Driver: 4 LED i serie → Q1 (N-FET) + R1 (sätter & HW-BEGRÄNSAR pulsströmmen = ögonsäkerhet) + C1 (levererar pulsen) + flyback\n"
    "• Mata VEMIT från 2S-batteri / boost (~12 V för serie-strängen). IR_MOD = 56 kHz från P4:ans RMT på gaten\n"
    "• ⚠️ 1–3 A kollimerat: MÄT/räkna accessible emission (Class 1) — R1 är vakten, inte firmware. Sikta 1 A först.\n"
    "• Kameran (OV5640) i mitten: matcha Ø14-öppning + 16 mm hålbild + FFC-läge mot din faktiska P4-modul"
)
ax.text(-BOARD_R-1, -BOARD_R-6, notes, ha="left", va="top", color="#aeb7c2",
        fontsize=8.0, family="monospace", zorder=9,
        bbox=dict(boxstyle="round,pad=0.6", fc="#11151b", ec="#30363d"))

lim = BOARD_R + 5
ax.set_xlim(-lim, lim); ax.set_ylim(-lim-13, lim+3); ax.axis("off")
plt.tight_layout()
out = "hardware/weapon-emitter-camera-860nm.png"
plt.savefig(out, dpi=150, facecolor=fig.get_facecolor())
print("wrote", out)
