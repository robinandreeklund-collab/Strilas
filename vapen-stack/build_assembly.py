#!/usr/bin/env python3
"""Bygg FYSISKT KORREKT assembly: brute-force pose för P4 & FC så att
(1) edge-stiften pekar IN i socketarna (mate), (2) optikens emitter pekar UT,
(3) korten ligger inom optikens kontur vid sidan om linsen. 3D-verifierat.
OUT = +z (optik native, emitter upp/ut); stacken hänger under (-z)."""
import json, numpy as np, cadquery as cq

GAP = 12.0
P = json.load(open("_pads_z.json"))
def arr(key): d=P[key]["pads"]; ks=sorted(d,key=lambda z:int(z)); return ks,np.array([d[k] for k in ks]),P[key]["pin_normal_z"]

optk, optP, optN = arr("optJ1")     # optik J1 (native), pins -z (öppning ned)
jbk,  jbP,  jbN  = arr("p4_JB")
jak,  jaP,  jaN  = arr("p4_JA")
fck,  fcP,  fcN  = arr("fc_J1")

def Rz(t): c,s=np.cos(t),np.sin(t); return np.array([[c,-s],[s,c]])
def pose2d(pts, th, flipx, flipy):
    q=(Rz(th)@pts.T).T
    if flipx: q=q*[1,-1]      # Rx180: y->-y
    if flipy: q=q*[-1,1]      # Ry180: x->-x
    return q

def find_pose(srcP, srcN, dstP, want_normal):
    """hitta (th,flipx,flipy,t) så srcP->dstP (pin k->k, <0.3mm) och transformerad pin-normal = want_normal."""
    best=None
    for th in (0, np.pi/2, np.pi, 3*np.pi/2):
        for fx in (False,True):
            for fy in (False,True):
                nz = srcN * (-1 if fx else 1) * (-1 if fy else 1)
                if round(nz)!=want_normal: continue
                q=pose2d(srcP, th, fx, fy)
                t=dstP[0]-q[0]                      # pin1->pin1
                err=np.max(np.linalg.norm((q+t)-dstP,axis=1))
                if err<0.3 and (best is None or err<best[0]):
                    best=(err,th,fx,fy,t)
    return best

# P4: J_B ska mata optik-J1. optik-J1 öppning -z (ned); P4 under → J_B-stift +z (upp).
bp=find_pose(jbP, jbN, optP, +1)
print("P4-pose (J_B→optJ1):", "FEL" if not bp else f"err={bp[0]:.3f}mm th={int(np.degrees(bp[1]))} flipx={bp[2]} flipy={bp[3]}")
# transformera P4 edge A med samma pose → mål för FC
def applied(pts, th,fx,fy,t): return pose2d(pts,th,fx,fy)+t
ja_posed=applied(jaP, bp[1],bp[2],bp[3],bp[4])
# P4-kropp (mellan J_B och J_A) i posed-läge — kolla inom optik + fri från lins
jb_posed=applied(jbP, bp[1],bp[2],bp[3],bp[4])
bodyx=[jb_posed[:,0].min(), jb_posed[:,0].max(), ja_posed[:,0].min(), ja_posed[:,0].max()]
print(f"  P4 edge B/A x-spann posed: [{min(bodyx):.1f},{max(bodyx):.1f}]  (optik x[123,177], lins~x150)")

# FC: J1 ska mata P4 edge A. edge A pin-normal (posed): jaN*(flip)... FC under P4 → FC-J1-stift +z (upp).
# edge A posed-normal:
eaN = jaN*(-1 if bp[2] else 1)*(-1 if bp[3] else 1)
fp=find_pose(fcP, fcN, ja_posed, +1)   # FC J1 stift upp mot edge A
print("FC-pose (J1→edgeA):", "FEL" if not fp else f"err={fp[0]:.3f}mm th={int(np.degrees(fp[1]))} flipx={fp[2]} flipy={fp[3]}")

# ---- bygg i cadquery ----
def cq_pose(shape, th, fx, fy, t, z):
    s=shape.rotate((0,0,0),(0,0,1), np.degrees(th))
    if fx: s=s.rotate((0,0,0),(1,0,0),180)
    if fy: s=s.rotate((0,0,0),(0,1,0),180)
    return s.translate((t[0], t[1], z))

opt=cq.importers.importStep("weapon-module.step")    # native, emitter +z = UT
p4 =cq.importers.importStep("p4-board.step")
fc =cq.importers.importStep("firecontrol.step")
optb=opt.val().BoundingBox()
p4_p=cq_pose(p4, bp[1],bp[2],bp[3],bp[4], optb.zmin-GAP)
fc_p=cq_pose(fc, fp[1],fp[2],fp[3],fp[4], optb.zmin-2*GAP)

# verifiering
print("\n[VERIFIERING]")
ez=opt.val().BoundingBox(); pz=p4_p.val().BoundingBox()
print(f"  optik z[{ez.zmin:.1f},{ez.zmax:.1f}] (emitter +z=UT)   P4 z[{pz.zmin:.1f},{pz.zmax:.1f}]")
print(f"  emitter & stack motsatta sidor: {'JA ✓' if pz.zmax<=ez.zmin+0.6 else 'NEJ ✗'}")
ok = bp and fp and bp[0]<0.3 and fp[0]<0.3 and pz.zmax<=ez.zmin+0.6
if ok:
    asm=cq.Assembly(name="STRILAS_vapen_stack")
    asm.add(opt,name="optik"); asm.add(p4_p,name="P4"); asm.add(fc_p,name="FC")
    asm.export("strilas-assembly.step"); print("\nskrev strilas-assembly.step ✓")
else:
    print("\n!! verifiering ej ren")
