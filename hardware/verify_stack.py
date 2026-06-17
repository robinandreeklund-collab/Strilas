#!/usr/bin/env python3
"""STRILAS — RIGORÖS stack-verifiering inför custom-PCB-beställning.
Läser de FAKTISKA korten och kontrollerar allt som måste stämma för att
optik + (köpt) P4 + FC ska passa ihop mekaniskt OCH elektriskt.

Kör: python3 hardware/verify_stack.py
"""
import math, pcbnew

EDGE_A = [None,"GPIO52","GPIO51","GND","GPIO31","GPIO30","GPIO29","GPIO28","GND","GPIO50",
          "GPIO49","GPIO5","GPIO4","GND","GPIO3","GPIO2","GPIO8","GPIO7","GND","GPIO24","GPIO25"]
EDGE_B = [None,"VBUS","VSYS","GND","EN","3V3","GPIO20","GPIO21","GND","GPIO22","GPIO23","RUN",
          "GPIO26","GND","GPIO27","GPIO32","GPIO33","GPIO46","GND","GPIO47","GPIO48"]
OX,OY=150.0,120.0
PASS=[]; FAIL=[]
def chk(cond,msg):
    (PASS if cond else FAIL).append(msg); print(("  ✓ " if cond else "  ✗ FEL: ")+msg)

def fpt(b,ref): return [g for g in b.GetFootprints() if g.GetReference()==ref][0]
def pads(b,ref): return {p.GetName():p.GetPosition() for p in fpt(b,ref).Pads()}
def fpname(b,ref): return str(fpt(b,ref).GetFPID().GetLibItemName())
def netmap(b,ref): return {p.GetName():p.GetNetname() for p in fpt(b,ref).Pads()}
def items(b): return list(b.GetFootprints())+list(b.GetDrawings())+list(b.GetTracks())+list(b.Zones())
def xform(b,a,c,o):
    ea=pcbnew.EDA_ANGLE(a,pcbnew.DEGREES_T)
    for it in items(b): it.Rotate(c,ea)
    for it in items(b): it.Move(o)
def fit(src,ref,d1,d2):
    b=pcbnew.LoadBoard(src); P=pads(b,ref); nB=str(len(P)); p1,p2=P['1'],P[nB]
    ang=math.degrees(math.atan2(d2.y-d1.y,d2.x-d1.x)-math.atan2(p2.y-p1.y,p2.x-p1.x)); best=None
    for tr in (ang,-ang,ang+180,ang-180):
        b2=pcbnew.LoadBoard(src); c=pads(b2,ref)['1']; xform(b2,tr,pcbnew.VECTOR2I(c.x,c.y),pcbnew.VECTOR2I(0,0))
        q1=pads(b2,ref)['1']; xform(b2,0,pcbnew.VECTOR2I(0,0),pcbnew.VECTOR2I(d1.x-q1.x,d1.y-q1.y))
        e=(pads(b2,ref)[nB]-d2).EuclideanNorm()/1e6
        if best is None or e<best[0]: best=(e,b2)
    return best[1]
def near(P, pts):  # P:VECTOR2I, pts:{name:VECTOR2I} -> (name,dist_mm)
    return min(((n,(p-P).EuclideanNorm()/1e6) for n,p in pts.items()),key=lambda t:t[1])

op=pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
p4=pcbnew.LoadBoard("hardware/p4-board.kicad_pcb")
fc=pcbnew.LoadBoard("hardware/firecontrol.kicad_pcb")

print("=== 1. KONTAKT-GÄNGA (optik/FC = hona, P4 = hane) ===")
chk("PinSocket" in fpname(op,"J1"), f"optik J1 = hona-sockel ({fpname(op,'J1')})")
chk("PinSocket" in fpname(fc,"J1"), f"FC J1 = hona-sockel ({fpname(fc,'J1')})")
chk("PinHeader" in fpname(p4,"J_A") and "PinHeader" in fpname(p4,"J_B"), "P4 J_A/J_B = hane-stift (löds på Waveshare-modulen)")

print("\n=== 2. optik J1 ↔ P4 edge B : LÄGE (per stift) + NÄT→GPIO ===")
OJ=pads(op,"J1"); ON=netmap(op,"J1")
p4b=fit("hardware/p4-board.kicad_pcb","J_B",OJ["1"],OJ["14"]); JB=pads(p4b,"J_B")
maxB=0
for k in range(1,15):
    j,d=near(OJ[str(k)],JB); maxB=max(maxB,d); n=ON[str(k)] or "(NC)"; gpio=EDGE_B[16-int(j)]
    print(f"   J1.{k:<2} {n:<14} ↔ J_B pad {j:<2} (WS-pin{16-int(j):<2} {gpio:<7})  d={d:.3f}mm")
