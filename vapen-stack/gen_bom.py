#!/usr/bin/env python3
"""Komplett BOM för STRILAS vapen-stack (optik + P4 + fire-control).
Läser de lokala nätlistorna + P4-modellen, grupperar per kort och skriver
BOM.csv + BOM.md. Plus externa moduler (kabelanslutna) som egen sektion."""
import re, csv, pcbnew
from collections import defaultdict

def from_net(path):
    t = open(path).read(); seg = t[t.find("(components"):t.find("(libparts")]
    out = []
    for blk in re.split(r"\(comp\b", seg)[1:]:
        ref = re.search(r'\(ref "([^"]+)"\)', blk)
        val = re.search(r'\(value "([^"]*)"\)', blk)
        fp = re.search(r'\(footprint "([^"]*)"\)', blk)
        if ref:
            out.append((ref.group(1), val.group(1) if val else "", fp.group(1) if fp else ""))
    return out

def from_pcb(path):
    b = pcbnew.LoadBoard(path)
    return [(f.GetReference(), f.GetValue(), str(f.GetFPID().GetLibItemName())) for f in b.GetFootprints()]

BOARDS = [
    ("Optik (weapon-module)", from_net("weapon-module.net")),
    ("Fire-control", from_net("firecontrol.net")),
    ("P4-carrier (lödbara headers på Waveshare-modulen)", from_pcb("p4-board.kicad_pcb")),
]

# externa / kabelanslutna moduler (ej på PCB)
EXTERNAL = [
    ("1", "ESP32-P4-WIFI6", "Waveshare", "Huvudprocessor (Pico-format). Edge B→optik, edge A→FC."),
    ("1", "PN532 NFC-modul", "modul", "Magasin-NFC. Kabel → FC J8 (I²C, 3V3)."),
    ("1", "USB-kamera (OV9281/B0332)", "modul", "Kabel → P4 J_CAM (USB 2.0)."),
    ("1", "LiPo-batteri", "—", "Kabel → optik J2 (VBAT)."),
    ("1", "Recoil-effektkort", "separat PCB", "eFuse+aktuator. Kabel → FC J7 (PWM/FAULT/GND)."),
    ("4", "Mikrobrytare", "—", "Trigger/rack/mag-release/magwell. Kabel → FC J3–J6."),
    ("4", "M2-standoff + skruv", "15 mm", "Genomgående stack: optik–P4–FC."),
]

def is_mech(ref, fp):
    return ref.startswith("H") and "MountingHole" in fp or ref.startswith("MP")

rows = []           # (board, refs, qty, value, footprint, typ)
for board, comps in BOARDS:
    groups = defaultdict(list)
    mech = defaultdict(list)
    for ref, val, fp in comps:
        (mech if is_mech(ref, fp) else groups)[(val, fp)].append(ref)
    for (val, fp), refs in sorted(groups.items()):
        rows.append((board, ",".join(sorted(refs)), len(refs), val, fp, "elektrisk"))
    for (val, fp), refs in sorted(mech.items()):
        rows.append((board, ",".join(sorted(refs)), len(refs), val, fp, "mekanik"))

# ---- CSV ----
with open("BOM.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Kort", "Referenser", "Antal", "Värde", "Footprint", "Typ"])
    for r in rows:
        w.writerow(r)
    w.writerow([])
    w.writerow(["EXTERNA MODULER (kabelanslutna)", "", "", "", "", ""])
    w.writerow(["Antal", "Artikel", "Variant", "Not", "", ""])
    for q, art, var, note in EXTERNAL:
        w.writerow([q, art, var, note, "", ""])

# ---- Markdown ----
with open("BOM.md", "w") as f:
    f.write("# STRILAS vapen-stack — komplett BOM\n\n")
    f.write("Stack: **optik (weapon-module) → ESP32-P4 → fire-control**. "
            "3V3 matas batteri→VSYS→P4-reg→3V3 (FC via edge-B-tapp).\n\n")
    tot = 0
    for board, _ in BOARDS:
        brows = [r for r in rows if r[0] == board]
        n = sum(r[2] for r in brows); tot += n
        f.write(f"## {board}  ({n} st)\n\n")
        f.write("| Antal | Referenser | Värde | Footprint | Typ |\n|---|---|---|---|---|\n")
        for _, refs, qty, val, fp, typ in brows:
            f.write(f"| {qty} | {refs} | {val} | `{fp}` | {typ} |\n")
        f.write("\n")
    f.write(f"## Externa moduler (kabelanslutna)\n\n")
    f.write("| Antal | Artikel | Variant | Not |\n|---|---|---|---|\n")
    for q, art, var, note in EXTERNAL:
        f.write(f"| {q} | {art} | {var} | {note} |\n")
    f.write(f"\n**PCB-komponenter totalt: {tot} st** (exkl. externa moduler).\n")

print(f"BOM.csv + BOM.md skrivna ({len(rows)} rader, "
      f"{sum(r[2] for r in rows)} PCB-komponenter + {len(EXTERNAL)} externa).")
