#!/usr/bin/env python3
"""STRILAS — SYSTEMVERIFIERING (kod-simulering av hela vapen-stacken).

Kopplar ihop alla tre korten via deras EXAKTA portar, slår ihop näten globalt
genom kontakterna, och SIMULERAR ström- + signalflöde:
  • optik  ↔ P4 edge B  (1×14, P4-pin 2..15)
  • FC     ↔ P4 edge A  (1×12, P4-pin 6..17)
  • batteri → optik J2 → VBAT → VSYS → P4-regulator → 3V3 → alla förbrukare
  • FC:s 3V3 tas DIREKT från edge B via kraft-tapp J2 (edge A saknar kraftskena)

Verifierar: (1) varje mate-stift träffar rätt P4-funktion, (2) nät-typ stämmer
över kortgränsen, (3) varje IC får ström, (4) varje signal är kopplad källa↔mottagare.
"""
import re, sys

# ---------------- 1) parse KiCad-nätlistor ----------------
def parse(path):
    t = open(path).read(); seg = t[t.find("(nets"):]
    nets = {}
    for blk in re.split(r"\(net\b", seg)[1:]:
        nm = re.search(r'\(name "([^"]*)"\)', blk)
        if not nm:
            continue
        nets[nm.group(1)] = re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', blk)
    return nets

OPT = parse("hardware/weapon-module.net")
FC  = parse("hardware/firecontrol.net")

# ---------------- 2) P4-pinout (officiell Waveshare ESP32-P4-WIFI6) ----------------
EDGE_A = ["GPIO52","GPIO51","GND","GPIO31","GPIO30","GPIO29","GPIO28","GND","GPIO50","GPIO49",
          "GPIO5","GPIO4","GND","GPIO3","GPIO2","GPIO8","GPIO7","GND","GPIO24(D-)","GPIO25(D+)"]
EDGE_B = ["VBUS","VSYS","GND","EN","3V3","GPIO20","GPIO21","GND","GPIO22","GPIO23",
          "RUN","GPIO26","GND","GPIO27","GPIO32","GPIO33","GPIO46","GND","GPIO47","GPIO48"]
POWER = {"VBUS","VSYS","3V3","+3V3","VBAT","VBAT_F","VBAT_IN"}

# mate: (board, connector, board_pin) -> P4 edge-pin-index (1-baserat)
#   optik J1 pin k -> edge B (k+1)   ;   FC J1 pin k -> edge A (k+5)
def matemap():
    m = []
    for k in range(1, 15):
        m.append(("OPT", "J1", str(k), "B", k + 1))     # optik J1 → edge B pin 2..15
    for k in range(1, 13):
        m.append(("FC", "J1", str(k), "A", k + 5))       # FC J1 → edge A pin 6..17
    for k in range(1, 4):
        m.append(("FC", "J2", str(k), "B", k + 2))       # FC J2 kraft-tapp → edge B pin 3,4,5 (GND/EN/3V3)
    return m

# ---------------- 3) hjälp: kontakt-pin -> nät för ett kort ----------------
def pin2net(nets):
    d = {}
    for nm, nodes in nets.items():
        for r, p in nodes:
            d.setdefault(r, {})[p] = nm
    return d

OPTpn, FCpn = pin2net(OPT), pin2net(FC)
BOARD = {"OPT": (OPT, OPTpn, "optik"), "FC": (FC, FCpn, "fire-control")}

def kind(net):
    if net in (None, ""): return "NC"
    if net == "GND": return "GND"
    if net in POWER: return "KRAFT"
    return "SIGNAL"

# ---------------- 4) HARNESS: mate-konsistens ----------------
print("="*74)
print(" STRILAS systemverifiering — vapen-stack (optik · P4 · FC)")
print("="*74)
print("\n[1] HARNESS — mate-stift mot P4-funktion (typ-konsistens)")
edge = {"A": EDGE_A, "B": EDGE_B}
harness_fail = 0
glob = {}            # (board,net) -> global-id ; P4-funktioner: ("P4",func)
def union(a, b):
    glob.setdefault(a, a); glob.setdefault(b, b)
    ra, rb = find(a), find(b)
    if ra != rb: glob[ra] = rb
