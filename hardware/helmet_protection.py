#!/usr/bin/env python3
"""STRILAS — lagg till KOMPLETT ingangsskydd pa hjalm-mb (PTC-sakring + omvandpol-P-FET) i
serie i batterimatningen, INKREMENTELLT (bevarar all routning). Splitsen J10->F1->Q2->VBAT
gors vattentat: gamla J10-VBAT-matningen tas bort och VBAT-natet sla ihop igen (connect_islands)
sa inget delas. Kor EFTER helmet_add_features (TVS+sense maste finnas). Fran repo-roten."""
import pcbnew, sys
sys.path.insert(0, "hardware")
from incr_route import Router
from p4_pinmap import parse_net

PCB = "hardware/helmet-mb.kicad_pcb"; NET = "hardware/helmet-mb.net"
FPDIR = "/usr/share/kicad/footprints"; OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))

NEW = {
    "F1": ("Fuse", "Fuse_1812_4532Metric", -9.0, 0.0, 0),          # PTC-sakring (VBAT_IN->VBAT_RAW), inter-sockel-gap
    "Q2": ("Package_TO_SOT_SMD", "SOT-23", -3.0, 0.0, 0),          # omvandpol-P-FET AO3401, gap (nara R7=main VBAT)
    "R13": ("Resistor_SMD", "R_0805_2012Metric", -0.5, 4.0, 90),   # gate->GND 100k (intill Q2)
    # (mata via maze-router: lang VBAT_IN J10->gap gar ej med L/Z)
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
    # pad-overlap koll
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    for nr in NEW:
        for of in b.GetFootprints():
            if of.GetReference() == nr:
                continue
            if any(p1.GetEffectiveShape().Collide(p2.GetEffectiveShape(), int(0.15e6))
                   for p1 in fps[nr].Pads() for p2 in of.Pads()):
                print(f"  !! PAD-OVERLAP {nr} <-> {of.GetReference()}");
    # re-synka nat (J10.1 VBAT->VBAT_IN, nya delar)
    netpad = {(r, p): nm for nm, nodes in nets.items() for r, p in nodes}
    def gn(nm):
        ni = b.FindNet(nm)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni)
        return ni
    j10_1 = [p for p in fps["J10"].Pads() if p.GetName() == "1"][0]
    ch = 0
    for f in b.GetFootprints():
        for pd in f.Pads():
            w = netpad.get((f.GetReference(), pd.GetName()))
            if w and pd.GetNetname() != w:
                pd.SetNet(gn(w)); ch += 1
    print(f"  re-synkade {ch} pad-nat")
    # ta bort gamla VBAT-spar som ror J10.1-padden (nu VBAT_IN). SPARA deras bortre andpunkter
    # (J10.1 var en VBAT-matnings-junction) -> aterskapas vid Q2.S sa VBAT-natet forblir helt.
    import json, math
    def _xy(p): return (round(p.x/1e6-OX, 3), round(OY-p.y/1e6, 3))
    sh = j10_1.GetEffectiveShape(); jp = _xy(j10_1.GetPosition())
    jl = {L for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if j10_1.IsOnLayer(L)}
    ends = []; rem = 0
    for t in list(b.GetTracks()):
        tl = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu} if t.Type() == pcbnew.PCB_VIA_T else {t.GetLayer()}
        if (jl & tl) and t.GetEffectiveShape().Collide(sh, int(0.2e6)):
            if t.Type() != pcbnew.PCB_VIA_T:
                s, e = _xy(t.GetStart()), _xy(t.GetEnd())
                far = e if math.hypot(e[0]-jp[0], e[1]-jp[1]) > math.hypot(s[0]-jp[0], s[1]-jp[1]) else s
                if math.hypot(far[0]-jp[0], far[1]-jp[1]) > 0.6:
                    ends.append(far)
            b.Remove(t); rem += 1
    json.dump(ends, open("/tmp/j10_ends.json", "w"))
    print(f"  tog bort {rem} gamla spar vid J10.1; sparade {len(ends)} junction-andpunkter")
    pcbnew.SaveBoard(PCB, b)
    print("  fas 1 klar (delar + nat + borttagning) — kor route_phase() i ny process")


def route_phase():
    """fas 2 (FRESK process pga pcbnew-SWIG): routa splitsen + sla ihop VBAT."""
    b = pcbnew.LoadBoard(PCB)
    R = Router(b, {"GND": [pcbnew.In1_Cu, pcbnew.B_Cu, pcbnew.F_Cu], "+3V3": [pcbnew.In2_Cu]})
    r = {}
    def hard(name, r1, p1, r2, p2, power=True):
        """kort: trace_between (ren direkt/L/Z). Annars maze, bredast kraftbredd som får plats."""
        if R.trace_between(r1, p1, r2, p2):
            r[name] = "OK (direkt)"; return True
        for w in ([0.5, 0.4, 0.3, 0.25] if power else [0.3, 0.25]):
            if R.maze_route(r1, p1, r2, p2, width=pcbnew.FromMM(w)):
                r[name] = f"OK maze @{w}mm"; return True
        r[name] = False; return False
    # series-kedjan J10 -> F1 -> Q2 (lang VBAT_IN gar via maze)
    hard("J10.1-F1(VBAT_IN)", "J10", "1", "F1", "1")
    hard("F1-Q2.D(VBAT_RAW)", "F1", "2", "Q2", "3")
    r["Q2.G-R13"] = R.trace_between("Q2", "1", "R13", "1")
    r["R13.2->GND"] = R.to_plane("R13", "2")
    # mata VBAT-natet fran Q2.S (-> R7, en main-VBAT-pad i gapet) + aterkoppla de pad som
    # J10-matningen forsorjde direkt (D11 TVS + J1 F9P-VCC blev oar nar stubbarna togs bort).
    hard("Q2.S->VBAT(R7)", "Q2", "2", "R7", "1")
    hard("D11.K->VBAT(R7)", "D11", "1", "R7", "1")
    hard("J1.VCC->VBAT(R7)", "J1", "1", "R7", "1")
    for k, v in r.items():
        print(f"  {k} = {v}")
    print("  connect_islands(VBAT):", R.connect_islands("VBAT"))
    clr, un = R.finish()
    print(f"DRC clearance={clr} unconnected={un}")
    if clr == 0 and un == 0:
        pcbnew.SaveBoard(PCB, b); print("SPARAD ✓")
    else:
        print("EJ ren — behover justering")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "route":
        route_phase()
    else:
        main()
