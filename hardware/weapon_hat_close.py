#!/usr/bin/env python3
"""STRILAS — VAPEN-HAT deterministisk STÄNGNING (steg 3): stäng nät som freerouting lämnade öppna,
utan freeroute-roulette. Använder incr_route.Router (4-lager; In1/In2 är TOMMA före GND-pour →
spår kan dra på inner-lager via via där F/B-maze fastnar). Bevarar ALL befintlig koppar.

Körs på det freeroutade kortet, FÖRE finish()/GND-pour. Kör: python3 hardware/weapon_hat_close.py <pcb>
"""
import sys, os, math, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from incr_route import Router

PCB = sys.argv[1] if len(sys.argv) > 1 else "hardware/weapon-hat.kicad_pcb"
F, In1, In2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
CU = [F, In1, In2, B]
# LAGER-PLAN (matchar övriga STRILAS-kort): In1=GND, In2=VBAT. → kraft droppar till plan via via,
# F/B frigörs för signaler. VBAT-pads kopplas till In2-planet (to_plane), ej trace-routas.
PLANES = {"GND": [F, In1, B], "VBAT": [In2]}


def split_nets(b, skip):
    """nät vars pads delar sig i >1 ö (= oansluten). Returnerar {net: [(ref,pad)...orphan]}. skip=plan-nät."""
    from collections import defaultdict
    R = Router(b, plane_nets={})
    netpads = defaultdict(list)
    for f in b.GetFootprints():
        for pd in f.Pads():
            n = pd.GetNetname()
            if n and n not in skip:
                netpads[n].append((f.GetReference(), pd.GetName(), id(pd)))
    out = {}
    for net, pads in netpads.items():
        if len(pads) < 2:
            continue
        main = R._main_cluster(net)
        orphans = [(r, p) for (r, p, i) in pads if i not in main]
        if orphans:                                    # alla lösa paddar (även helt orout. nät)
            out[net] = orphans
    return out


def main():
    b = pcbnew.LoadBoard(PCB)
    R = Router(b, plane_nets=PLANES)
    # STEG 3a: koppla VBAT-pads till In2-VBAT-planet (via) → kraftnätet ut ur F/B-trängseln.
    nv = 0
    for f in b.GetFootprints():
        for pd in f.Pads():
            if pd.GetNetname() == "VBAT":
                if R.to_plane(f.GetReference(), pd.GetName()):
                    nv += 1
    print(f"  close: VBAT→In2-plan, {nv} pads via", flush=True)
    # STEG 3b: stäng resterande split-signaler (ej GND/VBAT — de är plan)
    nets = split_nets(b, skip={"GND", "VBAT"})
    if not nets:
        print("  close: inga öppna nät"); return
    print(f"  close: stänger {list(nets)}", flush=True)
    for net, orphans in nets.items():
        for ref, pad in orphans:
            ok = R.trace(ref, pad)
            if not ok:
                # svårt nät → incr_route:s egen maze (F/B + via, inner-via-medveten)
                pts = R._net_points(net)
                done = False
                p0 = None
                for f in b.GetFootprints():
                    if f.GetReference() == ref:
                        for pp in f.Pads():
                            if pp.GetName() == pad: p0 = (f, pp)
                # hitta närmaste annan pad på nätet att maze:a mot
                if p0:
                    cand = sorted(((rr, qq) for (rr, qq, _i) in
                                   [(g.GetReference(), q.GetName(), id(q)) for g in b.GetFootprints() for q in g.Pads()
                                    if q.GetNetname() == net]
                                   if not (rr == ref and qq == pad)),
                                  key=lambda c: 0)
                    for rr, qq in cand[:6]:
                        if R.maze_route(ref, pad, rr, qq):
                            done = True; break
                print(f"    {net} {ref}.{pad}: {'OK(trace)' if ok else ('OK(maze)' if done else 'MISSLYCKADES')}", flush=True)
            else:
                print(f"    {net} {ref}.{pad}: OK(trace)", flush=True)
    pcbnew.SaveBoard(PCB, b)


if __name__ == "__main__":
    main()