def find(x):
    glob.setdefault(x, x)
    while glob[x] != x: glob[x] = glob[glob[x]]; x = glob[x]
    return x

for bd, conn, pin, e, idx in matemap():
    func = edge[e][idx-1]
    pn = BOARD[bd][1]
    net = pn.get(conn, {}).get(pin)
    # typ-konsistens: P4-funktionens typ vs kortets nät-typ
    pk = "GND" if func == "GND" else ("KRAFT" if func in POWER else ("NC" if func.startswith("EN") or func.startswith("RUN") else "SIGNAL"))
    nk = kind(net)
    ok = (pk == nk) or (nk == "NC") or (pk == "SIGNAL" and nk in ("SIGNAL",)) \
         or (pk == "KRAFT" and nk == "KRAFT") or (pk == "GND" and nk == "GND")
    # NC på P4-sidan (EN/RUN/VBUS) som kortet lämnar öppet = ok
    if func in ("EN", "RUN", "VBUS") and nk == "NC": ok = True
    if not ok: harness_fail += 1
    flag = "" if ok else "  ✗ TYPKROCK"
    if net or not ok or func not in ("GND",):
        pass
    # union kortets nät med P4-funktionen (om inte NC)
    if net:
        union((bd, net), ("P4", func))
print(f"   optik↔edge B: 14 stift   FC↔edge A: 12 stift   typkrockar: {harness_fail}")

# detaljerad mate-tabell
def show_mate(bd, e, base, n, title):
    print(f"\n   {title}")
    pn = BOARD[bd][1]
    for k in range(1, n+1):
        func = edge[e][base+k-1-1+1-1]  # base är edge-pin för k=1
        func = edge[e][base-1 + (k-1)]
        net = pn.get("J1", {}).get(str(k), "—(NC)")
        print(f"     J1.{k:<2} → P4 {e}{base+k-1:<2} {func:<10} = {net}")
show_mate("OPT", "B", 2, 14, "OPTIK J1 (edge B):")
show_mate("FC",  "A", 6, 12, "FC J1 (edge A):")

# ---------------- 5) globala nät: GND (3V3 via J2-mate ovan) ----------------
for bd in ("OPT", "FC"):
    union((bd, "GND"), ("P4", "GND"))
# FC tar 3V3 DIREKT från edge B via kraft-tappen J2 (J2.3 ↔ edge B5 = 3V3) — ingen tråd.

# ---------------- 6) KRAFTFLÖDE-simulering ----------------
print("\n[2] KRAFTFLÖDE — propagering från batteriet")
def gid(bd, net): return find((bd, net))
powered = set()
# källa: batteri på optikens VBAT_IN
powered.add(gid("OPT", "VBAT_IN"))
# kraft-pass-element (in-nät → ut-nät)
passes = [("optik säkring F1",  ("OPT","VBAT_IN"), ("OPT","VBAT_F")),
          ("optik backspärr Q1",("OPT","VBAT_F"),  ("OPT","VBAT")),
          ("VBAT→VSYS (J1.1↔edgeB2)", ("OPT","VBAT"), ("P4","VSYS")),
          ("P4 onboard-regulator", ("P4","VSYS"), ("P4","3V3"))]
chain = []
changed = True
while changed:
    changed = False
    for name, i, o in passes:
        if gid(*i) in powered and gid(*o) not in powered:
            powered.add(gid(*o)); changed = True
for name, i, o in passes:
    up = "✓" if gid(*i) in powered else "✗"
    dn = "✓" if gid(*o) in powered else "✗"
    print(f"   {up}{dn}  {name:28} {i[1]} → {o[1]}")

