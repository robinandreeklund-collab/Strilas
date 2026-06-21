#!/usr/bin/env python3
"""STRILAS — OPTIK-HUVUD (vapen v2): mini-PCB med kamera + 2 IR-emittrar ÖVER/UNDER kameran.

"Business end" på vapnet: bär Mira220-kameramodulen (mekaniskt) + 2× SFH4725AS (940 nm) i SERIE,
en över och en under kameran (symmetriskt kring optiska axeln → stråltyngdpunkt på siktlinjen).
Ingen aktiv elektronik — bara dioder + kollimator-hållarben + en JST för emitter-strömmen (drivs av
CC-sänkan på carriern). Kamerans egen 22-pin MIPI-FFC går separat till carriern (EMI-skild från pulsen).

⚠️ Kamera-mount-hålbilden (CAM_*) är PARAMETRISK platshållare (22 mm kvadrat) → sätt mot MIRA220MINI:s
   datablad innan tillverkning. Allt annat (emitter-läge, kollimator-ben, JST, outline) är definitivt.

Kör:  python3 hardware/optik_head.py   → hardware/optik-head.kicad_pcb (+ BOM/centroid)
"""
import pcbnew, os, csv, xlwt
OX, OY = 150.0, 120.0; MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
FPD = "/usr/share/kicad/footprints"; LOC = "/home/user/Strilas/hardware/strilas.pretty"

# --- geometri (mm, kamera-centrum = origo) ---
EMIT_DY   = 22.0     # emitter-offset över/under kameran
LEG_DXY   = 7.0      # Carclo-hållarben på ±7 kvadrat runt varje emitter
CAM_HOLE  = 11.0     # PARAMETRISK kamera-mount (±11 = 22 mm kvadrat) — sätt mot Mira220-datablad
BW, BH    = 16.0, 33.0  # halva outline → 32×66 mm vertikal remsa

