#!/usr/bin/env python3
"""Brygga de 2 emitter-nät Freerouting inte når (D2 inringad): N$2 (Rset→D2-anod) och
LED_MID (D2-katod→D3-anod). Via direkt på respektive padd → B.Cu genom de FRIA marginalerna
(topp y>=25 / vänsterkant x<=-16) där inga signaler routats. Körs efter ses_apply, FÖRE finish
(så GND-planet rensar runt). Per-nät paddsökning (robust mot pad-numrering)."""
import pcbnew
PCB = "hardware/weapon-module.kicad_pcb"
MM = pcbnew.FromMM


def V(x, y): return pcbnew.VECTOR2I(MM(150 + x), MM(120 - y))


def main():
    b = pcbnew.LoadBoard(PCB)
    def pads(net):
        nc = b.FindNet(net).GetNetCode()
        return nc, [p.GetPosition() for f in b.GetFootprints() for p in f.Pads() if p.GetNetCode() == nc]
    def via(p, nc):
        v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(nc); b.Add(v)
    def btrk(a, c, nc, w=0.4):
        t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c)
        t.SetWidth(MM(w)); t.SetLayer(pcbnew.B_Cu); t.SetNetCode(nc); b.Add(t)
    def bridge(net, wps):
        nc, pl = pads(net)
        pl.sort(key=lambda p: p.x)
        a, c = pl[0], pl[-1]
        via(a, nc); via(c, nc)
        chain = [a] + [V(*w) for w in wps] + [c]
        for i in range(len(chain) - 1):
            btrk(chain[i], chain[i + 1], nc)
        print(f"  {net}: bryggad ({len(pl)} paddar)")
    # LED_MID: D2-katod ↔ D3-anod via toppen (y=26, fri baksida ovan emittrarna)
    bridge("LED_MID", [(-12, 26), (12, 26)])
    # N$2: Rset ↔ D2-anod via vänsterkanten (x=-16, fri)
    bridge("N$2", [(-16, 17), (-16, 22)])
    pcbnew.SaveBoard(PCB, b)
    b.BuildConnectivity()
    try: un = b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError: un = b.GetConnectivity().GetUnconnectedCount()
    print(f"  oroutade = {un}")


if __name__ == "__main__":
    main()
