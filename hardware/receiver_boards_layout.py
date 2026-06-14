#!/usr/bin/env python3
"""
STRILAS — RECEIVER-/player-kort (väst + hjälm). INGEN kamera.
Två funktioner per kort:
  - TAR EMOT skott: Vishay TSOP4856 (56 kHz) + 940 nm bandpass  (skottet = 940 nm)
  - SYNS för skyttens kamera: 860 nm IR-konstellations-LED i känd geometri (PnP)

Genererar två PNG:
  - vest-detector-patch.png   (rektangulär, placera flera runt torso → zoner)
  - helmet-halo.png           (rund halo ovanpå hjälmen, 360° azimut + huvud-zon)

Placerings-/mekanikritningar för iteration, inte fab-färdiga Gerbers.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch

GREEN, GREEN_ED = "#0e5a2a", "#0a7d39"
PAD, SILK, CUT = "#d9b25a", "#e8f0e8", "#0b0e12"
TSOPC, LEDC = "#2b2f36", "#7a1f1f"

def draw_tsop(ax, x, y, idx, ang=0):
    """TSOP4856 front-facing: kropp + dome (mot betraktaren = utåt) + 3 pads."""
    from matplotlib.transforms import Affine2D
    t = Affine2D().rotate_deg(ang).translate(x, y) + ax.transData
    ax.add_patch(Rectangle((-2.9, -3.0), 5.8, 6.0, facecolor="#15171c", edgecolor=SILK, lw=1.0, transform=t, zorder=5))
    ax.add_patch(Circle((0, 1.4), 1.7, facecolor=TSOPC, edgecolor=SILK, lw=0.8, transform=t, zorder=6))
    for k in (-1, 0, 1):
        ax.add_patch(Rectangle((k*2.54-0.6, -3.7), 1.2, 1.5, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, transform=t, zorder=6))
    ax.text(x, y-0.6, f"S{idx}", ha="center", va="center", color=SILK, fontsize=6.0, fontweight="bold", zorder=7,
            rotation=ang)

def draw_led(ax, x, y, idx):
    """860 nm konstellations-LED + 2 pads."""
    ax.add_patch(Circle((x, y), 2.0, facecolor=LEDC, edgecolor=SILK, lw=1.0, zorder=6))
    ax.add_patch(Circle((x, y), 0.9, facecolor="#c0504d", edgecolor="none", zorder=7))
    ax.add_patch(Rectangle((x-3.4, y-0.7), 1.4, 1.4, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.add_patch(Rectangle((x+2.0, y-0.7), 1.4, 1.4, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.text(x, y+2.6, f"L{idx} 860nm", ha="center", va="bottom", color="#e0a0a0", fontsize=5.4, zorder=7)

def part(ax, x, y, w, h, ref, val):
    ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor="#15171c", edgecolor=SILK, lw=0.9, zorder=5))
    ax.text(x, y+0.2, ref, ha="center", va="center", color=SILK, fontsize=5.6, fontweight="bold", zorder=6)
    ax.text(x, y-h/2-0.5, val, ha="center", va="top", color="#aeb7c2", fontsize=5.0, zorder=6)

def connector(ax, x, y, pins, label):
    n = len(pins)
    ax.add_patch(Rectangle((x-(n-1)*1.27-2, y-1.4), (n-1)*2.54+4, 4.0, facecolor="#15171c", edgecolor=SILK, lw=1.0, zorder=5))
    for c in range(n):
        ax.add_patch(Circle((x-(n-1)*1.27+c*2.54, y), 0.65, facecolor=PAD, edgecolor="#7a5a1e", lw=0.5, zorder=6))
    ax.text(x, y-2.4, label, ha="center", va="top", color=SILK, fontsize=5.4, zorder=6)

# ============================================================ VEST PATCH
def vest_patch():
    BW, BH = 58.0, 42.0
    fig, ax = plt.subplots(figsize=(9.5, 7.6)); ax.set_aspect("equal")
    ax.set_facecolor("#0b0e12"); fig.patch.set_facecolor("#0b0e12")
    ax.add_patch(FancyBboxPatch((-BW/2+3, -BH/2+3), BW-6, BH-6, boxstyle="round,pad=3,rounding_size=4",
                 facecolor=GREEN, edgecolor=GREEN_ED, lw=2.5, zorder=1))
    # 3 TSOP (zon-täckning), front-facing
    for i, x in enumerate((-17, 0, 17)):
        draw_tsop(ax, x, 4, i+1)
    # 2 konstellations-LED i känd diagonal
    draw_led(ax, -22, 15, 1)
    draw_led(ax, 22, -13, 2)
    # OR-dioder + LED-driver
    part(ax, -14, -12, 8, 3.0, "D1–D3", "OR-dioder")
    part(ax, 2, -12, 5, 3.0, "Q1", "LED-drv")
    # kontakt
    connector(ax, 14, -16.5, ["V", "G", "DATA", "LEN"], "J1: VBAT·GND·DATA·LED_EN")
    # monteringshal / sy-hål
    for x, y in [(-25, 17), (25, 17), (-25, -17), (25, -17)]:
        ax.add_patch(Circle((x, y), 1.4, facecolor=CUT, edgecolor="#c98a3a", lw=1.0, zorder=4))
    ax.set_title("STRILAS — VÄST-detektor-patch (placera flera → zoner)", color="#e6edf3", fontsize=11, pad=10)
    notes = ("• S1–S3 TSOP4856 (56 kHz) framåtriktade + 940 nm bandpass → tar emot 940 nm-skottet (zon = vilken patch)\n"
             "• S1–S3 OR:as (D1–D3) → 1 DATA-linje/patch till väst-MCU (C5). L1/L2 = 860 nm-konstellation (PnP), känd diagonal\n"
             "• 58×42 mm, 4 sy-/skruvhål. J1 4-pol (VBAT·GND·DATA·LED_EN); LED_EN delad buss, MCU modulerar blink-ID\n"
             "• Placera ~4–6 runt torso (bröst/rygg/vä/hö) för 360° + zoner. ⚠️ 940 nm filter på TSOP, 860 nm på konstellation — blanda ej")
    ax.text(-BW/2, -BH/2-2, notes, ha="left", va="top", color="#aeb7c2", fontsize=7.2, family="monospace",
            zorder=9, bbox=dict(boxstyle="round,pad=0.6", fc="#11151b", ec="#30363d"))
    ax.set_xlim(-BW/2-3, BW/2+3); ax.set_ylim(-BH/2-15, BH/2+4); ax.axis("off")
    plt.tight_layout(); plt.savefig("hardware/vest-detector-patch.png", dpi=150, facecolor=fig.get_facecolor())
    print("wrote hardware/vest-detector-patch.png")

# ============================================================ HELMET HALO
def helmet_halo():
    R = 50.0; BOLT = 38.0; CENTER = 16.0
    fig, ax = plt.subplots(figsize=(9.5, 10.2)); ax.set_aspect("equal")
    ax.set_facecolor("#0b0e12"); fig.patch.set_facecolor("#0b0e12")
    ax.add_patch(Circle((0, 0), R, facecolor=GREEN, edgecolor=GREEN_ED, lw=2.5, zorder=1))
    # GNSS patch-antenn (uppåt) i centrum — bästa sky-view på hjälmen (full-system, bestyckas senare)
    ax.add_patch(Rectangle((-12, -12), 24, 24, facecolor="#0c2a3a", edgecolor="#3a9ad0", lw=1.5, zorder=4))
    ax.add_patch(Rectangle((-9, -9), 18, 18, facecolor="#103a4f", edgecolor="#3a9ad0", lw=0.7, ls=(0, (3, 3)), zorder=4))
    ax.text(0, 3.0, "GNSS PATCH", ha="center", va="center", color="#7fd0ff", fontsize=7.0, fontweight="bold", zorder=5)
    ax.text(0, -2.5, "~25×25 (uppåt)\nfull-system, ej v1", ha="center", va="center", color=SILK, fontsize=5.2, zorder=5)
    ax.add_patch(Circle((9.5, -9.5), 1.3, facecolor=CUT, edgecolor="#7fd0ff", lw=1.0, zorder=5))
    ax.text(9.5, -11.6, "U.FL→mott.", ha="center", va="top", color="#7fd0ff", fontsize=4.8, zorder=5)
    # 8 TSOP radiellt UTÅT (360° azimut)
    for i in range(8):
        a = i*45
        th = np.deg2rad(a)
        draw_tsop(ax, BOLT*np.cos(th), BOLT*np.sin(th), i+1, ang=a-90)
    # 4 konstellations-LED (860 nm) — hög vantage, syns runtom
    for i, a in enumerate((22.5, 112.5, 202.5, 292.5)):
        th = np.deg2rad(a)
        draw_led(ax, (CENTER+7)*np.cos(th), (CENTER+7)*np.sin(th), i+1)
    # kontakt
    connector(ax, 0, -R+6, ["V", "G", "DATA", "LEN"], "J1: VBAT·GND·DATA·LED_EN")
    for a in (45, 135, 225, 315):
        th = np.deg2rad(a)
        ax.add_patch(Circle(((R-4)*np.cos(th), (R-4)*np.sin(th)), 1.4, facecolor=CUT, edgecolor="#c98a3a", lw=1.0, zorder=4))
    ax.set_title("STRILAS — HJÄLM-halo (8× TSOP 360° + 860 nm-konstellation)", color="#e6edf3", fontsize=11, pad=12)
    notes = ("• 8× TSOP4856 radiellt UTÅT, 45° isär → 360° azimut-täckning för HUVUD-zonen (+ 940 nm bandpass)\n"
             "• 4× 860 nm-konstellations-LED högt placerade → syns för skyttens kamera från många vinklar (PnP)\n"
             "• CENTRUM: GNSS patch-antenn (uppåt) — högsta punkten = bästa sky-view. EN antenn = POSITION (ej heading).\n"
             "   U.FL → GNSS-mottagare på väst-noden. GND-plan under patchen; L-band (1,2–1,6 GHz) störs ej av 56 kHz-IR. EJ v1.\n"
             "• Ø100 mm ring, 4 skruvhål. J1 4-pol (delad DATA + LED_EN). Samma RX-elektronik som väst-patchen (OR:ade TSOP)")
    ax.text(-R, -R-7, notes, ha="left", va="top", color="#aeb7c2", fontsize=7.2, family="monospace",
            zorder=9, bbox=dict(boxstyle="round,pad=0.6", fc="#11151b", ec="#30363d"))
    ax.set_xlim(-R-4, R+4); ax.set_ylim(-R-18, R+4); ax.axis("off")
    plt.tight_layout(); plt.savefig("hardware/helmet-halo.png", dpi=150, facecolor=fig.get_facecolor())
    print("wrote hardware/helmet-halo.png")

if __name__ == "__main__":
    vest_patch(); helmet_halo()
