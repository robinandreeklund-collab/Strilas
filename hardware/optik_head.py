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
    for n in ("VBAT","IR_MOD","GND","LED_MID","LED_CATH","IDRV_SENSE","DRV_GATE","IDRV_REF","OPA_OUT","EMIT_SET","V_SET"): N(n)

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

    # CC-sänka (front, mittband). POSITIONER COURTYARD-RENSADE (0 komponent-överlapp): R_0805-
    # courtyarden är 3,36×1,9 mm (bredare än kroppen) → parterna måste stå ≥3,4 mm isär. Tidigare
    # hand-läggning klustrade dem så KROPPARNA överlappade (C2/U1, C3/U1, R3/R4, R5/R3) och R1 låg
    # över kamerahålet CAM2; verifierat via GetCourtyard→BooleanIntersection. Kvarvarande courtyard-
    # touch är BARA mekanik (MH/CL-hål + bak-JST), där bibliotekets courtyards är översällt stora —
    # hålen ligger >2 mm isär och pad/hål-clearance är 0 (ingen DRC).
    Uop = fp("Package_TO_SOT_SMD","SOT-23-5","U1","OPA171",-1.44,-3.75,0)
    for p,n in (("1","OPA_OUT"),("2","GND"),("3","IDRV_REF"),("4","IDRV_SENSE"),("5","VBAT")): setnet(Uop,p,n)
    Qd = fp("Package_TO_SOT_SMD","TO-252-2","Q1","AOD4184A",-9,-6,0)
    for p,n in (("1","DRV_GATE"),("2","LED_CATH"),("3","IDRV_SENSE")): setnet(Qd,p,n)
    # FAST 3A-områdes-sense (0R068 2512, 1W): max-ström = Vref_max/Rs = 0,206/0,068 ≈ 3,0A vid full PWM-duty.
    Rs = fp("Resistor_SMD","R_2512_6332Metric","R1","0R068",8,-4,0); setnet(Rs,"1","IDRV_SENSE"); setnet(Rs,"2","GND")  # flyttad ner/in: klar av CAM2-hålet + bak-JST-courtyarden
    # KONTINUERLIG STRÖM-SET (firmware): EMIT_SET = PWM (CM5 GPIO13/PWM1) → RC-filter (R7/C4) → V_SET (DC).
    # V_SET → R3/R4-delare → IDRV_REF = V_SET/16. Duty 0–100% → ström 0–3A. Boot: GPIO13 låg → 0A (av).
    R7 = fp("Resistor_SMD","R_0805_2012Metric","R7","10k",7.76,0.0,0); setnet(R7,"1","EMIT_SET"); setnet(R7,"2","V_SET")
    C4 = fp("Capacitor_SMD","C_0805_2012Metric","C4","1uF",3.84,1.86,90); setnet(C4,"1","V_SET"); setnet(C4,"2","GND")  # RC τ≈10ms → ren DC-ref
    # 56kHz-GRIND: IR_MOD → Q3-grind kortar IDRV_REF→GND. IR_MOD hög = LED AV, låg = LED PÅ (firmware inverterar).
    Q3 = fp("Package_TO_SOT_SMD","SOT-23","Q3","AO3400",7.97,3.0,0); setnet(Q3,"1","IR_MOD"); setnet(Q3,"2","GND"); setnet(Q3,"3","IDRV_REF")  # G/S/D
    Cvb= fp("Capacitor_SMD","C_1206_3216Metric","C3","22uF",0.27,-0.66,0); setnet(Cvb,"1","VBAT"); setnet(Cvb,"2","GND")  # VBAT-bulk 22µF/25V (in-stock) för 3A-pulsens flanker
    Rda= fp("Resistor_SMD","R_0805_2012Metric","R3","15k",7.5,-12.5,0); setnet(Rda,"1","V_SET"); setnet(Rda,"2","IDRV_REF")  # ref-delare övre (V_SET→IDRV_REF)
    Rdb= fp("Resistor_SMD","R_0805_2012Metric","R4","1k",11.3,-12.5,0); setnet(Rdb,"1","IDRV_REF"); setnet(Rdb,"2","GND")  # 3,8 mm från R3 (0805-courtyard 3,36) + klar av benhål CL7
    Rg = fp("Resistor_SMD","R_0805_2012Metric","R5","100R",3.53,-7.73,0); setnet(Rg,"1","OPA_OUT"); setnet(Rg,"2","DRV_GATE")
    Cop= fp("Resistor_SMD","R_0805_2012Metric","C1","100nF",11.0,-9.11,0); setnet(Cop,"1","VBAT"); setnet(Cop,"2","GND")
    Cc = fp("Resistor_SMD","R_0805_2012Metric","C2","100pF",-0.84,-6.69,0); setnet(Cc,"1","OPA_OUT"); setnet(Cc,"2","IDRV_SENSE")  # under U1, courtyard-rensad, nära OPA-utg

    # JST 3-pin (VBAT·IR_MOD·GND) på BAKSIDAN, THT
    J = fp("Connector_JST","JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical","J1","→HAT (VBAT·IR_MOD·GND·EMIT_SET)",16,-3,90,back=True)
    setnet(J,"1","VBAT"); setnet(J,"2","IR_MOD"); setnet(J,"3","GND"); setnet(J,"4","EMIT_SET")

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

    # BOM ur den GEMENSAMMA MPN-databasen (vapen-stack/gen_nextpcb.py) — samma beprövade, sourcade
    # delar som övriga kort → matchar på NextPCB. Grupperar per (värde, footprint); kontakter (JST/
    # PinSocket) = handlödda (DNP). Lins+hållare köps separat (DNP-rader).
    import sys as _sys, re as _re
    _sys.path.insert(0, "vapen-stack"); from gen_nextpcb import MPN as _MPN, is_conn as _is_conn
    from collections import defaultdict as _dd
    COLS=["Designator*","Quantity*","Manufacturer Part Number*","Manufacturer","Package/Footprint","Description","Procurement Type","Customer Note"]
    grp=_dd(list)
    for f in b.GetFootprints():
        fpn=str(f.GetFPID().GetLibItemName())
        if any(k in fpn for k in ("MountingHole","Fiducial","TestPoint")): continue
        if f.Pads() and all(p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH for p in f.Pads()): continue
        grp[(f.GetValue(), fpn)].append(f.GetReference())
    def _rk(r): m=_re.match(r'([A-Za-z]+)(\d+)',r); return (m.group(1),int(m.group(2))) if m else (r,0)
    rows=[]
    for (val,pkg) in sorted(grp):
        refs=sorted(grp[(val,pkg)],key=_rk)
        m=_re.search(r'_(\d{4})_',pkg); key=f"{val}@{m.group(1)}" if m and f"{val}@{m.group(1)}" in _MPN else val
        mpn,mfr,desc,proc,note=_MPN.get(key,("","",val,"","SAKNAR MPN — fyll i"))
        if _is_conn(pkg): proc="DNP"; note="Kund handlöder (THT) — DNP, ej i centroid. BOM = beställningsreferens."
        rows.append((",".join(refs),str(len(refs)),mpn,mfr,pkg,desc,proc,note))
    # inköpta optik-delar utan footprint (köps separat, monteras manuellt) — DNP
    rows.append(("LENS1,LENS2","2","10195","Carclo","Ø20 TIR-kollimator","IR-kollimatorlins (smal beam) över varje emitter","DNP","Köps separat, monteras manuellt"))
    rows.append(("LHOLD1,LHOLD2","2","10734","Carclo","20mm 4-bens-hållare (ritn.60575)","Lins-hållare över emittern","DNP","Köps separat, monteras manuellt"))
    for od in ("hardware/nextpcb","leverans/optik-head"):
        os.makedirs(od,exist_ok=True); wb=xlwt.Workbook(); ws=wb.add_sheet("BOM")
        for c,h in enumerate(COLS): ws.write(0,c,h)
        for r,row in enumerate(rows,1):
            for c,v in enumerate(row): ws.write(r,c,v)
        wb.save(f"{od}/optik-head-bom.xls")
    # CENTROID via SAMMA delade funktion som HAT (gen_nextpcb.centroid) → identiskt NextPCB-format
    # (Mid X(mm)/Mid Y(mm), Top/Bottom, ABSOLUTA koord = matchar gerbers). Läser sparat kort.
    from gen_nextpcb import centroid as _centroid
    for od in ("hardware/nextpcb","leverans/optik-head"):
        _centroid("hardware/optik-head.kicad_pcb", f"{od}/optik-head-centroid.csv")
    print("  BOM + centroid (allt SMT på framsidan; JST THT bak; centroid = HAT-format)")

if __name__ == "__main__":
    main()
