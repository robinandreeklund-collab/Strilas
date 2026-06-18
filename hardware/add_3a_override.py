#!/usr/bin/env python3
"""STRILAS — applicera 3A-override på det routade optikkortet (sense-sidan):
Rp(0R1,1206) + LÅG solder-jumper JP1 parallellt över Rsense(R2,0R2) → bygla = 3A, open = 1A (fail-safe).
Kopplar bara IDRV_SENSE↔GND (lokalt vid R2) → ingen op-amp-referens-routing. Byter F1→PTC_3A, emitter
→SFH4725AS. Bevarar all befintlig routning. Kör EN gång på c644fcf-kortet; därefter weapon_finish.
(Op-amp-referensen IDRV_REF är inmurad i det mättade delarområdet → sense-sidan valdes istället.)"""
import pcbnew
b=pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb"); MM=pcbnew.FromMM
def Vec(x,y): return pcbnew.VECTOR2I(MM(x),MM(y))
def suff(n): return n.split('/')[-1]
def netobj(s):
    for f in b.GetFootprints():
        for p in f.Pads():
            if suff(p.GetNetname())==s: return p.GetNet()
def pp(ref,pad):
    for f in b.GetFootprints():
        if f.GetReferenceAsString()==ref:
            for p in f.Pads():
                if p.GetName()==pad: return (p.GetPosition().x/1e6,p.GetPosition().y/1e6)
for f in b.GetFootprints():
    fid=f.GetFPIDAsString()
    if 'Fuse_1206' in fid: f.SetValue("PTC_3A")
    if 'IR_Emitter' in fid: f.SetValue("SFH4725AS_940nm_bin13")
isense=netobj("IDRV_SENSE"); gnd=netobj("GND")
novr=pcbnew.NETINFO_ITEM(b,"N_OVR"); b.Add(novr)
def add_fp(ld,nm,ref,val,x,y,nets,rot=0):
    fp=pcbnew.FootprintLoad(f"/usr/share/kicad/footprints/{ld}.pretty",nm)
    fp.SetReference(ref); fp.SetValue(val); fp.SetPosition(Vec(x,y))
    if rot: fp.SetOrientationDegrees(rot)
    for pd,nt in zip(list(fp.Pads()),nets): pd.SetNet(nt)
    b.Add(fp)
add_fp("Resistor_SMD","R_1206_3216Metric","R10","0R1",148.0,119.0,[isense,novr])
add_fp("Jumper","SolderJumper-2_P1.3mm_Open_TrianglePad1.0x1.5mm","JP1","3A-OVR",152.5,121.5,[novr,gnd])
(rp1x,rp1y)=pp('R10','1'); (rp2x,rp2y)=pp('R10','2')
(jp1x,jp1y)=pp('JP1','1'); (jp2x,jp2y)=pp('JP1','2'); (r21x,r21y)=pp('R2','1'); (r22x,r22y)=pp('R2','2')
def seg(n,layer,pts,w):
    for i in range(len(pts)-1):
        t=pcbnew.PCB_TRACK(b); t.SetStart(Vec(*pts[i])); t.SetEnd(Vec(*pts[i+1])); t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(n); b.Add(t)
F=pcbnew.F_Cu
seg(isense,F,[(r21x,r21y),(147.3,116.5),(rp1x,rp1y)],0.4)   # IDRV_SENSE: R2.1 -> Rp.1
seg(novr,F,[(rp2x,rp2y),(jp1x,jp1y)],0.4)                   # N_OVR: Rp.2 -> SJ.1
seg(gnd,F,[(jp2x,jp2y),(jp2x,118.0),(r22x,r22y)],0.4)       # GND: SJ.2 -> R2.2
pcbnew.SaveBoard("hardware/weapon-module.kicad_pcb",b)
print("sense3 (solder-jumper) klar; Rp@(%.1f,%.1f) SJ@(%.1f,%.1f)"%(rp1x,rp1y,jp1x,jp1y))
