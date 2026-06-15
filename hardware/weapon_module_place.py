#!/usr/bin/env python3
"""STRILAS — bygger en PLACERAD KiCad-PCB för vapen-modulen från netlistan (pcbnew-API).
Laddar footprints, placerar enligt weapon_emitter_layout, tilldelar nät, ritar 42×62-outline
+ kamerahål, 4 lager. Sparar weapon-module.kicad_pcb (öppningsbar i KiCad, redo att routa).

PLATSHÅLLAR-footprints (byt mot exakt del före skarp fab):
  D2/D3  LED_1206  → ams-OSRAM OSLON Black SFH 47xx (custom pad + thermal)
  U1     Bosch_LGA-14 → InvenSense ICM-45686 LGA-14 (verifiera pinout!)
"""
import pcbnew

FPDIR = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM
OX, OY = 150.0, 120.0          # offset så koordinaterna blir positiva på arket


def V(x_mm, y_mm):             # layout-y är upp+; pcbnew-y är ned+ → negera
    return pcbnew.VECTOR2I(MM(OX + x_mm), MM(OY - y_mm))


# ref -> (lib, footprint, x_mm, y_mm, rot, value)
PARTS = {
    "J1": ("Connector_PinHeader_2.54mm", "PinHeader_2x05_P2.54mm_Vertical", 0, -27, 0, "→P4 2x5"),
    "F1": ("Fuse", "Fuse_1206_3216Metric", -14, -20, 0, "PTC 1A"),
    "Q1": ("Package_TO_SOT_SMD", "SOT-23", -8, -20, 0, "AO3401 revP"),
    "R1": ("Resistor_SMD", "R_0805_2012Metric", -3, -20, 0, "100k"),
    "D1": ("Diode_SMD", "D_SMB", 3, -20, 0, "SMBJ12A TVS"),
    "C1": ("Capacitor_SMD", "C_1206_3216Metric", 9, -20, 0, "10uF"),
    "R2": ("Resistor_SMD", "R_2512_6332Metric", -6, 12, 0, "Rset 3R3"),
    "C2": ("Capacitor_SMD", "CP_Elec_6.3x7.7", 7, 12, 0, "220uF"),
    "D2": ("LED_SMD", "LED_1206_3216Metric", -10, 20, 0, "940nm*"),
    "D3": ("LED_SMD", "LED_1206_3216Metric", 10, 20, 0, "940nm*"),
    "Q2": ("Package_TO_SOT_SMD", "SOT-23", 16.5, -7, 0, "AO3400 gate"),
    "R3": ("Resistor_SMD", "R_0805_2012Metric", 16.5, -12, 0, "220R"),
    "U1": ("Package_LGA", "Bosch_LGA-14_3x2.5mm_P0.5mm", -16.5, 0, 0, "ICM-45686*"),
    "C3": ("Capacitor_SMD", "C_0402_1005Metric", -16.5, 7, 0, "100nF"),
    "C4": ("Capacitor_SMD", "C_0402_1005Metric", -16.5, -7, 0, "100nF"),
    "C5": ("Capacitor_SMD", "C_0805_2012Metric", -12, 0, 0, "1uF"),
    "H1": ("MountingHole", "MountingHole_2.5mm", 0, 27.5, 0, "M2.5"),
    "H2": ("MountingHole", "MountingHole_2.5mm", -17.5, -28.5, 0, "M2.5"),
    "H3": ("MountingHole", "MountingHole_2.5mm", 17.5, -28.5, 0, "M2.5"),
}

# nät -> [(ref, pad), ...]   (från weapon-module.net)
NETS = {
    "+3V3":   [("C3", "1"), ("C4", "1"), ("C5", "1"), ("J1", "4"), ("U1", "1"), ("U1", "2")],
    "GND":    [("C1", "2"), ("C2", "2"), ("C3", "2"), ("C4", "2"), ("C5", "2"), ("D1", "2"),
               ("J1", "2"), ("J1", "5"), ("Q2", "2"), ("R1", "2"), ("U1", "3")],
    "IMU_INT": [("J1", "10"), ("U1", "8")],
    "IR_MOD": [("J1", "3"), ("R3", "1")],
    "LED_CATH": [("D3", "2"), ("Q2", "3")],
    "LED_MID": [("D2", "2"), ("D3", "1")],
    "MISO":   [("J1", "8"), ("U1", "6")],
    "MOSI":   [("J1", "7"), ("U1", "5")],
    "N$1":    [("Q1", "1"), ("R1", "1")],
    "N$2":    [("D2", "1"), ("R2", "2")],
    "Q1_GATE": [("Q2", "1"), ("R3", "2")],
    "SCK":    [("J1", "6"), ("U1", "4")],
    "VBAT":   [("C1", "1"), ("C2", "1"), ("D1", "1"), ("Q1", "2"), ("R2", "1")],
    "VBAT_F": [("F1", "2"), ("Q1", "3")],
    "VBAT_IN": [("F1", "1"), ("J1", "1")],
    "nCS":    [("J1", "9"), ("U1", "7")],
}


def main():
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    fps = {}
    for ref, (lib, fp, x, y, rot, val) in PARTS.items():
        f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", fp)
        if f is None:
            print(f"  !! kunde inte ladda {lib}:{fp} ({ref})"); continue
        f.SetReference(ref); f.SetValue(val)
        f.SetPosition(V(x, y))
        if rot: f.SetOrientationDegrees(rot)
        board.Add(f); fps[ref] = f
    print(f"  placerade {len(fps)}/{len(PARTS)} komponenter")

    # nät
    for name, nodes in NETS.items():
        net = pcbnew.NETINFO_ITEM(board, name); board.Add(net)
        for ref, padname in nodes:
            f = fps.get(ref)
            if not f: continue
            for pad in f.Pads():
                if pad.GetName() == padname:
                    pad.SetNet(net)
    print(f"  tilldelade {len(NETS)} nät")

    # board-outline (rektangel 42×62) på Edge.Cuts
    pts = [(-21, -31), (21, -31), (21, 31), (-21, 31)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(*pts[i])); seg.SetEnd(V(*pts[(i+1) % 4]))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(MM(0.15)); board.Add(seg)
    # kamerahål (Ø16) i mitten på Edge.Cuts
    cam = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_CIRCLE)
    cam.SetCenter(V(0, -4)); cam.SetEnd(V(8, -4))
    cam.SetLayer(pcbnew.Edge_Cuts); cam.SetWidth(MM(0.15)); board.Add(cam)

    pcbnew.SaveBoard("hardware/weapon-module.kicad_pcb", board)
    print("  sparade hardware/weapon-module.kicad_pcb")


if __name__ == "__main__":
    main()
