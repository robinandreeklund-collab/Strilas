#!/usr/bin/env python3
"""STRILAS — route optik-head (41×56, 2-lager, GND-fyll båda sidor). Re-placeras av optik_head.py
(emittrar ±12 mm för Carclo 10734-fläns-clearance), routas här. Flöde som HAT-routern men 2-lager.
Kör:  python3 hardware/route_optik_head.py"""
import subprocess, os, shutil, pcbnew
PCB="hardware/optik-head.kicad_pcb"; DSN="hardware/optik-head.dsn"; SES="hardware/optik-head.ses"
MM=pcbnew.FromMM; OX,OY=150.0,120.0
def V(x,y): return pcbnew.VECTOR2I(MM(OX+x),MM(OY-y))
CU=[pcbnew.F_Cu,pcbnew.B_Cu]
def unrouted(path):
    b=pcbnew.LoadBoard(path); b.BuildConnectivity()
    try: return b.GetConnectivity().GetUnconnectedCount(True)
    except: return b.GetConnectivity().GetUnconnectedCount()
def finish(path):
    b=pcbnew.LoadBoard(path); g=b.FindNet("GND").GetNetCode()
    for z in list(b.Zones()): b.Remove(z)
    for L in CU:
        z=pcbnew.ZONE(b); z.SetLayer(L); z.SetNetCode(g); z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.2))
        ch=pcbnew.SHAPE_LINE_CHAIN()
        for x,y in [(-20.2,-27.7),(20.2,-27.7),(20.2,27.7),(-20.2,27.7)]: ch.Append(V(x,y))
        ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path,b)
def verify(path):
    b=pcbnew.LoadBoard(path); items=[]
    for t in b.GetTracks():
        lays=CU if t.Type()==pcbnew.PCB_VIA_T else [t.GetLayer()]; items.append((t.GetNetCode(),set(lays),t.GetEffectiveShape()))
    for f in b.GetFootprints():
        for pd in f.Pads(): items.append((pd.GetNetCode(),set(L for L in CU if pd.IsOnLayer(L)),pd.GetEffectiveShape()))
    v=sum(1 for i in range(len(items)) for j in range(i+1,len(items)) if items[i][0]!=items[j][0] and (items[i][1]&items[j][1]) and items[i][2].Collide(items[j][2],int(0.2e6)))
    return v,unrouted(path)

subprocess.run(["python3","hardware/optik_head.py"],stdout=subprocess.DEVNULL)
b=pcbnew.LoadBoard(PCB); b.SetCopperLayerCount(2)
for t in list(b.GetTracks()): b.Remove(t)
for z in list(b.Zones()): b.Remove(z)
pcbnew.SaveBoard(PCB,b); pcbnew.ExportSpecctraDSN(b,DSN)
subprocess.run(["python3","hardware/dsn_power_class.py",DSN])
shutil.copy(PCB,"/tmp/_oh_placed.kicad_pcb"); best=None
for seed in range(1,9):
    if os.path.exists(SES): os.remove(SES)
    subprocess.run(["timeout","-k","5","240","xvfb-run","-a","java","-jar","/opt/freerouting.jar","-de",DSN,"-do",SES,"-mp","100"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["bash","-c","pkill -9 -f freerouting.jar 2>/dev/null;pkill -9 Xvfb 2>/dev/null;true"])
    if not os.path.exists(SES) or os.path.getsize(SES)<800: print(f"seed{seed}:ingen SES",flush=True); continue
    shutil.copy("/tmp/_oh_placed.kicad_pcb",PCB)
    subprocess.run(["python3","hardware/ses_apply.py",PCB,SES],stdout=subprocess.DEVNULL)
    u=unrouted(PCB); print(f"seed{seed}:oanslutna={u}",flush=True)
    if best is None or u<best[0]: best=(u,seed); shutil.copy(PCB,"/tmp/_oh_best.kicad_pcb")
    if u==0: break
shutil.copy("/tmp/_oh_best.kicad_pcb",PCB); finish(PCB)
v,un=verify(PCB); print(f"FINAL clearance@0.2={v} oanslutna={un}",flush=True)
if v==0 and un==0:
    os.system("rm -rf /tmp/gboh && mkdir -p /tmp/gboh")
    subprocess.run(["kicad-cli","pcb","export","gerbers","--subtract-soldermask","-o","/tmp/gboh/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["kicad-cli","pcb","export","drill","-o","/tmp/gboh/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    os.makedirs("leverans/optik-head",exist_ok=True)
    subprocess.run(["bash","-c","cd /tmp/gboh && zip -q -r - . > /home/user/Strilas/leverans/optik-head/optik-head-gerbers.zip"])
    subprocess.run(["kicad-cli","pcb","export","step","-f","--subst-models","-o","leverans/optik-head/optik-head.step",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("REN → leverans/optik-head/",flush=True)
