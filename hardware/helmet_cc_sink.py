#!/usr/bin/env python3
"""STRILAS — konvertera hjälm-mb:s konstellations-driver till FIRMWARE-TRIMBAR CC-sänka,
INKREMENTELLT (bevarar all 886-spårs routning — freerouting hänger på detta kort). Lägger
op-amp (U9) + sense (R14) + 3A-override (R15) + tak-delare (R16/R17) + RC (C23) i ett KOMPAKT
kluster intill Q1 (clear-pocket-scannat → korta länkar, ren trace_between), flyttar R4(gate)
dit, ändrar R4/R5-R7-värden, ompekar Q1.S→sense + R4.1→op-amp-OUT, och routar BARA klustret.
R5-R7 behåller 2512-footprint → ring-routningen rörs ej. Mönster = helmet_protection.py (2-fas).
  python3 hardware/helmet_cc_sink.py         # fas 1 (delar + nät + stub-borttagning + R4-flytt)
  python3 hardware/helmet_cc_sink.py route   # fas 2 (route klustret + verifiera + spara)
"""
import sys, math, pcbnew
sys.path.insert(0, "hardware")
from incr_route import Router

PCB = "hardware/helmet-mb.kicad_pcb"; NET = "hardware/helmet-mb.net"
FPDIR = "/usr/share/kicad/footprints"; OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))
ALL_CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]

NEW = {   # kompakt kluster, clear av F_Cu-koppar (scannat) — korta länkar (≤4,2 mm)
    "U9":  ("Package_TO_SOT_SMD", "SOT-23-5", -6.0, 23.5, 0),
    "R14": ("Resistor_SMD", "R_1206_3216Metric", -2.69, 24.21, 90),
    "R15": ("Resistor_SMD", "R_0805_2012Metric", -0.5, 25.12, 90),
    "R16": ("Resistor_SMD", "R_0805_2012Metric", -10.5, 20.2, 90),   # pin1 (LED_EN) på In1-spårets clear-punkt → direkt via
    "R17": ("Resistor_SMD", "R_0805_2012Metric", -13.15, 20.85, 0),
    "C23": ("Capacitor_SMD", "C_0805_2012Metric", -12.8, 23.0, 0),
}
R4MOVE = (-5.19, 20.85, 0)   # flytta gate-R R4 in i klustret (gamla läget 5,20 → gate-spåret över center)
NEWVAL = {"U9": "OPA171", "R14": "0R2", "R15": "0R1 DNP=1A/montera=3A", "R16": "15k", "R17": "1k", "C23": "100nF"}
VALUE_CHANGE = {"R4": "100R", "R5": "1R", "R6": "1R", "R7": "1R"}

# KIRURGISK nät-tilldelning (BARA paddar vars konnektivitet ändras — rör EJ codec/P4/ljud-nät).
# Gaten (Q1.1+R4.2) BEHÅLLER befintligt board-nät. IDRV_GATE = op-amp OUT → R4.1.
ASSIGN = {
    ("Q1", "2"): "IDRV_SENSE", ("R14", "1"): "IDRV_SENSE", ("R15", "2"): "IDRV_SENSE", ("U9", "4"): "IDRV_SENSE",
    ("U9", "3"): "IDRV_REF",   ("R16", "2"): "IDRV_REF",   ("R17", "1"): "IDRV_REF",   ("C23", "1"): "IDRV_REF",
    ("R4", "1"): "IDRV_GATE",  ("U9", "1"): "IDRV_GATE",
    ("U9", "2"): "GND", ("R14", "2"): "GND", ("R15", "1"): "GND", ("R17", "2"): "GND", ("C23", "2"): "GND",
    ("U9", "5"): "VBAT", ("R16", "1"): "LED_EN",
}


