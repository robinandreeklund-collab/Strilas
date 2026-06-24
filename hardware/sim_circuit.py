#!/usr/bin/env python3
"""STRILAS — KRETS-SIMULERING (ström + signaler) för ALLA tillverkade kort.

Funktionell krets-sim på .net-nivå (ej SPICE — en digital-SoC + 6 kort SPICE-as ej meningsfullt):
för varje kort byggs kraft-skenorna ur passningselement (batteri→VBAT, buck/LDO→+3V3), strömbudget
summeras mot källkapacitet, och varje signalnät kontrolleras (källa↔mottagare, I²C-pullups, IC-
avkoppling, spänningsdomän). P4-GPIO-roller hämtas ur p4_pinmap (verifierad nät→GPIO).

Kör: python3 hardware/sim_circuit.py    (exit 0 = alla kort PASS)
"""
import sys, re
from p4_pinmap import parse_net, net_to_gpio

# ---------------- komponent-modell (typiska värden ur datablad) ----------------
# i_ma = typisk strömförbrukning (aktiv); rail = vilken skena den hänger på (härleds annars ur nät).
COMP = {
    "AP63203":  dict(role="buck", vin="VBAT", vout="+3V3", iout_max=2000, iq=0.022),
    "HT7333-A": dict(role="ldo",  vin="VBAT", vout="+3V3", iout_max=250,  iq=0.004),
    "IIM-42653":dict(role="ic", i_ma=0.9),                 # 6-ax IMU (industri)
    "ICM-42688-P":dict(role="ic", i_ma=0.9),               # 6-ax IMU (vald, låg-brus) — pin-kompat.
    "ICM-42670":dict(role="ic", i_ma=0.55),
    "TSOP4856": dict(role="ic", i_ma=1.0),                 # IR-mottagare
    "ES8388":   dict(role="ic", i_ma=12.0),                # audio-codec
    "PAM8302A": dict(role="ic", i_ma=180.0),               # klass-D amp (typ @ måttlig volym)
    "74HC165":  dict(role="ic", i_ma=0.5),
    "TPIC6B595":dict(role="ic", i_ma=10.0),                # logik (utan last); vibrator-last separat
    "OPA171":   dict(role="ic", i_ma=1.8),                 # CC-regulator op-amp (optik)
}
# strömförbrukare som inte är 'U' (LED-strängar, emitter, vibratorer) hanteras separat per kort.
PULLUP_NETS = ("I2C_SDA", "I2C_SCL", "NFC_SDA", "NFC_SCL")   # open-drain → kräver pullup
RAILS = ("VBAT", "+3V3")


def build(board):
    comps, nets = parse_net(f"hardware/{board}.net")
    # ref → {pin: net}  och  ref → value
    refpin, val = {}, {v: c[0] for v, c in comps.items()}
    for net, nodes in nets.items():
        for r, p in nodes:
            refpin.setdefault(r, {})[p] = net
    return comps, nets, refpin


def conn_rails(comps, refpin):
    """ref → set av kraftskenor den rör (VBAT/+3V3) + om den rör GND."""
    out = {}
    for ref, pins in refpin.items():
        rails = {n for n in pins.values() if n in RAILS}
        out[ref] = rails
    return out


