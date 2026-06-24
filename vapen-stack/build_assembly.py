#!/usr/bin/env python3
"""STRILAS hop-assembly — PARALLELL STAPEL (som användarens montering):
optik med lins/IR/kamera UTÅT (vänd 180° om X), P4 + FC parallellt BAKOM, INOM
optikens kontur, 12 mm gap. P4/FC native; optikens J1 är speglad i netlistan så
den stackade (ansikte-mot-ansikte) monteringen kopplas rätt. Verifierar geometri:
edge-paddar sammanfaller, P4/FC inom konturen, lins utåt."""
import json, numpy as np, cadquery as cq

GAP = 12.0
P = json.load(open("_pads_z.json"))
def arr(k): d=P[k]["pads"]; ks=sorted(d,key=lambda z:int(z)); return np.array([d[x] for x in ks])
J1o=arr("optJ1"); JB=arr("p4_JB"); JA=arr("p4_JA"); FCp=arr("fc_J1")
def Rz(t): c,s=np.cos(t),np.sin(t); return np.array([[c,-s],[s,c]])

opt=cq.importers.importStep("weapon-module.step")
p4 =cq.importers.importStep("p4-board.step")
fc =cq.importers.importStep("firecontrol.step")
ob=opt.val().BoundingBox(); cx=(ob.xmin+ob.xmax)/2; cy=(ob.ymin+ob.ymax)/2; cz=(ob.zmin+ob.zmax)/2
OPTX=(ob.xmin,ob.xmax)

# optik vänd 180° om X (lins -z ut, J1 +z mot stacken)
J1f=np.c_[J1o[:,0], 2*cy-J1o[:,1]]

def place_set(src_pts, dst_pts, th, body_pts):
    """rotera src med th, centroid→dst-centroid; returnera transform-funk + edgeA-pose + set-fel."""
    R=Rz(np.radians(th)); q=(R@src_pts.T).T; t=dst_pts.mean(0)-q.mean(0)
    qs=q+t
    D=np.linalg.norm(qs[:,None,:]-dst_pts[None,:,:],axis=2); err=D.min(1).max()
    body=(R@body_pts.T).T+t
    return th,t,R,err,body

# P4: hitta th (90/270) så J_B sammanfaller med J1f OCH edge A hamnar INOM optiken
bestP=None
for th in (90,270):
    _,t,R,err,body=place_set(JB,J1f,th,JA)
    inside = body[:,0].min()>=OPTX[0]-1 and body[:,0].max()<=OPTX[1]+1
    if err<0.3 and inside: bestP=(th,t,R,body)
    print(f"  P4 th={th}: J_B↔J1-fel {err:.3f}mm  edge A x[{body[:,0].min():.0f},{body[:,0].max():.0f}] inom optik={inside}")
th,t,R,jaP = bestP
print(f"\nVALD P4: th={th} (edge A inom optikens kontur)")

# FC: J1 → posed edge A (native, rak); samma centroid+rotation
bestF=None
for thf in (0,90,180,270):
    _,tf,Rf,errf,_=place_set(FCp,jaP,thf,FCp)
    if errf<0.3: bestF=(thf,tf,Rf,errf)
thf,tf,Rf,errf=bestF
print(f"FC: th={thf}  J1↔edgeA-fel {errf:.3f}mm")

# ---- bygg ----
optP=opt.rotate((cx,cy,cz),(cx+1,cy,cz),180)              # lins ut
optTop=optP.val().BoundingBox().zmax
p4P=p4.rotate((0,0,0),(0,0,1),th).translate((t[0],t[1],optTop+GAP))
fcP=fc.rotate((0,0,0),(0,0,1),thf).translate((tf[0],tf[1],optTop+2*GAP))

oz=optP.val().BoundingBox(); pz=p4P.val().BoundingBox(); fz=fcP.val().BoundingBox()
print("\n[VERIFIERING]")
print(f"  optik z[{oz.zmin:.1f},{oz.zmax:.1f}] (lins -z UT)  P4 z[{pz.zmin:.1f},{pz.zmax:.1f}]  FC z[{fz.zmin:.1f},{fz.zmax:.1f}]")
print(f"  P4 x[{pz.xmin:.0f},{pz.xmax:.0f}] inom optik x[{OPTX[0]:.0f},{OPTX[1]:.0f}]: {pz.xmin>=OPTX[0]-2 and pz.xmax<=OPTX[1]+2}")
print(f"  emitter ut & stack bakom (motsatta sidor): {'JA ✓' if pz.zmin>oz.zmin else 'NEJ ✗'}")
asm=cq.Assembly(name="STRILAS_vapen_stack")
asm.add(optP,name="optik"); asm.add(p4P,name="P4"); asm.add(fcP,name="FC")
asm.export("strilas-assembly.step"); print("\nskrev strilas-assembly.step ✓")
