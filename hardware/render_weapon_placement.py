#!/usr/bin/env python3
"""STRILAS — placeringsgranskning av vapen-optikmodulen (FÖRE routning).
Topp-vy: komponent-courtyards + referenser, samt mekanik-overlays:
P4-fotavtryck (bakom, vänster), kamera (B0332 38×38) + B4B-ZR-kontakt (höger),
Ø16-lins, 3 synkade P4-standoff, centrum-kort-hål. Bekräfta innan routning."""
import pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

b = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
OX, OY = 150.0, 120.0
fig, ax = plt.subplots(figsize=(8.5, 10.5), facecolor="white")

# kort-outline 54×74
ax.add_patch(FancyBboxPatch((-27, -37), 54, 74, boxstyle="round,pad=0,rounding_size=2.5",
             fc="#0b6b3a", ec="#06301a", lw=2, zorder=1))

# P4-fotavtryck (bakom, vänster): centrum (-16,0), 21 bred (x) × 71 lång (y)
ax.add_patch(Rectangle((-16-10.5, -35.525), 21, 71.05, fill=False, ec="#ff3030", lw=2, ls="--", zorder=5))
ax.text(-16, 30, "P4 (bakom,\n15 mm standoff)", fontsize=7, ha="center", color="#ff6060", zorder=6)
# ESP-modulzon på P4 (övre änden) + USB (nedre)
ax.text(-16, -33, "USB-änd", fontsize=6, ha="center", color="#ff8080", zorder=6)

# kamera B0332 38×38 om lins (0,-6), kontakt B4B-ZR på HÖGER kant (+x)
ax.add_patch(Rectangle((0-19, -6-19), 38, 38, fill=False, ec="#40c0ff", lw=1.5, ls=":", zorder=4))
ax.text(-12, -6, "B0332-kamera\n38×38 (bakom)", fontsize=6.5, ha="center", color="#40c0ff", zorder=6)
ax.add_patch(Rectangle((19, -6-3, ), 3, 6, fc="#2050ff", ec="#001", lw=1, zorder=5))
ax.text(23.5, -6, "B4B-ZR\n(USB-kabel)", fontsize=6, ha="left", va="center", color="#3060ff", zorder=6, rotation=90)
# lins Ø16
ax.add_patch(Circle((0, -6), 8, fc="#0a0a0a", ec="#ddd", lw=1, zorder=6))
ax.text(0, -6, "Ø16", fontsize=6, ha="center", va="center", color="#eee", zorder=7)

SYNC = {"H5", "H6", "H7", "H20"}
def col(ref):
    if ref in SYNC: return "#30ff60"     # P4-standoff
    if ref == "H4": return "#40c0ff"     # centrum-kort-hål
    if ref in ("H1", "H2", "H3"): return "#dddddd"  # kort-hörn
    if ref.startswith("H"): return "#caa"           # ben/kamera
    if ref == "J1": return "#ffd040"     # P4-kantkontakt
    return "#ffe8b0"

for f in b.GetFootprints():
    ref = f.GetReference()
    fx = f.GetPosition().x/1e6-OX; fy = -(f.GetPosition().y/1e6-OY)
    pads = list(f.Pads())
    if ref.startswith("H") and len(pads) == 1:        # monteringshål → cirkel
        r = max(p.GetSize().x for p in pads)/2e6
        ax.add_patch(Circle((fx, fy), max(r, 1.0), fill=False, ec=col(ref), lw=1.6, zorder=8))
    else:                                             # komponent → tight pad-bbox
        xs = [p.GetPosition().x/1e6-OX for p in pads]; ys = [-(p.GetPosition().y/1e6-OY) for p in pads]
        pw = max(p.GetSize().x for p in pads)/1e6; ph = max(p.GetSize().y for p in pads)/1e6
        x0, x1 = min(xs)-pw/2, max(xs)+pw/2; y0, y1 = min(ys)-ph/2, max(ys)+ph/2
        ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False, ec=col(ref), lw=1.1, zorder=8))
    ax.text(fx, fy-2.2 if ref.startswith("H") else fy, ref, fontsize=5.5, ha="center",
            va="center", color="#fff", zorder=9, weight="bold")

# legend-text
ax.text(-26.5, -36.3, "grön=P4-standoff (H5/H6/H7)  blå=centrum H4  gul=J1  cyan=kamera  röd=P4",
        fontsize=6, color="#fff", zorder=10)
ax.set_aspect("equal"); ax.set_xlim(-30, 32); ax.set_ylim(-40, 40); ax.axis("off")
ax.set_title("STRILAS vapen-optikmodul — PLACERINGSFÖRSLAG (P4 vänster), före routning\n"
             "kraft/skydd-remsa → högerkant • Rset(R2)+bulk(C2) nära emittrarna • J1 → vänsterkant",
             fontsize=9, weight="bold")
plt.tight_layout()
plt.savefig("hardware/weapon-placement-proposal.png", dpi=160, facecolor="white")
print("wrote hardware/weapon-placement-proposal.png")
