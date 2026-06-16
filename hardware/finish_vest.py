#!/usr/bin/env python3
"""Re-poola väst-patch med SOLID GND-pad-anslutning (inga termiska gap → alla GND-pads
får koppar), verifiera, exportera Gerbers + STEP."""
import subprocess, pcbnew
PCB="hardware/vest-patch.kicad_pcb"
MM=pcbnew.FromMM
b=pcbnew.LoadBoard(PCB)
gnd=None
for f in b.GetFootprints():
    for pd in f.Pads():
        if pd.GetNetname()=="GND": gnd=pd.GetNetCode()
for z in [x for x in b.Zones()]: b.Remove(z)
bb=b.GetBoardEdgesBoundingBox(); m=MM(0.4)
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z=pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(gnd)
    z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2)); z.SetIsFilled(False)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    ch=pcbnew.SHAPE_LINE_CHAIN()
    for x,y in [(bb.GetLeft()+m,bb.GetTop()+m),(bb.GetRight()-m,bb.GetTop()+m),
                (bb.GetRight()-m,bb.GetBottom()-m),(bb.GetLeft()+m,bb.GetBottom()-m)]:
        ch.Append(int(x),int(y))
    ch.SetClosed(True); z.AddPolygon(ch); b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(PCB, b)

b=pcbnew.LoadBoard(PCB); b.BuildConnectivity()
try: un=b.GetConnectivity().GetUnconnectedCount(True)
except TypeError: un=b.GetConnectivity().GetUnconnectedCount()
CU=[pcbnew.F_Cu, pcbnew.B_Cu]; items=[]
for t in b.GetTracks():
    lays=CU if t.Type()==pcbnew.PCB_VIA_T else [t.GetLayer()]
    items.append((t.GetNetCode(), set(lays), t.GetEffectiveShape()))
for f in b.GetFootprints():
    for pd in f.Pads(): items.append((pd.GetNetCode(), set(L for L in CU if pd.IsOnLayer(L)), pd.GetEffectiveShape()))
v=sum(1 for i in range(len(items)) for j in range(i+1,len(items))
      if items[i][0]!=items[j][0] and (items[i][1]&items[j][1]) and items[i][2].Collide(items[j][2], int(0.2e6)))
print(f"oconnected={un}  clearance-brott@0.2mm={v}")
if un==0 and v==0:
    import os
    os.makedirs("/tmp/gbv", exist_ok=True); os.system("rm -rf /tmp/gbv/*")
    subprocess.run(["kicad-cli","pcb","export","gerbers","-o","/tmp/gbv/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["kicad-cli","pcb","export","drill","-o","/tmp/gbv/",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    os.system("cd /tmp/gbv && zip -q -r - . > /dev/null; cd - >/dev/null")
    subprocess.run(["bash","-c","cd /tmp/gbv && zip -q -r - . > /home/user/Strilas/hardware/vest-patch-gerbers.zip"])
    subprocess.run(["kicad-cli","pcb","export","step","-f","--subst-models","-o","hardware/vest-patch.step",PCB],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("REN board → Gerbers + STEP exporterade.")
else:
    print("EJ REN — fixa innan export.")
