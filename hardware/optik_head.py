#!/usr/bin/env python3
"""STRILAS — OPTIK-HUVUD (vapen v2): mini-PCB med kamera + 2 IR-emittrar ÖVER/UNDER kameran.

"Business end" på vapnet: bär VEYE AR0234M-kameran (mitten) + 2× SFH4725AS (940 nm) i SERIE, en över och
en under kameran (symmetriskt kring optiska axeln → stråltyngdpunkt på siktlinjen). Över VARJE emitter
sitter en **Carclo 10734-linshållare + 10003-lins** → kollimerar till SMAL beam (räckvidd). Hålbilden
för hållaren = 4 ben Ø2.1 på **±4,5 mm (x) × ±7,8 mm (y)** kring emittern (= gamla optik-kortets 10734-
mönster, verifierat). Ingen aktiv elektronik — bara dioder + ben-hål + en JST för emitter-strömmen
(drivs av CC-sänkan på carriern). Kamerans egen RPi-CSI-FFC går separat till carriern (EMI-skild).

Kameran (VEYE AR0234M + M12-lins) fästs i mitten (2× M2 M12-hållare). JST = VERTIKAL på BAKSIDAN (ej kant-
monterad → tar ej kant-plats); emitter-strömmen via 2 spår till dess THT-pads.

Kör:  python3 hardware/optik_head.py   → hardware/optik-head.kicad_pcb (+ BOM/centroid)
"""
import pcbnew, os, csv, xlwt
OX, OY = 150.0, 120.0; MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
FPD = "/usr/share/kicad/footprints"; LOC = "/home/user/Strilas/hardware/strilas.pretty"

# --- geometri (mm, kamera-centrum = origo) ---
EMIT_DY  = 22.0          # emitter-offset över/under kameran
LEG_DX, LEG_DY = 4.5, 7.8  # Carclo 10734-hållarens 4 ben: ±4,5 (x) × ±7,8 (y) (= gamla kortet)
M12_PITCH = 18.0         # kamerans M12-linshållare (2× M2 @ ±9 mm)
BW, BH = 16.0, 33.0      # halva outline → 32×66 mm vertikal remsa

