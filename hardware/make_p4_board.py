#!/usr/bin/env python3
"""STRILAS — enkelt PCB av ESP32-P4-WIFI6 (Waveshare, 71.05×21.00 mm) för monterings-
visualisering: kort-outline, 4 hörn-monteringshål, 2 kant-pinrader (2.54 mm), USB-C-markering.
Inte ett tillverknings-kort — bara mekanik/montering för stacken mot optikkortet."""
import pcbnew

OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
FPDIR = "/usr/share/kicad/footprints"


def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))


def main():
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(2)
    HW, HH = 35.525, 10.5          # halv 71.05 × 21.00

    # outline
    pts = [(-HW, -HH), (HW, -HH), (HW, HH), (-HW, HH)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1) % 4]))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)

    def hole(ref, x, y, fp="MountingHole:MountingHole_2.2mm_M2"):
        lib, name = fp.split(":")
        f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", name)
        f.SetReference(ref); f.SetPosition(V(x, y)); b.Add(f)

    # 4 hörn-monteringshål (M2), ~3 mm in från hörnen (Waveshare ~6 mm-tabb)
    mx, my = HW - 3.0, HH - 3.0
    for i, (sx, sy) in enumerate([(-1, 1), (1, 1), (-1, -1), (1, -1)]):
        hole(f"MP{i+1}", sx*mx, sy*my)

    # 2 kant-pinrader (1×20, 2.54), längs långsidorna, ~18 mm isär
    for ref, yy in (("J_L", 9.0), ("J_R", -9.0)):
        f = pcbnew.FootprintLoad(f"{FPDIR}/Connector_PinHeader_2.54mm.pretty",
                                 "PinHeader_1x20_P2.54mm_Vertical")
        f.SetReference(ref); f.SetPosition(V(0, yy)); f.SetOrientationDegrees(90); b.Add(f)

    # USB-C + ESP-modul-markering (silk)
    def silk_rect(x0, y0, x1, y1, txt):
        for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetLayer(pcbnew.F_SilkS); s.SetWidth(MM(0.15)); b.Add(s)
        t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetPosition(V((x0+x1)/2, (y0+y1)/2))
        t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2))); b.Add(t)
    silk_rect(-34, -4, -29, 4, "USB-C")          # USB-C vänster ände
    silk_rect(22, -7, 33, 7, "ESP32-P4")         # ESP-modul höger ände

    pcbnew.SaveBoard("hardware/p4-board.kicad_pcb", b)
    print("wrote hardware/p4-board.kicad_pcb (71.05×21.00, 4 M2-hål, 2×1x20 kant-rader)")


if __name__ == "__main__":
    main()
