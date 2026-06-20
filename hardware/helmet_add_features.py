#!/usr/bin/env python3
"""STRILAS — inkrementell tillaggning pa hjalm-mb (BEVARAR de 831 routade spåren).
Rent ADDITIVT (ingen kraftvags-splits): TVS (D11) pa VBAT, batteri-sense (R11/R12/C22 ->
VBAT_SENSE -> J8[7]) och 4 testpunkter. Deterministisk routning via incr_route.
(Omvandpol-FET utelamnad: keyad JST-XH -> omvand isattning fysiskt forhindrad.)
Kor: python3 hardware/helmet_add_features.py  (fran repo-roten)"""
import pcbnew, sys
sys.path.insert(0, "hardware")
from incr_route import Router
from p4_pinmap import parse_net

PCB = "hardware/helmet-mb.kicad_pcb"; NET = "hardware/helmet-mb.net"
FPDIR = "/usr/share/kicad/footprints"; OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

NEW = {
    "D11": ("Diode_SMD", "D_SMB", -9.0, -37.0, 0),                 # TVS SMBJ12A pa VBAT (nara batteri J10)
    "R11": ("Resistor_SMD", "R_0805_2012Metric", -16.0, 13.5, 90), # sense topp 100k (VBAT->VBAT_SENSE)
    "R12": ("Resistor_SMD", "R_0805_2012Metric", -16.0, 18.0, 90), # sense botten 47k
    "C22": ("Capacitor_SMD", "C_0805_2012Metric", -20.0, 18.0, 90),# sense-filter 100nF
}


def main():
    comps, nets = parse_net(NET)
    b = pcbnew.LoadBoard(PCB)
    have = {f.GetReference() for f in b.GetFootprints()}
    for ref, (lib, fp, x, y, rot) in NEW.items():
        if ref in have:
            print(f"  {ref} finns"); continue
        f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", fp)
        f.SetReference(ref); f.SetPosition(V(x, y))
        if rot: f.SetOrientationDegrees(rot)
        b.Add(f); print(f"  + {ref} @({x},{y})")
    netpad = {(r, p): nm for nm, nodes in nets.items() for r, p in nodes}
    def gn(nm):
        ni = b.FindNet(nm)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni)
        return ni
    ch = 0
    for f in b.GetFootprints():
        for pd in f.Pads():
            w = netpad.get((f.GetReference(), pd.GetName()))
            if w and pd.GetNetname() != w:
                pd.SetNet(gn(w)); ch += 1
    print(f"  re-synkade {ch} pad-nat")
    pcbnew.SaveBoard(PCB, b)

    b = pcbnew.LoadBoard(PCB)
    R = Router(b, {"GND": [pcbnew.In1_Cu, pcbnew.B_Cu, pcbnew.F_Cu], "+3V3": [pcbnew.In2_Cu]})
    r = {}
    r["D11.K->VBAT"] = R.trace_between("D11", "1", "J10", "1")  # TVS-katod -> batteri-VBAT (J10.1, huvud-ö)
    r["D11.A->GND"] = R.to_plane("D11", "2")                    # TVS-anod GND via->In1
    r["R11.1->VBAT"] = R.trace_between("R11", "1", "J8", "2")                # sense topp -> J8[2]=VBAT (nara)
    r["R12.1-R11.2"] = R.trace_between("R12", "1", "R11", "2")               # VBAT_SENSE
    r["C22.1-R11.2"] = R.trace_between("C22", "1", "R11", "2")
    r["VSENSE-J8.7"] = R.trace_between("R11", "2", "J8", "7")
    r["R12.2->GND"] = R.to_plane("R12", "2"); r["C22.2->GND"] = R.to_plane("C22", "2")  # GND via->In1
    for k, v in r.items():
        print(f"  {k} = {v}")
    clr, un = R.finish()
    print(f"DRC clearance={clr} unconnected={un}")
    if clr == 0 and un == 0:
        pcbnew.SaveBoard(PCB, b); print("SPARAD ✓")
    else:
        print("EJ ren — behover justering")


if __name__ == "__main__":
    main()