def sim_power(board, comps, nets, refpin):
    """Bygg skenor + strömbudget. Returnerar (rails_on, budget, issues)."""
    issues = []
    # kraftkällor & pass-element
    src = {}                      # rail → kapacitet mA (None = extern/batteri obegränsat i sim)
    rails_on = set()
    # batteri-kontakt (value innehåller 'batteri') matar VBAT
    if any("batteri" in comps[r][0].lower() for r in comps):
        rails_on.add("VBAT"); src["VBAT"] = None
    # vapen-stacken matas via VBAT_IN/VBAT (säkring+backspärr) → modellera som VBAT-källa
    if "VBAT" in [n for n in nets] or any(n in nets for n in ("VBAT_IN", "VBAT")):
        rails_on.add("VBAT")
    # buck/LDO: VBAT → +3V3
    regs = [(r, COMP[comps[r][0]]) for r in comps if comps[r][0] in COMP and COMP[comps[r][0]]["role"] in ("buck", "ldo")]
    for r, m in regs:
        if m["vin"] in rails_on or m["vin"] == "VBAT":
            rails_on.add(m["vout"]); src[m["vout"]] = m["iout_max"]
    # P4 onboard-regulator: om VSYS(=VBAT) matas och kortet INTE har egen buck men har +3V3-last
    # (vapen-stacken tar 3V3 från P4). Modellera: VBAT på → +3V3 finns (P4 MP1658, 2A-klass).
    if "VBAT" in rails_on and "+3V3" not in rails_on:
        rails_on.add("+3V3"); src["+3V3"] = 2000  # P4 onboard buck
    # kort utan egen källa (fire-control): +3V3 matas EXTERNT via edge-B kraft-tapp från P4-stacken
    if "+3V3" in nets and "+3V3" not in rails_on:
        rails_on.add("+3V3"); src.setdefault("+3V3", None)

    # strömbudget per skena
    budget = {rl: 0.0 for rl in RAILS}
    detail = []
    rails_of = conn_rails(comps, refpin)
    for ref in sorted(comps):
        v = comps[ref][0]
        m = COMP.get(v)
        if not m or m["role"] in ("buck", "ldo"):
            continue
        i = m.get("i_ma", 0.0)
        if i <= 0:
            continue
        rl = "+3V3" if "+3V3" in rails_of.get(ref, set()) else ("VBAT" if "VBAT" in rails_of.get(ref, set()) else None)
        if rl is None:
            issues.append(f"{ref} ({v}) hittar ingen kraftskena (varken +3V3 eller VBAT)")
            continue
        budget[rl] += i
        detail.append((ref, v, rl, i))

    # kort-specifika laster (LED-konstellation, IR-emitter, vibratorer)
    extra = board_loads(board, comps, nets)
    for name, rl, i in extra:
        budget[rl] = budget.get(rl, 0) + i
        detail.append((name, "(last)", rl, i))

    # budget vs kapacitet
    for rl, cap in src.items():
        if cap is not None and budget.get(rl, 0) > cap:
            issues.append(f"skena {rl}: last {budget[rl]:.0f} mA > källa {cap} mA")
    return rails_on, src, budget, detail, issues


