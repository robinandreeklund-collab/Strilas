#!/usr/bin/env python3
"""STRILAS — lagg till batteri-sense (R7/R8/C8) + 4 testpunkter pa optik-kortet UTAN att
flytta befintliga (verifierade) delar. Laddar existerande board, adderar de nya footprintsen
pa valda fria fickor, och RE-SYNKAR alla pad-nat fran weapon-module.net (sa J1[6] gar fran NC
till VBAT_SENSE m.m.). Darefter omroutas via route_optik.py (bevarar placeringen).
Kor: python3 hardware/weapon_add_features.py   (fran repo-roten)"""
import pcbnew, sys
sys.path.insert(0, "hardware")
from p4_pinmap import parse_net

PCB = "hardware/weapon-module.kicad_pcb"
NET = "hardware/weapon-module.net"
FPDIR = "/usr/share/kicad/footprints"
OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

# nya delar: ref -> (lib, footprint, x, y, rot)  -- fria fickor i nedre omradet (lins Ø16 @ (0,-6))
# Batteri-sense (3 delar) i spar-fritt fack; VBAT_SENSE dras till J1[6]@(25.3,-7.6).
# (Testpunkter utelamnas pa optik: bandtatt precisionskort + IMU-SPI-header/kontakter
#  ger redan provatkomst; TP-tillagg skapade for mycket trangsel mot J1/CC-drivaren.)
NEW = {
    "R7":  ("Resistor_SMD", "R_0805_2012Metric", 14.0, -16.0, 0),    # Rst 100k (VBAT->VBAT_SENSE)
    "R8":  ("Resistor_SMD", "R_0805_2012Metric", 10.0, -16.0, 0),    # Rsb 47k (VBAT_SENSE->GND)
    "C8":  ("Capacitor_SMD", "C_0805_2012Metric", 6.0, -16.0, 0),    # Csns 100nF filter
}


def main():
    comps, nets = parse_net(NET)
    b = pcbnew.LoadBoard(PCB)
    have = {f.GetReference() for f in b.GetFootprints()}
    for ref, (lib, fp, x, y, rot) in NEW.items():
        if ref in have:
            print(f"  {ref} finns redan — hoppar"); continue
        f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", fp)
        if f is None:
            print(f"  !! kan ej ladda {lib}:{fp}"); sys.exit(1)
        f.SetReference(ref); f.SetPosition(V(x, y))
        if rot: f.SetOrientationDegrees(rot)
        b.Add(f); print(f"  + {ref} @({x},{y}) {fp}")
    # re-synka nat: bygg namn->NETINFO (skapa saknade), satt varje pad enligt .net
    netpad = {}
    for nm, nodes in nets.items():
        for r, p in nodes:
            netpad[(r, p)] = nm
    existing = {b.GetNetInfo().GetNetItem(nm) for nm in []}  # noop
    def get_net(nm):
        ni = b.FindNet(nm)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni)
        return ni
    changed = 0
    for f in b.GetFootprints():
        ref = f.GetReference()
        for pd in f.Pads():
            want = netpad.get((ref, pd.GetName()))
            if want is None:
                continue
            if pd.GetNetname() != want:
                pd.SetNet(get_net(want)); changed += 1
    print(f"  re-synkade {changed} pad-nat")
    pcbnew.SaveBoard(PCB, b)
    print(f"{PCB}: {len(NEW)} delar adderade, nat re-synkade (KOR route_optik.py for omroutning)")


if __name__ == "__main__":
    main()
