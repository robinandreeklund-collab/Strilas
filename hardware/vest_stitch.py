#!/usr/bin/env python3
"""STRILAS — handrouta det enda VBAT-stift Freerouting inte når på den KOMPAKTA väst-patchen:
R4.1 (höger LED-serieR) ligger ensam på högerkanten, isolerad från VBAT-trunken (vänster).
Dra VBAT R4.1→R3.1 på B_Cu längs den fria nederkant-korridoren. Körs efter ses_apply, i route_vest."""
import pcbnew
b = pcbnew.LoadBoard("hardware/vest-patch.kicad_pcb")
OX, OY = 150.0, 120.0
def V(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY - y))
nc = b.FindNet("VBAT").GetNetCode()
pts = [(16.5, -1.5), (16.5, -12.8), (-16.5, -12.8), (-16.5, -1.46)]   # R4.1 → botten → R3.1, B_Cu
for i in range(len(pts) - 1):
    t = pcbnew.PCB_TRACK(b); t.SetStart(V(*pts[i])); t.SetEnd(V(*pts[i + 1]))
    t.SetWidth(pcbnew.FromMM(0.4)); t.SetLayer(pcbnew.B_Cu); t.SetNetCode(nc); b.Add(t)
pcbnew.SaveBoard("hardware/vest-patch.kicad_pcb", b)
print("  stitch: VBAT R4.1→R3.1 på B_Cu (nederkant)")
