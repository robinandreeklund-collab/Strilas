#!/usr/bin/env python3
"""STRILAS — ta bort ref-des + värde + fristående titel-text från SILKSCREEN (F/B.SilkS).
NextPCB monterar SMT från centroid+BOM → silk-texter behövs ej, och auto-placerade beteckningar
hamnar ofta över pads (fabriken klipper dem → trasig/oläslig text). Detta döljer alla
footprinters referens/värde-text på silk + raderar fristående silk-PCB_TEXT. KOMPONENT-
OUTLINES (footprint-grafik) och pin-1-markörer behålls. Körs FÖRE gerber-export.
Kör:  python3 hardware/strip_fab_silk.py <board.kicad_pcb>
"""
import sys, pcbnew
SILK = (pcbnew.F_SilkS, pcbnew.B_SilkS)
def strip(path):
    b = pcbnew.LoadBoard(path); n_txt = n_std = 0
    for f in b.GetFootprints():
        for t in (f.Reference(), f.Value()):
            if t.GetLayer() in SILK and t.IsVisible():
                t.SetVisible(False); n_txt += 1
        # ev. extra användartext i footprinten på silk
        for it in f.GraphicalItems():
            if it.GetClass() in ("PCB_TEXT","FP_TEXT") and it.GetLayer() in SILK and it.IsVisible():
                it.SetVisible(False); n_txt += 1
    for d in list(b.GetDrawings()):
        if d.GetClass() in ("PCB_TEXT","PCB_TEXTBOX") and d.GetLayer() in SILK:
            b.Remove(d); n_std += 1
    pcbnew.SaveBoard(path, b)
    print(f"  {path}: dolde {n_txt} ref/värde-texter, raderade {n_std} fristående silk-texter")
if __name__ == "__main__":
    strip(sys.argv[1])
