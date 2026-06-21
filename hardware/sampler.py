#!/usr/bin/env python3
"""STRILAS — STOR SAMPLER (20 IR-emittrar) för lager-koll (EJ för beställning).
850/860nm högintensiva IR-emittrar som PASSAR konstellationen (kamera-spårning 150m, PWM-pulsad,
bandpass rejekterar 940nm-taggen). Över alla märken — kör genom offertverktyget, välj den som är
in-stock + har högst radians (mW/sr) vid er driftström/puls. VALUE=MPN. Kör: python3 hardware/sampler.py
"""
import pcbnew, csv, os
MM = pcbnew.FromMM
OX, OY = 150.0, 100.0
FPDIR = "/usr/share/kicad/footprints"
LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strilas.pretty")
PCB = "hardware/sampler.kicad_pcb"
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

OSLON = ("strilas", "IR_Emitter_OSRAM_OSLON_Black_SFH4725S")   # 3.85mm 2-pad (OSRAM/Vishay-stora)
P3535 = ("LED_SMD", "LED_PLCC-2_3.4x3.0mm_AK")                  # 3535/SMD-3-klass
# (MPN, footprint, not) — 20 st, 850/860nm, sorterade märkesvis
IR = [
    ("SFH4715AS",          OSLON, "OSRAM 860nm OSLON ~780mW/sr (original)"),
    ("SFH4715S",           OSLON, "OSRAM 850nm OSLON Nanostack"),
    ("SFH4715",            OSLON, "OSRAM 850nm OSLON 90°"),
    ("SFH4716AS",          OSLON, "OSRAM 850nm OSLON 150°"),
    ("SFH4716S",           OSLON, "OSRAM 850nm OSLON Nanostack 150°"),
    ("VSMY98545",          OSLON, "Vishay 850nm ±45° 350mW/sr@1A 1600@5Apuls (PULS=bäst)"),
    ("VSMY2853G",          OSLON, "Vishay 850nm ±28° (svagare)"),
    ("VSMY3850",           P3535, "Vishay 850nm"),
    ("VSMY1850X01",        P3535, "Vishay 850nm hög-hastighet"),
    ("L1I0-0850050200000", P3535, "Lumileds LUXEON IR 850nm 50° (HÖG intensitet)"),
    ("L1I0-0850060000000", P3535, "Lumileds LUXEON IR 850nm 60° (hög intensitet)"),
    ("L1I0-0850090000000", P3535, "Lumileds LUXEON IR 850nm 90° 750mW/sr (VF 3,2V→1LED/gren)"),
    ("L1I0-0850150000000", P3535, "Lumileds LUXEON IR 850nm 150° 335mW/sr"),
    ("L1I0-0850955800000", P3535, "Lumileds LUXEON IR 850nm 95×58° asymmetrisk"),
    ("RS-3535MWAR",        P3535, "NationStar 850nm 3535 (verifiera IR ej RGB!)"),
    ("RS-3535MWAM",        P3535, "NationStar 850nm 3535"),
    ("15435385AA350",      P3535, "Würth WL-SIMW 855nm 3535"),
    ("15435394A3050",      P3535, "Würth 850nm 3535"),
    ("IN-P32ZTIR",         P3535, "Inolux 850nm 3535"),
    ("HIR19-21C/L11",      P3535, "Everlight 850nm"),
]


def add(b, ref, libfp, mpn, x, y):
    lib, fp = libfp
    f = pcbnew.FootprintLoad(LOCAL if lib == "strilas" else f"{FPDIR}/{lib}.pretty", fp)
    f.SetReference(ref); f.SetValue(mpn); f.SetPosition(V(x, y)); b.Add(f)
    t = pcbnew.PCB_TEXT(b); t.SetText(mpn); t.SetPosition(V(x, y - 3.6))
    t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(pcbnew.VECTOR2I(MM(0.6), MM(0.6)))
    t.SetTextThickness(MM(0.1)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)


def main():
    b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)
    rows = []
    for i, (mpn, fp, note) in enumerate(IR):
        col, rw = i % 5, i // 5
        x = -28 + col * 14; y = 19 - rw * 13
        add(b, f"D{i+1}", fp, mpn, x, y); rows.append((f"D{i+1}", mpn, fp[1], note))
    title = pcbnew.PCB_TEXT(b); title.SetText("STRILAS SAMPLER — 20 IR-emitter 850/860nm (lager-koll, EJ best.)")
    title.SetPosition(V(0, 29)); title.SetLayer(pcbnew.F_SilkS)
    title.SetTextSize(pcbnew.VECTOR2I(MM(1.1), MM(1.1))); title.SetTextThickness(MM(0.18))
    title.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(title)
    W, H = 38, 26
    for a, c in (((-W, -H), (W, -H)), ((W, -H), (W, H)), ((W, H), (-W, H)), ((-W, H), (-W, -H))):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*c))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    pcbnew.SaveBoard(PCB, b)
    with open("hardware/sampler-bom.csv", "w", newline="") as fp:
        w = csv.writer(fp); w.writerow(["Designator", "Quantity", "Manufacturer Part Number", "Footprint", "Comment"])
        for ref, mpn, foot, note in rows: w.writerow([ref, 1, mpn, foot, note])
    with open("hardware/sampler-centroid.csv", "w", newline="") as fp:
        w = csv.writer(fp); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for f in b.GetFootprints():
            p = f.GetPosition(); w.writerow([f.GetReference(), f"{p.x/1e6-OX:.3f}", f"{OY-p.y/1e6:.3f}", "top", f.GetOrientationDegrees()])
    print(f"{PCB}: {len(rows)} IR-emitter-varianter (fler-märkes). BOM+centroid skrivna.")
    for ref, mpn, foot, note in rows: print(f"  {ref:4} {mpn:20} {note}")


if __name__ == "__main__":
    main()
