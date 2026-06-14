#!/usr/bin/env python3
"""
STRILAS — VAPNETS optikmodul v1 (KOMPLETT).
Precis sikteskamera + IR-skottemitter + IMU + driver pa ETT kort.

Topvy (top view), rund fire-control-modul som klampas pa vapnet:
  - CENTRUM: sikteskamera (OV5640 NoIR + 860 nm IR-pass + TELEFOTO M12) = PRECISIONEN
    (ser malets IR-konstellation -> solvePnP -> baring sub-0.1 grader)
  - RING: 4x SFH 4715AS (860 nm) + Carclo 10195 (~20 mm) kollimator = SKOTTSTRALE
    (LOS + kodad ID, 100-150 m). Samboresiktad: skott foljer kamerans axel.
  - IMU ICM-45686 (host-side attityd, fyller mellan kamerabildrutor + rekyl)
  - emitter-driver: N-FET + Rsense (HW-stromgrans = ogonsakerhet) + reservoarcap + flyback
  - kontakt mot ESP32-P4: IR_MOD, VEMIT, EN, 3V3, GND + I2C (SDA/SCL); kamera via FFC

Placerings-/mekanikritning for iteration, inte fab-fardiga Gerbers.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

BOARD_R   = 40.0           # Ø80 mm (stort: 4x Ø20 optik runt en 25x24 kamera)
EMIT_OFF  = 21.0           # emitter-position (+/-21, +/-21)
LENS_R    = 10.0           # Carclo 10195 ~Ø20 mm
CAM_W, CAM_H = 25.0, 24.0  # OV5640-modul (mat din egen!)
CAM_BARREL = 9.0           # telefoto-M12-barrel radie (Ø18)
CAM_HOLE_X, CAM_HOLE_Y = 21.0, 19.0

GREEN, GREEN_ED = "#0e5a2a", "#0a7d39"
PAD, SILK, CUT  = "#d9b25a", "#e8f0e8", "#0b0e12"
IRC, LENSC, CAMC = "#7a1f1f", "#3a6ea5", "#00bcd4"

fig, ax = plt.subplots(figsize=(11.5, 12.6))
ax.set_aspect("equal"); ax.set_facecolor("#0b0e12"); fig.patch.set_facecolor("#0b0e12")

# ---- kort + samboresikt-kors ----
ax.add_patch(Circle((0, 0), BOARD_R, facecolor=GREEN, edgecolor=GREEN_ED, lw=2.5, zorder=1))
ax.plot([-BOARD_R, BOARD_R], [0, 0], color="#243044", lw=0.7, ls=":", zorder=1)
ax.plot([0, 0], [-BOARD_R, BOARD_R], color="#243044", lw=0.7, ls=":", zorder=1)

# ---- central sikteskamera (telefoto) ----
ax.add_patch(Rectangle((-CAM_W/2, -CAM_H/2), CAM_W, CAM_H, facecolor="#10212a",
                       edgecolor=SILK, lw=1.3, zorder=3))
ax.add_patch(Circle((0, 0), CAM_BARREL+1.4, facecolor="#0c1418", edgecolor=CAMC, lw=1.4, zorder=4))
ax.add_patch(Circle((0, 0), CAM_BARREL, facecolor=CUT, edgecolor=SILK, lw=1.3, zorder=5))
ax.text(0, 1.2, "SIKTESKAMERA", ha="center", va="center", color=CAMC, fontsize=6.6, fontweight="bold", zorder=6)
ax.text(0, -2.2, "OV5640 NoIR\n860nm IR-pass\nTELEFOTO M12", ha="center", va="center", color=SILK, fontsize=5.8, zorder=6)
for sx in (-1, 1):
    for sy in (-1, 1):
        ax.add_patch(Circle((sx*CAM_HOLE_X/2, sy*CAM_HOLE_Y/2), 1.0, facecolor=CUT, edgecolor="#c98a3a", lw=1.0, zorder=6))
ax.add_patch(Rectangle((-8, CAM_H/2 - 2.2), 16, 2.2, facecolor="#1c1c22", edgecolor=SILK, lw=0.8, zorder=4))
ax.text(0, CAM_H/2 + 1.0, "FFC → P4 MIPI-CSI", ha="center", va="bottom", color=SILK, fontsize=7, zorder=6)

# ---- 4x SFH 4715AS (860 nm) + Carclo-kollimator (skottstrale) ----
def draw_emitter(ax, x, y, idx):
    ax.add_patch(Circle((x, y), LENS_R, facecolor="none", edgecolor=LENSC, lw=1.8, zorder=5))
    ax.add_patch(Circle((x, y), LENS_R-2.0, facecolor="none", edgecolor=LENSC, lw=0.8, ls=":", zorder=5))
    # 3 Carclo-ben (pins) i PCB
    for ba in (90, 210, 330):
        bx, by = x + (LENS_R-0.8)*np.cos(np.deg2rad(ba)), y + (LENS_R-0.8)*np.sin(np.deg2rad(ba))
        ax.add_patch(Circle((bx, by), 0.7, facecolor=CUT, edgecolor=LENSC, lw=0.8, zorder=6))
    ax.add_patch(Rectangle((x-1.9, y-1.9), 3.8, 3.8, facecolor=IRC, edgecolor=SILK, lw=1.0, zorder=6))
    ax.add_patch(Rectangle((x-3.3, y-0.8), 1.4, 1.6, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.add_patch(Rectangle((x+1.9, y-0.8), 1.4, 1.6, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.text(x, y + (LENS_R+0.4 if y > 0 else -LENS_R-0.4), f"D{idx} SFH4715AS",
            ha="center", va="bottom" if y > 0 else "top", color=SILK, fontsize=6.4, zorder=6)

for i, (x, y) in enumerate([(-EMIT_OFF, EMIT_OFF), (EMIT_OFF, EMIT_OFF),
                            (-EMIT_OFF, -EMIT_OFF), (EMIT_OFF, -EMIT_OFF)]):
    draw_emitter(ax, x, y, i+1)

# ---- IMU (under kameran, pa boresight-axeln) ----
ax.add_patch(Rectangle((-3, -19.5), 6, 5, facecolor="#1d2530", edgecolor=SILK, lw=1.0, zorder=5))
ax.text(0, -17.0, "U2", ha="center", va="center", color=SILK, fontsize=6.4, fontweight="bold", zorder=6)
ax.text(0, -21.0, "ICM-45686 IMU (I²C)", ha="center", va="top", color="#aeb7c2", fontsize=6.0, zorder=6)

# ---- emitter-driver (fria center-botten) ----
def part(ax, x, y, w, h, ref, val):
    ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor="#15171c", edgecolor=SILK, lw=0.9, zorder=5))
    ax.text(x, y+0.2, ref, ha="center", va="center", color=SILK, fontsize=6.2, fontweight="bold", zorder=6)
    ax.text(x, y-h/2-0.5, val, ha="center", va="top", color="#aeb7c2", fontsize=5.6, zorder=6)
part(ax, -9.0, -26.0, 4.4, 3.2, "Q1", "AO3400")
part(ax,  0.0, -26.0, 4.2, 3.0, "R1", "Rsense")
part(ax,  9.0, -26.0, 4.8, 4.6, "C1", "220 µF")
part(ax, -6.0, -30.5, 3.0, 2.2, "Rg", "220 Ω")
part(ax,  3.0, -30.5, 3.4, 2.2, "D5", "SS54")

# ---- kontakt mot P4 (2x4) ----
hy = -35.0; hx0 = -1.5*2.54
ax.add_patch(Rectangle((hx0-2, hy-1.6), 2.54*3+4, 2.54+3.2, facecolor="#15171c", edgecolor=SILK, lw=1.0, zorder=5))
top = ["IR_MOD", "VEMIT", "EN", "GND"]; bot = ["3V3", "SDA", "SCL", "GND"]
for c in range(4):
    ax.add_patch(Circle((hx0 + c*2.54, hy+2.54), 0.7, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.add_patch(Circle((hx0 + c*2.54, hy), 0.7, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
ax.text(hx0 + 1.5*2.54, hy-2.6, "J1 (2×4): IR_MOD·VEMIT·EN·GND / 3V3·SDA·SCL·GND",
        ha="center", va="top", color=SILK, fontsize=6.2, zorder=6)

# ---- board-monteringshal (N/E/V) ----
for x, y in [(0, 37), (37, 0), (-37, 0)]:
    ax.add_patch(Circle((x, y), 1.4, facecolor=CUT, edgecolor="#c98a3a", lw=1.0, zorder=4))

# ---- mattlinjer ----
th = np.deg2rad(56)
ax.annotate("", xy=(BOARD_R*np.cos(th), BOARD_R*np.sin(th)), xytext=(0, 0),
            arrowprops=dict(arrowstyle="<->", color="#6fb3ff", lw=1.0), zorder=8)
ax.text(BOARD_R*0.5*np.cos(th)+1, BOARD_R*0.5*np.sin(th)+1, "Ø80 mm", color="#6fb3ff", fontsize=8, zorder=8)
ax.annotate("", xy=(EMIT_OFF, EMIT_OFF+11), xytext=(-EMIT_OFF, EMIT_OFF+11),
            arrowprops=dict(arrowstyle="<->", color="#6fb3ff", lw=0.9), zorder=8)
ax.text(0, EMIT_OFF+11.5, "emitter-kvadrat 42 mm (Carclo 10195 Ø20)", ha="center", color="#6fb3ff", fontsize=7, zorder=8)

# ---- titel + noter ----
ax.set_title("STRILAS — VAPNETS optikmodul v1: precis sikteskamera + 4× IR-emitter + IMU + driver",
             color="#e6edf3", fontsize=12, pad=12)
notes = (
    "NOTER\n"
    "• PRECISION = sikteskameran (NoIR + 860 nm IR-pass + telefoto M12) ser målets IR-konstellation → solvePnP → bäring sub-0.1°\n"
    "• SKOTT = 4× SFH 4715AS (860 nm) + Carclo 10195-kollimator, samboresiktad → kodad 56 kHz-stråle, 100–150 m (bred kon = bara LOS/ID)\n"
    "   – v1: bestycka 1–2 för skottet räcker; 4 = full ring (redundans + framtida aktiv-fiducial-beacon)\n"
    "• ⚠️ KAMERAN SER SINA EGNA 860 nm-EMITTRAR → lös med: (a) baffel mellan ring & lins + (b) emittrar avfyras BARA vid trigger\n"
    "   (kameran läser konstellationen mellan skott), ELLER (c) emitter på 940 nm + kamera-filter 860 nm = ren separation\n"
    "• Driver: Q1 + R1 (sätter & HW-BEGRÄNSAR pulsström = ögonsäkerhet, MÄT Class 1) + C1 (pulsen) + flyback; VEMIT från 2S/boost\n"
    "• IMU U2 på boresight-axeln (host-side attityd, fyller mellan bildrutor). Kamera = P4-stödd sensor (IMX296 funkar EJ på P4)\n"
    "• Mät din kameramodul → CAM_W/H/HOLE; Ø80 är stort (4× Ø20-optik) — färre emittrar/role-split → mindre kort"
)
ax.text(-BOARD_R-1, -BOARD_R-3, notes, ha="left", va="top", color="#aeb7c2",
        fontsize=7.6, family="monospace", zorder=9,
        bbox=dict(boxstyle="round,pad=0.6", fc="#11151b", ec="#30363d"))

lim = BOARD_R + 5
ax.set_xlim(-lim, lim); ax.set_ylim(-lim-15, lim+5); ax.axis("off")
plt.tight_layout()
out = "hardware/weapon-emitter-camera-860nm.png"
plt.savefig(out, dpi=150, facecolor=fig.get_facecolor())
print("wrote", out)
