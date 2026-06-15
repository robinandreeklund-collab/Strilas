#!/usr/bin/env python3
"""STRILAS — monteringsanalys: ESP32-P4-WIFI6 (uppmätt geometri) bakom optikkortet.
Vänster: P4-kortet (71.05×21.00) med 4 uppmätta monteringshål + 2 pinrader.
Höger: optikkortets baksida (54×74) med P4 stackad (centrum @ +13,0, 15 mm standoff),
       3 av P4:ans hål synkade till H5/H6/H7, centrum-kort-hål H4 mellan linserna."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

# --- P4 uppmätt geometri (mm, kortcentrum origo) ---
P4_HW, P4_HH = 35.525, 10.5
PIN1, PITCH, NPIN, ROWY = -31.005, 2.54, 20, 9.28
HOLE_Y, HXL, HXR = 9.15, -34.06, 19.73
P4_HOLES = [(HXL, HOLE_Y), (HXL, -HOLE_Y), (HXR, HOLE_Y), (HXR, -HOLE_Y)]

# P4 placerad bakom optikkortet HUGGANDE VÄNSTERKANTEN (kamerans kabelkontakt sitter
# på baksidans HÖGER → P4 måste vika vänster). Centrum @ (XC,0), längd längs y, bredd längs x.
XC, YC = -16.0, 0.0
def map_hole(u, v):   # P4 lokal (u=längd, v=bredd) -> vapen (x=v+XC, y=u)
    return (v + XC, u + YC)
SYNC = {  # vilka 3 P4-hål -> vilka vapen-standoff (vänsterläge)
    "H5": map_hole(HXL, -HOLE_Y),   # (-25.15, -34.06)  ytterkant-botten
    "H6": map_hole(HXL,  HOLE_Y),   # (-6.85, -34.06)   innerkant-botten
    "H7": map_hole(HXR,  HOLE_Y),   # (-6.85, 19.73)    innerkant-topp
}
SKIP = map_hole(HXR, -HOLE_Y)       # (-25.15, 19.73) — hoppas över (krockar med R2/Rset)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 7), facecolor="white")

# ---------------- vänster: P4-kortet ----------------
a1.add_patch(FancyBboxPatch((-P4_HW, -P4_HH), 2*P4_HW, 2*P4_HH,
             boxstyle="round,pad=0,rounding_size=1.5", fc="#0b6b3a", ec="#06301a", lw=2))
# USB-C
a1.add_patch(Rectangle((-P4_HW-1.5, -4.0), 3.0, 8.0, fc="#aaaaaa", ec="#555", lw=1))
a1.text(-P4_HW-0.2, 6.2, "USB-C", fontsize=7, ha="center")
# ESP-modul (18.27 zon)
a1.add_patch(Rectangle((17.3, -8.5), 35.525-17.3, 17.0, fc="#cfcabc", ec="#777", lw=1))
a1.text((17.3+35.525)/2, 0, "ESP32-P4\nmodul", fontsize=7, ha="center", va="center")
# pinrader
for i in range(NPIN):
    x = PIN1 + i*PITCH
    for y in (ROWY, -ROWY):
        a1.add_patch(Circle((x, y), 0.5, fc="#e6b84d", ec="#7a5a1a", lw=0.3))
a1.add_patch(Circle((PIN1, ROWY+1.6), 0.45, fc="none", ec="#fff", lw=1.0))
a1.text(PIN1, ROWY+2.8, "pin1\n4.52mm", fontsize=6, ha="center", color="#222")
# monteringshål
for (x, y) in P4_HOLES:
    a1.add_patch(Circle((x, y), 1.1, fc="#222", ec="#ff3030", lw=2))
a1.annotate("", xy=(-P4_HW, 12.5), xytext=(P4_HW, 12.5), arrowprops=dict(arrowstyle="<->"))
a1.text(0, 13.3, "71.05 mm", ha="center", fontsize=8)
a1.annotate("", xy=(-P4_HW-3.5, -P4_HH), xytext=(-P4_HW-3.5, P4_HH), arrowprops=dict(arrowstyle="<->"))
a1.text(-P4_HW-4.2, 0, "21.00", ha="center", va="center", rotation=90, fontsize=8)
a1.set_title("ESP32-P4-WIFI6 (uppmätt ur Waveshares måttritning)\n"
             "4 hål: vänster ±34.06 (USB-hörn) • höger +19.73 (ESP-kant), y=±9.15",
             fontsize=8.5)
a1.set_xlim(-44, 40); a1.set_ylim(-16, 16); a1.set_aspect("equal"); a1.axis("off")

# ---------------- höger: optikkortets baksida + P4 ----------------
a2.add_patch(FancyBboxPatch((-27, -37), 54, 74, boxstyle="round,pad=0,rounding_size=2.5",
             fc="#0b6b3a", ec="#06301a", lw=2))
# lins-urtag + emittrar
a2.add_patch(Circle((0, -6), 8, fc="#0a0a0a", ec="#ccc", lw=1)); a2.text(0, -6, "Ø16\nlins", fontsize=6, ha="center", va="center", color="#ddd")
for (ex, ey) in [(-12, 23), (12, 23)]:
    a2.add_patch(Circle((ex, ey), 1.4, fc="#7a0000", ec="#400"))
    a2.add_patch(Circle((ex, ey), 10, fill=False, ec="#888", lw=0.7, ls=":"))
a2.text(0, 31, "emittrar + Carclo 10734", fontsize=6, ha="center", color="#ddd")
# P4 fotavtryck (bakom, streckad) centrum (XC,0), 21 bred (x) × 71 lång (y)
a2.add_patch(Rectangle((XC-P4_HH, -P4_HW), 2*P4_HH, 2*P4_HW, fill=False, ec="#ff3030", lw=1.8, ls="--"))
a2.text(XC, 0, "P4\n(bakom,\n15mm standoff)", fontsize=6.5, ha="center", va="center", color="#ff8080")
# J1 kantkontakt — flyttas till VÄNSTERKANTEN (P4:ans yttre signalrad, x≈-25.3)
a2.add_patch(Rectangle((-26.1, -16.5), 1.6, 33.0, fc="#e6b84d", ec="#7a5a1a"))
a2.text(-23.6, 0, "J1 (ny)", fontsize=7, color="#222", rotation=90, va="center")
# nuvarande vänster-remsa (måste flytta) — markera i rött
for (cx, cy) in [(-24, 18), (-24, 10), (-24, 3), (-24, -4), (-24, -11), (-24, -18)]:
    a2.add_patch(Rectangle((cx-2.5, cy-1.2), 5, 2.4, fill=False, ec="#ff5050", lw=1.0))
a2.text(-24, -23, "kraft/driver-remsa\n(krockar m. J1 → flyttas)", fontsize=5.5,
        ha="center", color="#ff8080")
# synkade standoff-hål
for r, (x, y) in SYNC.items():
    a2.add_patch(Circle((x, y), 1.3, fc="#222", ec="#30ff60", lw=2.5))
    a2.text(x, y-3.0, r, fontsize=7, ha="center", color="#30ff60", weight="bold")
a2.add_patch(Circle((SKIP[0], SKIP[1]), 1.1, fc="none", ec="#ff3030", lw=1.2, ls=":"))
a2.text(SKIP[0], SKIP[1]+2.6, "P4-hål\n(skippas)", fontsize=5.5, ha="center", color="#ff8080")
# centrum-kort-hål H4
a2.add_patch(Circle((0, 28), 1.3, fc="#222", ec="#40c0ff", lw=2.5))
a2.text(0, 25, "H4 (kortfäste)", fontsize=6.5, ha="center", color="#40c0ff")
# hörn-hål
for (x, y) in [(-24, 34), (24, 34), (-22, -34)]:
    a2.add_patch(Circle((x, y), 1.1, fc="#222", ec="#aaa", lw=1.2))
a2.set_title("Optikkortets baksida (54×74) — P4 vid VÄNSTERKANTEN, 3 hål synkade\n"
             "H5(-25.15,-34.06) H6(-6.85,-34.06) H7(-6.85,19.73) • centrum H4(0,28)",
             fontsize=8.5)
a2.set_xlim(-30, 32); a2.set_ylim(-40, 40); a2.set_aspect("equal"); a2.axis("off")

fig.suptitle("STRILAS — ESP32-P4-WIFI6 monteringsanalys (uppmätt geometri, ingen STEP finns)",
             fontsize=12, weight="bold")
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("hardware/p4-mounting-analysis.png", dpi=160, facecolor="white")
print("wrote hardware/p4-mounting-analysis.png")
