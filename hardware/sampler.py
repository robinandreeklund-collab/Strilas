#!/usr/bin/env python3
"""STRILAS — SAMPLER/DEMO-kort för lager-koll (EJ för beställning). Placerar flera MPN-varianter
av de delar som inte matchade i offert-verktyget: PTC-säkring (1812) + omvändpol-P-FET (DPAK).
Sätter VALUE = MPN på varje footprint → BOM-kolumnen "Manufacturer Part Number" blir MPN.
Skriver kicad_pcb + BOM-CSV + centroid-CSV; gerbers exporteras av anroparen (kicad-cli).
Kör: python3 hardware/sampler.py
"""
import pcbnew, csv, os
MM = pcbnew.FromMM
OX, OY = 150.0, 100.0
FPDIR = "/usr/share/kicad/footprints"
PCB = "hardware/sampler.kicad_pcb"


def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

# (ref, MPN, lib, footprint, beskrivning) — PTC 3A/16V 1812 + P-FET DPAK (TO-252)
PTC_FP = ("Fuse", "Fuse_1812_4532Metric")
FET_FP = ("Package_TO_SOT_SMD", "TO-252-2")
PTC_MPN = [
    "MF-MSMF300/16-2",      # Bourns (original — ej matchad)
    "1812L300/16MR",        # Littelfuse PolySwitch 3A 16V 1812
    "1812L300/16PR",        # Littelfuse (alt suffix)
    "0ZCJ0300FF2E",         # Bel Fuse 0ZCJ 3A
    "miniSMDC300F-2",       # Littelfuse/Raychem miniSMDC (1812) 3A
    "SMD1812B300TF/16",     # generisk 1812 PPTC 3A/16V
]
FET_MPN = [
    "AOD4185A",             # Alpha&Omega -40V P-DPAK (original — ej matchad)
    "AOD4184A",             # A&O (KÄND i lager — referens)
    "AOD403",               # A&O -30V P-DPAK
    "FDD4685",              # onsemi -40V P-DPAK
    "IRFR5305TRPBF",        # Infineon -55V P-DPAK (klassiker)
]


def add(b, ref, lib, fp, mpn, x, y):
    f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", fp)
    f.SetReference(ref); f.SetValue(mpn); f.SetPosition(V(x, y))
    b.Add(f)
    # silk-etikett med MPN under delen
    t = pcbnew.PCB_TEXT(b); t.SetText(mpn); t.SetPosition(V(x, y - 4.5))
    t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
    t.SetTextThickness(MM(0.13)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)
    return f


def main():
    b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)
    rows = []
    # PTC-rad (övre)
    for i, mpn in enumerate(PTC_MPN):
        x = -27.5 + i * 11; add(b, f"F{i+1}", *PTC_FP, mpn, x, 9); rows.append((f"F{i+1}", mpn, PTC_FP[1]))
    # FET-rad (nedre)
    for i, mpn in enumerate(FET_MPN):
        x = -26 + i * 13; add(b, f"Q{i+1}", *FET_FP, mpn, x, -9); rows.append((f"Q{i+1}", mpn, FET_FP[1]))
    # titel-text + outline
    title = pcbnew.PCB_TEXT(b); title.SetText("STRILAS SAMPLER — lager-koll (EJ best.)")
    title.SetPosition(V(0, 18)); title.SetLayer(pcbnew.F_SilkS)
    title.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2))); title.SetTextThickness(MM(0.2))
    title.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(title)
    W, H = 33, 15
    for a, c in (((-W, -H), (W, -H)), ((W, -H), (W, H)), ((W, H), (-W, H)), ((-W, H), (-W, -H))):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*c))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    pcbnew.SaveBoard(PCB, b)
    # BOM-CSV (Designator, Quantity, Manufacturer Part Number, Footprint)
    with open("hardware/sampler-bom.csv", "w", newline="") as fp:
        w = csv.writer(fp); w.writerow(["Designator", "Quantity", "Manufacturer Part Number", "Footprint", "Comment"])
        for ref, mpn, foot in rows:
            w.writerow([ref, 1, mpn, foot, "PTC 3A/16V 1812" if ref.startswith("F") else "P-FET DPAK omvändpol"])
    # centroid-CSV
    with open("hardware/sampler-centroid.csv", "w", newline="") as fp:
        w = csv.writer(fp); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for f in b.GetFootprints():
            p = f.GetPosition(); w.writerow([f.GetReference(), f"{p.x/1e6-OX:.3f}", f"{OY-p.y/1e6:.3f}",
                                             "bottom" if f.IsFlipped() else "top", f.GetOrientationDegrees()])
    print(f"{PCB}: {len(rows)} delar ({len(PTC_MPN)} PTC + {len(FET_MPN)} FET). BOM+centroid skrivna.")
    for ref, mpn, foot in rows: print(f"  {ref}: {mpn}  ({foot})")


if __name__ == "__main__":
    main()
