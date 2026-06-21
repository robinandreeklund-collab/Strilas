#!/usr/bin/env python3
"""STRILAS — OPTIK-PCB (vapen v2, kompakt enligt CAD): porträtt ≤56×41, kamera tittar genom CUTOUT
topp, 2 IR-emittrar + Carclo 10734/10003 SIDA-VID-SIDA i botten. Kameran (VEYE AR0234M) sitter BAKOM
på 10 mm standoff, linsen genom cutouten; optik-PCB:n sitter 20 mm framför HAT/FC. Carclo-hållarnas
diameter sticker ut lite utanför 41 mm-kanten (OK per design).

Hål: lins-CUTOUT (Ø15, Edge_Cuts) · 4 kamera-standoff (M2.5, matchar AR0234M 29×29 — verifiera VEYE-DXF)
· 8 Carclo-ben (Ø2.1, ±4,5×±7,8/emitter) · 4 board-mount (M2.5, 20 mm standoff → HAT). JST emitter-ström
VERTIKAL på BAKSIDAN. Ingen aktiv elektronik (bara dioder + JST).

Kör:  python3 hardware/optik_head.py   → hardware/optik-head.kicad_pcb (+ BOM/centroid)
"""
import pcbnew, os, csv, xlwt, math
OX, OY = 150.0, 120.0; MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
FPD = "/usr/share/kicad/footprints"; LOC = "/home/user/Strilas/hardware/strilas.pretty"

# --- geometri (mm, board-centrum = origo); porträtt 41 (b) × 52 (h) ---
BW, BH = 20.5, 26.0       # halva → 41×52 mm (inom 56×41-envelopen)
LENS_C = (0.0, 11.0)      # lins-cutout-centrum (topp)
LENS_R = 7.5             # Ø15 cutout för M12-lins-barrel
CAM_PITCH = 24.0          # AR0234M 29×29 mont-hål (±12) — PARAMETRISK, sätt mot VEYE-DXF
EMIT_Y = -14.0            # emittrar i botten
EMIT_DX = 10.5            # sida-vid-sida (Carclo Ø~22 → centra ±10,5; ringen sticker ut lite)
LEG_DX, LEG_DY = 4.5, 7.8 # Carclo 10734-ben (= gamla kortet)

