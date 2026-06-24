#!/usr/bin/env python3
"""STRILAS — route om optik/vapen-modulen (54×74, 4-lager: In1=GND, In2=VBAT, F/B=GND-fyll).
Körs efter geometri-ändring (J1 flyttad, P4-hålbild tillagd, Q2/C2 flyttade). Samma flöde som
moderkorten: strip → DSN → power-klass → freeroute (loop) → ses_apply → kopparplan → verifiera."""
import subprocess, sys, math, shutil, os, pcbnew
PCB="hardware/weapon-module.kicad_pcb"; DSN="hardware/weapon-module.dsn"; SES="hardware/weapon-module.ses"
MM=pcbnew.FromMM; OX,OY=150.0,120.0
def V(x,y): return pcbnew.VECTOR2I(MM(OX+x),MM(OY-y))
PLANE_NETS=("GND","VBAT")
CU=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]

def unrouted(path):
    b=pcbnew.LoadBoard(path); items=[]
    for i,t in enumerate(b.GetTracks()):
        net=t.GetNetname()
        if not net: continue
        if t.Type()==pcbnew.PCB_VIA_T: p=t.GetPosition(); items.append((net,("v",i),[(p.x,p.y,None)]))
        else: s,e,L=t.GetStart(),t.GetEnd(),t.GetLayer(); items.append((net,("t",i),[(s.x,s.y,L),(e.x,e.y,L)]))
    netpads={}
    for f in b.GetFootprints():
        for p in f.Pads():
            net=p.GetNetname()
            if not net: continue
            pos=p.GetPosition(); lays=[L for L in CU if p.IsOnLayer(L)]
            key=("p",f.GetReference()+"."+p.GetName())
            items.append((net,key,[(pos.x,pos.y,L) for L in lays] or [(pos.x,pos.y,None)]))
            netpads.setdefault(net,[]).append(key)
    bynet={}
    for net,key,pts in items: bynet.setdefault(net,[]).append((key,pts))
    par={}
    def find(x):
        par.setdefault(x,x)
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    bad=0
    for net,pads in netpads.items():
        if net in PLANE_NETS or len(pads)<2: continue
        el=bynet.get(net,[])
        for i in range(len(el)):
            for j in range(i+1,len(el)):
                (ka,pa),(kb,pb)=el[i],el[j]
                if any((la is None or lb is None or la==lb) and math.hypot(xa-xb,ya-yb)<60000 for xa,ya,la in pa for xb,yb,lb in pb): par[find(ka)]=find(kb)
        if len({find(k) for k in pads})>1: bad+=1
    return bad

def verify(path):
    b=pcbnew.LoadBoard(path); items=[]
    for t in b.GetTracks():
        lays=CU if t.Type()==pcbnew.PCB_VIA_T else [t.GetLayer()]
        items.append((t.GetNetCode(),set(lays),t.GetEffectiveShape()))
    for f in b.GetFootprints():
        for pd in f.Pads(): items.append((pd.GetNetCode(),set(L for L in CU if pd.IsOnLayer(L)),pd.GetEffectiveShape()))
    v=sum(1 for i in range(len(items)) for j in range(i+1,len(items))
          if items[i][0]!=items[j][0] and (items[i][1]&items[j][1]) and items[i][2].Collide(items[j][2],int(0.2e6)))
    b.BuildConnectivity()
    try: un=b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError: un=b.GetConnectivity().GetUnconnectedCount()
    return v,un

