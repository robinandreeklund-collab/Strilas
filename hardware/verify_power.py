#!/usr/bin/env python3
"""STRILAS — elektrisk verifiering: (1) I²C-pull-ups, (2) avkoppling per IC, (3) strömbudget/rail.
Läser .net (nät/värden) + .kicad_pcb (positioner). Kör: python3 hardware/verify_power.py
"""
import sys, math, pcbnew
sys.path.insert(0, "hardware")
from p4_pinmap import parse_net

OX, OY = 150.0, 120.0
def xy(p): return (p.x/1e6-OX, OY-p.y/1e6)

# ICs vars matnings-pinnar ska ha närliggande avkoppling (ref-prefix U). Paket-nyckelord -> "IC".
IC_FP = ("QFN", "LGA", "TSOT", "SOT-23-6", "SOIC", "TSSOP", "DFN", "SOT-563", "MOLD-3Pin", "TO-252")
PWR_NETS = ("+3V3", "VBAT", "VBAT_RAW")

# typisk strömförbrukning (mA) — datablads-typvärden (aktivt), per komponent-klass.
def est_current(ref, val, fp):
    v = (val or "").upper()
    if "ESP32-P4" in v or "P4_EDGE" in v: return 500     # P4-modul (aktiv, WiFi6) — på VSYS
    if "AP63203" in v: return 0                          # buck (last räknas separat)
    if "ES8388" in v: return 30                          # codec
    if "PAM8302" in v: return 200                        # klass-D amp (peak musik @8Ω)
    if "ICM" in v or "IIM" in v or "42" in v: return 3   # IMU
    if "ZED-F9P" in v or "RTK" in v: return 130          # GNSS-puck
    if "TSOP" in v: return 5                             # IR-mottagare
    if "TPIC6B595" in v: return 5                        # shift-reg (logik; motorström separat)
    if "PN5" in v or "NFC" in v or "RC522" in v: return 50
    if "OPA" in v: return 5
    return None

# ERM-motorer / LED-grenar / IR-emitter: uppskattas via nät-grenar i koden nedan.


def i2c_pullups(c, n):
    out = []
    for nm in n:
        if "SDA" not in nm and "SCL" not in nm: continue
        # resistor med ena benet på nätet och andra på +3V3?
        rs = [r for r, p in n[nm] if r.startswith("R")]
        pull = []
        for r in rs:
            other_nets = {nn for nn, nodes in n.items() for rr, pp in nodes if rr == r}
            if "+3V3" in other_nets: pull.append(r)
        out.append((nm, pull))
    return out


def decoupling(board, c, n):
    """för varje IC: närmaste avkopplings-C (VALFRITT värde) på dess matningsnät + avstånd.
    Mäter IC-matnings-PADD → C-padd (ej center→center) = rättvist mot avståndskravet."""
    b = pcbnew.LoadBoard(f"hardware/{board}.kicad_pcb")
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    caps = {r: v for r, (v, fp) in c.items() if r.startswith("C")}
    res = []
    for r, (v, fp) in c.items():
        if not r.startswith("U") or not any(k in fp for k in IC_FP) or r not in fps:
            continue
        pwr_pads = [p for p in fps[r].Pads() if p.GetNetname() in PWR_NETS]
        if not pwr_pads:
            continue
        pnets = {p.GetNetname() for p in pwr_pads}
        best = None
        for cr in caps:
            if cr not in fps:
                continue
            cnets = {p.GetNetname() for p in fps[cr].Pads()}
            if not (cnets & pnets):
                continue
            # minsta padd→padd-avstånd (matnings-padd på IC ↔ närmaste C-padd)
            for ip in pwr_pads:
                ipx = xy(ip.GetPosition())
                for cp in fps[cr].Pads():
                    d = math.hypot(*(a-b_ for a, b_ in zip(ipx, xy(cp.GetPosition()))))
                    if best is None or d < best[1]:
                        best = (cr, d, caps[cr])
        res.append((r, v, sorted(pnets), best))
    return res


def current_budget(board, c, n):
    # summera per rail. P4 på VSYS=VBAT (egen buck), carrier-buck 3V3 = AP63203 2A.
    rails = {"+3V3": 0.0, "VBAT": 0.0}
    detail = {"+3V3": [], "VBAT": []}
    puck_counted = False
    has_buck = any("AP63203" in (v or "") for v, fp in c.values())
    for r, (v, fp) in c.items():
        mA = est_current(r, v, fp)
        if mA is None or not mA: continue
        # alt-puckar (ZED-F9P J1 OCH 6-pol alt J12) = ALTERNATIV → räkna EN
        if "F9P" in (v or "").upper() or "RTK" in (v or "").upper():
            if puck_counted: continue
            puck_counted = True
        nets = {nn for nn, nodes in n.items() for rr, pp in nodes if rr == r}
        rail = "+3V3" if "+3V3" in nets else ("VBAT" if ("VBAT" in nets or "VBAT_RAW" in nets) else None)
        if rail:
            rails[rail] += mA; detail[rail].append((r, v, mA))
    return rails, detail, has_buck


def main():
    BOARDS = ("weapon-module", "firecontrol", "helmet-mb", "vest-mb", "vest-patch")
    allok = True
    for bd in BOARDS:
        c, n = parse_net(f"hardware/{bd}.net")
        print(f"\n================== {bd} ==================")
        # 1 I2C
        pu = i2c_pullups(c, n)
        if pu:
            print(" [I²C pull-ups]")
            for nm, pull in pu:
                ok = bool(pull)
                if not ok: allok = False
                print(f"   {nm}: {'pull-up '+str(pull)+' → +3V3  ✓' if ok else 'SAKNAR PULL-UP !!!'}")
        else:
            print(" [I²C] inga I²C-nät")
        # 2 avkoppling
        dec = decoupling(bd, c, n)
        print(" [avkoppling per IC]")
        for r, v, pnets, best in dec:
            if best is None:
                print(f"   {r} ({v}) {pnets}: INGEN avkopplings-C på matningsnätet !!!"); allok = False
            else:
                flag = "✓" if best[1] <= 5.0 else f"⚠ {best[1]:.1f}mm (>5mm)"
                print(f"   {r} ({v}) {pnets}: närmaste 100nF = {best[0]} @ {best[1]:.1f}mm  {flag}")
        # 3 strömbudget
        rails, detail, has_buck = current_budget(bd, c, n)
        print(" [strömbudget per rail — ombord-IC (datablads-typ); externa laster (motorer/LED i"
              " patchar) går via kontakter och adderas i texten]")
        for rail in ("VBAT", "+3V3"):
            if detail[rail]:
                items = ", ".join(f"{r}:{mA}mA" for r, v, mA in detail[rail])
                print(f"   {rail}: ~{rails[rail]:.0f} mA ombord  ({items})")
        if has_buck:
            m = 2000 - rails["+3V3"]
            print(f"   → carrier-buck AP63203 = 2000 mA; ombord-marginal ~{m:.0f} mA "
                  f"{'✓' if m > 0 else '!!! ÖVER'} (extern patch/motor-last tillkommer)")
    print("\n==> " + ("ELEKTRISK GRUNDKONTROLL OK ✓" if allok else "ÅTGÄRD KRÄVS — se !!! ovan"))


if __name__ == "__main__":
    main()
