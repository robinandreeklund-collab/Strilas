#!/usr/bin/env python3
"""STRILAS — P4-montage sett FRÅN SIDAN (profil), svarar: åt vilket håll är USB-C vänd?

Härlett ur korten: optik J1 = B.Cu, P4 J_B = B.Cu (P4:s BAKSIDA mot optik),
medan P4 J_A (FC), USB-C och ESP ligger på F.Cu (P4:s FRAMSIDA, vänd BORT från optik).
Höjder i mm: USB-C-änden nederst, antenn överst (P4 = 71 mm lång).
Kör: python3 hardware/pinmap_profile.py → vapen-stack/ritningar/p4-montage-profil.png
"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow, FancyBboxPatch

BG="#33404c"; GREEN="#1f6b4a"; GE="#123f2b"; TXT="#eef3f6"; SILV="#c7ced4"; PINY="#d9b44a"; GP="#cfe8ff"
fig, ax = plt.subplots(figsize=(11.5, 13)); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.set_xlim(-12, 42); ax.set_ylim(-12, 82); ax.set_aspect("equal"); ax.axis("off")

# optik (kortet bakom) — tjock bar till vänster
ax.add_patch(Rectangle((-2.0, -2), 2.0, 75, fc=GREEN, ec=GE, lw=2))
ax.text(-7.5, 36, "OPTIK-kortet\n(bakom)", color=TXT, ha="center", va="center", fontsize=12, rotation=90, fontweight="bold")

# P4 — bar en bit framför optik (gap = socket-höjd ~11 mm)
P4X = 13.0
ax.add_patch(Rectangle((P4X, 0), 2.0, 71, fc=GREEN, ec=GE, lw=2))
ax.text(P4X+1, 74.5, "P4 (kant sedd från sidan)", color=TXT, ha="center", va="bottom", fontsize=11, fontweight="bold")

# gap-mått
ax.annotate("", xy=(0, -6), xytext=(P4X, -6), arrowprops=dict(arrowstyle="<->", color=GP, lw=1.5))
ax.text(P4X/2, -8.5, "~11 mm (socket-höjd, lyfts i Fusion)", color=GP, ha="center", va="top", fontsize=9)

# edge B: P4:s BAKSIDA (vänster sida, mot optik) → in i optikens socket. Stiften y≈7..40.
for y in range(8, 41, 4):
    ax.plot([0, P4X], [y, y], color=PINY, lw=1.4, zorder=2)
ax.add_patch(Rectangle((P4X-0.4, 7), 0.9, 34, fc="#11161b", ec="#445", lw=1, zorder=3))   # header-kropp på P4-bak
ax.text((P4X)/2, 47, "edge B – 14 stift\nP4:s BAKSIDA → in i optikens socket\n(B.Cu ↔ B.Cu)",
        color="#bfe6c9", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

# P4:s FRAMSIDA (höger sida, mot dig): USB-C (botten), ESP (topp), FC-stiftlist (mitten)
ax.add_patch(Rectangle((P4X+2, -2.5), 3.4, 7, fc=SILV, ec="#888", lw=1, zorder=3))         # USB-C
ax.text(P4X+8.5, 1, "◀ USB-C\n(nedåt, MOT DIG)", color=TXT, ha="left", va="center", fontsize=10, fontweight="bold")
ax.add_patch(Rectangle((P4X+2, 56), 3.0, 14, fc="#2a7d57", ec=GE, lw=1, zorder=3))          # ESP+antenn
ax.text(P4X+8.5, 63, "◀ ESP32-P4 + antenn\n(uppåt)", color=TXT, ha="left", va="center", fontsize=10, fontweight="bold")
for y in range(18, 45, 4):                                                                  # FC-stiftlist (guldstift) utåt
    ax.plot([P4X+2, P4X+8], [y, y], color=PINY, lw=2.2, zorder=2)
ax.text(P4X+9, 31, "edge A – 12 stift →\nFC STACKAR HÄR\n(de höga guld-stiften\ni din modell, F.Cu)",
        color="#bfe6c9", ha="left", va="center", fontsize=10, fontweight="bold")

# liten "kretsar"-markering på framsidan
for y in (50, 53, 11, 14):
    ax.add_patch(Rectangle((P4X+2, y), 1.6, 1.6, fc="#3a4650", ec="#222", lw=0.5, zorder=3))

# DIN VY-pil
ax.annotate("", xy=(P4X+9, 70), xytext=(33, 70), arrowprops=dict(arrowstyle="->", color="#ffd24a", lw=2.5))
ax.text(34, 70, "DIN VY\n(du ser P4:s\nKOMPONENTSIDA)", color="#ffd24a", ha="left", va="center", fontsize=11, fontweight="bold")

# titel + svar
ax.text(15, 80.5, "Hur P4 sitter på optik — sett från sidan", color=TXT, ha="center", va="center", fontsize=15, fontweight="bold")
ax.text(15, -11, "SVAR: USB-C / ESP / FC-stiftlist ligger på P4:s FRAMSIDA = vänd BORT från optik (mot dig).\n"
        "P4:s BAKSIDA (edge B-listen) går in i optikens socket. USB-C är alltså vänd framåt/nedåt — inte mot optik.",
        color="#bfe6c9", ha="center", va="center", fontsize=10.5, fontweight="bold")

import os; os.makedirs("vapen-stack/ritningar", exist_ok=True)
OUT="vapen-stack/ritningar/p4-montage-profil.png"
fig.savefig(OUT, dpi=150, facecolor=BG, bbox_inches="tight")
print("skrev", OUT)
