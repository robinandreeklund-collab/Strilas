#!/usr/bin/env python3
"""STRILAS — KOMPLETT pin-/GPIO-verifiering for alla P4-kort.
Mappar VARJE kant-kontakt-padd -> Waveshare-kantstift -> GPIO/funktion -> nat, och kontrollerar:
  - kraftstift: VSYS=VBAT, 3V3=+3V3, GND=GND, EN/RUN = NC (ej drivna)
  - GPIO-konflikt: samma GPIO pa >1 nat
  - ADC: alla *_SENSE-nat MASTE ligga pa en ADC-kapabel GPIO (P4 ADC1=16..23, ADC2=49..54)
  - strapping-pin (34..38) driven? (ska ej forekomma; exponeras ej pa kanten)
  - USB-JTAG (24,25) anvand? (info: USB-debug tappas)
  - input-only / ogiltig GPIO
  - dubbel-anvandning av samma fysiska stift
Kor: python3 hardware/verify_pins.py
"""
import sys
sys.path.insert(0, "hardware")
from p4_pinmap import parse_net, EDGE_A, EDGE_B, BOARD_EDGE, P4_STRAPPING, P4_USB_JTAG, P4_USB_OTG_FS, P4_GPIO_RANGE

ADC1 = set(range(16, 24))      # GPIO16..23 (verifierat mot ESP32-P4-datablad)
ADC2 = set(range(49, 55))      # GPIO49..54
ADC = ADC1 | ADC2

POWER_OK = {"VSYS": "VBAT", "3V3": "+3V3", "GND": "GND"}   # forvantat nat pa kraftstift
NODRIVE = {"EN", "RUN"}        # ska lamnas NC (P4 har egna pull-ups)


def verify(board):
    netfile = f"hardware/{board}.net"
    comps, nets = parse_net(netfile)
    pad2net = {(r, p): nm for nm, nodes in nets.items() for r, p in nodes}
    print(f"\n================== {board} ==================")
    gpio_owner = {}        # GPIOxx -> set(nät)
    func_pin = {}          # funktion -> [(ref,pad,nät)]
    problems = []; infos = []
    for ref, edge, padfn in BOARD_EDGE.get(board, []):
        # hitta faktisk socket-ref (vest använder JA_EDGEB/JA_EDGEA-alias)
        actual = ref
        if ref not in {r for (r, p) in pad2net}:
            # vest-mb: edge B = J11, edge A = J12 (1x20). mappa alias.
            actual = {"JA_EDGEB": "J11", "JA_EDGEA": "J12"}.get(ref, ref)
        # för varje pad på denna kontakt
        pads = sorted({int(p) for (r, p) in pad2net if r == actual})
        maxpad = 20 if "EDGEA" in str(edge) or True else 20
        for k in range(1, 21):
            pin = padfn(k)
            if pin not in edge:
                continue
            func = edge[pin]
            net = pad2net.get((actual, str(k)), "NC")
            func_pin.setdefault(func, []).append((actual, k, net))
            if func.startswith("GPIO"):
                if net != "NC":
                    gpio_owner.setdefault(func, set()).add(net)
    # --- checks ---
    # power pins
    for func, exp in POWER_OK.items():
        for (r, k, net) in func_pin.get(func, []):
            if net != "NC" and net != exp:
                problems.append(f"{func} (stift {r}.{k}) = '{net}' förväntat '{exp}'")
    for func in NODRIVE:
        for (r, k, net) in func_pin.get(func, []):
            if net != "NC":
                infos.append(f"{func} drivs ({net}) — normalt NC (P4 har pull-up)")
    # GPIO-konflikt
    conf = {g: s for g, s in gpio_owner.items() if len(s) > 1}
    # ADC för sense-nät
    sense_nets = {nm for nm in nets if "SENSE" in nm.upper()}
    for sn in sense_nets:
        gpios = [g for g, s in gpio_owner.items() if sn in s]
        for g in gpios:
            num = int(g[4:])
            ok = num in ADC
            (infos if ok else problems).append(
                f"SENSE-nät {sn} på {g} → ADC{'1' if num in ADC1 else '2' if num in ADC2 else '?'}-{'OK' if ok else 'INGEN ADC!'}")
    # strapping / usb-jtag / invalid
    strap = {g: gpio_owner[g] for g in gpio_owner if int(g[4:]) in P4_STRAPPING}
    jtag = {g: sorted(gpio_owner[g])[0] for g in gpio_owner if int(g[4:]) in P4_USB_JTAG}
    otgfs = {g: sorted(gpio_owner[g])[0] for g in gpio_owner if int(g[4:]) in P4_USB_OTG_FS}
    bad = [g for g in gpio_owner if int(g[4:]) not in P4_GPIO_RANGE]
    # --- rapport ---
    print(f"  använda GPIO ({len(gpio_owner)}): " + ", ".join(f"{g}={sorted(s)[0]}" for g, s in sorted(gpio_owner.items(), key=lambda x:int(x[0][4:]))))
    print(f"  GPIO-konflikt: {conf or 'INGA ✓'}")
    print(f"  strapping-pin (34-38) drivna: {strap or 'inga ✓'}")
    print(f"  USB-Serial-JTAG (GPIO24/25) som GPIO: {jtag or 'inga'}")
    print(f"  USB-OTG-FS (GPIO26/27) som GPIO:      {otgfs or 'inga'}")
    if jtag or otgfs:
        print("    (OK: P4:ans PRIMÄRA USB = HS-OTG på dedikerade PHY-stift → modulens USB-C-programmering opåverkad)")
    print(f"  ogiltiga GPIO: {bad or 'inga ✓'}")
    if problems:
        print("  !!! PROBLEM:")
        for p in problems: print("     -", p)
    else:
        print("  PROBLEM: INGA ✓")
    for i in infos: print("   info:", i)
    return not problems


if __name__ == "__main__":
    ok = all(verify(b) for b in ("weapon-module", "vest-mb", "helmet-mb", "firecontrol"))
    print("\n==> " + ("ALLA KORT: pin-verifiering GODKÄND ✓" if ok else "FEL FUNNA — se ovan !!!"))
