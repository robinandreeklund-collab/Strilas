#!/usr/bin/env python3
"""STRILAS — OPTIK-PCB (vapen v2): kompakt porträtt ≤56×41, ALLA SMT på FRAMSIDAN (enkelsidig
montering = billigare). Kamera-cutout topp; CC-sänka (OPA171+DPAK+0R2 sense+0R1 DNP+15k/1k+gate-R+
komp) i MITTBANDET; 2 IR-emittrar + Carclo 10734/10003 sida-vid-sida i BOTTEN. JST 3-pin (VBAT·IR_MOD·
GND) på BAKSIDAN (THT, handlödd). CC-sänkan flyttad hit från HAT → kortare puls-loop, lägre EMI; HAT
skickar bara DC VBAT + µA IR_MOD + GND. Kameran (VEYE AR0234M) sitter BAKOM på 10 mm standoff.

Placerar + tilldelar nät; routas av route_optik.py (freerouting + GND-fyll).
Kör:  python3 hardware/optik_head.py
"""
import pcbnew, os, csv, xlwt
OX, OY = 150.0, 120.0; MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
FPD = "/usr/share/kicad/footprints"; LOC = "/home/user/Strilas/hardware/strilas.pretty"

BW, BH = 20.5, 28.0       # 41×56 mm porträtt (max i 56×41-envelopen)
LENS_C = (0.0, 13.0); LENS_R = 9.0          # kamera-cutout topp (Ø18 — M12-linshållare; var Ø15, för tight)
CAM_PITCH = 25.0          # VEYE AR0234 29×29 mm: 4 hörnhål 2,00 mm in från kant → c/c 25×25 mm (veye.cc-måttritning)
EMIT_Y = -16.5; EMIT_DX = 11.25            # emittrar UPPFLYTTADE 2 mm så nedre benen släpper hörn-hålen; balans fläns/ben-kant
# Carclo 10734 (ritn. 60575): Ø22,1 fläns, 4-bens hålbild 9,0×15,60 mm.
# Hållaren ROTERAD 90° → benspann 15,60 mm i X, 9,0 mm i Y. Då hamnar de nedre benen på y=-14/-23
# (klarar hörn-M2.5-hålen vid y=-25,5) istället för y=-26,3 (krockade förut). c/c 22,6 ≥ 22,1 →
# runda flänsarna krockar ej; alla ben på kortet; fläns sticker ut över L/H-kant (OK enl. Robin).
LEG_DX, LEG_DY = 4.5, 7.8                   # halva hålbilden: 9,0 × 15,60 mm
HOLDER_OD = 22.1                            # Carclo 10734 ytterdiameter (dokumenteras på Cmts.User)

