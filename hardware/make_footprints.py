#!/usr/bin/env python3
"""STRILAS — generera kund-footprints (KiCad .kicad_mod) för delar utan biblioteksmatch.

1) InvenSense_LGA-14_2.5x3mm_ICM-456xx  — ICM-45686/45605 6-axlig IMU.
   Pinout verifierad mot TDK AN-000483 (EV_ICM-45605 EVB-guide, Figur 2) — pin-kompatibel
   med ICM-45686. 4 paddar vänster (1-4, topp→botten), 3 botten (5-7, v→h),
   4 höger (8-11, botten→topp), 3 topp (12-14, h→v). Pitch 0,5 mm, kropp 2,5×3,0 mm.

   1 AP_SDO/AP_AD0   2 RESV   3 RESV   4 INT1   5 VDDIO  6 GND   7 RESV
   8 VDD  9 INT2/FSYNC 10 RESV 11 RESV  12 AP_CS 13 AP_SCLK 14 AP_SDI

2) IR_Emitter_Vishay_VSMA1094750  — 940 nm hög-effekt-emitter (skottstråle).
   Land per Vishay-datablad DocNo 80365, ritning 6.550-5366.9-3: två sido-paddar
   (anod/katod) + central termisk padd. Katod = vänster + central slug (die-attach).
   Kropp 3,4×3,4 mm, Cu-area ~5,5×5,5 mm.
"""
import os

LIB = os.path.join(os.path.dirname(__file__), "strilas.pretty")


def pad(num, x, y, w, h, shape="roundrect", layers='"F.Cu" "F.Paste" "F.Mask"', rr=0.25):
    extra = f'(roundrect_rratio {rr})' if shape == "roundrect" else ""
    return (f'  (pad "{num}" smd {shape} (at {x:.4f} {y:.4f}) (size {w:.3f} {h:.3f}) '
            f'(layers {layers}) {extra})\n')


def line(x1, y1, x2, y2, layer, w=0.12):
    return (f'  (fp_line (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) '
            f'(stroke (width {w}) (type solid)) (layer "{layer}"))\n')


def circle(cx, cy, r, layer, w=0.12):
    return (f'  (fp_circle (center {cx:.3f} {cy:.3f}) (end {cx+r:.3f} {cy:.3f}) '
            f'(stroke (width {w}) (type solid)) (fill none) (layer "{layer}"))\n')


def rect(layer, hw, hh, w=0.1):
    s = ""
    pts = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    for i in range(4):
        a, b = pts[i], pts[(i+1) % 4]
        s += line(a[0], a[1], b[0], b[1], layer, w)
    return s


def model(path):
    return (f'  (model "{path}"\n    (offset (xyz 0 0 0))\n'
            f'    (scale (xyz 1 1 1))\n    (rotate (xyz 0 0 0))\n  )\n')


# storleksnära 3D-stand-ins (KiCad-paket): IMU≈QFN-16 3x3, emitter≈PLCC 3.5x3.5
M3D = "${KICAD6_3DMODEL_DIR}"
MDL_IMU = M3D + "/Package_DFN_QFN.3dshapes/QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm.step"
MDL_LED = M3D + "/LED_SMD.3dshapes/LED_WS2812B-Mini_PLCC4_3.5x3.5mm.step"


def header(name, descr):
    return (f'(footprint "{name}" (version 20221018) (generator strilas)\n'
            f'  (layer "F.Cu")\n  (descr "{descr}")\n'
            f'  (attr smd)\n'
            f'  (fp_text reference "REF**" (at 0 -3.2) (layer "F.SilkS")'
            f' (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
            f'  (fp_text value "{name}" (at 0 3.2) (layer "F.Fab")'
            f' (effects (font (size 0.8 0.8) (thickness 0.12))))\n')


# ---------------- ICM-456xx LGA-14 ----------------
def make_imu():
    name = "InvenSense_LGA-14_2.5x3mm_ICM-456xx"
    s = header(name, "TDK ICM-45686/45605 6-axis IMU, 14-pin LGA 2.5x3.0mm, 0.5mm pitch")
    BX, BY = 1.25, 1.50          # halv kropp (2.5 x 3.0)
    pw, ph = 0.40, 0.28          # sido-padd (lång axel = X)
    tw, th = 0.28, 0.40          # topp/botten-padd (lång axel = Y)
    xside = BX - 0.05            # paddcentrum nära kant (1.20)
    ytb = BY - 0.10              # 1.40
    ys = [0.75, 0.25, -0.25, -0.75]
    # vänster 1-4 (topp->botten)
    for i, y in enumerate(ys):
        s += pad(i+1, -xside, y, pw, ph)
    # botten 5-7 (vänster->höger): x = -0.5,0,+0.5
    for i, x in enumerate([-0.5, 0.0, 0.5]):
        s += pad(5+i, x, ytb, tw, th)
    # höger 8-11 (botten->topp): y = -0.75..+0.75
    for i, y in enumerate([-0.75, -0.25, 0.25, 0.75]):
        s += pad(8+i, xside, y, pw, ph)
    # topp 12-14 (höger->vänster): x = +0.5,0,-0.5
    for i, x in enumerate([0.5, 0.0, -0.5]):
        s += pad(12+i, x, -ytb, tw, th)
    # silk + fab + courtyard
    s += rect("F.Fab", BX, BY, 0.1)
    s += circle(-xside-0.45, 0.75, 0.12, "F.SilkS", 0.15)   # pin-1 markör
    s += line(-BX, -BY, -BX+0.4, -BY, "F.SilkS", 0.12)
    s += rect("F.CrtYd", BX+0.25, BY+0.25, 0.05)
    s += model(MDL_IMU)
    s += ")\n"
    open(os.path.join(LIB, name+".kicad_mod"), "w").write(s)
    print("wrote", name)


# ---------------- Vishay VSMA1094750 940nm ----------------
def make_led():
    name = "IR_Emitter_Vishay_VSMA1094750"
    s = header(name, "Vishay VSMA1094750X02 940nm high-power IR emitter, 3.4x3.4mm; "
                     "pad1=A(anod, hoger), pad2=K(katod, vanster+central termisk slug)")
    # Cu ~5.5x5.5. Sido-barrar (anod/katod) + central termisk slug (katod).
    side_w, side_h = 1.00, 2.80
    cen_w, cen_h = 1.90, 3.20
    xs = 1.95                 # sido-paddcentrum
    # pad 1 = anod (hoger)
    s += pad(1, xs, 0.0, side_w, side_h, rr=0.15)
    # pad 2 = katod (vanster sidobar)
    s += pad(2, -xs, 0.0, side_w, side_h, rr=0.15)
    # pad 2 = katod (central termisk slug, samma nat) -> dela paddnummer
    s += pad(2, 0.0, 0.0, cen_w, cen_h, rr=0.10)
    # kropp 3.4x3.4 (fab), katodmarkering, courtyard
    s += rect("F.Fab", 1.70, 1.70, 0.1)
    s += circle(0, 0, 1.55, "F.Fab", 0.1)                  # rund lins-kropp
    s += line(-2.95, 1.6, -2.45, 1.6, "F.SilkS", 0.15)     # katodstreck (vanster)
    s += circle(-2.7, 1.35, 0.12, "F.SilkS", 0.15)         # katodprick
    s += rect("F.CrtYd", 2.85, 2.85, 0.05)
    s += model(MDL_LED)
    s += ")\n"
    open(os.path.join(LIB, name+".kicad_mod"), "w").write(s)
    print("wrote", name)


if __name__ == "__main__":
    make_imu()
    make_led()
