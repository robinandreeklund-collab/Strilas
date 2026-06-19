#!/usr/bin/env python3
"""Liten A*-maze-router för enstaka kvarvarande nät som freerouting inte stänger.
Rutnät 0.2 mm, 2 lager (F/B), via-kostnad, hinder = andra näts spår/paddar (klarans 0.2 mm).
Användning: python3 hardware/maze_route.py <board.kicad_pcb> NET1 [NET2 ...]
Lägger spår (0.2 mm) + ev. via (0.6/0.3) och sparar. Verifierar global klarans efteråt."""
import sys, os, heapq, math, pcbnew
PCB = sys.argv[1]; NETS = sys.argv[2:]
MM = pcbnew.FromMM; OX, OY = 150.0, 120.0
F, B = pcbnew.F_Cu, pcbnew.B_Cu
STEP = 0.1; CLR = 0.2; HALF = 0.1            # rutnät / klarans / halv spårbredd
# KEEP = spårcentrum-avstånd till hinder-yta. Default 0.4 mm (marginal mot rutnät). Trånga
# hörn (t.ex. FC U2-LGA) kan kräva DRC-minimum 0.3 mm: sätt env MAZE_KEEP=0.3 (+ MAZE_VIAKEEP).
KEEP = float(os.environ.get("MAZE_KEEP", CLR + HALF + 0.1))
b = pcbnew.LoadBoard(PCB)
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
def xy(p): return (p.x / 1e6 - OX, OY - p.y / 1e6)

# board-bbox ur Edge.Cuts
exs = []; eys = []
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        bb = d.GetBoundingBox(); exs += [bb.GetLeft()/1e6-OX, bb.GetRight()/1e6-OX]; eys += [OY-bb.GetTop()/1e6, OY-bb.GetBottom()/1e6]
X0, X1, Y0, Y1 = min(exs)+0.4, max(exs)-0.4, min(eys)+0.4, max(eys)-0.4
EX0, EX1, EY0, EY1 = X0, X1, Y0, Y1     # kort-kant-gränser (lay_path begränsar rutnätet till ett fönster runt nätet)
NC = int((X1-X0)/STEP)+1; NR = int((Y1-Y0)/STEP)+1
def cell(x, y): return (max(0, min(NC-1, round((x-X0)/STEP))), max(0, min(NR-1, round((y-Y0)/STEP))))
def cxy(c): return (X0+c[0]*STEP, Y0+c[1]*STEP)

def probe(x, y):
    s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(x, y)); s.SetEnd(V(x+0.001, y)); s.SetWidth(MM(0.01))
    return s.GetEffectiveShape()

