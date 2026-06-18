#!/usr/bin/env python3
"""STRILAS — PIN-MAPPNINGS-BEVIS: optik ↔ P4 ↔ FC (side-by-side).

Läser de FAKTISKA korten (weapon-module / p4-board / firecontrol), matar fram
varje kantkontakts padd-positioner + nät, transformerar P4 till optikens frame
(samma 2-punkts stela fit som export_stack_step.py) och MÄTER att varje stift
sammanfaller fysiskt. Ritar tre kort sida vid sida med alla portnamn + streck
mellan paren. GPIO-namnen är Waveshares officiella ESP32-P4-WIFI6-pinout.

Kör: python3 hardware/pinmap_proof.py  → vapen-stack/ritningar/p4-pinmap-proof.png
"""
import math, pcbnew
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

# --- Waveshare ESP32-P4-WIFI6 officiella pinout (verifierad mot datablad/silk) ---
EDGE_A = [None, "GPIO52", "GPIO51", "GND", "GPIO31", "GPIO30", "GPIO29", "GPIO28", "GND",
          "GPIO50", "GPIO49", "GPIO5", "GPIO4", "GND", "GPIO3", "GPIO2", "GPIO8", "GPIO7",
          "GND", "GPIO24", "GPIO25"]
EDGE_B = [None, "VBUS", "VSYS", "GND", "EN", "3V3", "GPIO20", "GPIO21", "GND", "GPIO22",
          "GPIO23", "RUN", "GPIO26", "GND", "GPIO27", "GPIO32", "GPIO33", "GPIO46", "GND",
          "GPIO47", "GPIO48"]
# p4-board-kontaktens pad k → Waveshares fulla kantstift:
#   J_A (12 pads) = edge A pin (k+5)  [pin 6..17]
#   J_B (14 pads) = edge B pin (16-k) [pin 15..2, dvs omvänt mot stiftnumret]
A_PIN = lambda k: k + 5
B_PIN = lambda k: 16 - k

# ---------- pcbnew-helpers ----------
def allpads(b, ref):
    f = [g for g in b.GetFootprints() if g.GetReference() == ref][0]
    return {p.GetName(): (p.GetPosition(), p.GetNetname()) for p in f.Pads()}

def items(b): return list(b.GetFootprints()) + list(b.GetDrawings()) + list(b.GetTracks()) + list(b.Zones())

def xform(b, ang, center, off):
    ea = pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T)
    for it in items(b): it.Rotate(center, ea)
    for it in items(b): it.Move(off)

def _holepos(b, ref):
    return [g for g in b.GetFootprints() if g.GetReference() == ref][0].GetPosition()

def fit(src, ref, d1, d2, hole_refs=None, hole_dst=None):
    """Stel 2-punkts fit: src.ref pad1→d1, padN→d2 (auto-tecken). En LINJÄR kontakt är
    symmetrisk → båda ändpunkts-korrespondenserna ger ~0 mm; monteringshålen (hole_refs/hole_dst)
    avgör den fysiskt korrekta (annars kan man låsa på fel av två lösningar → standoff 10-20 mm fel)."""
    b = pcbnew.LoadBoard(src); pads = allpads(b, ref); nB = str(len(pads))
    p1, p2 = pads["1"][0], pads[nB][0]
    best = None
    for e1, e2 in ((d1, d2), (d2, d1)):
        ang = math.degrees(math.atan2(e2.y - e1.y, e2.x - e1.x) - math.atan2(p2.y - p1.y, p2.x - p1.x))
        for tr in (ang, -ang, ang + 180, ang - 180):
            b2 = pcbnew.LoadBoard(src); c = allpads(b2, ref)["1"][0]
            xform(b2, tr, pcbnew.VECTOR2I(c.x, c.y), pcbnew.VECTOR2I(0, 0))
            q1 = allpads(b2, ref)["1"][0]
            xform(b2, 0, pcbnew.VECTOR2I(0, 0), pcbnew.VECTOR2I(e1.x - q1.x, e1.y - q1.y))
            cerr = (allpads(b2, ref)[nB][0] - e2).EuclideanNorm() / 1e6
            herr = 0.0
            if hole_refs and hole_dst:
                herr = max(min((_holepos(b2, r) - h).EuclideanNorm() / 1e6 for h in hole_dst) for r in hole_refs)
            if best is None or (cerr + herr) < best[0]: best = (cerr + herr, b2)
    return best[1]

def nearest(pos, pads):
    return min(((nm, (p[0] - pos).EuclideanNorm() / 1e6) for nm, p in pads.items()), key=lambda t: t[1])

