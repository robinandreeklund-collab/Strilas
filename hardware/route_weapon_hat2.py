#!/usr/bin/env python3
"""STRILAS — route vapen-HAT, 4-LAGER med GND INKLUDERAT i freerouting.
Det täta 2-lagerskortet lämnade GND-pads inboxade (maze + post-stitch räckte ej).
4 lager ger freerouting plats att routa GND också (via till plan/spår). Sedan GND-
fyll på alla lager + verifiera 0/0 → leverans. Regenererar placeringen först."""
import subprocess, sys, math, shutil, os, re, pcbnew
PCB="hardware/weapon-hat.kicad_pcb"; DSN="hardware/weapon-hat.dsn"; SES="hardware/weapon-hat.ses"
MM=pcbnew.FromMM; OX,OY=150.0,120.0
def V(x,y): return pcbnew.VECTOR2I(MM(OX+x),MM(OY-y))
CU=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]

def _conn(path,names=False):
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
            key=("p",f.GetReference()+"."+p.GetName()); items.append((net,key,[(pos.x,pos.y,L) for L in lays] or [(pos.x,pos.y,None)])); netpads.setdefault(net,[]).append(key)
    bynet={}
    for net,key,pts in items: bynet.setdefault(net,[]).append((key,pts))
    par={}
    def find(x):
        par.setdefault(x,x)
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    bad=0; nm=[]
    for net,pads in netpads.items():
        if len(pads)<2: continue
        el=bynet.get(net,[])
        for i in range(len(el)):
            for j in range(i+1,len(el)):
                (ka,pa),(kb,pb)=el[i],el[j]
                if any((la is None or lb is None or la==lb) and math.hypot(xa-xb,ya-yb)<60000 for xa,ya,la in pa for xb,yb,lb in pb): par[find(ka)]=find(kb)
        if len({find(k) for k in pads})>1: bad+=1; nm.append(net)
    return nm if names else bad

def finish(path):
    b=pcbnew.LoadBoard(path)
    for z in list(b.Zones()): b.Remove(z)
    g=b.FindNet("GND").GetNetCode()
    for L in (pcbnew.F_Cu,pcbnew.B_Cu):
        z=pcbnew.ZONE(b); z.SetLayer(L); z.SetNetCode(g); z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2))
        ch=pcbnew.SHAPE_LINE_CHAIN()
        for x,y in [(-34.7,-28.7),(34.7,-28.7),(34.7,28.7),(-34.7,28.7)]: ch.Append(V(x,y))
        ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path,b)

def verify(path):
    b=pcbnew.LoadBoard(path); items=[]
    for t in b.GetTracks():
        lays=CU if t.Type()==pcbnew.PCB_VIA_T else [t.GetLayer()]; items.append((t.GetNetCode(),set(lays),t.GetEffectiveShape()))
    for f in b.GetFootprints():
        for pd in f.Pads(): items.append((pd.GetNetCode(),set(L for L in CU if pd.IsOnLayer(L)),pd.GetEffectiveShape()))
    v=sum(1 for i in range(len(items)) for j in range(i+1,len(items)) if items[i][0]!=items[j][0] and (items[i][1]&items[j][1]) and items[i][2].Collide(items[j][2],int(0.2e6)))
    b.BuildConnectivity()
    try: un=b.GetConnectivity().GetUnconnectedCount(True)
    except: un=b.GetConnectivity().GetUnconnectedCount()
    return v,un

# 1) regenerera ren placering + gör 4-lager
subprocess.run(["python3","hardware/weapon_hat_place.py"],stdout=subprocess.DEVNULL)
b=pcbnew.LoadBoard(PCB); b.SetCopperLayerCount(4)
for t in list(b.GetTracks()): b.Remove(t)
for z in list(b.Zones()): b.Remove(z)
pcbnew.SaveBoard(PCB,b)
pcbnew.ExportSpecctraDSN(b,DSN)
subprocess.run(["python3","hardware/dsn_power_class.py",DSN])
shutil.copy(PCB,"/tmp/_hat2_placed.kicad_pcb")
best=None
for seed in range(1,7):
    if os.path.exists(SES): os.remove(SES)
    subprocess.run(["timeout","-k","5","420","xvfb-run","-a","java","-jar","/opt/freerouting.jar","-de",DSN,"-do",SES,"-mp","100"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["bash","-c","pkill -9 -f freerouting.jar 2>/dev/null; pkill -9 Xvfb 2>/dev/null; true"])
    if not os.path.exists(SES) or os.path.getsize(SES)<1000: print(f"seed {seed}: ingen SES"); continue
    shutil.copy("/tmp/_hat2_placed.kicad_pcb",PCB)
    subprocess.run(["python3","hardware/ses_apply.py",PCB,SES],stdout=subprocess.DEVNULL)
    u=_conn(PCB); print(f"seed {seed}: oroutade={u}",flush=True)
    if best is None or u<best[0]: best=(u,seed); shutil.copy(PCB,"/tmp/_hat2_best.kicad_pcb")
    if u==0: break
shutil.copy("/tmp/_hat2_best.kicad_pcb",PCB)
left=_conn(PCB,names=True)
if left: print(f"kvar: {left} → maze"); subprocess.run(["python3","hardware/maze_route.py",PCB]+left)
finish(PCB)
v,un=verify(PCB); print(f"FINAL clearance@0.2={v} oanslutna={un}",flush=True)
if v==0 and un==0:
    os.system("rm -rf /tmp/gbhat && mkdir -p /tmp/gbhat")
    subprocess.run(["kicad-cli","pcb","export","gerbers","-o","/tmp/gbhat/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["kicad-cli","pcb","export","drill","-o","/tmp/gbhat/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    os.makedirs("leverans/weapon-hat",exist_ok=True)
    subprocess.run(["bash","-c","cd /tmp/gbhat && zip -q -r - . > /home/user/Strilas/leverans/weapon-hat/weapon-hat-gerbers.zip"])
    subprocess.run(["kicad-cli","pcb","export","step","-f","--subst-models","-o","leverans/weapon-hat/weapon-hat.step",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("REN → leverans/weapon-hat/",flush=True)
