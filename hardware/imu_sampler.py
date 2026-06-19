#!/usr/bin/env python3
"""STRILAS — IMU-SAMPLER (DEMO, EJ FÖR TILLVERKNING).

Ett kort med 18 olika IMU-kandidater (samma klass eller bättre än IIM-42653 — högre dps,
lägre brus, hög-g, hög-vibration, samt 9-axel). Syfte: ladda upp BOM:en till NextPCB och se
vilka som finns i lager DIREKT → välj en tillgänglig och beställ den på de riktiga korten
(weapon/firecontrol/helmet). Footprints är korrekta paket; del-familjer är pin-kompatibla
(TDK 42xxx/45xxx, ST LSM6DS, Bosch BMI) så en footprint täcker flera MPN.

Kör: python3 hardware/imu_sampler.py  → hardware/imu-sampler.kicad_pcb
"""
import pcbnew

MM = pcbnew.FromMM
OX, OY = 150.0, 100.0
KI = "/usr/share/kicad/footprints"
TDK = ("hardware/strilas.pretty", "InvenSense_LGA-14_2.5x3mm_ICM-456xx")  # TDK 42xxx/45xxx pin-kompatibel
BOSCH = (f"{KI}/Package_LGA.pretty", "Bosch_LGA-14_3x2.5mm_P0.5mm")
ST = (f"{KI}/Package_LGA.pretty", "LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y")
LGA16 = (f"{KI}/Package_LGA.pretty", "LGA-16_3x3mm_P0.5mm")
QFN24 = (f"{KI}/Sensor_Motion.pretty", "InvenSense_QFN-24_3x3mm_P0.4mm")

# (ref, MPN, tillverkare, footprint, kort-spec, lång beskrivning)
IMUS = [
    ("U1", "IIM-42653", "TDK InvenSense", TDK, "6ax 4000dps 32g IND", "BASLINJE: 6-ax industri, ±32g/±4000dps, -40..+105C"),
    ("U2", "IIM-42652", "TDK InvenSense", TDK, "6ax 2000dps 16g IND", "6-ax industri, ±16g/±2000dps, -40..+105C"),
    ("U3", "ICM-42688-P", "TDK InvenSense", TDK, "6ax 2000dps LAGBRUS", "6-ax ultra-lagt brus (bast-i-klass gyro-brus) - precision"),
    ("U4", "ICM-42670-P", "TDK InvenSense", TDK, "6ax 2000dps LAGEFFEKT", "6-ax lag-effekt (datablad i repo)"),
    ("U5", "ICM-40609-D", "TDK InvenSense", TDK, "6ax 2000dps 32g HOGG", "6-ax hog-g ±32g"),
    ("U6", "ICM-45686", "TDK InvenSense", TDK, "6ax 4000dps NY LAGBRUS", "Ny-gen 6-ax, ±32g/±4000dps, lagre brus an 426xx"),
    ("U7", "ICM-42688-V", "TDK InvenSense", TDK, "6ax 2000dps variant", "ICM-42688 V-variant (brett lager)"),
    ("U8", "BMI270", "Bosch", BOSCH, "6ax 2000dps LAGEFFEKT", "6-ax lag-effekt (drone/wearable), brett lager"),
    ("U9", "BMI323", "Bosch", BOSCH, "6ax 2000dps NY", "6-ax ny-gen Bosch"),
    ("U10", "BMI160", "Bosch", BOSCH, "6ax 2000dps", "6-ax (legacy men brett lager)"),
    ("U11", "BMI088", "Bosch", LGA16, "6ax 2000dps 24g VIBR", "6-ax HOG-VIBRATION (drone/robot) - bra for vapen-rekyl. OBS LGA-16 4.5mm (footprint approx)"),
    ("U12", "LSM6DSR", "STMicro", ST, "6ax 4000dps", "6-ax ±4000dps (matchar IIM-42653 dps)"),
    ("U13", "LSM6DSO32", "STMicro", ST, "6ax 2000dps 32g", "6-ax ±32g/±2000dps lag-effekt"),
    ("U14", "LSM6DSV16X", "STMicro", ST, "6ax 4000dps FUSION", "6-ax ±4000dps + inbyggd sensor-fusion (MLC)"),
    ("U15", "ISM330DHCX", "STMicro", ST, "6ax 4000dps IND", "6-ax industri ±4000dps (maskin/robot)"),
    ("U16", "ASM330LHHX", "STMicro", ST, "6ax 4000dps AUTO", "6-ax fordon AEC-Q100, ±4000dps (robustast)"),
    ("U17", "ICM-20948", "TDK InvenSense", QFN24, "9ax (a+g+mag)", "9-AXEL accel+gyro+magnetometer - bäring utan GNSS"),
    ("U18", "MPU-9250", "TDK InvenSense", QFN24, "9ax (a+g+mag)", "9-AXEL legacy men brett lager (EOL - verifiera)"),
]

COLS, COLP, ROWP = 6, 19.0, 24.0
X0, Y0 = -(COLS - 1) * COLP / 2, (3 - 1) * ROWP / 2 + 4


def V(x, y):
    return pcbnew.VECTOR2I(int((OX + x) * 1e6), int((OY - y) * 1e6))


def text(b, x, y, s, h=1.0, layer=None, bold=False):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(layer or pcbnew.F_SilkS); t.SetPosition(V(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); t.SetTextThickness(MM(0.2 if bold else 0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    b.Add(t)


def main():
    b = pcbnew.BOARD()
    for i, (ref, mpn, mfr, (lib, fpn), spec, desc) in enumerate(IMUS):
        c, r = i % COLS, i // COLS
        x, y = X0 + c * COLP, Y0 - r * ROWP
        fp = pcbnew.FootprintLoad(lib, fpn)
        fp.SetReference(ref); fp.SetValue(mpn)
        fp.SetPosition(V(x, y))
        # dölj footprintens egna ref/value-texter (vi sätter egna tydliga silk-rader)
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.Add(fp)
        text(b, x, y + 6.5, ref, 1.2, bold=True)        # refdes ovanför
        text(b, x, y - 6.0, mpn, 1.1, bold=True)          # MPN under
        text(b, x, y - 7.8, spec, 0.7)                    # spec-rad

    # board-outline (rektangel) + titel
    W, H = COLS * COLP + 6, 3 * ROWP + 22
    x0, x1, y0, y1 = -W / 2, W / 2, -H / 2, H / 2
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        seg = pcbnew.PCB_SHAPE(b); seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(ax, ay)); seg.SetEnd(V(bx, by)); seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(MM(0.15)); b.Add(seg)
    text(b, 0, y1 - 4, "STRILAS  IMU-SAMPLER", 2.2, bold=True)
    text(b, 0, y1 - 7.5, "DEMO - EJ FOR TILLVERKNING - 18 IMU-kandidater for NextPCB lager-koll", 1.0)
    text(b, 0, y0 + 4, "Ladda upp BOM -> se vilka som finns i lager -> bestall den pa weapon/helmet/vest", 0.9)
    text(b, 0, y0 + 2, "Sok: 6-ax >=2000dps (IIM-42653-klass) / hog-g / hog-vibr / 9-ax. Valj tillganglig.", 0.8)

    pcbnew.SaveBoard("hardware/imu-sampler.kicad_pcb", b)
    print(f"hardware/imu-sampler.kicad_pcb: {len(IMUS)} IMU-kandidater, board {W:.0f}x{H:.0f} mm")


if __name__ == "__main__":
    main()
