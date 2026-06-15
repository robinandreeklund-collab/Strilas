#!/usr/bin/env python3
"""STRILAS — efterbearbeta vapen-kortets routning till fab-färdigt skick:
  1) kopparplan: In1.Cu = GND, In2.Cu = VBAT, B.Cu = GND (retur), F.Cu = GND-fyll
  2) fyll zoner, rapportera oroutade

(Effektspår routas breda via klass 'power' i DSN; termiska vior läggs FÖRE routning.)
Körs efter ses_apply.py. Idempotent: tar bort gamla zoner först.
"""
import pcbnew

PCB = "hardware/weapon-module.kicad_pcb"
OX, OY = 150.0, 120.0
MM = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))


def main():
    b = pcbnew.LoadBoard(PCB)

    # ta bort ev. gamla zoner
    for z in list(b.Zones()):
        b.Remove(z)

    # 3) kopparplan över kort-outline (21×31 halv → marginal 0,3)
    def add_zone(layer, netname):
        z = pcbnew.ZONE(b)
        z.SetLayer(layer)
        z.SetNetCode(b.FindNet(netname).GetNetCode())
        z.SetLocalClearance(MM(0.25))
        z.SetMinThickness(MM(0.2))
        z.SetIsFilled(False)
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in [(-20.7, -30.7), (20.7, -30.7), (20.7, 30.7), (-20.7, 30.7)]:
            ch.Append(V(x, y))
        ch.SetClosed(True)
        z.AddPolygon(ch)
        b.Add(z)
        return z

    add_zone(pcbnew.In1_Cu, "GND")     # inre plan 1 = GND
    add_zone(pcbnew.In2_Cu, "VBAT")    # inre plan 2 = VBAT (effekt)
    add_zone(pcbnew.B_Cu, "GND")       # baksida = GND-retur (+ termisk spridning)
    add_zone(pcbnew.F_Cu, "GND")       # framsidans öppna ytor = GND

    # 4) fyll
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())

    pcbnew.SaveBoard(PCB, b)
    b.BuildConnectivity()
    try:
        un = b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError:
        un = b.GetConnectivity().GetUnconnectedCount()
    ntr = len([t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T])
    nvi = len([t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T])
    print(f"  4 zoner fyllda (In1=GND, In2=VBAT, B=GND, F=GND-fyll)")
    print(f"  {ntr} spår + {nvi} vior, oroutade={un}")


if __name__ == "__main__":
    main()
