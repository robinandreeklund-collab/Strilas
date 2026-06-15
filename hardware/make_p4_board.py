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

    def place_fp(ref, lib, name, x, y, rot=0):
        f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", name)
        f.SetReference(ref); f.SetPosition(V(x, y))
        if rot: f.SetOrientationDegrees(rot)
        b.Add(f); return f

    # MALE pin-header — bara de stift som FAKTISKT används monteras (kortet köps olött,
    # man löder endast nödvändiga header-stift). Mating-korten (optik/FC) får FEMALE socket.
    #   pin n castellation: x = PIN1_X + (n-1)*PITCH ; raden går +x vid rot90.
    # SANDWICH-STACK: optik UNDER, FC OVANPÅ → stiften pekar åt MOTSATTA håll:
    #   Edge B (y=-9.28): pin 2..15 (VSYS..GPIO32) → optik UNDER → stift NEDÅT (B_Cu) → 1×14 @ pin2
    #   Edge A (y=+9.28): pin 6..17 (GPIO29..GPIO7) → FC OVAN    → stift UPPÅT (F_Cu) → 1×12 @ pin6
    jb = place_fp("J_B", "Connector_PinHeader_2.54mm", "PinHeader_1x14_P2.54mm_Vertical",
                  PIN1_X + 1 * PITCH, -ROW_Y, 90)
    jb.Flip(jb.GetPosition(), False)                 # edge B nedåt (mot optiken)
    place_fp("J_A", "Connector_PinHeader_2.54mm", "PinHeader_1x12_P2.54mm_Vertical",
             PIN1_X + 5 * PITCH, ROW_Y, 90)           # edge A uppåt (mot FC) — behåll F_Cu

    # USB-C-mottagare i vänster ände (3D-modell → syns i STEP) — visar var USB ligger.
    place_fp("USBC", "Connector_USB", "USB_C_Receptacle_HRO_TYPE-C-31-M-12", -34.0, 0, 90)
    # Sekundär USB 2.0 (host) → kamera (under): 4-pin header (V/D-/D+/G), stift NEDÅT.
    jcam = place_fp("J_CAM", "Connector_PinHeader_2.54mm", "PinHeader_1x04_P2.54mm_Vertical",
                    -4.0, 0, 90)
    jcam.Flip(jcam.GetPosition(), False)             # kamera-USB nedåt (mot kameran)

    # silk-markeringar (USB-C + ESP-modul + pin-1)
    def silk_rect(x0, y0, x1, y1, txt):
        for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                     ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetLayer(pcbnew.F_SilkS)
            s.SetWidth(MM(0.15)); b.Add(s)
        t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetPosition(V((x0 + x1) / 2, (y0 + y1) / 2))
        t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2))); b.Add(t)

    silk_rect(17.3, -8.5, 35.5, 8.5, "ESP32-P4")         # ESP-modul, 18.27 mm höger zon
    # text-etiketter (USB-C-änd + kamera-USB-pinout)
    for tx, ty, s in ((-34.0, 6.5, "USB-C"), (-4.0, 3.2, "USB->KAM"), (4.5, -3.0, "V D- D+ G")):
        t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetPosition(V(tx, ty))
        t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(pcbnew.VECTOR2I(MM(0.9), MM(0.9))); b.Add(t)
    # pin-1-markör
    p1 = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_CIRCLE)
    p1.SetCenter(V(PIN1_X, ROW_Y + 1.8)); p1.SetEnd(V(PIN1_X + 0.4, ROW_Y + 1.8))
    p1.SetLayer(pcbnew.F_SilkS); p1.SetWidth(MM(0.2)); b.Add(p1)

    pcbnew.SaveBoard("hardware/p4-board.kicad_pcb", b)
    print("wrote hardware/p4-board.kicad_pcb (71.05×21.00; 4 M2-hål uppmätta; 2×1x20, pin1@4.52mm)")


if __name__ == "__main__":
    main()