def leftover_nets(path):
    b=pcbnew.LoadBoard(path); items=[]
    for i,t in enumerate(b.GetTracks()):
        net=t.GetNetname()
        if not net: continue
        if t.Type()==pcbnew.PCB_VIA_T: p=t.GetPosition(); items.append((net,("v",i),[(p.x,p.y,None)]))
        else: s,e,L=t.GetStart(),t.GetEnd(),t.GetLayer(); items.append((net,("t",i),[(s.x,s.y,L),(e.x,e.y,L)]))
    netpads={}
    for f in b.GetFootprints():
        for p in f.Pads():
            net=p.GetNetname()
            if not net: continue
            pos=p.GetPosition(); lays=[L for L in CU if p.IsOnLayer(L)]
            key=("p",f.GetReference()+"."+p.GetName())
            items.append((net,key,[(pos.x,pos.y,L) for L in lays] or [(pos.x,pos.y,None)]))
            netpads.setdefault(net,[]).append(key)
    bynet={}
    for net,key,pts in items: bynet.setdefault(net,[]).append((key,pts))
    par={}
    def find(x):
        par.setdefault(x,x)
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    out=[]
    for net,pads in netpads.items():
        if net in PLANE_NETS or len(pads)<2: continue
        el=bynet.get(net,[])
        for i in range(len(el)):
            for j in range(i+1,len(el)):
                (ka,pa),(kb,pb)=el[i],el[j]
                if any((la is None or lb is None or la==lb) and math.hypot(xa-xb,ya-yb)<60000 for xa,ya,la in pa for xb,yb,lb in pb): par[find(ka)]=find(kb)
        if len({find(k) for k in pads})>1: out.append(net)
    return out

b=pcbnew.LoadBoard(PCB)
_tr=list(b.GetTracks()); _zo=list(b.Zones())
for t in _tr: b.Remove(t)
for z in _zo: b.Remove(z)
pcbnew.SaveBoard(PCB,b)
pcbnew.ExportSpecctraDSN(b,DSN)
subprocess.run(["python3","hardware/dsn_power_class.py",DSN])
# frigör alla lager: uteslut planade nät (GND+VBAT) ur freerouting → de fylls som plan i weapon_finish
import re as _re
_d=open(DSN).read()
for _n in ("GND","VBAT"):
    _d=_re.sub(r'\n\s*\(net '+_n+r'\s*\(pins[^)]*\)\s*\)','',_d)
_d=_d.replace(" GND "," ").replace(" VBAT "," ")
open(DSN,"w").write(_d)
shutil.copy(PCB,"/tmp/_opt_placed.kicad_pcb")
clean=False; best=None
for seed in range(1,13):
    if os.path.exists(SES): os.remove(SES)
    subprocess.run(["timeout","-k","5","240","xvfb-run","-a","java","-jar","/opt/freerouting.jar","-de",DSN,"-do",SES,"-mp","100"],
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["bash","-c","pkill -9 -f freerouting.jar 2>/dev/null; pkill -9 Xvfb 2>/dev/null; true"])
    if not os.path.exists(SES) or os.path.getsize(SES)<1000:
        print(f"  seed {seed}: ingen SES",flush=True); continue
    shutil.copy("/tmp/_opt_placed.kicad_pcb",PCB)
    subprocess.run(["python3","hardware/ses_apply.py",PCB,SES],stdout=subprocess.DEVNULL)
    u=unrouted(PCB); print(f"  seed {seed}: signal-oroutade = {u}",flush=True)
    if best is None or u<best[0]: best=(u,seed); shutil.copy(PCB,"/tmp/_opt_best.kicad_pcb")
    if u==0: clean=True; break
shutil.copy("/tmp/_opt_best.kicad_pcb",PCB)
if not clean:
    left=leftover_nets(PCB)
    print(f"  bästa seed {best[1]}: {best[0]} kvar ({left}) → maze-router",flush=True)
    subprocess.run(["python3","hardware/maze_route.py",PCB]+left)
    if unrouted(PCB)!=0: print("!! maze kunde ej stänga alla",flush=True); sys.exit(1)
subprocess.run(["python3","hardware/weapon_finish.py"])   # kopparplan In1=GND/In2=VBAT/F+B=GND
v,un=verify(PCB); print(f"clearance@0.2mm = {v}   oconnected = {un}")
if v or un: print("!! DRC ej ren"); sys.exit(1)
print("REN board.")
