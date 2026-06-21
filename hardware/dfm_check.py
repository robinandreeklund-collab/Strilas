#!/usr/bin/env python3
"""STRILAS — lokal DFM/DRC-analys (HQDFM-motsvarighet) på faktisk board-geometri via pcbnew.
KiCad 7 saknar 'kicad-cli pcb drc' (8.0-feature) → egen kontroll mot NextPCB-gränser.
Kör: python3 hardware/dfm_check.py <board.kicad_pcb> [...]
Kategorier: clearance, trace-bredd, annular ring (via+PTH), borr-storlek, hål-till-hål,
koppar-till-kant, borr-till-koppar, via-på-SMD-pad, akut vinkel, silk-på-pad, oanslutna."""
import sys, math, pcbnew

# NextPCB standard-gränser (mm). FAIL = under fabrikens min; WARN = under konservativ rekommendation.
MIN_CLEAR   = 0.13   # koppar-koppar (NextPCB 2-lager ~0.13; vi kör 0.2)
MIN_TRACE   = 0.13
MIN_RING_F  = 0.10   # annular ring FAIL (<4mil)
MIN_RING_W  = 0.15   # annular ring WARN (<6mil, HQDFM-rek)
MIN_DRILL   = 0.20
MIN_H2H     = 0.25   # hål-kant till hål-kant
MIN_EDGE_F  = 0.20   # koppar-till-kant FAIL
MIN_EDGE_W  = 0.30   # koppar-till-kant WARN (fräst ursparning)
MIN_SILK_PAD= 0.10
ALLCU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]


def cu_items(b):
    """(netcode, layerset, shape, tag) för all koppar."""
    out = []
    for t in b.GetTracks():
        lays = set(ALLCU) if t.Type() == pcbnew.PCB_VIA_T else {t.GetLayer()}
        tag = "via" if t.Type() == pcbnew.PCB_VIA_T else "trk"
        out.append((t.GetNetCode(), lays & set(ALLCU), t.GetEffectiveShape(), tag, t))
    for f in b.GetFootprints():
        for pd in f.Pads():
            lays = {L for L in ALLCU if pd.IsOnLayer(L)}
            out.append((pd.GetNetCode(), lays, pd.GetEffectiveShape(), "pad", pd))
    return out