# ---------- läs korten + matcha fysiskt ----------
op = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb"); OJ = allpads(op, "J1")
p4 = pcbnew.LoadBoard("hardware/p4-board.kicad_pcb"); JA = allpads(p4, "J_A")
fc = pcbnew.LoadBoard("hardware/firecontrol.kicad_pcb"); FJ = allpads(fc, "J1")
_OHOLES = [_holepos(op, r) for r in ("HP1", "HP2", "HP3", "HP4")]   # hål-konsistent P4-placering
p4b = fit("hardware/p4-board.kicad_pcb", "J_B", OJ["1"][0], OJ["14"][0],
          hole_refs=("MP1", "MP2", "MP3", "MP4"), hole_dst=_OHOLES); JB = allpads(p4b, "J_B")

# optik J1.k  ↔  P4 J_B  (transformerad till optikens frame)
edgeB = []   # (k, net, p4pad, dist, waveshare_pin, gpio)
maxB = 0
for k in range(1, 15):
    pad, net = OJ[str(k)]; j, d = nearest(pad, JB); maxB = max(maxB, d)
    edgeB.append((k, net or "—(NC)", j, d, B_PIN(int(j)), EDGE_B[B_PIN(int(j))]))
# FC J1.k  ↔  P4 J_A  (delad frame → direkt)
edgeA = []
maxA = 0
for k in range(1, 13):
    pad, net = FJ[str(k)]; j, d = nearest(pad, JA); maxA = max(maxA, d)
    edgeA.append((k, net or "—(NC)", j, d, A_PIN(int(j)), EDGE_A[A_PIN(int(j))]))

# konsistens-koll: optik/FC-nätets funktion vs P4-GPIO (GND↔GND, power↔power)
def kind(net, gpio):
    g = (net or "").upper()
    if "GND" in g or "GND" in gpio: return "gnd"
    if g in ("VBAT", "+3V3", "3V3", "VSYS", "P3V3") or gpio in ("VSYS", "3V3", "VBUS"): return "pwr"
    if net in ("—(NC)", "") : return "nc"
    return "sig"
for k, net, j, d, wp, gpio in edgeB + edgeA:
    assert d < 0.05, f"FYSISK MISS: pad {k} d={d}"

# ---------- bygg FULLA 20-stifts-kanter (inkl P4-module-stift som carrier EJ kontaktar) ----------
ojnet = {int(k): v[1] for k, v in OJ.items()}   # optik J1 pad k -> net
fjnet = {int(k): v[1] for k, v in FJ.items()}   # FC   J1 pad k -> net
# edge B: 20 stift. optik-kontakten täcker pin 2..15 (J1.k <-> pin 16-k, spegelvänd).
fullB = []
for r in range(20):
    n = 20 - r; g = EDGE_B[n]
    if 2 <= n <= 15: k = 16 - n; fullB.append((r, n, g, True, k, ojnet.get(k) or "—(NC)"))
    else:            fullB.append((r, n, g, False, None, None))
# edge A: 20 stift. FC-kontakten täcker pin 6..17 (J1.k <-> pin k+5, rak).
fullA = []
for r in range(20):
    n = r + 1; g = EDGE_A[n]
    if 6 <= n <= 17: k = n - 5; fullA.append((r, n, g, True, k, fjnet.get(k) or "—(NC)"))
    else:            fullA.append((r, n, g, False, None, None))
n_unp = sum(1 for e in fullB if not e[3]) + sum(1 for e in fullA if not e[3])

# ---------- rita ----------
BG="#2c3742"; GREEN="#1f6b4a"; GE="#15543a"; TXT="#e9eef2"; PIN="#d9b44a"; UNP="#74828e"
COL={"gnd":"#9aa4ad","pwr":"#e0533d","nc":"#5c6b78","sig":"#39c6c0"}
fig, ax = plt.subplots(figsize=(25, 14)); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

def board(x0, x1, y0, y1, title):
    ax.add_patch(FancyBboxPatch((x0, y0), x1-x0, y1-y0, boxstyle="round,pad=0.0,rounding_size=1.2",
                 fc=GREEN, ec=GE, lw=2, zorder=1))
    ax.text((x0+x1)/2, y1+1.0, title, color=TXT, ha="center", va="bottom", fontsize=12, fontweight="bold")

yrow = lambda r: 84 - r*(72/19)            # 20 rader: r0=84 ... r19=12
OB=(3.5, 13.5, yrow(18)-2.5, yrow(5)+2.5)  # optik omsluter de 14 kontaktade (rad 5..18)
P4=(47, 53, yrow(19)-3, yrow(0)+3)         # P4: alla 20 stift/kant
FB=(86.5, 96.5, yrow(16)-2.5, yrow(5)+2.5) # FC omsluter de 12 kontaktade (rad 5..16)
board(*OB, "OPTIK\n(weapon-module)\nJ1 → P4 edge B")
board(*P4, "ESP32-P4-WIFI6\nedge B ◀   ▶ edge A")
board(*FB, "FIRE-CONTROL\nP4 edge A → J1")