def main():
    b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(2)
    nets = {}
    def N(n):
        if n not in nets: ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
        return nets[n]
    for n in ("VBAT","IR_MOD","GND","LED_MID","LED_CATH","IDRV_SENSE","DRV_GATE","IDRV_REF","OPA_OUT","EMIT_HI","R2_D"): N(n)

    def fp(lib, mod, ref, val, x, y, rot=0, back=False):
        f = pcbnew.FootprintLoad(LOC if lib == "strilas" else f"{FPD}/{lib}.pretty", mod)
        f.SetReference(ref); f.SetValue(val); f.SetPosition(V(x, y)); f.SetOrientationDegrees(rot); b.Add(f)
        if back: f.Flip(f.GetPosition(), False)
        return f
    def setnet(f, pad, net):
        for p in f.Pads():
            if p.GetName()==pad: p.SetNet(N(net))

    # 2 emittrar (front) sida-vid-sida, rot 90 → inner-pads i serie
    D1 = fp("strilas","IR_Emitter_OSRAM_OSLON_Black_SFH4725S","D1","SFH4725AS_940nm",-EMIT_DX,EMIT_Y,90)
    D2 = fp("strilas","IR_Emitter_OSRAM_OSLON_Black_SFH4725S","D2","SFH4725AS_940nm",+EMIT_DX,EMIT_Y,90)
    setnet(D1,"1","VBAT"); setnet(D1,"2","LED_MID"); setnet(D2,"1","LED_MID"); setnet(D2,"2","LED_CATH")

    # CC-sänka (front, mittband y≈-1..-12)
    Uop = fp("Package_TO_SOT_SMD","SOT-23-5","U1","OPA171",-1,-4,0)
    for p,n in (("1","OPA_OUT"),("2","GND"),("3","IDRV_REF"),("4","IDRV_SENSE"),("5","VBAT")): setnet(Uop,p,n)
    Qd = fp("Package_TO_SOT_SMD","TO-252-2","Q1","AOD4184A",-9,-6,0)
    for p,n in (("1","DRV_GATE"),("2","LED_CATH"),("3","IDRV_SENSE")): setnet(Qd,p,n)
    Rs = fp("Resistor_SMD","R_2512_6332Metric","R1","0R2",10,-3,0); setnet(Rs,"1","IDRV_SENSE"); setnet(Rs,"2","GND")
    # 3A-väljare: R2(0R068) i serie med N-FET Qsel → IDRV_SENSE. EMIT_HI hög = FET på = 3A; låg/flytande = 1A.
    # R2=0R068 vald så R2+Rds(AO3400 ~35mΩ@3V3) ≈ 0R1 → parallellt med R1(0R2) ≈ 0,067Ω → 3A. (2010/0,5W: ~0,4W.)
    Ro = fp("Resistor_SMD","R_2010_5025Metric","R2","0R068",7.8,0.6,0); setnet(Ro,"1","R2_D"); setnet(Ro,"2","IDRV_SENSE")
    Qsel = fp("Package_TO_SOT_SMD","SOT-23","Q2","AO3400",7.8,3.8,0); setnet(Qsel,"1","EMIT_HI"); setnet(Qsel,"2","GND"); setnet(Qsel,"3","R2_D")  # G/S/D
    Rgs = fp("Resistor_SMD","R_0805_2012Metric","R6","100k",3.5,2.0,90); setnet(Rgs,"1","EMIT_HI"); setnet(Rgs,"2","GND")  # gate-pulldown → default 1A
    Cvb= fp("Capacitor_SMD","C_1206_3216Metric","C3","47uF",0.0,-1.2,0); setnet(Cvb,"1","VBAT"); setnet(Cvb,"2","GND")  # VBAT-bulk för 3A-pulsens flanker
    Rda= fp("Resistor_SMD","R_0805_2012Metric","R3","15k",0,-9.8,0); setnet(Rda,"1","IR_MOD"); setnet(Rda,"2","IDRV_REF")  # flyttad: klar av uppflyttat benhål
    Rdb= fp("Resistor_SMD","R_0805_2012Metric","R4","1k",0,-11.5,0); setnet(Rdb,"1","IDRV_REF"); setnet(Rdb,"2","GND")  # flyttad: ut ur benets Ø3,5-frizon
    Rg = fp("Resistor_SMD","R_0805_2012Metric","R5","100R",3,-8,0); setnet(Rg,"1","OPA_OUT"); setnet(Rg,"2","DRV_GATE")
    Cop= fp("Resistor_SMD","R_0805_2012Metric","C1","100nF",12,-9,0); setnet(Cop,"1","VBAT"); setnet(Cop,"2","GND")
    Cc = fp("Resistor_SMD","R_0805_2012Metric","C2","100pF",-0.9,-6.3,0); setnet(Cc,"1","OPA_OUT"); setnet(Cc,"2","IDRV_SENSE")  # flyttad: klar av D1:s benhål + utanför fläns, nära OPA-utg

    # JST 3-pin (VBAT·IR_MOD·GND) på BAKSIDAN, THT
    J = fp("Connector_JST","JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical","J1","→HAT (VBAT·IR_MOD·GND·EMIT_HI)",16,-3,90,back=True)
    setnet(J,"1","VBAT"); setnet(J,"2","IR_MOD"); setnet(J,"3","GND"); setnet(J,"4","EMIT_HI")

    # mekaniska hål
    def hole(ref, mod, x, y):
        h = pcbnew.FootprintLoad(f"{FPD}/MountingHole.pretty", mod); h.SetReference(ref); h.SetPosition(V(x,y)); b.Add(h)
    lx, ly = LENS_C
    for i,(sx,sy) in enumerate([(1,1),(1,-1),(-1,1),(-1,-1)]): hole(f"CAM{i+1}","MountingHole_2.2mm_M2",lx+sx*CAM_PITCH/2,ly+sy*CAM_PITCH/2)
    n=1
    for ex in (-EMIT_DX,+EMIT_DX):
        # hållaren ROTERAD 90°: benspann 15,60 i X (LEG_DY), 9,0 i Y (LEG_DX) → båda monteras "åt andra hållet"
        for sx,sy in [(1,1),(1,-1),(-1,1),(-1,-1)]: hole(f"CL{n}","MountingHole_2.1mm",ex+sx*LEG_DY,EMIT_Y+sy*LEG_DX); n+=1
    for i,(sx,sy) in enumerate([(1,1),(1,-1),(-1,1),(-1,-1)]): hole(f"MH{i+1}","MountingHole_2.7mm_M2.5",sx*(BW-2.5),sy*(BH-2.5))

    # lins-cutout + outline + silk
    cir = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_CIRCLE); cir.SetCenter(V(*LENS_C)); cir.SetEnd(V(LENS_C[0]+LENS_R,LENS_C[1]))
    cir.SetLayer(pcbnew.Edge_Cuts); cir.SetWidth(MM(0.15)); b.Add(cir)
    # Carclo 10734 fläns-envelopp (Ø22,1) på Cmts.User — dokumenterar att flänsen sticker ut över kanten
    for ex in (-EMIT_DX, +EMIT_DX):
        hc = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_CIRCLE); hc.SetCenter(V(ex,EMIT_Y)); hc.SetEnd(V(ex+HOLDER_OD/2,EMIT_Y))
        hc.SetLayer(pcbnew.Cmts_User); hc.SetWidth(MM(0.12)); b.Add(hc)
    box = [(-BW,-BH),(BW,-BH),(BW,BH),(-BW,BH)]
    for i in range(4):
        s=pcbnew.PCB_SHAPE(b,pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*box[i])); s.SetEnd(V(*box[(i+1)%4]))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    t=pcbnew.PCB_TEXT(b); t.SetText("STRILAS OPTIK"); t.SetPosition(V(0,24)); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(1.0),MM(1.0))); t.SetTextThickness(MM(0.15)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t)

    pcbnew.SaveBoard("hardware/optik-head.kicad_pcb", b)
    print("placerade optik-PCB (41×56): kamera topp + CC-sänka mitt (front) + 2 emitter botten + JST bak")

    COLS=["Designator*","Quantity*","Manufacturer Part Number*","Manufacturer","Package/Footprint","Description","Procurement Type","Customer Note"]
    rows=[("D1,D2","2","SFH4725AS","ams OSRAM","strilas:SFH4725S","IR-emitter 940 nm (serie; Carclo 10734/10003 smal beam)","",""),
          ("U1","1","OPA171","TI","SOT-23-5","CC-sänka op-amp","",""),("Q1","1","AOD4184A","AOS","TO-252","pass-FET","",""),
          ("R1","1","WSL2512R2000","Vishay","R_2512","0R2 sense (1A-gren)","",""),
          ("R2","1","-","-","R_2010","0R068 sense (3A-gren, FET-switchad, ~0,4W)","",""),
          ("Q2","1","AO3400","AOS","SOT-23","N-FET: EMIT_HI(GPIO13) hög = 3A, låg = 1A","",""),
          ("R6","1","-","-","R_0805","100k gate-pulldown → default 1A (säkert)","",""),
          ("R3,R4,R5","3","-","-","R_0805","15k/1k-delare + 100R gate","",""),("C1,C2","2","-","-","R_0805-pkg","100nF/100pF","",""),
          ("C3","1","-","-","C_1206","47µF VBAT-bulk (3A-puls)","",""),
          ("(lins)","2+2","10734/10003","Carclo","Carclo","Linshållare + smal-beam-lins/emitter","","mekanisk"),
          ("J1","1","B3B-PH-K","JST","JST_PH_1x03","→HAT (VBAT·IR_MOD·GND) — VERTIKAL BAKSIDA","","THT handlödd")]
    for od in ("hardware/nextpcb","leverans/optik-head"):
        os.makedirs(od,exist_ok=True); wb=xlwt.Workbook(); ws=wb.add_sheet("BOM")
        for c,h in enumerate(COLS): ws.write(0,c,h)
        for r,row in enumerate(rows,1):
            for c,v in enumerate(row): ws.write(r,c,v)
        wb.save(f"{od}/optik-head-bom.xls")
        with open(f"{od}/optik-head-centroid.csv","w",newline="") as f:
            w=csv.writer(f); w.writerow(["Designator","Mid X","Mid Y","Layer","Rotation"])
            for ref in ("D1","D2","U1","Q1","Q2","R1","R2","R3","R4","R5","R6","C1","C2","C3"):
                ff=b.FindFootprintByReference(ref); p=ff.GetPosition()
                w.writerow([ref,f"{p.x/1e6-OX:.3f}",f"{OY-p.y/1e6:.3f}","top",ff.GetOrientationDegrees()])
    print("  BOM + centroid (allt SMT på framsidan; JST THT bak)")

if __name__ == "__main__":
    main()