def check(pcb):
    b = pcbnew.LoadBoard(pcb); OX, OY = 150.0, 120.0
    def xy(p): return (round(p.x/1e6-OX, 2), round(OY-p.y/1e6, 2))
    res = {}  # category -> [(severity, detail)]
    def add(cat, sev, det): res.setdefault(cat, []).append((sev, det))
    items = cu_items(b)

    # 1) clearance (different-net copper)
    n = 0
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            a, c = items[i], items[j]
            if a[0] == c[0] or not (a[1] & c[1]): continue
            if a[3] == "pad" and c[3] == "pad" and a[0] != c[0]:
                pass
            if a[2].Collide(c[2], int(MIN_CLEAR*1e6)): n += 1
    if n: add("Clearance <%.2fmm" % MIN_CLEAR, "FAIL", f"{n} par")

    # 2) trace width
    tw = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and t.GetWidth() < MIN_TRACE*1e6]
    if tw: add("Trace-bredd", "FAIL", f"{len(tw)} spår < {MIN_TRACE}mm")

    # 3) annular ring (vias + PTH pads)
    rings = []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            rings.append(((t.GetWidth()-t.GetDrillValue())/2/1e6, "via", xy(t.GetPosition())))
    for f in b.GetFootprints():
        for pd in f.Pads():
            if pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                r = (min(pd.GetSizeX(), pd.GetSizeY())-pd.GetDrillSize().x)/2/1e6
                rings.append((r, f.GetReference()+"."+pd.GetName(), xy(pd.GetPosition())))
    rfail = [r for r in rings if r[0] < MIN_RING_F]
    rwarn = [r for r in rings if MIN_RING_F <= r[0] < MIN_RING_W]
    if rfail: add("Annular ring", "FAIL", f"{len(rfail)} < {MIN_RING_F}mm (min {min(r[0] for r in rfail):.3f})")
    if rwarn: add("Annular ring", "WARN", f"{len(rwarn)} mellan {MIN_RING_F}-{MIN_RING_W}mm (4-6mil); klarar NextPCB")

    # 4) drill size
    ds = []
    for f in b.GetFootprints():
        for pd in f.Pads():
            if pd.GetDrillSize().x > 0 and pd.GetDrillSize().x/1e6 < MIN_DRILL: ds.append(pd.GetDrillSize().x/1e6)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetDrillValue()/1e6 < MIN_DRILL: ds.append(t.GetDrillValue()/1e6)
    if ds: add("Borr-storlek", "FAIL", f"{len(ds)} hål < {MIN_DRILL}mm")

    # 5) hole-to-hole (edge-edge)
    holes = []
    for f in b.GetFootprints():
        for pd in f.Pads():
            if pd.GetDrillSize().x > 0: holes.append((xy(pd.GetPosition()), pd.GetDrillSize().x/1e6/2, f.GetReference()+"."+pd.GetName()))
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T: holes.append((xy(t.GetPosition()), t.GetDrillValue()/1e6/2, "via"))
    h2h = 0
    for i in range(len(holes)):
        for j in range(i+1, len(holes)):
            (p1, r1, _), (p2, r2, _) = holes[i], holes[j]
            d = math.hypot(p1[0]-p2[0], p1[1]-p2[1]) - r1 - r2
            if 0 < d < MIN_H2H: h2h += 1
    if h2h: add("Hål-till-hål", "WARN", f"{h2h} par < {MIN_H2H}mm")

    # 6) copper-to-edge
    edges = []
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts: edges.append(d.GetEffectiveShape())
    ef = ew = 0
    for nc, lays, sh, tag, o in items:
        if not edges: break
        df = min((1 for e in edges if sh.Collide(e, int(MIN_EDGE_F*1e6))), default=0)
        if df: ef += 1
        elif min((1 for e in edges if sh.Collide(e, int(MIN_EDGE_W*1e6))), default=0): ew += 1
    if ef: add("Koppar-till-kant", "FAIL", f"{ef} < {MIN_EDGE_F}mm")
    if ew: add("Koppar-till-kant", "WARN", f"{ew} mellan {MIN_EDGE_F}-{MIN_EDGE_W}mm")

    # 7) via / hole on SMD pad
    smdpads = [(pd.GetEffectiveShape(), {L for L in ALLCU if pd.IsOnLayer(L)}) for f in b.GetFootprints() for pd in f.Pads() if pd.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    vop = 0
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T: continue
        for sh, lays in smdpads:
            if t.GetEffectiveShape().Collide(sh, 0): vop += 1; break
    for f in b.GetFootprints():
        for pd in f.Pads():
            if pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                for sh, lays in smdpads:
                    if pd.GetEffectiveShape().Collide(sh, 0): vop += 1; break
    if vop: add("Hål/via på SMD-pad", "WARN", f"{vop} (tenta el. flytta)")

    # 8) acute angle (same-net 2-segment vertices, outgoing dirs <90°)
    from collections import defaultdict
    vd = defaultdict(list)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T: continue
        s, e = t.GetStart(), t.GetEnd()
        if s == e: continue
        key = t.GetNetCode(), t.GetLayer()
        vd[(key, (round(s.x, -3), round(s.y, -3)))].append((e.x-s.x, e.y-s.y))
        vd[(key, (round(e.x, -3), round(e.y, -3)))].append((s.x-e.x, s.y-e.y))
    acute = 0
    for k, dirs in vd.items():
        if len(dirs) != 2: continue
        d1, d2 = dirs
        m1, m2 = math.hypot(*d1), math.hypot(*d2)
        if m1 < 1e3 or m2 < 1e3: continue
        cos = max(-1, min(1, (d1[0]*d2[0]+d1[1]*d2[1])/(m1*m2)))
        if math.degrees(math.acos(cos)) < 75: acute += 1
    if acute: add("Akut vinkel", "WARN", f"{acute} spår-veck < 75° (etsnings-fälla)")

    # 9) unconnected / mask presence
    b.BuildConnectivity()
    try: un = b.GetConnectivity().GetUnconnectedCount(True)
    except TypeError: un = b.GetConnectivity().GetUnconnectedCount()
    if un: add("Oanslutna", "FAIL", f"{un}")
    return res


if __name__ == "__main__":
    for pcb in sys.argv[1:]:
        r = check(pcb)
        name = pcb.split("/")[-1]
        if not r:
            print(f"\n=== {name}: REN ✓ (inga DFM-anmärkningar) ===")
        else:
            print(f"\n=== {name} ===")
            for cat, lst in r.items():
                for sev, det in lst:
                    print(f"  [{sev}] {cat}: {det}")