def main():
    b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)

    # nät: emitter-serie  JST.1 → D1(A) ; D1(K) → D2(A) [MID] ; D2(K) → JST.2
    VE = pcbnew.NETINFO_ITEM(b, "VBAT_E"); b.Add(VE)
    MID = pcbnew.NETINFO_ITEM(b, "LED_MID"); b.Add(MID)
    DR = pcbnew.NETINFO_ITEM(b, "LED_DRV"); b.Add(DR)

    # 2 emittrar (SFH4725AS) — D1 över, D2 under kameran
    def emitter(ref, y):
        e = pcbnew.FootprintLoad(LOC, "IR_Emitter_OSRAM_OSLON_Black_SFH4725S")
        e.SetReference(ref); e.SetValue("SFH4725AS_940nm"); e.SetPosition(V(0, y)); b.Add(e)
        return e
    D1 = emitter("D1", +EMIT_DY)     # över
    D2 = emitter("D2", -EMIT_DY)     # under
    # pad 1 = anod (A), pad 2 = katod (K)
    D1.FindPadByNumber("1").SetNet(VE);  D1.FindPadByNumber("2").SetNet(MID)
    D2.FindPadByNumber("1").SetNet(MID); D2.FindPadByNumber("2").SetNet(DR)

    # JST 2-pol (emitter-ström till/från carriern) — vid nedre kanten
    J = pcbnew.FootprintLoad(f"{FPD}/Connector_JST.pretty", "JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal")
    J.SetReference("J1"); J.SetValue("emitter→carrier (VBAT_E,DRV)")
    J.SetPosition(V(0, -30.0)); J.SetOrientationDegrees(0); b.Add(J)
    J.FindPadByNumber("1").SetNet(VE); J.FindPadByNumber("2").SetNet(DR)

    # --- trace-hjälp ---
    def track(net, pts, w=0.8):
        nc = net.GetNetCode()
        for i in range(len(pts) - 1):
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(*pts[i])); t.SetEnd(V(*pts[i + 1]))
            t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(nc); b.Add(t)
    def P(fp, n): p = fp.FindPadByNumber(n); return (p.GetPosition().x/1e6-OX, OY-p.GetPosition().y/1e6)
    j1, j2 = P(J, "1"), P(J, "2")
    d1a, d1k = P(D1, "1"), P(D1, "2"); d2a, d2k = P(D2, "1"), P(D2, "2")
    # VBAT_E: JST.1 → UNDER ben-raden (y=-31.8) → vänster rail (x=-14) → upp → D1.A
    track(VE, [j1, (j1[0], -31.8), (-14, -31.8), (-14, d1a[1]), d1a])
    # MID (serie): D1.K → höger rail (x=14) → ner → D2.A  (runt kamera-aperturen, ej över)
    track(MID, [d1k, (14, d1k[1]), (14, d2a[1]), d2a])
    # DRV: D2.K → höger om axeln → ner till JST.2 (klar av D2.A/MID-pad)
    track(DR, [d2k, (2.0, d2k[1]), (2.0, -31.2), (j2[0], -31.2), j2])

    # kamera-mount (4× M2) + kollimator-ben (4/emitter, Carclo Ø2.1) — mekaniska hål till GND
    def hole(ref, fp, x, y):
        h = pcbnew.FootprintLoad(f"{FPD}/MountingHole.pretty", fp)
        h.SetReference(ref); h.SetPosition(V(x, y)); b.Add(h)
    for i, (sx, sy) in enumerate([(1,1),(1,-1),(-1,1),(-1,-1)]):
        hole(f"CAM{i+1}", "MountingHole_2.2mm_M2", sx*CAM_HOLE, sy*CAM_HOLE)
    n = 1
    for ey in (+EMIT_DY, -EMIT_DY):
        for sx, sy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            hole(f"CL{n}", "MountingHole_2.1mm", sx*LEG_DXY, ey + sy*LEG_DXY); n += 1

    # outline 32×66 mm
    pts = [(-BW,-BH),(BW,-BH),(BW,BH),(-BW,BH)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1)%4])); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    # silk
    def silk(txt, x, y, sz=0.8):
        t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetPosition(V(x, y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(MM(sz), MM(sz))); t.SetTextThickness(MM(0.12))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)
    silk("STRILAS OPTIK-HEAD", 0, 31); silk("D1", 4, EMIT_DY); silk("D2", 4, -EMIT_DY); silk("MIRA220", 0, 0, 1.0)

    pcbnew.SaveBoard("hardware/optik-head.kicad_pcb", b)
    print("wrote hardware/optik-head.kicad_pcb (32×66 mm: kamera-mount + 2 emitter över/under + JST)")

    # --- BOM + centroid ---
    COLS = ["Designator*","Quantity*","Manufacturer Part Number*","Manufacturer","Package/Footprint","Description","Procurement Type","Customer Note"]
    rows = [
        ("D1,D2","2","SFH4725AS","ams OSRAM","strilas:SFH4725S","IR-emitter 940 nm OSLON Black GS-skott (2 i serie, över/under kameran; CC-sänka på carriern, 1 A/3 A)","","56 kHz-burst; eye-safe HW-tak på carriern"),
        ("J1","1","S2B-PH-K-S","JST","JST_PH_1x02","Emitter-ström → carrier (VBAT_E, DRV)","","2-pol; separat kabel från kamerans MIPI-FFC"),
    ]
    for outdir in ("hardware/nextpcb", "leverans/optik-head"):
        os.makedirs(outdir, exist_ok=True)
        wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
        for c, h in enumerate(COLS): ws.write(0, c, h)
        for r, row in enumerate(rows, 1):
            for c, v in enumerate(row): ws.write(r, c, v)
        wb.save(f"{outdir}/optik-head-bom.xls")
        with open(f"{outdir}/optik-head-centroid.csv", "w", newline="") as fp:
            w = csv.writer(fp); w.writerow(["Designator","Mid X","Mid Y","Layer","Rotation"])
            for ref in ("D1", "D2"):
                f = b.FindFootprintByReference(ref); p = f.GetPosition()
                w.writerow([ref, f"{p.x/1e6-OX:.3f}", f"{OY-p.y/1e6:.3f}", "top", f.GetOrientationDegrees()])
    print("  optik-head BOM + centroid → hardware/nextpcb + leverans/optik-head")
    print("  ⚠️ CAM-mount = parametrisk platshållare (22 mm kvadrat) — sätt mot MIRA220MINI-datablad")

if __name__ == "__main__":
    main()
