#!/usr/bin/env python3
"""STRILAS — monteringsmodell av ESP32-P4-WIFI6 (Waveshare, 71.00×21.00 mm).

SELEKTIVA HEADERS (P4 köps olött; kund löder bara de stift som används):
  • Edge B (mot OPTIK): 1×14 @ pin 2 → pins 2-15 (VSYS..GPIO32). Fria: pin 1 (VBUS) nederst
    vid USB-C + pins 16-20 överst. (Optik J1 = 1×14.)
  • Edge A (mot FC):    1×15 @ pin 6 → pins 6-20 (GPIO29..GPIO25). Fria: pins 1-5 nederst vid
    USB-C (GPIO52/51/GND/31/30). (FC J1 = 1×15.)
  • FC matas dessutom 3V3+GND från edge B pins 3-5 via FC:s 1×03-kraft-tapp (J2), motsatt långsida.
Pin 1 (båda kanterna) ligger vid USB-C-änden (PIN1_X) → därav "fria nederst". INGEN flip
(tidigare flip speglade pad-XY → falskt 9,89mm-mating-larm; borttaget). Verifierat: socket-mitt-
vs-hål-mitt-offset matchar pin-täckningen (optik 4,95≈5,08mm; FC 6,48≈6,35mm; tapp 16,4≈16,5mm),
och i Fusion mot tillverkarens STEP (hardware/P4/ESP32-P4-WIFI6_3d-20260109.stp = full 3D-sanning).
HÅL-positioner DXF-exakta; elektrisk pin-mapping verifierad mot .net via p4_pinmap.py.

Geometrin EXAKT avläst ur Waveshares OFFICIELLA DXF/STEP-måttritning
(hardware/P4/ESP32-P4-WIFI6_*-20260109.dxf, cirkel-koordinater i mm @ 1:1):

  • kort 71.00 × 21.00 mm, tjocklek 1.6 mm
  • 2 castellerade pinrader (1×20, 2.54 mm), pin-1 = 4.49 mm från vänsterkant
  • pinrader ±8.89 mm från kortcentrum (radspann 17.78 = EXAKT 7×2.54; ≈1.61 mm från långsidorna)
    [tidigare 9.28 var en okuläravläsning — DXF ger 8.89, korrigerat → matchande socklar]
  • 4 monteringshål Ø1.7 (NPTH, för M1.6):
      vänster par (USB-änden)  x = -34.10   (1.40 mm från vänsterkant)
      höger  par (ESP-modulen) x = +20.07   (54.2 mm hål-hål-spann)
      bägge i y = ±9.125 mm (hål-spann 18.25)
  • ESP32-P4-modul upptar höger ~18 mm (efter sista pinnen → högerkant)
  • USB-C i vänster ände

Inte ett tillverknings-kort — bara mekanik/montering för stacken mot optikkortet.
"""
import pcbnew

OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
FPDIR = "/usr/share/kicad/footprints"

# --- EXAKT geometri ur officiell DXF (mm, kortets geometriska centrum = origo) ---
HW, HH = 35.5, 10.5              # halv 71.00 × 21.00
PIN1_X = -31.01                  # pin-1 castellation (DXF: 4.49 mm från vänsterkant)
PITCH = 2.54
NPIN = 20
ROW_Y = 8.89                     # pinradernas y från centrum (DXF: spann 17.78 = 7×2.54)
HOLE_Y = 9.125                   # monteringshålens y (DXF: spann 18.25)
HOLE_XL = -34.10                 # vänster par (USB-hörnet, 1.40 mm från vänsterkant)
HOLE_XR = 20.07                  # höger par (54.2 mm hål-hål-spann)


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

    def hole(ref, x, y):
        # exakt Ø1.7 NPTH (officiell P4 → M1.6) som en fristående footprint med NPTH-pad
        f = pcbnew.FOOTPRINT(b); f.SetReference(ref); f.SetPosition(V(x, y))
        p = pcbnew.PAD(f); p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        p.SetShape(pcbnew.PAD_SHAPE_CIRCLE); p.SetLayerSet(p.UnplatedHoleMask())
        p.SetSize(pcbnew.VECTOR2I(MM(1.7), MM(1.7)))
        p.SetDrillSize(pcbnew.VECTOR2I(MM(1.7), MM(1.7)))
        p.SetPosition(V(x, y)); f.Add(p); b.Add(f)

    # 4 monteringshål (Ø1.7 NPTH) — EXAKTA DXF-positioner
    hole("MP1", HOLE_XL, HOLE_Y)    # topp-vänster (USB)
    hole("MP2", HOLE_XL, -HOLE_Y)   # botten-vänster (USB)
    hole("MP3", HOLE_XR, HOLE_Y)    # topp-höger (ESP-modul)
    hole("MP4", HOLE_XR, -HOLE_Y)   # botten-höger (ESP-modul)

    def place_fp(ref, lib, name, x, y, rot=0):
        f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", name)
        f.SetReference(ref); f.SetPosition(V(x, y))
        if rot: f.SetOrientationDegrees(rot)
        b.Add(f); return f

    # MALE pin-header — kortet köps OLÖTT; kund löder ENDAST de stift som används (selektivt).
    # Mating-korten (optik/FC) får FEMALE socket. pin n castellation: x = PIN1_X + (n-1)*PITCH.
    #   Edge B (y=-8.89): pins 2..15 (VSYS..GPIO32) → optik  → 1×14 @ pin2
    #   Edge A (y=+8.89): pins 6..20 (GPIO29..GPIO25) → FC   → 1×15 @ pin6
    # INGEN flip (gamla flip-buggen speglade pad-XY → falskt 9,89mm-mating). pad-XY = verkliga
    # castellation-XY. Stift-RIKTNING (upp/ned i sandwich) modelleras ej — full 3D = tillverkar-STEP.
    place_fp("J_B", "Connector_PinHeader_2.54mm", "PinHeader_1x14_P2.54mm_Vertical",
             PIN1_X + 1 * PITCH, -ROW_Y, 90)          # edge B: pins 2-15 (optik-J1, 14 st)
    place_fp("J_A", "Connector_PinHeader_2.54mm", "PinHeader_1x15_P2.54mm_Vertical",
             PIN1_X + 5 * PITCH, ROW_Y, 90)           # edge A: pins 6-20 (FC-J1, 15 st)

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
    print("wrote hardware/p4-board.kicad_pcb (71.00×21.00; 4×Ø1.7 NPTH DXF-exakta; 2×1x20 @ ±8.89, pin1@4.49mm)")


if __name__ == "__main__":
    main()