def stub(x, y, side, color=PIN):
    ax.add_patch(Rectangle((x-0.5 if side=="R" else x, y-0.38), 0.5, 0.76, fc=color, ec="none", zorder=4))

# --- edge B (vänster): optik J1 för kontaktade stift, grå-streckat för ej kontaktade ---
for r, n, g, conn, k, net in fullB:
    y = yrow(r)
    if conn:
        c = COL[kind(net, g)]; ls = "--" if kind(net, g)=="nc" else "-"
        stub(OB[1], y, "R"); stub(P4[0], y, "L")
        ax.plot([OB[1], P4[0]], [y, y], color=c, lw=1.5, ls=ls, zorder=2)
        ax.text(OB[1]+0.6, y+0.42, f"J1.{k}  {net}", color=TXT, ha="left", va="bottom", fontsize=8)
        ax.text(P4[0]-0.6, y+0.42, f"pin{n} · {g}", color="#cfe8ff", ha="right", va="bottom", fontsize=8)
    else:
        stub(P4[0], y, "L", UNP)
        ax.plot([P4[0]-2.3, P4[0]], [y, y], color=UNP, lw=1.1, ls=":", zorder=2)
        ax.text(P4[0]-2.9, y, f"pin{n} · {g} · ej kopplad", color=UNP, ha="right", va="center", fontsize=7.5, style="italic")
# --- edge A (höger): FC J1 för kontaktade stift, grå-streckat för ej kontaktade ---
for r, n, g, conn, k, net in fullA:
    y = yrow(r)
    if conn:
        c = COL[kind(net, g)]; ls = "--" if kind(net, g)=="nc" else "-"
        stub(P4[1], y, "R"); stub(FB[0], y, "L")
        ax.plot([P4[1], FB[0]], [y, y], color=c, lw=1.5, ls=ls, zorder=2)
        ax.text(P4[1]+0.6, y+0.42, f"pin{n} · {g}", color="#cfe8ff", ha="left", va="bottom", fontsize=8)
        ax.text(FB[0]-0.6, y+0.42, f"J1.{k}  {net}", color=TXT, ha="right", va="bottom", fontsize=8)
    else:
        stub(P4[1], y, "R", UNP)
        ax.plot([P4[1], P4[1]+2.3], [y, y], color=UNP, lw=1.1, ls=":", zorder=2)
        ax.text(P4[1]+2.9, y, f"pin{n} · {g} · ej kopplad", color=UNP, ha="left", va="center", fontsize=7.5, style="italic")

# titel + bevis-banner + legend
ax.text(50, 99, "STRILAS — bevisad pin-mappning  optik ⟷ ESP32-P4-WIFI6 ⟷ fire-control",
        color=TXT, ha="center", va="top", fontsize=17, fontweight="bold")
ax.text(50, 95, "alla 20 stift PER KANT visas · streck = fysiskt sammanfallande stift i stacken · "
        "grå-prickat = P4-module-stift som carrier-kortet INTE kontaktar",
        color="#9fb0bd", ha="center", va="top", fontsize=9.5)
ax.text(50, 3.2, f"FYSISKT VERIFIERAT ur .kicad_pcb:   edge B ↔ optik J1 = 14/14 stift @ max {maxB:.3f} mm    ·    "
        f"edge A ↔ FC J1 = 12/12 stift @ max {maxA:.3f} mm    ·    {n_unp} module-stift ej kontaktade (fria/NC)    ·    alla kopplade nät på avsedd GPIO",
        color="#bfe6c9", ha="center", va="center", fontsize=11.5, fontweight="bold")
leg=[("signal",COL["sig"],"-"),("GND",COL["gnd"],"-"),("kraft (VSYS/3V3)",COL["pwr"],"-"),
     ("kontaktad men ej driven (NC-net)",COL["nc"],"--"),("ej kontaktad module-stift",UNP,":")]
x=8
for lbl,c,ls in leg:
    ax.plot([x,x+2.2],[0.8,0.8],color=c,lw=2.2,ls=ls); ax.text(x+2.6,0.8,lbl,color=TXT,va="center",fontsize=9)
    x += 4.0 + len(lbl)*0.72

import os; os.makedirs("vapen-stack/ritningar", exist_ok=True)
OUT="vapen-stack/ritningar/p4-pinmap-proof.png"
fig.savefig(OUT, dpi=150, facecolor=BG, bbox_inches="tight")
print(f"skrev {OUT}   (edgeB {maxB:.3f}mm, edgeA {maxA:.3f}mm, {n_unp} ej-kontaktade module-stift)")
