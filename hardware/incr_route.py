#!/usr/bin/env python3
"""STRILAS — DETERMINISTISK inkrementell routning: bevarar ALL befintlig koppar och drar BARA
de nya anslutningarna (som finish_helmet_pullups.py, men generiskt). Ingen freerouting-roulette.

API (importeras av per-kort-skript):
  R = Router(board, plane_nets={"GND": [In1,F,B], "+3V3":[In2], ...})
  R.to_plane(ref, pad)                  # via fran pad -> plan (zon-fyll kopplar)
  R.trace(ref, pad, net)                # dra spar fran pad till narmaste befintliga koppar pa net
  R.trace_between(ref1,pad1, ref2,pad2) # dra spar mellan tva specifika paddar (samma net)
  R.finish()                            # fyll om zoner + returnera (clearance, unconnected)
Klarar korta/medellanga anslutningar: provar direkt-segment pa F/B, sen L-form, sen via-hopp.
Clearance kollas (0.2mm) mot all annan-net-koppar; valjer forsta rena vag."""
import math, pcbnew

OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
F, B = pcbnew.F_Cu, pcbnew.B_Cu
TW = MM(0.25)        # spar-bredd signal
VIA_D, VIA_DR = MM(0.6), MM(0.3)


def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
def xy(p): return (p.x / 1e6 - OX, OY - p.y / 1e6)


