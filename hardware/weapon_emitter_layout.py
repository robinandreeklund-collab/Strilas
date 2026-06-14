#!/usr/bin/env python3
"""
STRILAS — PCB-placeringsritning: VAPNETS optikmodul.
IR-emitter (860 nm) + sikteskamera + driver/strömgräns på ETT kort.

Topvy (top view) av en rund modul som klampas på vapnet:
  - 4x ams-OSRAM SFH 4715AS (860 nm) i kvadrat runt kameran (SAMBORESIKTAD ring)
    -> siktaxel = IR-axel, och de 4 utgor en aktiv fiducial-konstellation
  - central P4-stodd kameramodul (OV5640 ~25x24 mm, M12-lins; eller GS Mira220)
  - emitter-driver ombord: N-FET + stromsattnings-/sense-resistor (HW-stromgrans
    = ogonsakerhet) + reservoarkondensator + gate-resistor + flyback/TVS
  - kollimator-lins (~+/-5 grader) over varje LED -> 100-150 m rackvidd
  - kontakt mot ESP32-P4: IR_MOD (56 kHz fran RMT), VEMIT, 3V3, GND, EN

OBS: IMX296 funkar INTE pa P4 (Pi-only, ingen esp_cam_sensor-drivrutin).
Placerings-/mekanikritning for iteration, inte fab-fardiga Gerbers.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

BOARD_R   = 34.0      # Ø68 mm
EMIT_OFF  = 18.0      # emitter-position (x,y) = (+/-18, +/-18)
LENS_R    = 5.5       # kollimator-lins-radie (Ø11)
CAM_W, CAM_H = 25.0, 24.0   # realistisk OV5640-modul (mat din egen!)
CAM_LENS  = 8.0       # M12-lins-barrel radie (Ø16)
CAM_HOLE_X, CAM_HOLE_Y = 21.0, 12.5   # kamera-monteringshal centrum-avstand

GREEN, GREEN_ED = "#0e5a2a", "#0a7d39"
PAD, SILK, CUT  = "#d9b25a", "#e8f0e8", "#0b0e12"
IRC, LENSC      = "#7a1f1f", "#3a6ea5"

fig, ax = plt.subplots(figsize=(11, 11.8))
ax.set_aspect("equal"); ax.set_facecolor("#0b0e12"); fig.patch.set_facecolor("#0b0e12")

# ---- kort-outline + samboresikt-kors ----
ax.add_patch(Circle((0, 0), BOARD_R, facecolor=GREEN, edgecolor=GREEN_ED, lw=2.5, zorder=1))
ax.plot([-BOARD_R, BOARD_R], [0, 0], color="#243044", lw=0.7, ls=":", zorder=1)
ax.plot([0, 0], [-BOARD_R, BOARD_R], color="#243044", lw=0.7, ls=":", zorder=1)

# ---- central kameramodul (realistisk ~25x24 mm) ----
ax.add_patch(Rectangle((-CAM_W/2, -CAM_H/2), CAM_W, CAM_H, facecolor="#10212a",
                       edgecolor=SILK, lw=1.3, zorder=3))
# M12-lins-barrel
ax.add_patch(Circle((0, 0), CAM_LENS+1.2, facecolor="#0c1418", edgecolor=SILK, lw=1.0, zorder=4))
ax.add_patch(Circle((0, 0), CAM_LENS, facecolor=CUT, edgecolor=SILK, lw=1.4, zorder=5))
ax.text(0, 0, "KAMERA\nOV5640\n(M12)", ha="center", va="center", color=SILK, fontsize=7.2, zorder=6)
# 4 kamera-monteringshal
for sx in (-1, 1):
    for sy in (-1, 1):
        ax.add_patch(Circle((sx*CAM_HOLE_X/2, sy*CAM_HOLE_Y/2), 1.0, facecolor=CUT,
                            edgecolor="#c98a3a", lw=1.0, zorder=6))
# FFC-kontakt (topp av modulen)
ax.add_patch(Rectangle((-8, CAM_H/2 - 2.2), 16, 2.2, facecolor="#1c1c22", edgecolor=SILK, lw=0.8, zorder=4))
ax.text(0, CAM_H/2 + 1.2, "FFC → P4 MIPI-CSI", ha="center", va="bottom", color=SILK, fontsize=7, zorder=6)

# ---- 4x SFH 4715AS (860 nm) + kollimator i kvadrat (hornen) ----
def draw_emitter(ax, x, y, idx):
    ax.add_patch(Circle((x, y), LENS_R, facecolor="none", edgecolor=LENSC, lw=1.6, zorder=5))
    ax.add_patch(Circle((x, y), LENS_R-1.4, facecolor="none", edgecolor=LENSC, lw=0.8, ls=":", zorder=5))
    ax.add_patch(Rectangle((x-1.9, y-1.9), 3.8, 3.8, facecolor=IRC, edgecolor=SILK, lw=1.0, zorder=6))
    ax.add_patch(Rectangle((x-1.9-1.4, y-0.8), 1.4, 1.6, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.add_patch(Rectangle((x+1.9, y-0.8), 1.4, 1.6, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    lbl_y = y + LENS_R + 0.4 if y > 0 else y - LENS_R - 0.4
    ax.text(x, lbl_y, f"D{idx} SFH4715AS", ha="center",
            va="bottom" if y > 0 else "top", color=SILK, fontsize=6.6, zorder=6)

for i, (x, y) in enumerate([(-EMIT_OFF, EMIT_OFF), (EMIT_OFF, EMIT_OFF),
                            (-EMIT_OFF, -EMIT_OFF), (EMIT_OFF, -EMIT_OFF)]):
    draw_emitter(ax, x, y, i+1)

# ---- emitter-driver (nedre fria bagen, mellan de tva nedre emittrarna) ----
def part(ax, x, y, w, h, ref, val):
    ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor="#15171c", edgecolor=SILK, lw=0.9, zorder=5))
    ax.text(x, y+0.2, ref, ha="center", va="center", color=SILK, fontsize=6.4, fontweight="bold", zorder=6)
    ax.text(x, y-h/2-0.5, val, ha="center", va="top", color="#aeb7c2", fontsize=5.8, zorder=6)

part(ax, -8.0, -23.0, 4.5, 3.2, "Q1", "AO3400")
part(ax,  0.0, -23.0, 4.2, 3.0, "R1", "Rsense 1–3 Ω")
part(ax,  8.0, -23.0, 4.8, 4.6, "C1", "220 µF")
part(ax, -4.0, -27.0, 3.0, 2.4, "Rg", "220 Ω")
part(ax,  4.0, -27.0, 3.6, 2.4, "D5", "SS54")

# ---- kontakt mot P4 (1x5), langst ner ----
hy = -31.0; hx0 = -2*2.54
ax.add_patch(Rectangle((hx0-2, hy-1.8), 2.54*4+4, 4.0, facecolor="#15171c", edgecolor=SILK, lw=1.0, zorder=5))
for c, lbl in enumerate(["IR_MOD", "VEMIT", "3V3", "GND", "EN"]):
    ax.add_patch(Circle((hx0 + c*2.54, hy), 0.7, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.text(hx0 + c*2.54, hy-2.3, lbl, ha="center", va="top", color=SILK, fontsize=5.6, rotation=90, zorder=6)
ax.text(15, hy, "→ ESP32-P4 (1×5)", ha="left", va="center", color=SILK, fontsize=7.5, zorder=6)

# ---- board-monteringshal M2.5 (N/E/S/V mellan emittrarna) ----
for x, y in [(0, 31), (31, 0), (-31, 0)]:
    ax.add_patch(Circle((x, y), 1.4, facecolor=CUT, edgecolor="#c98a3a", lw=1.0, zorder=4))

# ---- mattlinjer ----
def dim(r, label, ang):
    th = np.deg2rad(ang)
    ax.annotate("", xy=(r*np.cos(th), r*np.sin(th)), xytext=(0, 0),
                arrowprops=dict(arrowstyle="<->", color="#6fb3ff", lw=1.0), zorder=8)
    ax.text(r*0.5*np.cos(th)+1.2, r*0.5*np.sin(th)+1.2, label, color="#6fb3ff", fontsize=8, zorder=8)
dim(BOARD_R, "Ø68 mm", 57)
ax.annotate("", xy=(-CAM_W/2, CAM_H/2+3.5), xytext=(CAM_W/2, CAM_H/2+3.5),
            arrowprops=dict(arrowstyle="<->", color="#9bd49b", lw=0.9), zorder=8)
ax.text(0, CAM_H/2+4.2, "kamera ~25×24 mm (mät din modul)", ha="center", color="#9bd49b", fontsize=7, zorder=8)
ax.annotate("", xy=(EMIT_OFF, EMIT_OFF+7), xytext=(-EMIT_OFF, EMIT_OFF+7),
            arrowprops=dict(arrowstyle="<->", color="#6fb3ff", lw=0.9), zorder=8)
ax.text(0, EMIT_OFF+7.6, "emitter-kvadrat 36 mm", ha="center", color="#6fb3ff", fontsize=7.5, zorder=8)

# ---- titel + noter ----
ax.set_title("STRILAS — VAPNETS optikmodul: 4× SFH 4715AS (860 nm) + kamera + driver (topvy)",
             color="#e6edf3", fontsize=12.5, pad=14)
notes = (
    "NOTER\n"
    "• 4× SFH 4715AS (860 nm) i kvadrat runt kameran = SAMBORESIKTAD → siktaxel = IR-axel; de 4 = aktiv fiducial-konstellation\n"
    "• Varje LED i fokus på en kollimator (~±5°) → 100–150 m räckvidd\n"
    "• Driver: 4 LED i serie → Q1 (N-FET) + R1 (sätter & HW-BEGRÄNSAR pulsströmmen = ögonsäkerhet) + C1 (levererar pulsen) + flyback\n"
    "• VEMIT från 2S-batteri / boost (~12 V för serie-strängen); IR_MOD = 56 kHz från P4:ans RMT på gaten\n"
    "• ⚠️ 1–3 A kollimerat: MÄT/räkna accessible emission (Class 1) — R1 är vakten, inte firmware. Sikta 1 A först.\n"
    "• Kamera = P4-STÖDD sensor: OV5640 (v1, i kitet) eller GS Mira220. IMX296 funkar INTE på P4. Mät din modul → CAM_W/H/HOLE."
)
ax.text(-BOARD_R-1, -BOARD_R-3, notes, ha="left", va="top", color="#aeb7c2",
        fontsize=7.9, family="monospace", zorder=9,
        bbox=dict(boxstyle="round,pad=0.6", fc="#11151b", ec="#30363d"))

lim = BOARD_R + 5
ax.set_xlim(-lim, lim); ax.set_ylim(-lim-13, lim+5); ax.axis("off")
plt.tight_layout()
out = "hardware/weapon-emitter-camera-860nm.png"
plt.savefig(out, dpi=150, facecolor=fig.get_facecolor())
print("wrote", out)