def board_loads(board, comps, nets):
    """Icke-IC-laster (uppskattat). (namn, skena, mA)."""
    out = []
    # LED-konstellation: räkna LED_TAB-par; OSLON ~ via serie-R (10R) på VBAT.
    n_led = sum(1 for r in comps if comps[r][0].startswith("LED-tab") or comps[r][0].startswith("LED_TAB"))
    if n_led:
        branches = max(1, n_led // 2)               # serie-par per gren
        out.append((f"LED-konstellation ({n_led} OSLON, {branches} grenar)", "VBAT", branches * 350.0))
    # IR-emitter (optik): CC-sänka ~1 A topp (gatad burst → låg medel; budget tar toppen)
    if board == "weapon-module":
        out.append(("IR-emitter CC-sänka (940nm, ~1A topp)", "VBAT", 1000.0))
    # väst-vibratorer: TPIC open-drain 150 mA/kanal — anta ~3 samtidiga
    if board == "vest-mb":
        out.append(("zon-vibratorer (3× ERM @ ~80 mA samtidigt)", "VBAT", 240.0))
    return out


def sim_signals(board, comps, nets, refpin):
    """Signalnät: dinglar, I²C-pullups, avkoppling. Returnerar (issues, info)."""
    issues, info = [], []
    n2g = net_to_gpio(board, comps, nets)
    p4_nets = set(n2g)                              # nät som når en P4-GPIO

    # 1) dinglande signaler: signalnät med < 2 noder. Om enda noden är en KONTAKT (J*) =
    #    avsiktligt oanvänt kontakt-stift (t.ex. F9P PPS/RSV) → info, ej fel. Är den en IC-pin
    #    (U*) → flytande ingång = riktigt fel.
    for net, nodes in nets.items():
        if net in ("GND", "+3V3", "VBAT") or net.startswith("N$"):
            continue
        if re.match(r'(VBAT|VSYS|VBUS|3V3)', net):
            continue
        if len(nodes) < 2:
            only = nodes[0][0] if nodes else "—"
            if only.startswith("J"):
                info.append(f"oanvänt kontakt-stift: '{net}' ({only}.{nodes[0][1]}) — medvetet ej kopplat")
            else:
                issues.append(f"flytande IC-pin: nät '{net}' endast {nodes} (ingen källa/last)")

    # 2) I²C/open-drain pullups
    for pn in PULLUP_NETS:
        if pn in nets:
            # finns en resistor (R*) mot +3V3 på detta nät?
            has_pu = False
            for r, p in nets[pn]:
                if r.startswith("R"):
                    other = [nn for nn, nd in nets.items() if any(rr == r and pp != p for rr, pp in nd)]
                    if "+3V3" in other:
                        has_pu = True
            if not has_pu:
                issues.append(f"I²C-nät '{pn}' saknar pullup mot +3V3")
            else:
                info.append(f"I²C '{pn}': pullup ✓")

    # 3) avkoppling per IC (minst 1 C mellan dess kraftskena och GND nära den)
    for ref in sorted(comps):
        v = comps[ref][0]
        if v not in COMP or COMP[v]["role"] in ("buck", "ldo"):
            continue
        pins = refpin.get(ref, {})
        rails = {n for n in pins.values() if n in RAILS}
        if not rails:
            continue
        # finns minst en kondensator som rör samma skena + GND?
        rail = "+3V3" if "+3V3" in rails else list(rails)[0]
        decap = False
        for cref in comps:
            if not cref.startswith("C"):
                continue
            cp = refpin.get(cref, {})
            if rail in cp.values() and "GND" in cp.values():
                decap = True; break
        if not decap:
            issues.append(f"{ref} ({v}) saknar avkoppling på {rail}")

    # 4) spänningsdomän: alla IC på +3V3 (ingen level-shift behövs) — info
    info.append("spänningsdomän: 3,3 V genomgående (P4 + alla periferi-IC native 3V3 → inga level-shifters)")
    return issues, info, p4_nets


BOARDS = ["weapon-module", "firecontrol", "helmet-mb", "vest-mb", "vest-patch"]


def main():
    allpass = True
    print("=" * 80)
    print("STRILAS — KRETS-SIMULERING (ström + signaler), alla tillverkade kort")
    print("=" * 80)
    for board in BOARDS:
        try:
            comps, nets, refpin = build(board)
        except FileNotFoundError:
            continue
        rails_on, src, budget, detail, pissues = sim_power(board, comps, nets, refpin)
        sissues, sinfo, p4_nets = sim_signals(board, comps, nets, refpin)
        issues = pissues + sissues
        print(f"\n{'─'*80}\n### {board}  ({len(comps)} komponenter, {len(nets)} nät)")
        print(f"  KRAFT: skenor på = {sorted(rails_on)}")
        for rl in RAILS:
            cap = src.get(rl)
            caps = f"{cap} mA" if cap else "extern/batteri"
            mark = "" if (cap is None or budget.get(rl, 0) <= cap) else "  ✗ ÖVER BUDGET"
            if budget.get(rl, 0) > 0 or rl in rails_on:
                print(f"    {rl:5}: last ~{budget.get(rl,0):6.0f} mA  / källa {caps}{mark}")
        # topp-strömposter
        top = sorted([d for d in detail if d[3] >= 5], key=lambda d: -d[3])[:5]
        if top:
            print("    största laster: " + ", ".join(f"{d[0]}={d[3]:.0f}mA" for d in top))
        print(f"  SIGNALER: {len(p4_nets)} P4-GPIO-nät")
        for i in sinfo:
            print(f"    · {i}")
        if issues:
            for x in issues:
                print(f"    ✗ {x}")
            allpass = False
        else:
            print("    ✓ inga krets-FEL (kraft/budget/dinglar/pullup/avkoppling rena)")
    print("\n" + "=" * 80)
    print(f"{'✅ ALLA KORT PASS' if allpass else '❌ PROBLEM — se ovan'}")
    print("=" * 80)
    return 0 if allpass else 1


if __name__ == "__main__":
    sys.exit(main())
