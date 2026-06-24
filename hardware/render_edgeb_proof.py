#!/usr/bin/env python3
"""STRILAS — edge-B standoff-lås-bevis (REPRODUCERBART, läser live-geometri).
Ritar optikens J1-socket (14 stift) med VERKLIGA padd-positioner ur weapon-module.kicad_pcb,
de 4 P4-standoff-hålen (H5/H6/H7/H20) som streckade ringar, och bredvid varje stift den
P4 edge-B-funktion det möter i den STACKADE (ansikte-mot-ansikte, J_B flippad → SPEGLAD)
monteringen: optik J1.k ↔ P4 edge-B-stift (15-k). Färg grön=kopplad, röd=NC.
Verifierat 0.000 mm mot _pads_z-geometrin (build_assembly.py)."""
import re, pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

PCB = "hardware/weapon-module.kicad_pcb"
# P4 edge B full (Waveshare-officiell, ESP-änd→USB-änd); optik-fönstret = idx 1..14 (VSYS..GPIO32)
EDGE_B = ["VBUS", "VSYS", "GND", "EN", "3V3", "GPIO20", "GPIO21", "GND", "GPIO22", "GPIO23",
          "RUN", "GPIO26", "GND", "GPIO27", "GPIO32", "GPIO33", "GPIO46", "GND", "GPIO47", "GPIO48"]
POWER = {"VSYS", "3V3", "VBUS", "VBAT", "+3V3"}


def main():
    b = pcbnew.LoadBoard(PCB)
    j1 = [f for f in b.GetFootprints() if f.GetReference() == "J1"][0]
    pads = {pd.GetName(): (pd.GetPosition().x / 1e6, pd.GetPosition().y / 1e6,
                           pd.GetNetname()) for pd in j1.Pads()}
    holes = {f.GetReference(): (f.GetPosition().x / 1e6, f.GetPosition().y / 1e6)
             for f in b.GetFootprints() if f.GetReference() in ("H5", "H6", "H7", "H20")}

    fig, ax = plt.subplots(figsize=(8, 11), facecolor="white")
    Y = lambda y: -y  # flippa så stift 1 hamnar överst

    # standoff-hål (streckade ringar) — det fysiska låset
    for ref, (x, y) in holes.items():
        ax.add_patch(Circle((x, Y(y)), 1.6, fill=False, ec="#888", ls="--", lw=1.4))
        ax.text(x, Y(y), ref, ha="center", va="center", fontsize=7, color="#888")

    # J1-stift: padd (guld) + ring (grön=kopplad, röd=NC) + etikett "J1.k net  ↔  P4 edge B (15-k)"
    for k in range(1, 15):
        x, y, net = pads[str(k)]
        p4 = EDGE_B[15 - k]
        nc = net in ("", None)
        ring = "#d22" if nc else "#1a1"
        ax.add_patch(Rectangle((x - 0.5, Y(y) - 0.5), 1.0, 1.0, fc="#c9a227", ec="#000", lw=0.5, zorder=3))
        ax.add_patch(Circle((x, Y(y)), 1.15, fill=False, ec=ring, lw=2.2, zorder=2))
        lab = f"J1.{k}  {'(NC) ' + p4 if nc else net}   ↔  P4 {p4}"
        # match-typkoll
        if nc:
            mk, mc = "–", "#999"
        else:
            ok = (net == "GND" and p4 == "GND") or (net in POWER and p4 in POWER) \
                 or (net not in POWER and net != "GND" and p4.startswith("GPIO"))
            mk, mc = ("✓", "#080") if ok else ("✗", "#c00")
        ax.text(x + 2.6, Y(y), lab, ha="left", va="center", fontsize=8.5,
                color="#111", weight="bold" if not nc else "normal")
        ax.text(x + 1.7, Y(y), mk, ha="center", va="center", fontsize=11, color=mc, weight="bold")

    ax.set_title("STRILAS edge-B standoff-lås-bevis\n"
                 "optik J1-socket ↔ P4 edge B (STACKAD, speglad: J1.k ↔ stift 15-k)\n"
                 "streckad ring = P4-standoff-hål  ·  grön = kopplad  ·  röd = NC",
                 fontsize=10, weight="bold")
    ax.set_aspect("equal")
    ax.relim(); ax.autoscale_view()
    ax.margins(0.15)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("hardware/edgeB-match-proof.png", dpi=140, facecolor="white")
    print("wrote hardware/edgeB-match-proof.png")


if __name__ == "__main__":
    main()
