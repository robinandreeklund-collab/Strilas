#!/usr/bin/env python3
"""STRILAS — LED-TAB micro-PCB (konstellations-LED på fast 90°-vinklad fot).
En liten PCB (~6×11 mm) med EN högeffekt-OSLON SFH4715AS (860 nm) + en 2-håls fot (1×2 2.54 mm).
NextPCB SMT-placerar OSLON:en (precision). I foten löder kund en RIGHT-ANGLE (90°) stiftlist —
samma 2-håls mönster som en rak list, men den vinklade håller tab:en STELT LODRÄT (90°) mot discen
utan handböjning, samma vinkel varje exemplar. Stiften går rakt ner i hjälm-discens tab-sockel
(D5-D10). Tab:en står lodrät → OSLON:en strålar VÅGRÄT radiellt ut mot horisonten. 6 st/hjälm."""
import pcbnew
OX, OY = 150.0, 120.0; MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
FPD = "/usr/share/kicad/footprints"; LOC = "/home/user/Strilas/hardware/strilas.pretty"

def main():
    b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)
    # OSLON (emitterar ut tab-facet) nära toppen
    led = pcbnew.FootprintLoad(LOC, "IR_Emitter_OSRAM_OSLON_Black_SFH4725S")
    led.SetReference("D1"); led.SetValue("SFH4715AS_860nm"); led.SetPosition(V(0, 2.5)); b.Add(led)
    # 2-håls fot (1x2, 2.54 mm) — SAMMA hålmönster för rak ELLER 90°-vinklad stiftlist.
    # Kund löder en RIGHT-ANGLE (90°) stiftlist här → håller tab:en stelt lodrät utan handböjning.
    hdr = pcbnew.FootprintLoad(f"{FPD}/Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Vertical")
    hdr.SetReference("J1"); hdr.SetValue("right-angle 90° fot 1x2 → disc"); hdr.SetPosition(V(-1.27, -3.5)); hdr.SetOrientationDegrees(90); b.Add(hdr)
    # nät: A→ben1, K→ben2
    A = pcbnew.NETINFO_ITEM(b, "A"); b.Add(A); K = pcbnew.NETINFO_ITEM(b, "K"); b.Add(K)
    for p in led.Pads(): p.SetNet(A if p.GetName()=="1" else K)
    for p in hdr.Pads(): p.SetNet(A if p.GetName()=="1" else K)
    # 2 korta spår (F.Cu) pad→ben
    def track(n, pts):
        for i in range(len(pts)-1):
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(*pts[i])); t.SetEnd(V(*pts[i+1]))
            t.SetWidth(MM(0.4)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(b.FindNet(n).GetNetCode()); b.Add(t)
    aL=led.FindPadByNumber("1").GetPosition(); kL=led.FindPadByNumber("2").GetPosition()
    a1=hdr.FindPadByNumber("1").GetPosition(); k2=hdr.FindPadByNumber("2").GetPosition()
    def U(p): return (p.x/1e6-OX, OY-p.y/1e6)
    # A dras runt VÄNSTER kant (dogleg) → klarar centrerade LED-K-padden; K dras direkt på HÖGER sida.
    track("A", [U(aL), (-1.6, 3.55), (-1.6, -3.5), U(a1)])
    track("K", [U(kL), U(k2)])
    # kant-cuts 6×11
    pts=[(-3,-5.5),(3,-5.5),(3,5.5),(-3,5.5)]
    for i in range(4):
        s=pcbnew.PCB_SHAPE(b,pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1)%4]))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    # silk
    t=pcbnew.PCB_TEXT(b); t.SetText("STRILAS LED"); t.SetPosition(V(0,-1)); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(0.7),MM(0.7))); t.SetTextThickness(MM(0.12)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)
    pcbnew.SaveBoard("hardware/led-tab.kicad_pcb", b)
    print("wrote hardware/led-tab.kicad_pcb (6×11mm: OSLON + 2 ben-hål, 2 spår)")

if __name__ == "__main__": main()
