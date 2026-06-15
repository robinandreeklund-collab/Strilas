#!/usr/bin/env python3
"""De 2 emitter-näten Freerouting inte når (3-padds OSLON-anoder inringade av lins/
kamerahål/ben): N$2 (Rset→D2-anod) och LED_MID (D2-katod→D3-anod). Dras explicit på
F.Cu genom fria kanaler. Anod = nedre padd (nås underifrån), katod = övre.
Körs efter ses_apply, FÖRE finish."""
import pcbnew

PCB = "hardware/weapon-module.kicad_pcb"
OX, OY = 150.0, 120.0
MM = pcbnew.FromMM


def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))


def main():
    b = pcbnew.LoadBoard(PCB)
    def padpos(ref, name, pick):
        cs = [p.GetPosition() for f in b.GetFootprints() if f.GetReference() == ref
              for p in f.Pads() if p.GetName() == name]
        cs.sort(key=lambda v: v.y)            # störst .y = lägst i kort → 'lo'(anod)
        return cs[-1] if pick == "lo" else cs[0]
    def track(pts, net, w=0.4):
        n = b.FindNet(net).GetNetCode()
        for i in range(len(pts) - 1):
            t = pcbnew.PCB_TRACK(b); t.SetStart(pts[i]); t.SetEnd(pts[i+1])
            t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(n); b.Add(t)

    r2 = padpos("R2", "2", "lo"); d2a = padpos("D2", "1", "lo")
    d2k = padpos("D2", "2", "hi"); d3a = padpos("D3", "1", "lo")
    # N$2: R2.2 → upp längs vänster → D2-anod underifrån
    track([r2, V(-12, 14), d2a], "N$2")
    # LED_MID: D2-katod → upp/över (y26, under kollimatorerna) → höger → D3-anod från höger
    track([d2k, V(-12, 26), V(20, 26), V(20, 22), d3a], "LED_MID")

    pcbnew.SaveBoard(PCB, b)
    b.BuildConnectivity()
    try: un = b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError: un = b.GetConnectivity().GetUnconnectedCount()
    print(f"  2 emitter-spår (F.Cu) tillagda; oroutade = {un}")


if __name__ == "__main__":
    main()