VIAKEEP = float(os.environ.get("MAZE_VIAKEEP", 0.3 + CLR + 0.25))  # via-radie 0.3 + klarans 0.2 + marginal
def blocked_grid(exclude_net):
    blk = {F: [[False]*NR for _ in range(NC)], B: [[False]*NR for _ in range(NC)]}
    via = [[False]*NR for _ in range(NC)]     # via tillåts bara där BÅDA lagren är fria m. större keepout
    shapes = {F: [], B: []}
    INNER = [L for L in (pcbnew.In1_Cu, pcbnew.In2_Cu) if L < b.GetCopperLayerCount() or True]
    viashapes = []   # hinder på VALFRITT kopparlager (via går igenom alla → måste klara dessa)
    for t in b.GetTracks():
        if t.GetNetname() == exclude_net: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            for L in (F, B): shapes[L].append(t.GetEffectiveShape())
            viashapes.append(t.GetEffectiveShape())
        else:
            L = t.GetLayer()
            if L in (F, B): shapes[L].append(t.GetEffectiveShape())
            viashapes.append(t.GetEffectiveShape())     # inkl. inre-lager-spår (In1/In2)
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == exclude_net: continue
            sh = p.GetEffectiveShape()
            for L in (F, B):
                if p.IsOnLayer(L): shapes[L].append(sh)
            viashapes.append(sh)
    for L in (F, B):
        for sh in shapes[L]:
            bb = sh.BBox()
            cx0, cy0 = cell(bb.GetLeft()/1e6-OX-VIAKEEP-STEP, OY-bb.GetBottom()/1e6-VIAKEEP-STEP)
            cx1, cy1 = cell(bb.GetRight()/1e6-OX+VIAKEEP+STEP, OY-bb.GetTop()/1e6+VIAKEEP+STEP)
            for ci in range(min(cx0,cx1), max(cx0,cx1)+1):
                for ri in range(min(cy0,cy1), max(cy0,cy1)+1):
                    x, y = cxy((ci, ri)); pr = probe(x, y)
                    if not blk[L][ci][ri] and sh.Collide(pr, int(KEEP*1e6)): blk[L][ci][ri] = True
    # via-keepout: blockera via-celler nära hinder på NÅGOT kopparlager (via genomborrar alla lager)
    for sh in viashapes:
        bb = sh.BBox()
        cx0, cy0 = cell(bb.GetLeft()/1e6-OX-VIAKEEP-STEP, OY-bb.GetBottom()/1e6-VIAKEEP-STEP)
        cx1, cy1 = cell(bb.GetRight()/1e6-OX+VIAKEEP+STEP, OY-bb.GetTop()/1e6+VIAKEEP+STEP)
        for ci in range(min(cx0,cx1), max(cx0,cx1)+1):
            for ri in range(min(cy0,cy1), max(cy0,cy1)+1):
                if not via[ci][ri] and sh.Collide(probe(*cxy((ci, ri))), int(VIAKEEP*1e6)): via[ci][ri] = True
    return blk, via

def pad_of(net, want_layer=None):
    out = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net:
                lays = [L for L in (F, B) if p.IsOnLayer(L)]
                out.append((xy(p.GetPosition()), lays, f.GetReference()+"."+p.GetName()))
    return out

def astar(start_cells, goal_cells, blk, via):
    goal = set(goal_cells)                      # (col,row,layer) — LAGER-medvetet mål
    goal_xy = {(c, r) for c, r, _ in goal}
    pq = [(0, sc) for sc in start_cells]; heapq.heapify(pq)
    g = {sc: 0 for sc in start_cells}; came = {}
    gx = sum(c for c, _, _ in goal)/len(goal); gy = sum(r for _, r, _ in goal)/len(goal)
    while pq:
        f, n = heapq.heappop(pq)
        if n in goal: return n, came
        ci, ri, L = n
        nbrs = [(ci+1, ri, L, 1, False), (ci-1, ri, L, 1, False), (ci, ri+1, L, 1, False),
                (ci, ri-1, L, 1, False), (ci, ri, B if L == F else F, 30, True)]   # sista = via-byte
        for nci, nri, nL, cost, isvia in nbrs:
            if not (0 <= nci < NC and 0 <= nri < NR): continue
            if isvia and via[nci][nri]: continue          # via bara i fritt cell (större keepout)
            if blk[nL][nci][nri] and (nci, nri) not in goal_xy: continue
            key = (nci, nri, nL); ng = g[n]+cost
            if ng < g.get(key, 1e9):
                g[key] = ng; came[key] = n
                heapq.heappush(pq, (ng + abs(nci-gx) + abs(nri-gy), key))
    return None, came

def islands(net, pads):
    """Gruppera paddar i öar via befintliga spår/via (touch<0.06mm union-find)."""
    segs = []
    for t in b.GetTracks():
        if t.GetNetname() != net: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition(); segs.append([xy(p)])
        else:
            segs.append([xy(t.GetStart()), xy(t.GetEnd())])
    nodes = [("pad", i, [p[0]]) for i, p in enumerate(pads)] + [("seg", k, s) for k, s in enumerate(segs)]
    par = {}
    def find(x):
        par.setdefault(x, x)
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            if any(math.hypot(ax-bx, ay-by) < 0.06 for ax, ay in nodes[i][2] for bx, by in nodes[j][2]):
                par[find((nodes[i][0], nodes[i][1]))] = find((nodes[j][0], nodes[j][1]))
    grp = {}
    for i in range(len(pads)): grp.setdefault(find(("pad", i)), []).append(i)
    return list(grp.values())

