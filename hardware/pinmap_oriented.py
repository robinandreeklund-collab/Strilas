#!/usr/bin/env python3
"""STRILAS — FYSISK, SKALENLIG pin-karta för P4 (orienterad som Fusion-modellen).

Komplement till pinmap_proof.py (logiska strecken). Denna ritar P4 i SAMMA vy som
3D-modellen — USB-C nedåt, WiFi/BT-antenn uppåt, FC-sidan (edge A) till höger,
optik-sidan (edge B) till vänster — med kortets igenkännbara delar (USB-C, antenn,
kamera-kontakt J_CAM, 4 monteringshål) på sina RIKTIGA platser, och varje
kantkontakt-stift utritat där det faktiskt sitter + vad det är/går till.

Allt ur de faktiska korten (board-rel mm). Kör:
  python3 hardware/pinmap_oriented.py  → vapen-stack/ritningar/p4-pinmap-fysisk.png
"""
import pcbnew
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

EDGE_A = [None, "GPIO52", "GPIO51", "GND", "GPIO31", "GPIO30", "GPIO29", "GPIO28", "GND",
          "GPIO50", "GPIO49", "GPIO5", "GPIO4", "GND", "GPIO3", "GPIO2", "GPIO8", "GPIO7",
          "GND", "GPIO24", "GPIO25"]
EDGE_B = [None, "VBUS", "VSYS", "GND", "EN", "3V3", "GPIO20", "GPIO21", "GND", "GPIO22",
          "GPIO23", "RUN", "GPIO26", "GND", "GPIO27", "GPIO32", "GPIO33", "GPIO46", "GND",
          "GPIO47", "GPIO48"]
OX, OY = 150.0, 120.0

def jnets(path, ref):
    b = pcbnew.LoadBoard(path)
    f = [g for g in b.GetFootprints() if g.GetReference() == ref][0]
    return {int(p.GetName()): p.GetNetname() for p in f.Pads()}
OJ = jnets("hardware/weapon-module.kicad_pcb", "J1")   # optik J1.k -> net
FJ = jnets("hardware/firecontrol.kicad_pcb", "J1")     # FC   J1.k -> net

# J_A pad k @ x = -18.31 + (k-1)*2.54, y=+8.89  → Waveshare edge A pin (k+5), FC J1.k
# J_B pad k @ x = -28.47 + (k-1)*2.54, y=-8.89  → Waveshare edge B pin (16-k), optik J1.k
edgeA = [(k, -18.31 + (k-1)*2.54, EDGE_A[k+5], FJ.get(k) or "—(NC)", k+5) for k in range(1, 13)]
edgeB = [(k, -28.47 + (k-1)*2.54, EDGE_B[16-k], OJ.get(k) or "—(NC)", 16-k) for k in range(1, 15)]

def kind(net, gpio):
    g = (net or "").upper()
    if "GND" in g or gpio == "GND": return "gnd"
    if g in ("VBAT", "+3V3", "3V3", "VSYS") or gpio in ("VSYS", "3V3", "VBUS"): return "pwr"
    if net in ("—(NC)", "", None): return "nc"
    return "sig"

# ---------- rita (board→skärm: REN ROTATION 90° moturs = riktig framsidesvy, USB-C ner) ----------
BG="#33404c"; GREEN="#1f6b4a"; GE="#123f2b"; TXT="#eef3f6"; PIN="#d9b44a"
DARK="#20262d"; SILV="#c7ced4"; GP="#cfe8ff"
COL={"gnd":"#9aa4ad","pwr":"#e0533d","nc":"#7d8a96","sig":"#39c6c0"}
S = lambda bx, by: (-by, bx)                     # rotation (det=+1), EJ spegling → framsida
fig, ax = plt.subplots(figsize=(15.5, 13)); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.set_aspect("equal"); ax.set_xlim(-60, 60); ax.set_ylim(-44, 46); ax.axis("off")

def brect(x0, x1, y0, y1, **kw):                 # rektangel i board-koord
    (sx0, sy0), (sx1, sy1) = S(x0, y0), S(x1, y1)
    ax.add_patch(Rectangle((min(sx0,sx1), min(sy0,sy1)), abs(sx1-sx0), abs(sy1-sy0), **kw))

# P4-kort + delar
ax.add_patch(FancyBboxPatch(S(-35.55,-10.55), 21.1, 71.1, boxstyle="round,pad=0,rounding_size=1.5",
             fc=GREEN, ec=GE, lw=2, zorder=1))