def main():
    b = pcbnew.LoadBoard(PCB)
    have = {f.GetReference() for f in b.GetFootprints()}
    for ref, (lib, fp, x, y, rot) in NEW.items():
        if ref in have:
            print(f"  {ref} finns redan"); continue
        f = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", fp)
        f.SetReference(ref); f.SetValue(NEWVAL.get(ref, "")); f.SetPosition(V(x, y))
        if rot: f.SetOrientationDegrees(rot)
        b.Add(f); print(f"  + {ref} ({NEWVAL.get(ref,'')}) @({x},{y})")
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    for ref, val in VALUE_CHANGE.items():
        fps[ref].SetValue(val)
    pad_of = {(f.GetReference(), pd.GetName()): pd for f in b.GetFootprints() for pd in f.Pads()}
    # pad-overlap-koll
    for nr in NEW:
        npads = [pad_of[k] for k in pad_of if k[0] == nr]
        for of in b.GetFootprints():
            if of.GetReference() in (nr,) or of.GetReference() not in {k[0] for k in pad_of}: continue
            opads = [pad_of[k] for k in pad_of if k[0] == of.GetReference()]
            if any(p1.GetEffectiveShape().Collide(p2.GetEffectiveShape(), int(0.15e6)) for p1 in npads for p2 in opads):
                print(f"  !! PAD-OVERLAP {nr} <-> {of.GetReference()}")
    def gn(nm):
        ni = b.FindNet(nm)
        if ni is None: ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni)
        return ni
    changed = []
    for (ref, pin), newnet in ASSIGN.items():
        pd = pad_of[(ref, pin)]; old = pd.GetNetname()
        if old != newnet:
            changed.append((ref, pin, old, newnet)); pd.SetNet(gn(newnet))
    print(f"  re-synkade {len(changed)} pad-nät kirurgiskt")
    # riv gamla stubbar vid ändrade paddar (R4.1 LED_EN, Q1.2 GND) + R4.2 gate-spår (R4 flyttas)
    rem = 0
    def rip(pad, oldnet):
        nonlocal rem
        sh = pad.GetEffectiveShape(); pl = {L for L in ALL_CU if pad.IsOnLayer(L)}
        for t in list(b.GetTracks()):
            tl = set(ALL_CU) if t.Type() == pcbnew.PCB_VIA_T else {t.GetLayer()}
            if (pl & tl) and t.GetNetname() == oldnet and t.GetEffectiveShape().Collide(sh, int(0.2e6)):
                b.Remove(t); rem += 1
    for ref, pin, old, newnet in changed:
        if old: rip(pad_of[(ref, pin)], old)
    r4p2 = pad_of[("R4", "2")]; rip(r4p2, r4p2.GetNetname())
    fps["R4"].SetPosition(V(*R4MOVE[:2])); fps["R4"].SetOrientationDegrees(R4MOVE[2])
    print(f"  rev {rem} gamla stubbar; flyttade R4 → {R4MOVE[:2]}")
    pcbnew.SaveBoard(PCB, b)
    print("  fas 1 klar — kör 'route'")


def led_en_via(R, b):
    """R16.1 (F_Cu) → närmaste LED_EN-koppar på INNER-lager (In1/In2): ren F-stub + GENOMGÅENDE via
    (träffar inner-spåret; zon-omfyllning ger plan-clearance runt vian)."""
    led = R._net("LED_EN")
    r16 = None
    for pd in R.fps["R16"].Pads():
        if pd.GetName() == "1": p = pd.GetPosition(); r16 = (p.x/1e6-OX, OY-p.y/1e6)
    inner = {pcbnew.In1_Cu, pcbnew.In2_Cu}; cand = []
    for t in b.GetTracks():
        if t.GetNetname() != "LED_EN" or t.Type() == pcbnew.PCB_VIA_T or t.GetLayer() not in inner: continue
        s = (t.GetStart().x/1e6-OX, OY-t.GetStart().y/1e6); e = (t.GetEnd().x/1e6-OX, OY-t.GetEnd().y/1e6)
        for f in [i/10.0 for i in range(0, 11)]:        # sampla LÄNGS spåret (var pkt = möjlig via)
            cand.append((s[0]+(e[0]-s[0])*f, s[1]+(e[1]-s[1])*f))
    cand.sort(key=lambda q: math.hypot(q[0]-r16[0], q[1]-r16[1]))
    obs = R._obstacles("LED_EN")
    for tgt in cand:
        if math.hypot(tgt[0]-r16[0], tgt[1]-r16[1]) < 0.4: continue
        if not R._via_clear(tgt, obs): continue
        segs = None
        if R._seg_clear(r16, tgt, pcbnew.F_Cu, obs):
            segs = [(r16, tgt)]
        else:
            for cor in ((tgt[0], r16[1]), (r16[0], tgt[1])):
                if R._seg_clear(r16, cor, pcbnew.F_Cu, obs) and R._seg_clear(cor, tgt, pcbnew.F_Cu, obs):
                    segs = [(r16, cor), (cor, tgt)]; break
        if not segs: continue
        for a, c in segs: R._add_track(a, c, pcbnew.F_Cu, led)
        v = pcbnew.PCB_VIA(b); v.SetPosition(V(*tgt)); v.SetDrill(MM(0.3)); v.SetWidth(MM(0.6))
        v.SetNet(led); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
        return f"via@{tuple(round(x,1) for x in tgt)}"
    return "ingen reachable via-punkt"


