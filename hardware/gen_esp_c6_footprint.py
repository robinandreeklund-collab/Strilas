#!/usr/bin/env python3
"""STRILAS — genererar ESP32-C6-MINI-1 + ESP32-C6-MINI-1U footprints → hardware/strilas.pretty/.

Härlett ur Espressif "ESP32-C6-MINI-1 & MINI-1U Datasheet v1.5":
  • Modulbredd 13.20 mm; längd 16.60 mm (-1, PCB-antenn) / 12.50 mm (-1U, U.FL-kontakt).
  • 53 pads: 47 castellerade perimeter-pads (pin 1–47) + 4 hörn-GND (50–53) + center-GND-termik (48/49).
  • Perimeter-pad 0.70×0.40 mm, pitch 0.80 mm; hörn 0.70×0.70; center 3×3 termik 1.45 mm.
  • Pinout (DS tabell 3-1): vänster 1–11 (topp→botten), botten 12–24 (vä→hö), höger 25–35 (botten→topp),
    topp 36–47 (vä→hö). GND = 1,2,11,14,36~53. -1 har antenn-keepout ovanför pad-fältet.

BÅDA varianterna delar EXAKT samma land pattern; bara kropps-outline (antenn-area) skiljer →
samma footprint duger för placering, -1U valdes för STRILAS (extern antenn ut ur vapenhuset).

Kör:  python3 hardware/gen_esp_c6_footprint.py
"""
import os

PRETTY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strilas.pretty")
PITCH = 0.80
PER_W, PER_L = 0.40, 0.70          # perimeter-pad: bredd (pitch-led) × längd (inåt)
CORNER = 0.70                      # hörn-GND-pad
TH_SZ, TH_P = 1.45, 1.95          # center-termik: padstorlek + pitch (3×3 → ~5.40 mm)
XW = 5.60                          # vänster/höger pad-centrum |x|
YH = 5.30                          # topp/botten pad-centrum |y| (+ hörn |x|/|y|)
BODY_W = 13.20                     # modulbredd
GND = {1, 2, 11, 14, *range(36, 54)}


def pad(num, x, y, sx, sy):
    return (f'  (pad "{num}" smd rect (at {x:.3f} {y:.3f}) (size {sx:.3f} {sy:.3f}) '
            f'(layers "F.Cu" "F.Paste" "F.Mask"))')


def lines_rect(x0, y0, x1, y1, layer, w):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    return [f'  (fp_line (start {a[0]:.3f} {a[1]:.3f}) (end {b[0]:.3f} {b[1]:.3f}) '
            f'(layer "{layer}") (width {w}))' for a, b in zip(pts, pts[1:])]


def build(name, body_len_top):
    """body_len_top = kroppens övre kant (+y); -1U = +6.25 (12.50 totalt), -1 = +10.35 (16.60, antenn)."""
    P = []
    # vänster: pin 1–11, topp→botten
    for i in range(11):
        P.append((i + 1, -XW, YH - 0.30 - PITCH * i, PER_L, PER_W))
    # botten: pin 12–24, vä→hö (13 st, centrerade)
    bx = -(12 * PITCH) / 2
    for k in range(13):
        P.append((12 + k, bx + PITCH * k, -YH, PER_W, PER_L))
    # höger: pin 25–35, botten→topp (11 st)
    for k in range(11):
        P.append((25 + k, XW, -(YH - 0.30) + PITCH * k, PER_L, PER_W))
    # topp: pin 36–47, vä→hö (12 st, centrerade)
    tx = -(11 * PITCH) / 2
    for k in range(12):
        P.append((36 + k, tx + PITCH * k, YH, PER_W, PER_L))
    # hörn-GND: 50 BL, 51 BR, 52 TL, 53 TR
    P += [(50, -YH, -YH, CORNER, CORNER), (51, YH, -YH, CORNER, CORNER),
          (52, -YH, YH, CORNER, CORNER), (53, YH, YH, CORNER, CORNER)]
    # center-termik 3×3: centrum=49, övriga=48 (samma GND-nät)
    for iy in (-1, 0, 1):
        for ix in (-1, 0, 1):
            num = 49 if (ix == 0 and iy == 0) else 48
            P.append((num, ix * TH_P, iy * TH_P, TH_SZ, TH_SZ))

    yb = -6.25                                  # nedre kropps-kant (gemensam)
    half = BODY_W / 2
    out = [f'(footprint "{name}" (version 20221018) (generator strilas) (layer "F.Cu")',
           '  (attr smd)',
           f'  (fp_text reference "REF**" (at 0 {yb-1.0:.2f}) (layer "F.SilkS")'
           ' (effects (font (size 1 1) (thickness 0.15))))',
           f'  (fp_text value "{name}" (at 0 {body_len_top+1.0:.2f}) (layer "F.Fab")'
           ' (effects (font (size 1 1) (thickness 0.15))))']
    # kropps-outline (F.Fab) + courtyard (F.CrtYd)
    out += lines_rect(-half, yb, half, body_len_top, "F.Fab", 0.10)
    out += lines_rect(-half - 0.25, yb - 0.25, half + 0.25, body_len_top + 0.25, "F.CrtYd", 0.05)
    # antenn-keepout-markering för -1 (ovanför pad-fältet)
    if body_len_top > 7:
        out += lines_rect(-half, YH + 0.5, half, body_len_top, "F.Fab", 0.10)
    # pin1-markör + silk
    out.append(f'  (fp_circle (center {-XW:.2f} {YH+0.6:.2f}) (end {-XW+0.3:.2f} {YH+0.6:.2f})'
               ' (layer "F.SilkS") (width 0.12) (fill none))')
    for num, x, y, sx, sy in P:
        out.append(pad(num, x, y, sx, sy))
    out.append(')')
    path = os.path.join(PRETTY, f"{name}.kicad_mod")
    with open(path, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"{path}: {len(P)} pads, kropp {BODY_W}×{body_len_top-yb:.2f} mm")


if __name__ == "__main__":
    build("ESP32-C6-MINI-1U", 6.25)    # 12.50 mm, U.FL extern antenn (STRILAS-val)
    build("ESP32-C6-MINI-1", 10.35)    # 16.60 mm, on-board PCB-antenn + keepout
