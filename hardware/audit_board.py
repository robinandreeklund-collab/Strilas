#!/usr/bin/env python3
"""STRILAS — FULL kort-revision (ETT kort/process pga pcbnew-SWIG).
Kör: python3 hardware/audit_board.py <board>
Kontrollerar:
  1. DRC: clearance@0.2mm + unconnected (routning-integritet)
  2. PCB↔.net net-konsistens: varje pad-nät i PCB == .net (fångar netlist/PCB-desync)
  3. Kontakt-polaritet: kända polariserade kontakter (XT30) pin→nät vs footprint-silk
  4. Polariserade 2-pin (dioder D*): pin1/pin2-nät för manuell granskning
  5. P4-pinout: VSYS/GND/3V3/EN samt GPIO-konflikt (två nät på samma GPIO)
"""
import sys, re, pcbnew
sys.path.insert(0, "hardware")
from p4_pinmap import parse_net, net_to_gpio, EDGE_A, EDGE_B, P4_GPIO_RANGE, P4_STRAPPING, P4_USB_JTAG

board = sys.argv[1]
PCB = f"hardware/{board}.kicad_pcb"
NET = f"hardware/{board}.net"

# polariserade kontakter: footprint-nyckel → {pinnamn: förväntad polaritet}
POLARIZED_CONN = {
    "AMASS_XT30PW-M": {"1": "GND(−)", "2": "VBAT(+)"},   # silk: pin1=−, pin2=+
}

# per-footprint anod-pad (resten = katod). Källa: SKiDL-part-templates + make_footprints.py.
#   D_SOD-123 / D_SMB: pin1=katod (generisk KiCad-konvention, banded).
#   LED_Tab / IR_Emitter_OSRAM: pin1=ANOD (led_tab.py / make_footprints.py land E062.3010.91-06).
ANODE_PAD = {"LED_Tab": "1", "IR_Emitter_OSRAM_OSLON_Black_SFH4725S": "1"}   # default annars = pin2 (anod), pin1=katod

b = pcbnew.LoadBoard(PCB)
CU = [L for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if b.IsLayerEnabled(L)]
print(f"===== {board}  ({b.GetCopperLayerCount()} lager: {[pcbnew.LayerName(L) for L in CU]}) =====")

# --- 1. DRC ---
items = []
for t in b.GetTracks():
    lays = CU if t.Type() == pcbnew.PCB_VIA_T else [t.GetLayer()]
    items.append((t.GetNetCode(), set(lays), t.GetEffectiveShape()))
for f in b.GetFootprints():
    for pd in f.Pads():
        items.append((pd.GetNetCode(), set(L for L in CU if pd.IsOnLayer(L)), pd.GetEffectiveShape()))
clr = sum(1 for i in range(len(items)) for j in range(i + 1, len(items))
          if items[i][0] != items[j][0] and (items[i][1] & items[j][1]) and items[i][2].Collide(items[j][2], int(0.2e6)))
b.BuildConnectivity()
try: un = b.GetConnectivity().GetUnconnectedCount(True)
except TypeError: un = b.GetConnectivity().GetUnconnectedCount()
print(f"[1] DRC  clearance@0.2mm={clr}  unconnected={un}  spår={len(list(b.GetTracks()))}   {'OK' if clr==0 and un==0 else '!!! FEL'}")

# --- 2. PCB↔.net net-konsistens ---
comps, nets = parse_net(NET)
netpad = {}   # (ref,pin) -> netname  (ur .net)
for nm, nodes in nets.items():
    for ref, pin in nodes:
        netpad[(ref, pin)] = nm
mism = 0
for f in b.GetFootprints():
    ref = f.GetReference()
    for pd in f.Pads():
        pin = pd.GetName()
        if not pin:
            continue
        pcbnet = pd.GetNetname()
        netnet = netpad.get((ref, pin))
        if netnet is None:
            continue   # pad utan nod i .net (NC/mekanisk)
        # normalisera: tom PCB-nät vs .net
        if pcbnet != netnet:
            mism += 1
            if mism <= 12:
                print(f"    DESYNC {ref}.{pin}: PCB='{pcbnet}'  .net='{netnet}'")
print(f"[2] PCB↔.net  net-mismatch={mism}   {'OK' if mism==0 else '!!! FEL'}")