def main():
    b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)
    VE = pcbnew.NETINFO_ITEM(b, "VBAT_E"); b.Add(VE)
    MID = pcbnew.NETINFO_ITEM(b, "LED_MID"); b.Add(MID)
    DR = pcbnew.NETINFO_ITEM(b, "LED_DRV"); b.Add(DR)

    # 2 emittrar (SFH4725AS) — D1 över, D2 under kameran. pad1=anod(A), pad2=katod(K)
    def emitter(ref, y):
        e = pcbnew.FootprintLoad(LOC, "IR_Emitter_OSRAM_OSLON_Black_SFH4725S")
        e.SetReference(ref); e.SetValue("SFH4725AS_940nm"); e.SetPosition(V(0, y)); b.Add(e); return e
    D1 = emitter("D1", +EMIT_DY); D2 = emitter("D2", -EMIT_DY)
    D1.FindPadByNumber("1").SetNet(VE);  D1.FindPadByNumber("2").SetNet(MID)
    D2.FindPadByNumber("1").SetNet(MID); D2.FindPadByNumber("2").SetNet(DR)

    # JST 2-pol VERTIKAL på BAKSIDAN (ej kant-monterad) — emitter-ström till/från carriern
    J = pcbnew.FootprintLoad(f"{FPD}/Connector_JST.pretty", "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical")
    J.SetReference("J1"); J.SetValue("emitter→carrier"); J.SetPosition(V(13.0, 5.0)); J.SetOrientationDegrees(90)
    b.Add(J); J.Flip(J.GetPosition(), False)             # lägg till FÖRST, sedan → baksidan (B.Cu)
    J.FindPadByNumber("1").SetNet(VE); J.FindPadByNumber("2").SetNet(DR)

    # --- spår (F.Cu) ---
    def track(net, pts, w=0.8):
        nc = net.GetNetCode()
        for i in range(len(pts) - 1):
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(*pts[i])); t.SetEnd(V(*pts[i + 1]))
            t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(nc); b.Add(t)
    def P(fp, n): p = fp.FindPadByNumber(n); return (p.GetPosition().x/1e6-OX, OY-p.GetPosition().y/1e6)
    j1, j2 = P(J, "1"), P(J, "2"); d1a, d1k = P(D1, "1"), P(D1, "2"); d2a, d2k = P(D2, "1"), P(D2, "2")
    # VBAT_E: JST.1 → höger rail (x14) UPP → D1.A (under lins, klar av ben)
    track(VE, [j1, (14, j1[1]), (14, d1a[1]), d1a])
    # DRV: JST.2 → höger rail (x14) NER → D2.K
    track(DR, [j2, (14, j2[1]), (14, d2k[1]), d2k])
    # MID (serie): D1.K → vänster rail (x-14) → D2.A
    track(MID, [d1k, (-14, d1k[1]), (-14, d2a[1]), d2a])

    # --- mekaniska hål ---
    def hole(ref, fp, x, y):
        h = pcbnew.FootprintLoad(f"{FPD}/MountingHole.pretty", fp); h.SetReference(ref); h.SetPosition(V(x, y)); b.Add(h)
    hole("CAM1", "MountingHole_2.2mm_M2", -M12_PITCH/2, 0.0)     # kamera M12-hållare
    hole("CAM2", "MountingHole_2.2mm_M2", +M12_PITCH/2, 0.0)
    n = 1                                                         # Carclo 10734-ben: 4/emitter (±4,5 × ±7,8)
    for ey in (+EMIT_DY, -EMIT_DY):
        for sx, sy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            hole(f"CL{n}", "MountingHole_2.1mm", sx*LEG_DX, ey + sy*LEG_DY); n += 1

    # outline 32×66 + silk
    pts = [(-BW,-BH),(BW,-BH),(BW,BH),(-BW,BH)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1)%4])); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    def silk(txt, x, y, sz=0.8):
        t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetPosition(V(x, y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(MM(sz),MM(sz))); t.SetTextThickness(MM(0.12)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)
    silk("STRILAS OPTIK-HEAD", 0, 31); silk("D1", 6, EMIT_DY); silk("D2", 6, -EMIT_DY); silk("AR0234", 0, 0, 1.0)

    pcbnew.SaveBoard("hardware/optik-head.kicad_pcb", b)
    print("wrote hardware/optik-head.kicad_pcb (32×66: 2 emitter + Carclo-10734-ben + kamera + JST baksida)")

    # --- BOM + centroid ---
    COLS = ["Designator*","Quantity*","Manufacturer Part Number*","Manufacturer","Package/Footprint","Description","Procurement Type","Customer Note"]
    rows = [
        ("D1,D2","2","SFH4725AS","ams OSRAM","strilas:SFH4725S","IR-emitter 940 nm OSLON Black GS-skott (2 i serie, över/under kameran; CC-sänka på carriern, 1 A/3 A)","","56 kHz-burst; eye-safe HW-tak på carriern"),
        ("(lins)","2","10734","Carclo","Carclo_10734","Linshållare 10734 över varje emitter (för 10003-lins)","","mekanisk, kund-monterad på ben-hålen (Ø2.1)"),
        ("(lins)","2","10003","Carclo","Carclo_10003","Carclo 10003 SMAL-beam-lins (i 10734-hållaren)","","mekanisk; ger smal stråle → räckvidd"),
        ("J1","1","B2B-PH-K","JST","JST_PH_1x02_Vertical","Emitter-ström → carrier (VBAT_E, DRV) — VERTIKAL, BAKSIDA","","2-pol THT; ej kant-monterad"),
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
    print("  Carclo 10734-hållare + 10003-lins över VARJE emitter (smal beam); JST vertikal på baksidan")

if __name__ == "__main__":
    main()
