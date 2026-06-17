#!/usr/bin/env python3
"""Lägg projektnamnet 'STRILAS' på F.SilkS på varje kort, i en verifierat fri zon (ingen pad-krock).
Körs på de routade korten (silk påverkar ej routning). Kör om efter ev. omplacering/omroutning."""
import pcbnew, sys
OX,OY=150.0,120.0; MM=pcbnew.FromMM
def V(x,y): return pcbnew.VECTOR2I(MM(OX+x),MM(OY-y))
# kandidat-positioner (x,y,size_mm) per kort — första utan pad-krock väljs
CAND={
 "weapon-module":[(0,-33,1.6),(0,34,1.6),(0,-34.5,1.4),(-14,-34,1.3)],
 "firecontrol":[(0,-8.6,1.0),(-22,7.5,0.9),(0,8.6,0.9),(22,-7.5,0.9)],
 "vest-patch":[(0,10.8,1.0),(0,-10.8,1.0),(0,11.5,0.9)],
 "helmet-mb":[(0,33,1.8),(0,-33,1.8),(0,7,1.6),(30,0,1.6)],
 "vest-mb":[(0,17,1.8),(0,-17,1.8),(0,0,1.8)],
}
def pads_bbox(b):
    out=[]
    for f in b.GetFootprints():
        for p in f.Pads():
            bb=p.GetBoundingBox(); out.append((bb.GetLeft()/1e6-OX,bb.GetRight()/1e6-OX,OY-bb.GetBottom()/1e6,OY-bb.GetTop()/1e6))
    return out
def clear(x,y,w,h,pads,m=0.4):
    x0,x1,y0,y1=x-w/2-m,x+w/2+m,y-h/2-m,y+h/2+m
    for px0,px1,py0,py1 in pads:
        if not(px1<x0 or px0>x1 or py1<y0 or py0>y1): return False
    return True
only=sys.argv[1].replace("_","-") if len(sys.argv)>1 else None
for name in CAND:
    if only and name!=only: continue
    p=f"hardware/{name}.kicad_pcb"; b=pcbnew.LoadBoard(p)
    # ta bort ev. tidigare STRILAS-text
    for d in list(b.GetDrawings()):
        if d.Type()==pcbnew.PCB_TEXT_T and d.GetText()=="STRILAS": b.Remove(d)
    pads=pads_bbox(b); placed=None
    for x,y,sz in CAND[name]:
        w=len("STRILAS")*sz*0.75; h=sz
        if clear(x,y,w,h,pads):
            t=pcbnew.PCB_TEXT(b); t.SetText("STRILAS"); t.SetPosition(V(x,y)); t.SetLayer(pcbnew.F_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(MM(sz),MM(sz))); t.SetTextThickness(MM(sz*0.15))
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); b.Add(t); placed=(x,y,sz); break
    if placed: pcbnew.SaveBoard(p,b); print(f"{name}: STRILAS @ {placed}")
    else: print(f"{name}: !! ingen fri zon i kandidaterna")