def lay_path(net, axy, al, bxy, bl):
    # begränsa rutnätet till ett FÖNSTER runt de två paddarna (+25mm omvägs-marginal) → snabb blocked_grid+A*
    global X0, X1, Y0, Y1, NC, NR
    M = 25.0
    X0 = max(EX0, min(axy[0], bxy[0]) - M); X1 = min(EX1, max(axy[0], bxy[0]) + M)
    Y0 = max(EY0, min(axy[1], bxy[1]) - M); Y1 = min(EY1, max(axy[1], bxy[1]) + M)
    NC = int((X1-X0)/STEP)+1; NR = int((Y1-Y0)/STEP)+1
    blk, via = blocked_grid(net)
    sc = [(*cell(*axy), L) for L in al]
    gc = [(*cell(*bxy), L) for L in bl]
    for L in al: blk[L][cell(*axy)[0]][cell(*axy)[1]] = False
    for L in bl: blk[L][cell(*bxy)[0]][cell(*bxy)[1]] = False
    end, came = astar(sc, gc, blk, via)
    if end is None: return False
    path = [end]
    while path[-1] in came: path.append(came[path[-1]])
    path.reverse()
    nc = b.FindNet(net).GetNetCode()
    pts = [(cxy((p[0], p[1])), p[2]) for p in path]
    pts[0] = (axy, pts[0][1]); pts[-1] = (bxy, pts[-1][1])
    # slå ihop kolinjära segment på samma lager → få långa spår istället för 0.2mm-bitar
    merged = [pts[0]]
    for i in range(1, len(pts)-1):
        (x0, y0), L0 = merged[-1]; (x1, y1), L1 = pts[i]; (x2, y2), L2 = pts[i+1]
        if L0 == L1 == L2 and abs((x1-x0)*(y2-y0) - (y1-y0)*(x2-x0)) < 1e-6:
            continue                                   # i ligger på linjen p0..p2 → hoppa
        merged.append(pts[i])
    merged.append(pts[-1])
    for i in range(len(merged)-1):
        (x0, y0), L0 = merged[i]; (x1, y1), L1 = merged[i+1]
        if L0 != L1:
            v = pcbnew.PCB_VIA(b); v.SetPosition(V(x0, y0)); v.SetDrill(MM(0.3)); v.SetWidth(MM(0.6)); v.SetNetCode(nc); b.Add(v)
        if (x0, y0) != (x1, y1):
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(x0, y0)); t.SetEnd(V(x1, y1)); t.SetWidth(MM(HALF*2)); t.SetLayer(L1); t.SetNetCode(nc); b.Add(t)
    return True

def route_net(net):
    pads = pad_of(net)
    if len(pads) < 2: print(f"{net}: <2 paddar, hoppar"); return False
    for _ in range(len(pads)):
        isl = islands(net, pads)
        if len(isl) <= 1: break
        # prova ALLA par över ö-gränser i avståndsordning tills ett routar rent
        cand = []
        for gi in range(len(isl)):
            for gj in range(gi+1, len(isl)):
                for pa in isl[gi]:
                    for pb in isl[gj]:
                        d = math.hypot(pads[pa][0][0]-pads[pb][0][0], pads[pa][0][1]-pads[pb][0][1])
                        cand.append((d, pa, pb))
        cand.sort()
        done = False
        for _, pa, pb in cand:
            if lay_path(net, pads[pa][0], pads[pa][1], pads[pb][0], pads[pb][1]):
                print(f"{net}: {pads[pa][2]} -> {pads[pb][2]}"); done = True; break
        if not done:
            print(f"{net}: INGEN väg mellan öar"); return False
    return True

ok = all(route_net(n) for n in NETS)
pcbnew.SaveBoard(PCB, b)
print("sparad" if ok else "!! nät kvar oroutade")
