#!/usr/bin/env python3
"""STRILAS — PORT-MATCHNINGSKARTA: varje kontaktstift etiketterat, mate-paren
ställda bredvid varandra (optik↔P4 edge B, FC↔P4 edge A) med ✓/✗ så att man
SER direkt om allt matchar. Plus fan-out-portar (FC J2–J8, optik J2) listade.
Färg: röd=kraft, svart=GND, grön=GPIO, blå=signal, grå=NC."""
import re, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def parse(path):
    t = open(path).read(); seg = t[t.find("(nets"):]; nets = {}
    for blk in re.split(r"\(net\b", seg)[1:]:
        nm = re.search(r'\(name "([^"]*)"\)', blk)
        if nm: nets[nm.group(1)] = re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', blk)
    return nets
def pin2net(nets):
    d = {}
    for nm, nodes in nets.items():
        for r, p in nodes: d.setdefault(r, {})[p] = nm
    return d

OPT = pin2net(parse("hardware/weapon-module.net"))
FC  = pin2net(parse("hardware/firecontrol.net"))
EDGE_A = ["GPIO52","GPIO51","GND","GPIO31","GPIO30","GPIO29","GPIO28","GND","GPIO50","GPIO49",
          "GPIO5","GPIO4","GND","GPIO3","GPIO2","GPIO8","GPIO7","GND","GPIO24","GPIO25"]
EDGE_B = ["VBUS","VSYS","GND","EN","3V3","GPIO20","GPIO21","GND","GPIO22","GPIO23",
          "RUN","GPIO26","GND","GPIO27","GPIO32","GPIO33","GPIO46","GND","GPIO47","GPIO48"]
POWER = {"VBUS","VSYS","3V3","+3V3","VBAT","VBAT_F","VBAT_IN"}

def col(net):
    if net in (None, "", "—"): return "#cfcfcf"
    if net == "GND": return "#222"
    if net in POWER or net in ("VSYS","3V3","VBUS","EN","RUN"): return "#d33"
    if net.startswith("GPIO"): return "#4a4"
    return "#37c"
def tcol(net): return "#fff" if net in (None,"","—") or net=="GND" or net in POWER else "#fff"

fig, ax = plt.subplots(figsize=(13.5, 11), facecolor="white")
def chip(x, y, w, txt, c, fs=8.0, tc="#fff"):
    ax.add_patch(Rectangle((x, y), w, 0.82, fc=c, ec="#000", lw=0.6, zorder=2))
    ax.text(x+w/2, y+0.41, txt, ha="center", va="center", fontsize=fs, color=tc, zorder=3, weight="bold")

def ladder(x0, y0, title, left_pairs, edge_name):
    """left_pairs: list of (board_pin_label, board_net, p4_func). y0=topp."""
    ax.text(x0+5.4, y0+1.0, title, ha="center", fontsize=10, weight="bold")
    ax.text(x0+2.3, y0+0.15, "kort", ha="center", fontsize=7.5, style="italic")
    ax.text(x0+8.4, y0+0.15, "P4 "+edge_name, ha="center", fontsize=7.5, style="italic")
    for i, (pl, bn, pf) in enumerate(left_pairs):
        y = y0 - 1.0 - i*0.95
        chip(x0, y, 4.6, f"{pl}  {bn if bn else '—(NC)'}", col(bn), 7.2)
        chip(x0+6.2, y, 4.6, pf, col(pf), 7.2)
        # match: board-net funktion stämmer med P4-funktion? NC = alltid OK (reserv)
        nc = bn in (None, "", "—")
        ok = nc \
             or (bn == "GND" and pf == "GND") \
             or (bn in POWER and pf in POWER) \
             or (bn and not bn.startswith("GPIO") and bn != "GND" and bn not in POWER and pf.startswith("GPIO"))
        mark = "–" if nc else ("✓" if ok else "✗")
        mc = "#999" if nc else ("#080" if ok else "#c00")
        ax.text(x0+5.7, y+0.41, mark, ha="center", va="center", fontsize=11, color=mc, weight="bold")

# ---- edge B: optik J1 (14) ↔ P4 edge B pin 2..15 ----
optJ1 = OPT.get("J1", {})
pairsB = [(f"J1.{k}", optJ1.get(str(k)), EDGE_B[k]) for k in range(1, 15)]  # k→edgeB pin k+1 → idx k
ladder(1, 22, "OPTIK J1  ↔  P4 EDGE B", pairsB, "edge B")

# ---- edge A: FC J1 (12) ↔ P4 edge A pin 6..17 ----
fcJ1 = FC.get("J1", {})
pairsA = [(f"J1.{k}", fcJ1.get(str(k)), EDGE_A[k+4]) for k in range(1, 13)]  # k→edgeA pin k+5 → idx k+4
ladder(15.5, 22, "FC J1  ↔  P4 EDGE A", pairsA, "edge A")

# ---- fan-out & kraftportar ----
def strip(x, y, title, conn, pn):
    ax.text(x, y+0.95, title, fontsize=9, weight="bold")
    pins = sorted(pn.get(conn, {}), key=lambda z: int(z) if z.isdigit() else 99)
    for i, p in enumerate(pins):
        n = pn[conn][p]
        chip(x+i*3.4, y, 3.2, f"{p}:{n}", col(n), 6.6)

ax.text(15.5, 9.3, "FC fan-out & kraft-portar", fontsize=10, weight="bold")
strip(15.5, 8.0, "J2  3V3-in (← optik +3V3)", "J2", FC)
strip(15.5, 6.6, "J8  NFC PN532 (I²C)", "J8", FC)
strip(15.5, 5.2, "J7  recoil-effektkort", "J7", FC)
strip(15.5, 3.8, "J3 TRIG · J4 RACK · J5 MAG-REL · J6 MAGWELL (+GND)", "J3", FC)
ax.text(15.5, 3.55, "  (J3–J6: pin1=signal, pin2=GND)", fontsize=6.5, color="#555")

ax.text(1, 9.3, "OPTIK kraft-port", fontsize=10, weight="bold")
strip(1, 8.0, "J2  batteri-in (LiPo)", "J2", OPT)
ax.text(1, 6.9, "Kraftväg: J2 → F1 säkring → Q1 backspärr → VBAT → J1.1 → P4 VSYS → 3V3", fontsize=7.2, color="#333")
ax.text(1, 6.3, "IR-emitter (D2/D3) matas av VBAT, moduleras av IR_MOD (GPIO20) via Q2.", fontsize=7.2, color="#333")

ax.text(7.5, 1.6, "röd=kraft   svart=GND   grön=GPIO   blå=signal   grå=NC      ✓=matchar   ✗=krock",
        ha="center", fontsize=8.5, color="#333")
ax.set_xlim(0, 27); ax.set_ylim(1, 24); ax.axis("off")
ax.set_title("STRILAS — PORT-MATCHNING: varje stift etiketterat, mate-par sida vid sida",
             fontsize=12.5, weight="bold")
plt.tight_layout(); plt.savefig("hardware/port-matching.png", dpi=150, facecolor="white")
print("wrote hardware/port-matching.png")
