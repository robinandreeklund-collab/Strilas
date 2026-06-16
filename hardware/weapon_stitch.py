#!/usr/bin/env python3
"""STRILAS — handrouta de 2 kraftstift på J1 (P4 edge B) som Freerouting inte når som SPÅR
i det täta optikkortet: +3V3 (J1.11) och VBAT (J1.14), längst ned i vänstra hörnet (boxade av
kamerahål H10 + P4-standoff H5). VBAT når visserligen In2-VBAT-planet via planet, men vi lägger
ändå ett explicit spår längs den TOMMA nederkant-korridoren för robusthet; +3V3 (ej plan) MÅSTE
handroutas. Lägren verifierade fria: B_Cu i vänsterkant-korridoren och hela nederkanten.
Körs EFTER ses_apply, FÖRE flip_j1_back + weapon_finish (J1-paddar är THT → bevaras vid flip)."""
import pcbnew
b = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
OX, OY = 150.0, 120.0
def V(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY - y))
def nc(n): return b.FindNet(n).GetNetCode()
def seg(net, layer, pts, w):
    code = nc(net)
    for i in range(len(pts) - 1):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*pts[i])); t.SetEnd(V(*pts[i + 1]))
        t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(layer); t.SetNetCode(code); b.Add(t)
def via(net, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(pcbnew.FromMM(0.6)); v.SetDrill(pcbnew.FromMM(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(nc(net)); b.Add(v)

# +3V3: B_Cu upp vänsterkant (fri), via på C3.1 (+3V3-pad @ -22,-7.48), klar av MISO (x≈-24)
seg("+3V3", pcbnew.B_Cu, [(-25.28, -20.26), (-23.5, -20.26), (-23.5, -7.48), (-22.0, -7.48)], 0.25)
via("+3V3", -22.0, -7.48)
# VBAT: B_Cu längs tom nederkant, stigare vid x20.5 (klar av hål H3 @x24) in i C1.1 (@22.53,-15)
seg("VBAT", pcbnew.B_Cu, [(-25.28, -27.88), (-24.0, -30.5), (20.5, -30.5), (20.5, -15.0), (22.53, -15.0)], 0.4)
via("VBAT", 22.53, -15.0)
pcbnew.SaveBoard("hardware/weapon-module.kicad_pcb", b)
print("  stitch: +3V3 (J1.11→C3.1) + VBAT (J1.14→C1.1) handroutade på B_Cu")
