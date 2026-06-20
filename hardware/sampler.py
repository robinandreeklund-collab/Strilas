#!/usr/bin/env python3
"""STRILAS — SAMPLER/DEMO-kort för lager-koll (EJ för beställning).

v2: de delar som ännu saknar in-stock-lösning:
  • PTC-säkring 1812 — MÅSTE vara 16V-märkt (2S 8,4V; 6V-varianter som miniSMDC300F duger EJ).
  • IR-emitter (OSLON Black) — SFH4715AS hade 96–107 dgr ledtid → leta in-stock 850/860/940nm.
(P-FET löstes: AOD403 in-stock P-ch -30V drop-in. PTC-6V miniSMDC förkastad: underdimensionerad.)

Sätter VALUE = MPN per footprint → BOM-kolumnen "Manufacturer Part Number" = MPN.
Kör: python3 hardware/sampler.py
"""
import pcbnew, csv
MM = pcbnew.FromMM
OX, OY = 150.0, 100.0
FPDIR = "/usr/share/kicad/footprints"
import os
LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strilas.pretty")
PCB = "hardware/sampler.kicad_pcb"


def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

PTC_FP = ("Fuse", "Fuse_1812_4532Metric")
IR_FP = ("strilas", "IR_Emitter_OSRAM_OSLON_Black_SFH4725S")
# PTC 1812, 16V-märkt (2S), hold ~2,5-3,5A
PTC_MPN = [
    "MF-MSMF300/16-2",      # Bourns 3A/16V
    "1812L300/16MR",        # Littelfuse 3A/16V
    "1812L300/16DR",        # Littelfuse 3A/16V (alt reel)
    "1812L260/16DR",        # Littelfuse 2,6A/16V (lägre hold, ev mer i lager)
    "0ZCG0300FF2C",         # Bel Fuse 3A/16V
    "MF-MSMF250/16-2",      # Bourns 2,5A/16V (driftström ~1,6A → räcker)
]
# IR-emitter OSLON Black (kamera-konstellation 150m) — 850/860/940nm, samma footprint
IR_MPN = [
    "SFH4715AS",            # OSRAM 860nm (originalet — 96-107 dgr)
    "SFH4716AS",            # OSRAM 850nm OSLON Black (högre effekt)
    "SFH4725AS",            # OSRAM 940nm (optikens — mer i lager)
    "SFH4775S",             # OSRAM 940nm hög-effekt OSLON Black
    "SFH4770S",             # OSRAM 850nm OSLON Black SFH4770
]


def add(b, ref, libfp, mpn, x, y):
    lib, fp = libfp
    path = LOCAL if lib == "strilas" else f"{FPDIR}/{lib}.pretty"
    f = pcbnew.FootprintLoad(path, fp)
    f.SetReference(ref); f.SetValue(mpn); f.SetPosition(V(x, y)); b.Add(f)
    t = pcbnew.PCB_TEXT(b); t.SetText(mpn); t.SetPosition(V(x, y - 4.5))
    t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(pcbnew.VECTOR2I(MM(0.7), MM(0.7)))
    t.SetTextThickness(MM(0.12)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)


def main():
    b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)
    rows = []
    for i, mpn in enumerate(PTC_MPN):
        x = -27.5 + i * 11; add(b, f"F{i+1}", PTC_FP, mpn, x, 9); rows.append((f"F{i+1}", mpn, PTC_FP[1], "PTC 3A/16V 1812"))
    for i, mpn in enumerate(IR_MPN):
        x = -22 + i * 11; add(b, f"D{i+1}", IR_FP, mpn, x, -9); rows.append((f"D{i+1}", mpn, IR_FP[1], "IR-emitter OSLON Black"))
    title = pcbnew.PCB_TEXT(b); title.SetText("STRILAS SAMPLER v2 — PTC 16V + IR-emitter (lager-koll, EJ best.)")
    title.SetPosition(V(0, 18)); title.SetLayer(pcbnew.F_SilkS)
    title.SetTextSize(pcbnew.VECTOR2I(MM(1.1), MM(1.1))); title.SetTextThickness(MM(0.18))
    title.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(title)
    W, H = 35, 15
    for a, c in (((-W, -H), (W, -H)), ((W, -H), (W, H)), ((W, H), (-W, H)), ((-W, H), (-W, -H))):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*c))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    pcbnew.SaveBoard(PCB, b)
    with open("hardware/sampler-bom.csv", "w", newline="") as fp:
        w = csv.writer(fp); w.writerow(["Designator", "Quantity", "Manufacturer Part Number", "Footprint", "Comment"])
        for ref, mpn, foot, com in rows: w.writerow([ref, 1, mpn, foot, com])
    with open("hardware/sampler-centroid.csv", "w", newline="") as fp:
        w = csv.writer(fp); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for f in b.GetFootprints():
            p = f.GetPosition(); w.writerow([f.GetReference(), f"{p.x/1e6-OX:.3f}", f"{OY-p.y/1e6:.3f}",
                                             "bottom" if f.IsFlipped() else "top", f.GetOrientationDegrees()])
    print(f"{PCB}: {len(rows)} delar ({len(PTC_MPN)} PTC-16V + {len(IR_MPN)} IR). BOM+centroid skrivna.")
    for ref, mpn, foot, com in rows: print(f"  {ref}: {mpn}  ({com})")


if __name__ == "__main__":
    main()
