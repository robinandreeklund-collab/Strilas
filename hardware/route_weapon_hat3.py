#!/usr/bin/env python3
"""STRILAS — route vapen-HAT (56×41, 34 komp), 4-LAGER med GND inkluderat i freerouting."""
import subprocess,os,shutil,math,re,pcbnew
PCB="hardware/weapon-hat.kicad_pcb";DSN="hardware/weapon-hat.dsn";SES="hardware/weapon-hat.ses"
MM=pcbnew.FromMM;OX,OY=150.0,120.0
def V(x,y):return pcbnew.VECTOR2I(MM(OX+x),MM(OY-y))
CU=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
def unrouted(path):
    b=pcbnew.LoadBoard(path);b.BuildConnectivity()
    try:return b.GetConnectivity().GetUnconnectedCount(True)
    except:return b.GetConnectivity().GetUnconnectedCount()
def leftover_nets(path):
    import math
    from collections import defaultdict
    b=pcbnew.LoadBoard(path);items=[]
    for i,t in enumerate(b.GetTracks()):
        net=t.GetNetname()
        if not net:continue
        if t.Type()==pcbnew.PCB_VIA_T:p=t.GetPosition();items.append((net,("v",i),[(p.x,p.y,None)]))
        else:s,e=t.GetStart(),t.GetEnd();items.append((net,("t",i),[(s.x,s.y,t.GetLayer()),(e.x,e.y,t.GetLayer())]))
    netpads=defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            net=p.GetNetname()
            if not net:continue
            pos=p.GetPosition();lays=[L for L in CU if p.IsOnLayer(L)];key=("p",f.GetReference()+"."+p.GetName())
            items.append((net,key,[(pos.x,pos.y,L) for L in lays] or [(pos.x,pos.y,None)]));netpads[net].append(key)
    bynet=defaultdict(list)
    for net,key,pts in items:bynet[net].append((key,pts))
    out=[]
    for net,pads in netpads.items():
        if net=="GND" or len(pads)<2:continue
        el=bynet[net];par={}
        def find(x):
            par.setdefault(x,x)
            while par[x]!=x:par[x]=par[par[x]];x=par[x]
            return x
        for i in range(len(el)):
            for j in range(i+1,len(el)):
                (ka,pa),(kb,pb)=el[i],el[j]
                if any((la is None or lb is None or la==lb) and math.hypot(xa-xb,ya-yb)<60000 for xa,ya,la in pa for xb,yb,lb in pb):par[find(ka)]=find(kb)
        if len({find(k) for k in pads})>1:out.append(net)
    return out
def finish(path):
    b=pcbnew.LoadBoard(path);g=b.FindNet("GND").GetNetCode()
    for z in list(b.Zones()):b.Remove(z)
    for L in (pcbnew.F_Cu,pcbnew.B_Cu):
        z=pcbnew.ZONE(b);z.SetLayer(L);z.SetNetCode(g);z.SetLocalClearance(MM(0.3));z.SetMinThickness(MM(0.2))
        ch=pcbnew.SHAPE_LINE_CHAIN()
        for x,y in [(-27.7,-20.2),(27.7,-20.2),(27.7,20.2),(-27.7,20.2)]:ch.Append(V(x,y))
        ch.SetClosed(True);z.AddPolygon(ch);b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(path,b)
def verify(path):
    b=pcbnew.LoadBoard(path);items=[]
    for t in b.GetTracks():
        lays=CU if t.Type()==pcbnew.PCB_VIA_T else [t.GetLayer()];items.append((t.GetNetCode(),set(lays),t.GetEffectiveShape()))
    for f in b.GetFootprints():
        for pd in f.Pads():items.append((pd.GetNetCode(),set(L for L in CU if pd.IsOnLayer(L)),pd.GetEffectiveShape()))
    v=sum(1 for i in range(len(items)) for j in range(i+1,len(items)) if items[i][0]!=items[j][0] and (items[i][1]&items[j][1]) and items[i][2].Collide(items[j][2],int(0.2e6)))
    return v,unrouted(path)
subprocess.run(["python3","hardware/weapon_hat_place.py"],stdout=subprocess.DEVNULL)
b=pcbnew.LoadBoard(PCB);b.SetCopperLayerCount(4)
for t in list(b.GetTracks()):b.Remove(t)
for z in list(b.Zones()):b.Remove(z)
pcbnew.SaveBoard(PCB,b);pcbnew.ExportSpecctraDSN(b,DSN)
subprocess.run(["python3","hardware/dsn_power_class.py",DSN])
shutil.copy(PCB,"/tmp/_hat3_placed.kicad_pcb");best=None
for seed in range(1,7):
    if os.path.exists(SES):os.remove(SES)
    subprocess.run(["timeout","-k","5","360","xvfb-run","-a","java","-jar","/opt/freerouting.jar","-de",DSN,"-do",SES,"-mp","100"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["bash","-c","pkill -9 -f freerouting.jar 2>/dev/null;pkill -9 Xvfb 2>/dev/null;true"])
    if not os.path.exists(SES) or os.path.getsize(SES)<1000:print(f"seed{seed}:ingen SES",flush=True);continue
    shutil.copy("/tmp/_hat3_placed.kicad_pcb",PCB)
    subprocess.run(["python3","hardware/ses_apply.py",PCB,SES],stdout=subprocess.DEVNULL)
    u=unrouted(PCB);print(f"seed{seed}:oanslutna={u}",flush=True)
    if best is None or u<best[0]:best=(u,seed);shutil.copy(PCB,"/tmp/_hat3_best.kicad_pcb")
    if u==0:break
shutil.copy("/tmp/_hat3_best.kicad_pcb",PCB)
if unrouted(PCB):
    left=leftover_nets(PCB);print(f"maze-router för kvarvarande: {left}",flush=True)
    if left:subprocess.run(["python3","hardware/maze_route.py",PCB]+left)
finish(PCB)
v,un=verify(PCB);print(f"FINAL clearance@0.2={v} oanslutna={un}",flush=True)
if v==0 and un==0:
    os.system("rm -rf /tmp/gbhat && mkdir -p /tmp/gbhat")
    subprocess.run(["kicad-cli","pcb","export","gerbers","--subtract-soldermask","-o","/tmp/gbhat/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["kicad-cli","pcb","export","drill","-o","/tmp/gbhat/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    os.makedirs("leverans/weapon-hat",exist_ok=True)
    subprocess.run(["bash","-c","cd /tmp/gbhat && zip -q -r - . > /home/user/Strilas/leverans/weapon-hat/weapon-hat-gerbers.zip"])
    subprocess.run(["kicad-cli","pcb","export","step","-f","--subst-models","-o","leverans/weapon-hat/weapon-hat.step",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("REN → leverans/weapon-hat/",flush=True)
