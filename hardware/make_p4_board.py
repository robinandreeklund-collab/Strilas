#!/usr/bin/env python3
"""STRILAS — monteringsmodell av ESP32-P4-WIFI6 (Waveshare, 71.05×21.00 mm).
Geometrin är uppmätt ur Waveshares måttritning (ESP32-P4-WIFI6-details-size),
eftersom ingen STEP-fil finns. Alla mått verifierade mot ritningens kotor:

  • kort 71.05 × 21.00 mm, tjocklek 1.61 mm
  • 2 castellerade pinrader (1×20, 2.54 mm), pin-1 = 4.52 mm från vänsterkant
  • pinrader 9.28 mm från kortcentrum (≈1.22 mm från långsidorna)
  • 4 monteringshål:
      vänster par (USB-änden)  x = -34.06   (1.46 mm från vänsterkant)
      höger  par (ESP-modulen) x = +19.73   (vid modulens vänsterkant)
      bägge i y = ±9.15 mm (i linje med pinraderna)
  • ESP32-P4-modul upptar höger 18.27 mm (efter sista pinnen → högerkant)
  • USB-C i vänster ände

Inte ett tillverknings-kort — bara mekanik/montering för stacken mot optikkortet.
"""
import pcbnew

OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
FPDIR = "/usr/share/kicad/footprints"

# --- uppmätt geometri (mm, kortcentrum = origo) ---
HW, HH = 35.525, 10.5            # halv 71.05 × 21.00
PIN1_X = -31.005                 # 4.52 mm från vänsterkant (-35.525 + 4.52)
PITCH = 2.54
NPIN = 20
ROW_Y = 9.28                     # pinradernas y-avstånd från centrum
HOLE_Y = 9.15                    # monteringshålens y
HOLE_XL = -34.06                 # vänster par (USB-hörnet)
HOLE_XR = 19.73                  # höger par (ESP-modulens vänsterkant)


def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))


def main():
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(2)

    # outline
    pts = [(-HW, -HH), (HW, -HH), (HW, HH), (-HW, HH)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i + 1) % 4]))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)

    def hole(ref, x, y, fp="MountingHole:MountingHole_2.2mm_M2"):
        lib, name = fp.split(":")
        f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", name)
        f.SetReference(ref); f.SetPosition(V(x, y)); b.Add(f)

    # 4 monteringshål (M2) — uppmätta positioner
    hole("MP1", HOLE_XL, HOLE_Y)    # topp-vänster (USB)
    hole("MP2", HOLE_XL, -HOLE_Y)   # botten-vänster (USB)
    hole("MP3", HOLE_XR, HOLE_Y)    # topp-höger (ESP-modul)
    hole("MP4", HOLE_XR, -HOLE_Y)   # botten-höger (ESP-modul)

    # 2 castellerade pinrader (1×20, 2.54), pin-1 = 4.52 mm från vänsterkant.
    # OBS: footprintens origo = pin-1; raden går +x därifrån (pin1@-31.0 → pin20@+17.25).
    for ref, yy in (("J_TOP", ROW_Y), ("J_BOT", -ROW_Y)):
        f = pcbnew.FootprintLoad(f"{FPDIR}/Connector_PinHeader_2.54mm.pretty",
                                 "PinHeader_1x20_P2.54mm_Vertical")
        f.SetReference(ref); f.SetPosition(V(PIN1_X, yy))
        f.SetOrientationDegrees(90); b.Add(f)

    # silk-markeringar (USB-C + ESP-modul + pin-1)
    def silk_rect(x0, y0, x1, y1, txt):
        for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                     ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetLayer(pcbnew.F_SilkS)
            s.SetWidth(MM(0.15)); b.Add(s)
        t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetPosition(V((x0 + x1) / 2, (y0 + y1) / 2))
        t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2))); b.Add(t)

    silk_rect(-35.5, -5.5, -31.0, 5.5, "USB-C")          # USB-C, vänster ände
    silk_rect(17.3, -8.5, 35.5, 8.5, "ESP32-P4")         # ESP-modul, 18.27 mm höger zon
    # pin-1-markör
    p1 = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_CIRCLE)
    p1.SetCenter(V(PIN1_X, ROW_Y + 1.8)); p1.SetEnd(V(PIN1_X + 0.4, ROW_Y + 1.8))
    p1.SetLayer(pcbnew.F_SilkS); p1.SetWidth(MM(0.2)); b.Add(p1)

    pcbnew.SaveBoard("hardware/p4-board.kicad_pcb", b)
    print("wrote hardware/p4-board.kicad_pcb (71.05×21.00; 4 M2-hål uppmätta; 2×1x20, pin1@4.52mm)")


if __name__ == "__main__":
    main()
