import pcbnew, sys, re, math
net_f, pcb_f = sys.argv[1], sys.argv[2]
CU=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
# --- parse netlist: comp footprints + net nodes ---
t=open(net_f).read()
comp_fp={}
for m in re.finditer(r'\(comp\s*\(ref "([^"]+)"\).*?\(footprint "([^"]+)"\)', t, re.S): comp_fp[m.group(1)]=m.group(2)
nets={}
ns=t[t.index("(nets"):]
for blk in re.split(r'\(net\s*\(code', ns)[1:]:
    nm=re.search(r'\(name "([^"]+)"\)', blk); nodes=re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', blk)
    if nm and nodes: nets[nm.group(1)]=nodes
b=pcbnew.LoadBoard(pcb_f)
fps={f.GetReference():f for f in b.GetFootprints()}
padnames={r:set(p.GetName() for p in f.Pads()) for r,f in fps.items()}
issues=[]
# 1) varje komponent i netlistan finns på kortet + footprint matchar
for r,fp in comp_fp.items():
    if r not in fps: issues.append(f"SAKNAR komponent {r} på kortet"); continue
    bfp=str(fps[r].GetFPID().GetLibItemName())
    want=fp.split(":")[1]
    if bfp!=want: issues.append(f"{r}: footprint {bfp} != netlist {want}")
# 2) varje net-nod har matchande pad + pad har rätt net tilldelat
unassigned=0
for netname,nodes in nets.items():
    for ref,pin in nodes:
        if ref not in fps: continue
        if pin not in padnames[ref]:
            issues.append(f"{ref}: pad '{pin}' saknas i footprint (net {netname} EJ ansluten!)")
            continue
        # pad net == netname?
        for p in fps[ref].Pads():
            if p.GetName()==pin and p.GetNetname()!=netname:
                unassigned+=1
# 3) anslutning + clearance (efter pour)
try: pcbnew.ZONE_FILLER(b).Fill(b.Zones())
except: pass
b.BuildConnectivity()
try: un=b.GetConnectivity().GetUnconnectedCount(True)
except TypeError: un=b.GetConnectivity().GetUnconnectedCount()
# clearance@0.2
items=[]
for tr in b.GetTracks():
    lays=CU if tr.Type()==pcbnew.PCB_VIA_T else [tr.GetLayer()]
    items.append((tr.GetNetCode(),set(lays),tr.GetEffectiveShape()))
for f in b.GetFootprints():
    for pd in f.Pads(): items.append((pd.GetNetCode(),set(L for L in CU if pd.IsOnLayer(L)),pd.GetEffectiveShape()))
cl=sum(1 for i in range(len(items)) for j in range(i+1,len(items))
       if items[i][0]!=items[j][0] and (items[i][1]&items[j][1]) and items[i][2].Collide(items[j][2],int(0.2e6)))
print(f"=== {pcb_f.split('/')[-1]} ===")
print(f"  komponenter: netlist {len(comp_fp)}, board {len(fps)}")
print(f"  oanslutna (ratsnest): {un}   clearance@0.2mm: {cl}   pad-net-fel: {unassigned}")
if issues:
    print(f"  PROBLEM ({len(issues)}):")
    for i in issues[:20]: print("   -",i)
else:
    print("  ✓ alla footprints matchar, alla net-noder har pad")