def route_phase():
    b = pcbnew.LoadBoard(PCB)
    R = Router(b, {"GND": [pcbnew.In1_Cu, pcbnew.B_Cu, pcbnew.F_Cu], "+3V3": [pcbnew.In2_Cu]})
    res = {}
    def padxy(ref, pin):
        for pd in R.fps[ref].Pads():
            if pd.GetName() == pin: p = pd.GetPosition(); return (p.x/1e6-OX, OY-p.y/1e6)
    def same_island(net, A, B):
        it, groups = R._islands(net)
        ga = gb = None
        for gi, g in enumerate(groups):
            for i in g:
                if it[i][2][0] == "pad":
                    if it[i][2][1] == A: ga = gi
                    if it[i][2][1] == B: gb = gi
        return ga is not None and ga == gb
    def link(name, r1, p1, targets):
        """anslut r1.p1 till NÅGON av targets (samma nät) — REN trace_between, verifierad."""
        for r2, p2 in targets:
            if (r2, p2) == (r1, p1): continue            # ej till sig själv
            if R.trace_between(r1, p1, r2, p2) and same_island(R._pad(r1, p1).GetNetname(), f"{r1}.{p1}", f"{r2}.{p2}"):
                res[name] = f"→{r2}.{p2}"; return True
        res[name] = "FAIL"; return False
    # ORDNING: trånga plan/inner-anslutningar (U9.2 GND-via, LED_EN-via) FÖRST — annars boxar
    # signal-spåren in dem. GND-paddar → plan-via; om blockerad → närliggande GND-pad.
    for ref, pad in [("U9", "2"), ("C23", "2"), ("R14", "2"), ("R15", "1"), ("R17", "2")]:
        if R.to_plane(ref, pad):
            res[f"{ref}.{pad}→GND"] = "plan"
        else:
            link(f"{ref}.{pad}→GND", ref, pad, [("C23", "2"), ("R17", "2"), ("R14", "2"), ("R15", "1")])
    # LED_EN: R16.1 → befintlig LED_EN-koppar på In1 via F-stub + GENOMGÅENDE via (träffar inner-lagret)
    res["LED_EN→In1"] = led_en_via(R, b)
    # kluster-signal-länkar — flera mål-alternativ per nät (trace_between, verifierad ansl.)
    link("Q1.S→sense", "Q1", "2", [("R14", "1"), ("U9", "4"), ("R15", "2")])
    link("R14→U9.IN-", "R14", "1", [("U9", "4"), ("R15", "2")])
    link("R15→sense", "R15", "2", [("R14", "1"), ("U9", "4")])
    link("U9.IN+→ref", "U9", "3", [("R16", "2"), ("C23", "1"), ("R17", "1")])
    link("R16→ref", "R16", "2", [("R17", "1"), ("C23", "1")])
    link("R17→C23", "R17", "1", [("C23", "1"), ("R16", "2")])
    link("U9.OUT→R4.1", "U9", "1", [("R4", "1")])
    link("R4.2→Q1.G", "R4", "2", [("Q1", "1")])
    # VBAT-matning op-amp → närmaste VBAT-pad
    link("U9.V+→VBAT", "U9", "5", [("R6", "1"), ("R5", "1"), ("R11", "1")])
    for k, v in res.items(): print(f"  {k} = {v}")
    clr, un = R.finish()
    print(f"DRC clearance={clr} unconnected={un}")
    pcbnew.SaveBoard(PCB, b)
    if clr == 0 and un == 0:
        print("SPARAD ✓ REN"); return
    print("!! EJ ren (sparad för inspektion)")
    CU = ALL_CU
    items = []
    for t in b.GetTracks():
        lays = CU if t.Type() == pcbnew.PCB_VIA_T else [t.GetLayer()]
        p = t.GetPosition(); items.append((t.GetNetname(), t.GetNetCode(), set(lays), t.GetEffectiveShape(), (round(p.x/1e6-OX,1), round(OY-p.y/1e6,1))))
    for f in b.GetFootprints():
        for pd in f.Pads():
            items.append((pd.GetNetname(), pd.GetNetCode(), set(L for L in CU if pd.IsOnLayer(L)), pd.GetEffectiveShape(), f.GetReference()+"."+pd.GetName()))
    seen = 0
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            a, c = items[i], items[j]
            if a[1] == c[1] or not (a[2] & c[2]): continue
            if a[3].Collide(c[3], int(0.2e6)):
                print(f"   CLR: {a[0]}@{a[4]} <-> {c[0]}@{c[4]}"); seen += 1
                if seen > 10: break
        if seen > 10: break
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "route": route_phase()
    else: main()
