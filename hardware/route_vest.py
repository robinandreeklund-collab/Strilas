#!/usr/bin/env python3
"""STRILAS — route väst-patch (2-lager) rent: GND-pour FÖRST (så freerouting bara drar
signalnät, ej GND), freeroute, applicera SES, re-fyll pour, verifiera, Gerbers/STEP."""
import subprocess, sys, math, pcbnew
PCB="hardware/vest-patch.kicad_pcb"; DSN="hardware/vest-patch.dsn"; SES="hardware/vest-patch.ses"
MM=pcbnew.FromMM

def pour_gnd(path):
    b=pcbnew.LoadBoard(path)
    for z in [x for x in b.Zones()]: b.Remove(z)
    bb=b.GetBoardEdgesBoundingBox(); gnd=b.FindNet("GND").GetNetCode(); m=MM(0.4)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z=pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(gnd)
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2)); z.SetIsFilled(False)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # solid GND-pad-anslutning → inga termiska gap
        ch=pcbnew.SHAPE_LINE_CHAIN()
        for x,y in [(bb.GetLeft()+m,bb.GetTop()+m),(bb.GetRight()-m,bb.GetTop()+m),
                    (bb.GetRight()-m,bb.GetBottom()-m),(bb.GetLeft()+m,bb.GetBottom()-m)]:
            ch.Append(int(x),int(y))
        ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(path,b)

def unrouted(path):
    b=pcbnew.LoadBoard(path); tr={}
    for t in b.GetTracks(): tr.setdefault(t.GetNetCode(),[]).extend(
        [(t.GetStart().x/1e6,t.GetStart().y/1e6),(t.GetEnd().x/1e6,t.GetEnd().y/1e6)])
    return sum(1 for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() not in ("","GND")
        and not any(math.hypot(p.GetPosition().x/1e6-ex,p.GetPosition().y/1e6-ey)<0.4 for ex,ey in tr.get(p.GetNetCode(),[])))

def verify(path):
    b=pcbnew.LoadBoard(path); CU=[pcbnew.F_Cu,pcbnew.B_Cu]; items=[]
    for t in b.GetTracks():
        lays=CU if t.Type()==pcbnew.PCB_VIA_T else [t.GetLayer()]
        items.append((t.GetNetCode(),set(lays),t.GetEffectiveShape()))
    for f in b.GetFootprints():
        for pd in f.Pads(): items.append((pd.GetNetCode(),set(L for L in CU if pd.IsOnLayer(L)),pd.GetEffectiveShape()))
    v=0
    for i in range(len(items)):
        for j in range(i+1,len(items)):
            if items[i][0]==items[j][0] or not(items[i][1]&items[j][1]): continue
            if items[i][2].Collide(items[j][2],int(0.2e6)): v+=1
    b.BuildConnectivity()
    try: un=b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError: un=b.GetConnectivity().GetUnconnectedCount()
    return v,un

# 1) route ALLA nät (inkl GND som spår) — ingen pour → inga GND-öar (2-lager, som originalet)
import shutil; shutil.copy(PCB,"/tmp/_vest_pp.kicad_pcb")
b=pcbnew.LoadBoard(PCB); pcbnew.ExportSpecctraDSN(b,DSN)
clean=False
for seed in range(1,9):
    subprocess.run(["xvfb-run","-a","java","-jar","/opt/freerouting.jar","-de",DSN,"-do",SES,"-mp","200"],
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    shutil.copy("/tmp/_vest_pp.kicad_pcb",PCB)
    subprocess.run(["python3","hardware/ses_apply.py",PCB,SES],stdout=subprocess.DEVNULL)
    u=unrouted(PCB)
    print(f"  seed {seed}: oroutade={u}")
    if u==0: clean=True; break
if not clean: print("!! ingen ren routning"); sys.exit(1)
v,un=verify(PCB); print(f"clearance-brott@0.2mm={v}  oconnected={un}")
if v or un: print("!! DRC ej ren"); sys.exit(1)
print("REN board.")
# Gerbers + STEP
import os
os.system("rm -rf /tmp/gbv && mkdir -p /tmp/gbv")
subprocess.run(["kicad-cli","pcb","export","gerbers","-o","/tmp/gbv/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(["kicad-cli","pcb","export","drill","-o","/tmp/gbv/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(["bash","-c","cd /tmp/gbv && zip -q -r - . > /home/user/Strilas/hardware/vest-patch-gerbers.zip"])
subprocess.run(["kicad-cli","pcb","export","step","-f","--subst-models","-o","hardware/vest-patch.step",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print("Gerbers + STEP exporterade.")