brect(-35.6, -32.0, -4.6, 4.6, fc=SILV, ec="#888", lw=1, zorder=3)          # USB-C-tabb (botten)
ax.text(*S(-37.6, 0), "USB-C\n(botten)", color=TXT, ha="center", va="center", fontsize=9, rotation=90, fontweight="bold")
brect(16.5, 34.5, -9.0, 9.0, fc="#2a7d57", ec=GE, lw=1, zorder=2)            # ESP+antenn-zon (topp)
ax.text(*S(25.5, 0), "ESP32-P4-WIFI6\nmodul + WiFi/BT-antenn", color=TXT, ha="center", va="center", fontsize=9, rotation=90, fontweight="bold")
brect(-11, 3, -2.6, 2.6, fc="#11161b", ec="#445", lw=1, zorder=3)            # kamera-kontakt (mitten)
ax.text(*S(-4, 0), "kamera\nJ_CAM", color=GP, ha="center", va="center", fontsize=7.5, rotation=90)
for (mx,my),lbl in [((-34.10,9.12),"MP1"),((-34.10,-9.12),"MP2"),((20.07,9.12),"MP3"),((20.07,-9.12),"MP4")]:
    sx,sy=S(mx,my); ax.add_patch(Circle((sx,sy),1.0,fc=BG,ec=SILV,lw=1.4,zorder=3))

def stub(bx, by, color):
    sx, sy = S(bx, by); ax.add_patch(Rectangle((sx-0.7, sy-0.7), 1.4, 1.4, fc=color, ec="none", zorder=4))

# framsidesvy: edge A (y=+8.89) hamnar till VÄNSTER → FC ;  edge B (y=-8.89) till HÖGER → optik
for k, bx, gpio, net, wp in edgeA:                            # VÄNSTER (FC, 12 stift)
    c = COL[kind(net, gpio)]; sx, sy = S(bx, 8.89)
    stub(bx, 8.89, PIN); ax.plot([sx, -22], [sy, sy], color=c, lw=1.6, zorder=2)
    ax.text(-22.6, sy, f"FC J1.{k} · {net}   ←   {gpio} · pin{wp}", color=TXT, ha="right", va="center", fontsize=9)
for k, bx, gpio, net, wp in edgeB:                            # HÖGER (optik, 14 stift)
    c = COL[kind(net, gpio)]; sx, sy = S(bx, -8.89)
    stub(bx, -8.89, PIN); ax.plot([sx, 22], [sy, sy], color=c, lw=1.6, zorder=2)
    ax.text(22.6, sy, f"pin{wp} · {gpio}   →   optik J1.{k} · {net}", color=TXT, ha="left", va="center", fontsize=9)

# kant-rubriker
ax.text(-32, 40, "◀  edge A – 12 stift  →  FC\n(FC stackar här)", color="#bfe6c9", ha="center", va="center", fontsize=11, fontweight="bold")
ax.text(30, 40, "edge B – 14-stift  →  OPTIK  ▶\n(in i optikens socket, kortet bakom)", color="#bfe6c9", ha="center", va="center", fontsize=11, fontweight="bold")
ax.text(0, 45.5, "STRILAS — P4 fysisk pin-karta (samma vy som din Fusion-modell)", color=TXT, ha="center", va="center", fontsize=15, fontweight="bold")
ax.text(0, 42.7, "Vy = P4:s KOMPONENTSIDA mot dig (USB-C/ESP/FC-stift på denna sida, vänd BORT från optik). Baksidan = edge B in i optikens socket.",
        color="#9fb0bd", ha="center", va="center", fontsize=8.5)
ax.text(0, -41.5, "pin 1 på varje kant = NÄRMAST USB-C (botten) · stigande stiftnr uppåt mot antennen · "
        "färg: signal / GND / kraft / NC", color="#9fb0bd", ha="center", va="center", fontsize=9.5)
ax.text(0, -38.0, "P4-modulen har 20 stift/kant; vapen-carriern kontaktar bara dessa 14 (edge B) + 12 (edge A) — "
        "övriga module-stift lediga (se p4-pinmap-proof.png).", color="#7f8b96", ha="center", va="center", fontsize=8.5, style="italic")
# liten färglegend
for i,(lbl,kk) in enumerate([("signal","sig"),("GND","gnd"),("kraft","pwr"),("NC/ej driven","nc")]):
    x=-26+i*15; ax.plot([x,x+2],[-44,-44],color=COL[kk],lw=2.4); ax.text(x+2.4,-44,lbl,color=TXT,va="center",fontsize=9)

import os; os.makedirs("vapen-stack/ritningar", exist_ok=True)
OUT="vapen-stack/ritningar/p4-pinmap-fysisk.png"
fig.savefig(OUT, dpi=150, facecolor=BG, bbox_inches="tight")
print("skrev", OUT)
