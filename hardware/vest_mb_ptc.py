#!/usr/bin/env python3
"""STRILAS — lagg till PTC-sakring (F1) i serie pa vest-mb batteri-ingang, INKREMENTELLT
(bevarar 590 routade spar). Splits: J13.2 (VBAT_IN) -> F1 -> VBAT_RAW -> Q1.D. VBAT_RAW ar
ett 2-nods-nat -> ren insattning. Tva faser (pcbnew-SWIG: en LoadBoard/process).
  fas 1: python3 hardware/vest_mb_ptc.py        (add+resync+remove+save)
  fas 2: python3 hardware/vest_mb_ptc.py route  (route+save)"""
import pcbnew, sys, math
sys.path.insert(0, "hardware")
from incr_route import Router, xy
from p4_pinmap import parse_net

PCB = "hardware/vest-mb.kicad_pcb"; NET = "hardware/vest-mb.net"
FPDIR = "/usr/share/kicad/footprints"; OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

NEW = {"F1": ("Fuse", "Fuse_1812_4532Metric", 36.5, -10.5, 90)}  # PTC 1812 nara J13/Q1


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
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    for nr in NEW:
        for of in b.GetFootprints():
            if of.GetReference() != nr and any(p1.GetEffectiveShape().Collide(p2.GetEffectiveShape(), int(0.15e6))
                                               for p1 in fps[nr].Pads() for p2 in of.Pads()):
                print(f"  !! PAD-OVERLAP {nr}<->{of.GetReference()}")
    netpad = {(r, p): nm for nm, nodes in nets.items() for r, p in nodes}
    def gn(nm):
        ni = b.FindNet(nm)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni)
        return ni
    # J13.2 ar nu VBAT_IN -> ta bort gamla VBAT_RAW-spar som ror J13.2-padden
    j13_2 = [p for p in fps["J13"].Pads() if p.GetName() == "2"][0]
    sh = j13_2.GetEffectiveShape()
    jl = {L for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if j13_2.IsOnLayer(L)}
    ch = 0
    for f in b.GetFootprints():
        for pd in f.Pads():
            w = netpad.get((f.GetReference(), pd.GetName()))
            if w and pd.GetNetname() != w:
                pd.SetNet(gn(w)); ch += 1
    print(f"  re-synkade {ch} pad-nat")
    rem = 0
    for t in list(b.GetTracks()):
        tl = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu} if t.Type() == pcbnew.PCB_VIA_T else {t.GetLayer()}
        if (jl & tl) and t.GetEffectiveShape().Collide(sh, int(0.2e6)):
            b.Remove(t); rem += 1
    print(f"  tog bort {rem} gamla spar vid J13.2")
    pcbnew.SaveBoard(PCB, b)
    print("  fas 1 klar -> kor 'route'")


def route_phase():
    b = pcbnew.LoadBoard(PCB)
    R = Router(b, {"GND": [pcbnew.In1_Cu, pcbnew.F_Cu, pcbnew.B_Cu], "VBAT": [pcbnew.In2_Cu]})
    r = {}
    r["J13.2-F1(VBAT_IN)"] = R.trace_between("J13", "2", "F1", "1")
    r["F1-Q1.D(VBAT_RAW)"] = R.trace_between("F1", "2", "Q1", "3")
    for k, v in r.items():
        print(f"  {k} = {v}")
    print("  connect_islands(VBAT_RAW):", R.connect_islands("VBAT_RAW"))
    print("  connect_islands(VBAT_IN):", R.connect_islands("VBAT_IN"))
    clr, un = R.finish()
    print(f"DRC clearance={clr} unconnected={un}")
    if clr == 0 and un == 0:
        pcbnew.SaveBoard(PCB, b); print("SPARAD ✓")
    else:
        print("EJ ren")


if __name__ == "__main__":
    (route_phase if len(sys.argv) > 1 and sys.argv[1] == "route" else main)()
