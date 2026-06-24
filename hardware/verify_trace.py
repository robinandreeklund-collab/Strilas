#!/usr/bin/env python3
"""STRILAS — strömtålighet (IPC-2221) + termiska via:or under FET/buck.
(1) Per kraftnät: minsta spårbredd → tillåten ström (1oz Cu, yttre lager) vs förväntad ström.
(2) FET/buck: räknar via:or i/nära komponentens termiska padd (värmeavledning till plan).
Kör: python3 hardware/verify_trace.py
"""
import sys, math, pcbnew
sys.path.insert(0, "hardware")
from p4_pinmap import parse_net
from collections import defaultdict

OX, OY = 150.0, 120.0
def xy(p): return (p.x/1e6-OX, OY-p.y/1e6)

# IPC-2221 yttre lager: I = k*dT^0.44*A^0.725, A i mil², k=0.048. 1oz = 1.378 mil tjock.
def ampacity(w_mm, dT=10, oz=1.0):
    A = (w_mm/0.0254) * (1.378*oz)          # mil²
    return 0.048 * dT**0.44 * A**0.725       # A

# förväntad DRIFTSTRÖM per kraftnät (A) — steady/operativ (datablads-/design-uppskattning).
# Huvud-batterirail = P4(VSYS ~0,7A topp) + buck-in (3V3-last). IR-konstellationens grenström
# (LED_A/M/CATH) är PWM-PULSAD (kamera-synk, låg duty) → topp tas av batteri/XT30-burst + koppar-
# termisk massa, EJ steady spårrating; här anges driftsnitt.
EXPECT = {
  "weapon-module": {"VBAT":1.2, "VBAT_IN":1.2, "VBAT_F":1.2, "LED_MID":1.0, "LED_CATH":1.0,
                    "IDRV_SENSE":1.0, "N$2":1.0},
  "vest-mb":       {"VBAT":1.6, "VBAT_IN":1.6, "VBAT_RAW":1.6,
                    **{f"VIB{i}":0.12 for i in range(1,11)}},
  "helmet-mb":     {"VBAT":1.0, "VBAT_IN":1.0, "VBAT_RAW":1.0,
                    "LED_CATH":1.2, **{f"LED_A{i}":0.6 for i in range(1,4)},
                    **{f"LED_M{i}":0.6 for i in range(1,4)}},
  "vest-patch":    {"VBAT":1.2, "LED_CATH":1.2, **{f"LED_A{i}":0.6 for i in range(1,4)},
                    **{f"LED_M{i}":0.6 for i in range(1,4)}},
}

# FET/buck-delar vars termiska padd ska ha via:or (DPAK-tab, buck-EP)
THERMAL_PARTS = ("AOD4185", "AOD4184", "AP63203", "AO3401")   # värme-genererande effekt-delar


def min_widths(b):
    w = defaultdict(lambda: 1e9)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T: continue
        w[t.GetNetname()] = min(w[t.GetNetname()], t.GetWidth()/1e6)
    return w


def thermal_vias(b, comps):
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    out = []
    for r, (v, fp) in comps.items():
        if not any(k in (v or "") for k in THERMAL_PARTS): continue
        if r not in fps: continue
        f = fps[r]
        # största padden = termisk tab/EP
        pads = list(f.Pads())
        tab = max(pads, key=lambda p: p.GetBoundingBox().GetWidth()*p.GetBoundingBox().GetHeight())
        bb = tab.GetBoundingBox(); m = int(0.3e6)
        nvia = sum(1 for vi in vias
                   if bb.GetX()-m <= vi.GetPosition().x <= bb.GetRight()+m
                   and bb.GetY()-m <= vi.GetPosition().y <= bb.GetBottom()+m
                   and vi.GetNetname() == tab.GetNetname())
        # bredd på tab (mm) för referens
        out.append((r, v, tab.GetNetname(), nvia,
                    round(tab.GetBoundingBox().GetWidth()/1e6,1), round(tab.GetBoundingBox().GetHeight()/1e6,1)))
    return out


def main():
    BOARDS = ("weapon-module", "vest-mb", "helmet-mb", "vest-patch")
    issues = 0
    for bd in BOARDS:
        comps, nets = parse_net(f"hardware/{bd}.net")
        b = pcbnew.LoadBoard(f"hardware/{bd}.kicad_pcb")
        w = min_widths(b)
        print(f"\n================== {bd} ==================")
        print(" [strömtålighet: min-bredd → A@10°C / A@20°C  vs  förväntad]")
        for nm, I in sorted(EXPECT.get(bd, {}).items()):
            if nm not in w: continue
            wm = w[nm]; a10 = ampacity(wm, 10); a20 = ampacity(wm, 20)
            ok = a20 >= I            # tillåt 20°C-höjning som gräns
            tight = a10 < I <= a20
            flag = "✓" if a10 >= I else ("~ (ok@20°C)" if ok else "!!! FÖR SMAL")
            if not ok: issues += 1
            if I >= 0.1:   # visa bara kraft-nät av betydelse
                print(f"   {nm:11} {wm:.2f}mm → {a10:.2f}A/{a20:.2f}A  vs {I:.2f}A  {flag}")
        print(" [termiska via:or under effekt-delar (FET/buck)]")
        for r, v, net, nvia, tw, th in thermal_vias(b, comps):
            flag = "✓" if nvia >= 2 else ("(SOT-23, ej kritiskt)" if "AO3401" in (v or "") else "⚠ få/inga")
            print(f"   {r} ({v}) tab-nät={net} {tw}×{th}mm: {nvia} via  {flag}")
    print("\n==> " + ("STRÖMTÅLIGHET OK ✓" if issues == 0 else f"!!! {issues} kraftnät för smala — åtgärda"))


if __name__ == "__main__":
    main()