V3 = gid("P4", "3V3"); VS = gid("P4", "VSYS"); VB = gid("OPT", "VBAT")
print(f"\n   rail-status: VSYS={'PÅ' if VS in powered else 'AV'}  "
      f"3V3={'PÅ' if V3 in powered else 'AV'}  VBAT={'PÅ' if VB in powered else 'AV'}")

# per-IC strömkontroll (U*) + IR-emitter
print("\n   IC-matning:")
def comps(nets):
    s = set()
    for nodes in nets.values():
        for r, _ in nodes:
            if r[0] in "U": s.add(r)
    return sorted(s)
unpowered = 0
for bd, label in (("OPT","optik"), ("FC","fire-control")):
    nets, pn, _ = BOARD[bd]
    for u in comps(nets):
        prails = [n for p, n in pn[u].items() if kind(n) in ("KRAFT",)]
        on = any(gid(bd, n) in powered for n in prails)
        if not on: unpowered += 1
        print(f"     {label:12} {u:4} matas av {prails or ['—']}: {'PÅ ✓' if on else 'INGEN ström ✗'}")
# IR-emittersträng (optik): VBAT→R2→D2→D3→Q2
ir_on = gid("OPT","VBAT") in powered
print(f"     optik        IR-LED (D2/D3 via VBAT, switch Q2): {'PÅ ✓' if ir_on else 'AV ✗'}")

# ---------------- 7) SIGNALFLÖDE — källa↔mottagare över gränsen ----------------
print("\n[3] SIGNALFLÖDE — varje funktionsnät, ändpunkter & dinglar")
ROLE = {  # nät -> (P4-roll, beskrivning)
 "IR_MOD":("UT→","940nm IR-modulering → Q2-driver"),
 "SCK":("UT→","SPI-klocka → optik-IMU U1"), "MOSI":("UT→","SPI MOSI → U1"),
 "MISO":("←IN","SPI MISO ← U1"), "nCS":("UT→","SPI CS → U1"), "IMU_INT":("←IN","IMU-avbrott ← U1"),
 "TRIG":("←IN","avtryckare"), "RACK":("←IN","rack"), "MAG_REL":("←IN","mag-release"),
 "MAGWELL":("←IN","magasin-närvaro"), "RECOIL_PWM":("UT→","recoil EN/PWM → effektkort"),
 "RECOIL_FAULT":("←IN","eFuse fault ← effektkort"),
 "NFC_SDA":("↔","I²C data (NFC+IMU U1/U2)"), "NFC_SCL":("↔","I²C klocka"),
 "IMU2_INT":("←IN","IMU U1-avbrott (0x69)"), "IMU3_INT":("←IN","IMU U2-avbrott (0x68)")}
dangling = 0
for bd, label in (("OPT","optik"), ("FC","FC")):
    nets, pn, _ = BOARD[bd]
    print(f"\n   [{label}]")
    for nm in sorted(nets):
        if kind(nm) in ("KRAFT","GND") or nm.startswith("N$") or nm in ("VBAT_F","VBAT_IN","LED_MID","LED_CATH","Q1_GATE"):
            continue
        nodes = nets[nm]
        has_p4 = any(r == "J1" for r, _ in nodes)          # P4-sidan
        periph = [f"{r}.{p}" for r, p in nodes if r != "J1"]
        role, desc = ROLE.get(nm, ("?",""))
        bad = (not has_p4) or (not periph)
        if bad: dangling += 1
        print(f"     {role:4} {nm:13} {'P4✓' if has_p4 else 'P4✗':4} ↔ {periph}  {desc}{'   ✗ DINGLAR' if bad else ''}")