chk(maxB<0.05, f"alla 14 optik-stift sammanfaller med edge B (max {maxB:.3f} mm)")

print("\n=== 3. FC J1 ↔ P4 edge A : LÄGE (per stift) + NÄT→GPIO ===")
FJ=pads(fc,"J1"); FN=netmap(fc,"J1"); JA=pads(p4,"J_A"); maxA=0
for k in range(1,13):
    j,d=near(FJ[str(k)],JA); maxA=max(maxA,d); n=FN[str(k)] or "(NC)"; gpio=EDGE_A[int(j)+5]
    print(f"   J1.{k:<2} {n:<14} ↔ J_A pad {j:<2} (WS-pin{int(j)+5:<2} {gpio:<7})  d={d:.3f}mm")
chk(maxA<0.05, f"alla 12 FC-stift sammanfaller med edge A (max {maxA:.3f} mm)")

print("\n=== 4. STANDOFF/MONTERINGSHÅL linjerar (går att skruva ihop) ===")
# P4 monteringshål
MP={n:p for n,p in [(r,fpt(p4,r).GetPosition()) for r in ["MP1","MP2","MP3","MP4"]]}
MPt={n:fpt(p4b,n).GetPosition() for n in ["MP1","MP2","MP3","MP4"]}   # transf. till optikens frame
# optikens P4-standoffhål: leta de 4 hål som ligger närmast P4:s MP-hål
opholes={f.GetReference():f.GetPosition() for f in op.GetFootprints() if "MountingHole" in fpname(op,f.GetReference())}
maxS=0
for n,P in MPt.items():
    r,d=near(P,opholes); maxS=max(maxS,d)
    print(f"   P4 {n} ↔ optik {r}  d={d:.3f}mm")
chk(maxS<0.2, f"P4:s 4 hål linjerar med optikens standoff-hål (max {maxS:.3f} mm)")
# FC monteringshål vs P4 (samma frame redan)
fcholes={r:fpt(fc,r).GetPosition() for r in ["H1","H2","H3","H4"]}
maxF=max(near(P,fcholes)[1] for P in MP.values())
for n,P in MP.items():
    r,d=near(P,fcholes); print(f"   P4 {n} ↔ FC {r}  d={d:.3f}mm")
chk(maxF<0.2, f"FC:s 4 hål linjerar med P4:s hål (max {maxF:.3f} mm)")

print("\n=== 5. INGEN GPIO-KROCK (optik edge B vs FC edge A disjunkta) ===")
opg={EDGE_B[16-int(k)] for k in range(1,15) if (ON[str(k)] and EDGE_B[16-int(k)].startswith("GPIO"))}
fcg={EDGE_A[int(k)+5] for k in range(1,13) if (FN[str(k)] and EDGE_A[int(k)+5].startswith("GPIO"))}
clash=opg & fcg
chk(not clash, f"optik-GPIO {sorted(opg)} ∩ FC-GPIO {sorted(fcg)} = {sorted(clash) or 'tom (OK)'}")

print("\n=== 6. DRC (0 oanslutna + 0 clearance) på custom-korten ===")
CU=[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu]
def drc(path):
    b=pcbnew.LoadBoard(path); b.BuildConnectivity()
    try: un=b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError: un=b.GetConnectivity().GetUnconnectedCount()
    it=[]
    for t in b.GetTracks():
        ly=CU if t.Type()==pcbnew.PCB_VIA_T else [t.GetLayer()]; it.append((t.GetNetCode(),set(ly),t.GetEffectiveShape()))
    for f in b.GetFootprints():
        for pd in f.Pads(): it.append((pd.GetNetCode(),set(L for L in CU if pd.IsOnLayer(L)),pd.GetEffectiveShape()))
    v=sum(1 for i in range(len(it)) for j in range(i+1,len(it)) if it[i][0]!=it[j][0] and (it[i][1]&it[j][1]) and it[i][2].Collide(it[j][2],int(0.2e6)))
    return un,v
for nm,path in [("optik","hardware/weapon-module.kicad_pcb"),("firecontrol","hardware/firecontrol.kicad_pcb")]:
    un,v=drc(path); chk(un==0 and v==0, f"{nm}: unconnected={un} clearance={v}")

print("\n================  SAMMANFATTNING  ================")
print(f"  PASS: {len(PASS)}   FAIL: {len(FAIL)}")
print("  ALLT OK — stacken passar ihop." if not FAIL else "  !!! ÅTGÄRDA OVAN INNAN BESTÄLLNING")