# --- 3. polariserade kontakter ---
print("[3] polariserade kontakter:")
found_pol = False
for f in b.GetFootprints():
    fpn = str(f.GetFPID().GetLibItemName())
    for key, exp in POLARIZED_CONN.items():
        if key in fpn:
            found_pol = True
            for pd in sorted(f.Pads(), key=lambda p: p.GetName()):
                pin = pd.GetName()
                if pin in exp:
                    want = exp[pin]; got = pd.GetNetname()
                    ok = (("GND" in want and got == "GND") or ("VBAT" in want and got == "VBAT"))
                    print(f"    {f.GetReference()} {fpn.split('_')[1]} pin{pin}: nät='{got}'  förväntat={want}  {'OK' if ok else '!!! POLARITET FEL'}")
if not found_pol:
    print("    (inga inneboende-polariserade kontakter)")

# --- 4. polariserade 2-pin dioder/LED/emitter (rätt anod/katod per footprint) ---
print("[4] dioder/LED/emitter (anod→katod = framström):")
dn = 0
for f in sorted(b.GetFootprints(), key=lambda x: x.GetReference()):
    ref = f.GetReference()
    if not ref.startswith("D"):
        continue
    fpn = str(f.GetFPID().GetLibItemName())
    pins = {pd.GetName(): pd.GetNetname() for pd in f.Pads()}
    apad = ANODE_PAD.get(fpn, "2")               # default: pin2=anod, pin1=katod
    kpad = "1" if apad == "2" else "2"
    print(f"    {ref:5} {f.GetValue():22} A(pin{apad})='{pins.get(apad,'')}'  K(pin{kpad})='{pins.get(kpad,'')}'")
    dn += 1
if dn == 0:
    print("    (inga)")

# --- 5. P4-pinout ---
print("[5] P4-pinout:")
if board in ("weapon-module", "firecontrol", "helmet-mb", "vest-mb"):
    n2g = net_to_gpio(board, comps, nets)
    gpio_owner = {}   # func -> set(nets)
    for net, lst in n2g.items():
        for ref, pad, pin, func in lst:
            gpio_owner.setdefault(func, set()).add(net)
    # 5a kraft-stift rätt nät
    POWER = {"VSYS": "VBAT", "3V3": ("+3V3", "P3V3", "3V3"), "VBUS": None}
    for func, want in POWER.items():
        if func in gpio_owner:
            got = gpio_owner[func]
            if want is None:
                print(f"    {func}: {sorted(got)}")
            else:
                wants = (want,) if isinstance(want, str) else want
                ok = all(any(w in g for w in wants) for g in got)
                print(f"    {func} → {sorted(got)}  {'OK' if ok else '!!! FEL (förväntat '+str(wants)+')'}")
    # GND-stiften: alla som landar på GND-func ska vara GND-nät
    if "GND" in gpio_owner:
        gnd_ok = gpio_owner["GND"] == {"GND"} or gpio_owner["GND"] <= {"GND"}
        print(f"    GND-stift → {sorted(gpio_owner['GND'])}  {'OK' if gnd_ok else '!!! FEL'}")
    # 5b GPIO-konflikt: samma GPIO-func med >1 nät
    conf = {f: s for f, s in gpio_owner.items() if f.startswith("GPIO") and len(s) > 1}
    print(f"    GPIO-konflikt (samma stift, >1 nät): {conf if conf else 'inga'}  {'OK' if not conf else '!!! FEL'}")
    # 5c strapping/USB-JTAG-användning (info)
    used_strap = {f for f in gpio_owner if f.startswith("GPIO") and int(f[4:]) in P4_STRAPPING}
    used_jtag = {f for f in gpio_owner if f.startswith("GPIO") and int(f[4:]) in P4_USB_JTAG}
    if used_strap: print(f"    INFO strapping-pin använd: {sorted(used_strap)} → {{f:sorted(gpio_owner[f]) for f in used_strap}}")
    if used_jtag:  print(f"    INFO USB-JTAG-pin använd: {sorted(used_jtag)} → { {f: sorted(gpio_owner[f]) for f in used_jtag} }")
    # 5d ogiltigt GPIO-nummer
    bad = [f for f in gpio_owner if f.startswith("GPIO") and int(f[4:]) not in P4_GPIO_RANGE]
    print(f"    ogiltiga GPIO-nr: {bad if bad else 'inga'}")
else:
    print("    (ej P4-kort)")