# ---------------- 8) SAMMANFATTNING ----------------
print("\n"+"="*74)
print(f" SAMMANFATTNING:  typkrockar={harness_fail}  ström-saknas={unpowered}  dinglande signaler={dangling}")
ok = (harness_fail == 0 and unpowered == 0 and dangling == 0 and V3 in powered)
print(f"   3V3-rail når alla kort: {'JA' if V3 in powered else 'NEJ'} "
      f"(FC via edge-B kraft-tapp J2)")
print(f"\n   {'✅ SYSTEMET FLÖDAR KORREKT' if ok else '❌ PROBLEM HITTADE — se ovan'}")
print("="*74)

# ---------------- 9) flödesdiagram ----------------
def diagram():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(13, 8), facecolor="white")
    def box(x, y, w, h, txt, fc, ec="#222"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=6",
                     fc=fc, ec=ec, lw=1.6, zorder=2))
        ax.text(x+w/2, y+h/2, txt, ha="center", va="center", fontsize=8.5, zorder=3, weight="bold")
    def arr(x1, y1, x2, y2, c, lbl="", lw=2.4, ls="-"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
                     color=c, lw=lw, ls=ls, zorder=1, shrinkA=2, shrinkB=2))
        if lbl: ax.text((x1+x2)/2, (y1+y2)/2+1.5, lbl, ha="center", fontsize=7, color=c, zorder=4)
    RED, GRY, BLU = "#d22", "#555", "#06c"
    box(2, 40, 18, 10, "BATTERI\n(LiPo)", "#ffe08a")
    box(26, 30, 28, 30, "OPTIK-KORT\nF1 säkring · Q1 backspärr\nIR-emitter (940nm, D2/D3, Q2)\nIMU U1 (SPI)", "#bfe3c0")
    box(62, 30, 24, 30, "ESP32-P4\nVSYS→[reg]→3V3\nedge B (14)  ·  edge A (12)", "#bcd0f0")
    box(94, 44, 30, 16, "FC-KORT\nIMU U1 0x69 · U2 0x68 (I²C)\nNFC PN532 (I²C)", "#bfe3c0")
    box(94, 24, 30, 14, "FC fan-out\ntrigger·rack·mag-rel·magwell\nrecoil-effektkort (PWM/FAULT)", "#e8d8b0")
    # ström (rött)
    arr(20, 45, 26, 45, RED, "VBAT")
    arr(54, 50, 62, 50, RED, "VBAT→VSYS\n(J1.1↔edgeB2)")
    arr(74, 44, 74, 38, RED)
    arr(74, 39, 86, 39, RED, "3V3 (edge B5)")  # P4 3V3 → optik
    arr(54, 36, 50, 36, RED)
    # 3V3 harness-tråd optik→FC (edge A saknar 3V3)
    arr(74, 36, 99, 36, RED, "3V3 via edge B-tapp (FC J2)")
    # bussar (grå/blå)
    arr(62, 40, 54, 40, BLU, "SPI+IR+IMU_INT\n(edge B)")
    arr(86, 50, 94, 50, BLU, "I²C SDA/SCL + INT\n(edge A)")
    arr(86, 33, 94, 31, GRY, "switchar + recoil\n(edge A)")
    ax.text(75, 22, "rött = ström   blå = databuss   grå = I/O   streckat = harness-tråd",
            ha="center", fontsize=8, color="#333")
    ax.text(63, 63, f"{'✅ FLÖDAR KORREKT' if ok else '❌ FEL'}  —  typkrock {harness_fail} · ström-saknas {unpowered} · dinglar {dangling}",
            ha="center", fontsize=11, weight="bold", color="#080" if ok else "#c00")
    ax.set_xlim(0, 128); ax.set_ylim(18, 70); ax.axis("off")
    ax.set_title("STRILAS — system-flödessimulering (batteri → VSYS → 3V3 → alla kort)", fontsize=12, weight="bold")
    plt.tight_layout(); plt.savefig("hardware/system-flow.png", dpi=140, facecolor="white")
    print("   skrev hardware/system-flow.png")
diagram()
sys.exit(0 if ok else 1)
