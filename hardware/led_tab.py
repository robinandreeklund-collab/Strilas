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
    # Lumileds L1I0-0850090200000 (LUXEON IR Domed, 850nm, 90°, 1.5A DC, Vf~3.2V@1A, ~2× VSMY mW/sr) —
    # emitterar ut tab-facetten. Pad1=anod (mitt+höger), pad2=katod (VÄNSTER, K-mark). Pinout verif. SamacSys.
    led = pcbnew.FootprintLoad(LOC, "L1I0_IR")
    led.SetReference("D1"); led.SetValue("L1I0-0850090200000"); led.SetPosition(V(0, 1.8))
    led.SetOrientationDegrees(180); b.Add(led)   # rot180 → anod=vänster+mitt, katod=höger (90°-mönster symm → optiskt gratis); ben-routning korsar ej
    # 2-håls fot (1x2, 2.54 mm) — RIGHT-ANGLE (horisontell) stiftlist: pinnarna går 90° UT från
    # tab-kanten och rakt NER i moderkortets 2-hålssockel → tab:en står stelt LODRÄT (90°) UTAN
    # handböjning, samma vinkel varje exemplar. Hålmönstret (2.54 mm) = identiskt mot moderkortets sockel.
    hdr = pcbnew.FootprintLoad(f"{FPD}/Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Horizontal")
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
    def U(p): return (p.x/1e6-OX, OY-p.y/1e6)
    ap = [U(p.GetPosition()) for p in led.Pads() if p.GetName()=="1"]   # 2 anod-pads (rot180 → mitt x=0 + vänster x=-0.75)
    kp = [U(p.GetPosition()) for p in led.Pads() if p.GetName()=="2"][0]  # katod (rot180 → HÖGER x=+0.75)
    a1=U(hdr.FindPadByNumber("1").GetPosition()); k2=U(hdr.FindPadByNumber("2").GetPosition())
    ax = min(p[0] for p in ap)                                          # vänstra anod-padden
    # anod: förena de 2 anod-paddarna + dra VÄNSTER om LED ner till ben1 (A) — dogleg
    track("A", [ap[0], ap[1]])
    track("A", [(ax, ap[0][1]), (-2.4, ap[0][1]), (-2.4, a1[1]), a1])
    # katod: höger pad → HÖGER om LED ner till ben2 (K)
    track("K", [kp, (2.4, kp[1]), (2.4, k2[1]), k2])
    # kant-cuts 6×11
    pts=[(-3,-5.5),(3,-5.5),(3,5.5),(-3,5.5)]
    for i in range(4):
        s=pcbnew.PCB_SHAPE(b,pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1)%4]))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    # silk
    t=pcbnew.PCB_TEXT(b); t.SetText("STRILAS LED"); t.SetPosition(V(0,-1)); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(0.7),MM(0.7))); t.SetTextThickness(MM(0.12)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)
    pcbnew.SaveBoard("hardware/led-tab.kicad_pcb", b)
    print("wrote hardware/led-tab.kicad_pcb (6×11mm: L1I0 + 2 ben-hål, 2 spår)")
    # --- BOM + centroid (NextPCB-format) → hålls i synk med kortet ---
    import xlwt, csv, os
    COLS = ["Designator*","Quantity*","Manufacturer Part Number*","Manufacturer","Package/Footprint","Description","Procurement Type","Customer Note"]
    bom_rows = [
        ("D1","1","L1I0-0850090200000","Lumileds","L1I0_IR","IR-LED 850nm LUXEON IR Domed 90° (konstellation, på 90°-tab; ~750mW/sr@1A ≈2× VSMY, 1.5A DC-rating, Vf~3.2V)","C","NextPCB SMT-PLACERAR; 850nm matchar kamera-bandpass (rejekterar 940nm-taggen). Pinout pad1=K verif. SamacSys; vår footprint pad2=K (konsekvent m schema)"),
        ("J1","1","2.54-1x02-RA","generisk","PinHeader_1x02_P2.54mm_Horizontal","Right-angle (90°) stiftlist 1x02 2.54mm — håller LED-tab lodrät utan böjning","","Handlöds av kund hemma (THT right-angle) — med i BOM, ej i centroid"),
    ]
    for outdir in ("hardware/nextpcb", "leverans/led-tab"):
        os.makedirs(outdir, exist_ok=True)
        wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
        for c, h in enumerate(COLS): ws.write(0, c, h)
        for r, row in enumerate(bom_rows, 1):
            for c, v in enumerate(row): ws.write(r, c, v)
        wb.save(f"{outdir}/led-tab-bom.xls")
        with open(f"{outdir}/led-tab-centroid.csv", "w", newline="") as fp:
            w = csv.writer(fp); w.writerow(["Designator","Mid X","Mid Y","Layer","Rotation"])
            d1 = next(f for f in b.GetFootprints() if f.GetReference() == "D1")
            p = d1.GetPosition(); w.writerow(["D1", f"{p.x/1e6-OX:.3f}", f"{OY-p.y/1e6:.3f}", "top", d1.GetOrientationDegrees()])  # endast D1 (J1=THT kund)
    print("  led-tab BOM + centroid (L1I0) → hardware/nextpcb + leverans/led-tab")

if __name__ == "__main__": main()
