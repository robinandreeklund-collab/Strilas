#!/usr/bin/env python3
"""STRILAS — SAMPLER/DEMO-kort för lager-koll (EJ för beställning).

v3: IR-emitter-alternativ ÖVER FLERA TILLVERKARE (ej bara OSRAM) — 850/855/860nm högeffekt
som monteraren (NextPCB/LCSC) ska kunna ha i DIREKTLAGER + montera (ingen kund-sourcing/DNP,
inget skickas till Kina). OSLON 2,3×2,3 ersätts då av 3535-paket (footprint-byte på patch+hjälm).
Kamera-konstellation: 850/855nm OK med kamerans bandpass (rejekterar 940nm tagg-ljuset).

VALUE = MPN per footprint. Kör: python3 hardware/sampler.py
"""
import pcbnew, csv, os
MM = pcbnew.FromMM
OX, OY = 150.0, 100.0
FPDIR = "/usr/share/kicad/footprints"
LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strilas.pretty")
PCB = "hardware/sampler.kicad_pcb"


def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

OSLON = ("strilas", "IR_Emitter_OSRAM_OSLON_Black_SFH4725S")
P3535 = ("LED_SMD", "LED_PLCC-2_3.4x3.0mm_AK")          # 2-pad ~3535-klass för 3535-emitter
# (ref, MPN, footprint, tillverkare/not) — högeffekt IR 850-860nm, lager-koll över märken
IR = [
    ("SFH4715AS",       OSLON, "OSRAM 860nm OSLON (referens — ej i direktlager)"),
    ("RS-3535MWAR",     P3535, "Foshan NationStar 850nm 3535 (LCSC i lager)"),
    ("RS-3535MWAM",     P3535, "Foshan NationStar 850nm 3535"),
    ("15435385AA350",   P3535, "Würth WL-SIMW 855nm 3535"),
    ("IN-P32ZTIR",      P3535, "Inolux 850nm 3535"),
    ("VSMY2853G",       P3535, "Vishay 850nm"),
    ("HIR19-21C/L11",   P3535, "Everlight 850nm"),
    ("XL-3535SURC-850", P3535, "XINGLIGHT 850nm 3535"),
]


def add(b, ref, libfp, mpn, x, y):
    lib, fp = libfp
    f = pcbnew.FootprintLoad(LOCAL if lib == "strilas" else f"{FPDIR}/{lib}.pretty", fp)
    f.SetReference(ref); f.SetValue(mpn); f.SetPosition(V(x, y)); b.Add(f)
    t = pcbnew.PCB_TEXT(b); t.SetText(mpn); t.SetPosition(V(x, y - 4.0))
    t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(pcbnew.VECTOR2I(MM(0.65), MM(0.65)))
    t.SetTextThickness(MM(0.11)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)


def main():
    b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)
    rows = []
    for i, (mpn, fp, note) in enumerate(IR):
        col, rw = i % 4, i // 4
        x = -24 + col * 16; y = 7 - rw * 14
        add(b, f"D{i+1}", fp, mpn, x, y); rows.append((f"D{i+1}", mpn, fp[1], note))
    title = pcbnew.PCB_TEXT(b); title.SetText("STRILAS SAMPLER v3 — IR-emitter 850/860nm fler-märkes (lager-koll, EJ best.)")
    title.SetPosition(V(0, 17)); title.SetLayer(pcbnew.F_SilkS)
    title.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0))); title.SetTextThickness(MM(0.16))
    title.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(title)
    W, H = 36, 14
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
            p = f.GetPosition(); w.writerow([f.GetReference(), f"{p.x/1e6-OX:.3f}", f"{OY-p.y/1e6:.3f}",
                                             "bottom" if f.IsFlipped() else "top", f.GetOrientationDegrees()])
    print(f"{PCB}: {len(rows)} IR-emitter-varianter (fler-märkes). BOM+centroid skrivna.")
    for ref, mpn, foot, note in rows: print(f"  {ref}: {mpn:18} {note}")


if __name__ == "__main__":
    main()