def main():
    b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)
    VE = pcbnew.NETINFO_ITEM(b, "VBAT_E"); b.Add(VE)
    MID = pcbnew.NETINFO_ITEM(b, "LED_MID"); b.Add(MID)
    DR = pcbnew.NETINFO_ITEM(b, "LED_DRV"); b.Add(DR)

    # 2 emittrar sida-vid-sida i botten, ROT 90 (pads horisontellt → ren serie). pad1=A, pad2=K
    def emitter(ref, x, rot):
        e = pcbnew.FootprintLoad(LOC, "IR_Emitter_OSRAM_OSLON_Black_SFH4725S")
        e.SetReference(ref); e.SetValue("SFH4725AS_940nm"); e.SetPosition(V(x, EMIT_Y)); e.SetOrientationDegrees(rot); b.Add(e); return e
    D1 = emitter("D1", -EMIT_DX, 90); D2 = emitter("D2", +EMIT_DX, 90)   # speglade → inner-pads möts
    D1.FindPadByNumber("1").SetNet(VE);  D1.FindPadByNumber("2").SetNet(MID)
    D2.FindPadByNumber("1").SetNet(MID); D2.FindPadByNumber("2").SetNet(DR)

    # JST 2-pol VERTIKAL på BAKSIDAN, UNDER emittrarna (öppen yta, klar av kamera-hål)
    J = pcbnew.FootprintLoad(f"{FPD}/Connector_JST.pretty", "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical")
    J.SetReference("J1"); J.SetValue("emitter→HAT"); J.SetPosition(V(0.0, -9.0)); J.SetOrientationDegrees(90)
    b.Add(J); J.Flip(J.GetPosition(), False)
    J.FindPadByNumber("1").SetNet(VE); J.FindPadByNumber("2").SetNet(DR)

    def track(net, pts, w=0.8):
        for i in range(len(pts)-1):
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(*pts[i])); t.SetEnd(V(*pts[i+1]))
            t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(net.GetNetCode()); b.Add(t)
    def P(fp, n): p = fp.FindPadByNumber(n); return (p.GetPosition().x/1e6-OX, OY-p.GetPosition().y/1e6)
    j1, j2 = P(J,"1"), P(J,"2"); d1a,d1k = P(D1,"1"),P(D1,"2"); d2a,d2k = P(D2,"1"),P(D2,"2")
    # MID (serie): D1.K → D2.A — de inre paddarna, kort horisontell
    track(MID, [d1k, ((d1k[0]+d2a[0])/2, d1k[1]), d2a])
    # VBAT_E: JST.1 → D1.A (yttre vänster pad), DRV: JST.2 → D2.K (yttre höger pad)
    track(VE, [j1, (d1a[0], j1[1]), d1a])
    track(DR, [j2, (d2k[0], j2[1]), d2k])

    # mekaniska hål
    def hole(ref, fp, x, y):
        h = pcbnew.FootprintLoad(f"{FPD}/MountingHole.pretty", fp); h.SetReference(ref); h.SetPosition(V(x,y)); b.Add(h)
    lx, ly = LENS_C
    for i,(sx,sy) in enumerate([(1,1),(1,-1),(-1,1),(-1,-1)]):                 # kamera-standoff (AR0234M)
        hole(f"CAM{i+1}", "MountingHole_2.5mm", lx+sx*CAM_PITCH/2, ly+sy*CAM_PITCH/2)
    n=1                                                                        # Carclo-ben 4/emitter
    for ex in (-EMIT_DX, +EMIT_DX):
        for sx,sy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            hole(f"CL{n}", "MountingHole_2.1mm", ex+sx*LEG_DX, EMIT_Y+sy*LEG_DY); n+=1
    for i,(sx,sy) in enumerate([(1,1),(1,-1),(-1,1),(-1,-1)]):                 # board-mount → HAT (20 mm)
        hole(f"MH{i+1}", "MountingHole_2.5mm", sx*(BW-2.5), sy*(BH-2.5))

    # lins-CUTOUT (rund Edge_Cuts-cirkel)
    cir = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_CIRCLE); cir.SetCenter(V(*LENS_C))
    cir.SetEnd(V(LENS_C[0]+LENS_R, LENS_C[1])); cir.SetLayer(pcbnew.Edge_Cuts); cir.SetWidth(MM(0.15)); b.Add(cir)
    # outline
    pts = [(-BW,-BH),(BW,-BH),(BW,BH),(-BW,BH)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1)%4]))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    def silk(txt,x,y,sz=0.8):
        t=pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetPosition(V(x,y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(MM(sz),MM(sz))); t.SetTextThickness(MM(0.12)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)
    silk("STRILAS OPTIK", 0, 23); silk("AR0234", 0, 4); silk("D1", -EMIT_DX, EMIT_Y+2.5); silk("D2", EMIT_DX, EMIT_Y+2.5)

    pcbnew.SaveBoard("hardware/optik-head.kicad_pcb", b)
    print("wrote optik-head.kicad_pcb (41×52 porträtt: lins-cutout topp, 2 emitter+Carclo botten, kamera bak)")

    COLS = ["Designator*","Quantity*","Manufacturer Part Number*","Manufacturer","Package/Footprint","Description","Procurement Type","Customer Note"]
    rows = [
        ("D1,D2","2","SFH4725AS","ams OSRAM","strilas:SFH4725S","IR-emitter 940 nm (2 i serie, sida-vid-sida botten; Carclo 10734/10003 → smal beam)","","CC-sänka på HAT; eye-safe 1A/3A"),
        ("(lins)","2","10734","Carclo","Carclo_10734","Linshållare över emitter","","mekanisk, på ben-hål (Ø2.1); ringen sticker ut lite utanför kant"),
        ("(lins)","2","10003","Carclo","Carclo_10003","Smal-beam-lins i hållaren","","mekanisk"),
        ("J1","1","B2B-PH-K","JST","JST_PH_1x02_Vertical","Emitter-ström → HAT (VBAT_E,DRV) — VERTIKAL BAKSIDA","","2-pol THT"),
    ]
    for outdir in ("hardware/nextpcb","leverans/optik-head"):
        os.makedirs(outdir, exist_ok=True); wb=xlwt.Workbook(); ws=wb.add_sheet("BOM")
        for c,h in enumerate(COLS): ws.write(0,c,h)
        for r,row in enumerate(rows,1):
            for c,v in enumerate(row): ws.write(r,c,v)
        wb.save(f"{outdir}/optik-head-bom.xls")
        with open(f"{outdir}/optik-head-centroid.csv","w",newline="") as fp:
            w=csv.writer(fp); w.writerow(["Designator","Mid X","Mid Y","Layer","Rotation"])
            for ref in ("D1","D2"):
                f=b.FindFootprintByReference(ref); p=f.GetPosition()
                w.writerow([ref,f"{p.x/1e6-OX:.3f}",f"{OY-p.y/1e6:.3f}","top",f.GetOrientationDegrees()])
    print("  BOM + centroid; kamera mekanisk (AR0234M bak på 10mm standoff, lins genom cutout)")

if __name__ == "__main__":
    main()