class Router:
    def __init__(self, board, plane_nets):
        self.b = board
        self.plane = plane_nets               # netname -> [layers]
        self.cu = [F, pcbnew.In1_Cu, pcbnew.In2_Cu, B]
        self.fps = {f.GetReference(): f for f in board.GetFootprints()}

    def _net(self, nm):
        ni = self.b.FindNet(nm)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(self.b, nm); self.b.Add(ni)
        return ni

    def _pad(self, ref, pad):
        for p in self.fps[ref].Pads():
            if p.GetName() == pad:
                return p
        raise KeyError(f"{ref}.{pad}")

    def _obstacles(self, net):
        """alla koppar-shapes (track/pad/via) som INTE tillhor net -> (layerset, shape)."""
        obs = []
        for t in self.b.GetTracks():
            if t.GetNetname() == net:
                continue
            lays = set(self.cu) if t.Type() == pcbnew.PCB_VIA_T else {t.GetLayer()}
            obs.append((lays, t.GetEffectiveShape()))
        for f in self.b.GetFootprints():
            for pd in f.Pads():
                if pd.GetNetname() == net:
                    continue
                lays = {L for L in self.cu if pd.IsOnLayer(L)}
                obs.append((lays, pd.GetEffectiveShape()))
        return obs

    def _seg_clear(self, a, b, layer, obs, clr=MM(0.2)):
        s = pcbnew.SHAPE_SEGMENT(V(*a), V(*b), TW)
        for lays, shp in obs:
            if layer in lays and s.Collide(shp, clr):
                return False
        return True

    def _add_track(self, a, b, layer, net, width=TW):
        t = pcbnew.PCB_TRACK(self.b); t.SetStart(V(*a)); t.SetEnd(V(*b))
        t.SetWidth(width); t.SetLayer(layer); t.SetNet(net); self.b.Add(t)

    def _add_via(self, p, net):
        v = pcbnew.PCB_VIA(self.b); v.SetPosition(V(*p))
        v.SetDrill(VIA_DR); v.SetWidth(VIA_D); v.SetNet(net)
        v.SetLayerPair(F, B); self.b.Add(v)

    def _via_clear(self, p, obs, clr=MM(0.2)):
        c = pcbnew.SHAPE_SEGMENT(V(*p), V(*p), VIA_D)   # noll-langd tjockt segment = cirkel Ø VIA_D
        for lays, shp in obs:
            if c.Collide(shp, clr):
                return False
        return True

    def to_fill(self, ref, pad):
        """net har redan zon-fyll pa paddens lager (t.ex. GND pa F.Cu) -> inget behovs;
        zon-omfyllningen kopplar padden. (No-op; verifieras i finish.)"""
        return True

    def to_plane(self, ref, pad):
        """koppla pad till plan-net pa ANNAT lager via en clearance-kollad via (+ ev kort F-stub)."""
        pd = self._pad(ref, pad); net = pd.GetNet(); nm = net.GetNetname()
        p = xy(pd.GetPosition()); obs = self._obstacles(nm)
        offs = [(0, 0)] + [(dx, dy) for r in (1.0, 1.4, 1.8, 2.2, 2.6, 3.0)
                           for dx, dy in [(r, 0), (-r, 0), (0, r), (0, -r), (r, r), (-r, -r), (r, -r), (-r, r)]]
        for dx, dy in offs:
            vp = (p[0] + dx, p[1] + dy)
            if not self._via_clear(vp, obs):
                continue
            if (dx or dy) and not self._seg_clear(p, vp, F, obs):
                continue
            if dx or dy:
                self._add_track(p, vp, F, net)
            self._add_via(vp, net)
            return True
        return False

    def _main_cluster(self, net):
        """returnera koppar-ITEMS i NÄTETS STÖRSTA sammanhängande ö (Collide(0) union-find).
        Undviker att dra spår till isolerade stubbar (=> oansluten ö)."""
        cu = self.cu
        it = []
        for t in self.b.GetTracks():
            if t.GetNetname() != net:
                continue
            lays = set(cu) if t.Type() == pcbnew.PCB_VIA_T else {t.GetLayer()}
            it.append((lays, t.GetEffectiveShape(), t))
        for f in self.b.GetFootprints():
            for pd in f.Pads():
                if pd.GetNetname() == net:
                    it.append(({L for L in cu if pd.IsOnLayer(L)}, pd.GetEffectiveShape(), pd))
        for z in self.b.Zones():
            if z.GetNetname() == net:
                for L in cu:
                    if z.IsOnLayer(L):
                        it.append(({L}, z.GetFilledPolysList(L), z))
        n = len(it); par = list(range(n))
        def find(x):
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        for i in range(n):
            for j in range(i + 1, n):
                if (it[i][0] & it[j][0]) and it[i][1].Collide(it[j][1], 0):
                    par[find(i)] = find(j)
        groups = {}
        for i in range(n):
            groups.setdefault(find(i), []).append(i)
        if not groups:
            return set()
        main = max(groups.values(), key=len)
        return {id(it[i][2]) for i in main}

    def _net_points(self, net):
        """koppar-punkter (pad-center + track-andar) pa net STÖRSTA ö, med lager."""
        main = self._main_cluster(net)
        pts = []
        for t in self.b.GetTracks():
            if t.GetNetname() != net or t.Type() == pcbnew.PCB_VIA_T or id(t) not in main:
                continue
            pts.append((xy(t.GetStart()), t.GetLayer()))
            pts.append((xy(t.GetEnd()), t.GetLayer()))
        for f in self.b.GetFootprints():
            for pd in f.Pads():
                if pd.GetNetname() == net and id(pd) in main:
                    pts.append((xy(pd.GetPosition()), F if pd.IsOnLayer(F) else B))
        if not pts:   # fallback: alla punkter om ingen huvud-ö hittas
            for f in self.b.GetFootprints():
                for pd in f.Pads():
                    if pd.GetNetname() == net:
                        pts.append((xy(pd.GetPosition()), F if pd.IsOnLayer(F) else B))
        return pts

    def trace_between(self, ref1, pad1, ref2, pad2):
        p1 = xy(self._pad(ref1, pad1).GetPosition())
        p2 = xy(self._pad(ref2, pad2).GetPosition())
        net = self._pad(ref1, pad1).GetNet()
        return self._route(p1, p2, net, net.GetNetname())

    def trace(self, ref, pad, exclude_self=True):
        pd = self._pad(ref, pad); net = pd.GetNet(); nm = net.GetNetname()
        p1 = xy(pd.GetPosition())
        cands = self._net_points(nm)
        # exkludera punkter pa samma footprint-pad (oss sjalva)
        cands = [(p, L) for (p, L) in cands if math.hypot(p[0]-p1[0], p[1]-p1[1]) > 0.3]
        cands.sort(key=lambda c: math.hypot(c[0][0]-p1[0], c[0][1]-p1[1]))
        for (p2, L) in cands[:12]:
            if self._route(p1, p2, net, nm):
                return True
        return False

    def maze_route(self, ref1, pad1, ref2, pad2, step=0.6, clr=MM(0.25), width=TW):
        """rutnatsbaserad maze-router (BFS, 2 lager F/B + via) for SVÅRA langa nat dar
        direkt/L/Z misslyckas. Undviker annan-net-koppar (track/pad/via; zoner ignoreras,
        de fylls om runt det nya spåret). Lagger spår + vior langs hittad vag."""
        import heapq
        pdA = self._pad(ref1, pad1); pdB = self._pad(ref2, pad2)
        net = pdA.GetNet(); nm = net.GetNetname()
        pa = xy(pdA.GetPosition()); pb = xy(pdB.GetPosition())
        obs = self._obstacles(nm)
        # board-grans ur Edge.Cuts
        xs = [pa[0], pb[0]]; ys = [pa[1], pb[1]]
        for d in self.b.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts:
                bb = d.GetBoundingBox()
                xs += [bb.GetX()/1e6-OX, bb.GetRight()/1e6-OX]; ys += [OY-bb.GetBottom()/1e6, OY-bb.GetTop()/1e6]
        x0, x1 = min(xs)-2, max(xs)+2; y0, y1 = min(ys)-2, max(ys)+2
        nx = int((x1-x0)/step)+1; ny = int((y1-y0)/step)+1
        def cell(p): return (int(round((p[0]-x0)/step)), int(round((p[1]-y0)/step)))
        def pt(gx, gy): return (x0+gx*step, y0+gy*step)
        # blockerad[lager][gy*nx+gx]
        F_, B_ = 0, 1
        blk = {F_: bytearray(nx*ny), B_: bytearray(nx*ny)}
        bvia = bytearray(nx*ny)     # cell dar en VIA klipper annan-net-koppar (inner-lager In1/In2)
        lay = {F_: F, B_: B}
        inner = {pcbnew.In1_Cu, pcbnew.In2_Cu}
        margin = int(clr) + int(MM(0.35))   # extra marginal -> spåret hålls undan obstaklen
        for lays, shp in obs:
            bb = shp.BBox(); bx0 = bb.GetX()/1e6-OX; bx1 = bb.GetRight()/1e6-OX
            by0 = OY-bb.GetBottom()/1e6; by1 = OY-bb.GetTop()/1e6
            Ls = [L for L in (F_, B_) if lay[L] in lays]
            via_blk = bool(lays & inner)        # inner-koppar -> en via dit klipper
            if not Ls and not via_blk: continue
            gx0, gy0 = cell((bx0, by0)); gx1, gy1 = cell((bx1, by1))
            for ax in range(max(0,min(gx0,gx1)-2), min(nx,max(gx0,gx1)+3)):
                for ay in range(max(0,min(gy0,gy1)-2), min(ny,max(gy0,gy1)+3)):
                    cx, cy = pt(ax, ay)
                    seg = pcbnew.SHAPE_SEGMENT(V(cx, cy), V(cx, cy), width)
                    if shp.Collide(seg, margin):
                        for L in Ls: blk[L][ay*nx+ax] = 1
                        if via_blk: bvia[ay*nx+ax] = 1
        sa = cell(pa); sb = cell(pb)
        for L in (F_, B_):  # frigor start/mal-cellerna (egna paddar)
            blk[L][sa[1]*nx+sa[0]] = 0; blk[L][sb[1]*nx+sb[0]] = 0
        bvia[sa[1]*nx+sa[0]] = 0; bvia[sb[1]*nx+sb[0]] = 0
        # BFS (A*) over (gx,gy,layer)
        start = (sa[0], sa[1], F_ if pdA.IsOnLayer(F) else B_)
        goalL = F_ if pdB.IsOnLayer(F) else B_
        goal = (sb[0], sb[1], goalL)
        def h(n): return (abs(n[0]-sb[0])+abs(n[1]-sb[1]))*step
        pq = [(0, start)]; came = {start: None}; cost = {start: 0}
        found = None
        while pq:
            _, cur = heapq.heappop(pq)
            if (cur[0], cur[1]) == (sb[0], sb[1]):
                found = cur; break
            cx, cy, cl = cur
            def freec(gx, gy, gl):
                return 0 <= gx < nx and 0 <= gy < ny and (not blk[gl][gy*nx+gx] or (gx,gy)==(sb[0],sb[1]))
            # 8-riktning (diagonaler => rakare/renare spår) + via
            steps = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
            nbrs = [(cx+dx, cy+dy, cl, dx, dy) for dx,dy in steps] + [(cx,cy,1-cl,0,0)]
            for gx, gy, gl, dx, dy in nbrs:
                if not (0<=gx<nx and 0<=gy<ny): continue
                if blk[gl][gy*nx+gx] and (gx,gy)!=(sb[0],sb[1]): continue
                if gl != cl and bvia[gy*nx+gx]: continue   # via far ej klippa inner-koppar
                if dx and dy and not (freec(cx+dx,cy,cl) and freec(cx,cy+dy,cl)):
                    continue   # diagonal: hörn-klipp ej tillatet (bada ortogonala grannar fria)
                diag = 1.414 if (dx and dy) else 1.0
                nb = (gx, gy, gl)
                c2 = cost[cur] + (step*diag if gl==cl else step*3)  # via-straff
                if nb not in cost or c2 < cost[nb]:
                    cost[nb] = c2; came[nb] = cur; heapq.heappush(pq, (c2+h(nb), nb))
        if not found:
            return False
        path = []
        n = found
        while n is not None: path.append(n); n = came[n]
        path.reverse()
        # SLÅ IHOP kollineära steg -> långa rena segment (ej trappsteg)
        simp = [path[0]]
        for i in range(1, len(path)-1):
            a, b_, c = path[i-1], path[i], path[i+1]
            if a[2] == b_[2] == c[2]:
                d1 = (b_[0]-a[0], b_[1]-a[1]); d2 = (c[0]-b_[0], c[1]-b_[1])
                if d1[0]*d2[1]-d1[1]*d2[0] == 0 and (d1[0]*d2[0]+d1[1]*d2[1]) > 0:
                    continue   # samma riktning -> hoppa mellanpunkten
            simp.append(b_)
        simp.append(path[-1])
        prev = None
        for nde in simp:
            p = pt(nde[0], nde[1])
            if prev is not None:
                if prev[2] != nde[2]:
                    self._add_via(p, net)
                else:
                    self._add_track(pt(prev[0], prev[1]), p, lay[nde[2]], net, width)
            prev = nde
        self._add_track(pa, pt(*sa), lay[start[2]], net, width)
        self._add_track(pb, pt(*sb), lay[goalL], net, width)
        return True

    def trace_point(self, ref, pad, pt):
        """dra spar fran pad till en GODTYCKLIG punkt (x,y) pa samma nat (t.ex. en gammal
        track-andpunkt). Anvands for att aterskapa en matnings-junction vid en ny FET-source."""
        pd = self._pad(ref, pad); net = pd.GetNet()
        return self._route(xy(pd.GetPosition()), tuple(pt), net, net.GetNetname())

    def _route(self, p1, p2, net, nm):
        obs = self._obstacles(nm)
        bvia = self._via_clear(p1, obs) and self._via_clear(p2, obs)
        # 1) direkt pa F el B
        for layer in (F, B):
            if layer == B and not bvia:
                continue
            if self._seg_clear(p1, p2, layer, obs):
                if layer == B:
                    self._add_via(p1, net); self._add_via(p2, net)
                self._add_track(p1, p2, layer, net); return True
        # 2) L-form (2 segment) pa F el B
        for layer in (F, B):
            if layer == B and not bvia:
                continue
            for corner in ((p2[0], p1[1]), (p1[0], p2[1])):
                if self._seg_clear(p1, corner, layer, obs) and self._seg_clear(corner, p2, layer, obs):
                    if layer == B:
                        self._add_via(p1, net); self._add_via(p2, net)
                    self._add_track(p1, corner, layer, net); self._add_track(corner, p2, layer, net)
                    return True
        # 3) Z-form (3 segment) pa F: mittpunkt-offset i bada riktningar
        mids = []
        for frac in (0.5,):
            mx = p1[0] + (p2[0]-p1[0])*frac; my = p1[1] + (p2[1]-p1[1])*frac
            for off in (1.5, -1.5, 2.5, -2.5, 3.5, -3.5):
                mids += [((mx+off, p1[1]), (mx+off, p2[1])), ((p1[0], my+off), (p2[0], my+off))]
        for c1, c2 in mids:
            if (self._seg_clear(p1, c1, F, obs) and self._seg_clear(c1, c2, F, obs)
                    and self._seg_clear(c2, p2, F, obs)):
                self._add_track(p1, c1, F, net); self._add_track(c1, c2, F, net); self._add_track(c2, p2, F, net)
                return True
        return False

    def _islands(self, net):
        """returnera lista av öar (var = lista av item-index) for net via Collide(0)-union-find."""
        cu = self.cu
        it = []
        for t in self.b.GetTracks():
            if t.GetNetname() != net:
                continue
            lays = set(cu) if t.Type() == pcbnew.PCB_VIA_T else {t.GetLayer()}
            it.append((lays, t.GetEffectiveShape(), ("trk", t)))
        for f in self.b.GetFootprints():
            for pd in f.Pads():
                if pd.GetNetname() == net:
                    it.append(({L for L in cu if pd.IsOnLayer(L)}, pd.GetEffectiveShape(), ("pad", f.GetReference() + "." + pd.GetName(), pd)))
        for z in self.b.Zones():
            if z.GetNetname() == net:
                for L in cu:
                    if z.IsOnLayer(L):
                        it.append(({L}, z.GetFilledPolysList(L), ("zone", L)))
        n = len(it); par = list(range(n))
        def find(x):
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        for i in range(n):
            for j in range(i + 1, n):
                if (it[i][0] & it[j][0]) and it[i][1].Collide(it[j][1], 0):
                    par[find(i)] = find(j)
        groups = {}
        for i in range(n):
            groups.setdefault(find(i), []).append(i)
        return it, list(groups.values())

    def connect_islands(self, net):
        """slå ihop ALLA öar i net till EN sammanhängande ö (garanterar full anslutning efter
        en kraftvägs-splits). Routar mellan närmaste punkter på olika öar tills 1 ö kvarstår."""
        for _ in range(12):
            it, groups = self._islands(net)
            # bara öar som innehåller minst en pad räknas (rena track-stubbar utan pad ignoreras)
            real = [g for g in groups if any(it[i][2][0] == "pad" for i in g)]
            if len(real) <= 1:
                return True
            # punkter per ö (pad-center + track-andar)
            def pts(g):
                out = []
                for i in g:
                    k = it[i][2]
                    if k[0] == "pad":
                        out.append((xy(k[2].GetPosition()), F if k[2].IsOnLayer(F) else B))
                    elif k[0] == "trk" and k[1].Type() != pcbnew.PCB_VIA_T:
                        out.append((xy(k[1].GetStart()), k[1].GetLayer()))
                        out.append((xy(k[1].GetEnd()), k[1].GetLayer()))
                return out
            # koppla ö[0] till närmaste andra ö
            base = real[0]; bpts = pts(base)
            best = None
            for g in real[1:]:
                for (q, lq) in pts(g):
                    for (p, lp) in bpts:
                        d = (p[0]-q[0])**2 + (p[1]-q[1])**2
                        if best is None or d < best[0]:
                            best = (d, p, q)
            if not best or not self._route(best[1], best[2], self._net_obj(net), net):
                return False
        return False

    def _net_obj(self, nm):
        return self._net(nm)

    def finish(self):
        pcbnew.ZONE_FILLER(self.b).Fill(self.b.Zones())
        # DRC
        items = []
        for t in self.b.GetTracks():
            lays = set(self.cu) if t.Type() == pcbnew.PCB_VIA_T else {t.GetLayer()}
            items.append((t.GetNetCode(), lays, t.GetEffectiveShape()))
        for z in self.b.Zones():
            for L in self.cu:
                if z.IsOnLayer(L):
                    items.append((z.GetNetCode(), {L}, z.GetFilledPolysList(L)))
        for f in self.b.GetFootprints():
            for pd in f.Pads():
                items.append((pd.GetNetCode(), {L for L in self.cu if pd.IsOnLayer(L)}, pd.GetEffectiveShape()))
        clr = sum(1 for i in range(len(items)) for j in range(i+1, len(items))
                  if items[i][0] != items[j][0] and (items[i][1] & items[j][1]) and items[i][2].Collide(items[j][2], int(0.2e6)))
        self.b.BuildConnectivity()
        try: un = self.b.GetConnectivity().GetUnconnectedCount(True)
        except TypeError: un = self.b.GetConnectivity().GetUnconnectedCount()
        return clr, un
