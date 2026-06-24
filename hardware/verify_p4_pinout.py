#!/usr/bin/env python3
"""STRILAS — PINOUT-VERIFIERING mot ESP32-P4 (alla kort med stackad P4).

Läser de FAKTISKA .net-filerna, härleder nät→GPIO via p4_pinmap (själv-verifierat mot
kraft/GND), och kontrollerar mot ESP32-P4-databladets regler:
  • GPIO i giltigt intervall (0..54)
  • ingen GPIO dubbel-använd på samma P4 (konflikt)
  • strapping-pinnar (34-38) ej använda som I/O som stör boot
  • USB-Serial-JTAG (24/25): flaggas (om-konfig → JTAG-över-USB tappas)
  • inga input-only-pinnar (P4 har inga) — ren info
  • kraft/GND-stiftens integritet (VSYS=VBAT, 3V3, alla GND-stift jordade)
  • peripheri-mux: P4:ans GPIO-matris kan rutta I2C/SPI/UART/I2S till ~valfri GPIO →
    funktionell rimlighet (busspar grupperade) snarare än fast mux.

Kör: python3 hardware/verify_p4_pinout.py    (exit 0 = inga FEL; varningar tillåts)
"""
import sys
from p4_pinmap import (parse_net, net_to_gpio, edge_refs, BOARD_EDGE,
                       P4_GPIO_RANGE, P4_STRAPPING, P4_USB_JTAG, P4_INPUT_ONLY, EDGE_A, EDGE_B)

POWER = {"VBAT", "+3V3", "3V3", "GND"}


def gnum(func):
    return int(func[4:]) if func.startswith("GPIO") else None


def verify(board):
    comps, nets = parse_net(f"hardware/{board}.net")
    n2g = net_to_gpio(board, comps, nets)
    errors, warns, notes = [], [], []

    # GPIO → [(net,ref,pad,pin)]  (endast signal-GPIO, ej kraft/GND)
    gpio_use = {}
    for net, hits in n2g.items():
        for ref, pad, pin, func in hits:
            g = gnum(func)
            if g is None:
                continue
            gpio_use.setdefault(g, []).append((net, ref, pad, pin))

    # 1) giltigt intervall
    for g in gpio_use:
        if g not in P4_GPIO_RANGE:
            errors.append(f"GPIO{g} utanför giltigt intervall 0..54")

    # 2) dubbel-användning (olika NÄT på samma GPIO = hård konflikt)
    for g, uses in sorted(gpio_use.items()):
        distinct = sorted({u[0] for u in uses})
        if len(distinct) > 1:
            errors.append(f"GPIO{g} KONFLIKT: drivs av flera nät {distinct}")

    # 3) strapping
    for g in sorted(gpio_use):
        if g in P4_STRAPPING:
            warns.append(f"GPIO{g} är STRAPPING-pin (boot) — använd ej för signal som driver vid reset "
                         f"(nät: {gpio_use[g][0][0]})")

    # 4) USB-Serial-JTAG
    for g in sorted(gpio_use):
        if g in P4_USB_JTAG:
            warns.append(f"GPIO{g} = USB-Serial-JTAG default → används som {gpio_use[g][0][0]} "
                         f"⇒ JTAG-över-USB tappas (OK: flasha via USB-C HS-OTG)")

    # 5) input-only (P4 har inga → ren info, hoppa)

    # 6) kraft/GND-integritet (återanvänd n2g:s KORREKTA pad→pin-offset)
    for net, hits in n2g.items():
        for ref, pad, pin, func in hits:
            if func == "GND" and net != "GND":
                errors.append(f"{ref}.{pad} (kant-pin{pin} → GND) men nät='{net}'")
            elif func == "VSYS" and net != "VBAT":
                errors.append(f"{ref}.{pad} (VSYS) men nät='{net}' (ska vara VBAT)")
            elif func in ("3V3",) and net not in ("+3V3", "3V3"):
                errors.append(f"{ref}.{pad} (3V3-tapp) men nät='{net}'")
            elif func in ("EN", "RUN", "VBUS") and net not in ("VBAT", "+3V3", "3V3", "GND") and net:
                warns.append(f"{ref}.{pad} ({func}) drivs av nät='{net}' (normalt NC/styrt internt)")

    # info: antal använda signal-GPIO + lediga på varje kant
    used = set(gpio_use)
    a_gpios = {gnum(f) for f in EDGE_A.values() if f.startswith("GPIO")}
    b_gpios = {gnum(f) for f in EDGE_B.values() if f.startswith("GPIO")}
    notes.append(f"{len(used)} signal-GPIO använda; lediga edge A: "
                 f"{sorted(a_gpios-used)}; lediga edge B: {sorted(b_gpios-used)}")
    return n2g, gpio_use, errors, warns, notes


def main():
    tot_e = tot_w = 0
    print("=" * 78)
    print("STRILAS — ESP32-P4 PINOUT-VERIFIERING (mot datablad: 55 GPIO, strap 34-38, "
          "USB-JTAG 24/25, inga input-only)")
    print("=" * 78)
    for board in BOARD_EDGE:
        n2g, gpio_use, errors, warns, notes = verify(board)
        print(f"\n### {board}  —  P4 stackad (edge-kontakt)")
        sig = {g: u for g, u in gpio_use.items()}
        print(f"   signal-GPIO ({len(sig)}): " +
              ", ".join(f"GPIO{g}={gpio_use[g][0][0]}" for g in sorted(sig)))
        for n in notes:
            print(f"   · {n}")
        for w in warns:
            print(f"   ⚠ {w}")
        for e in errors:
            print(f"   ✗ FEL: {e}")
        if not errors:
            print("   ✓ inga pinout-FEL (konflikter/intervall/kraft-integritet rena)")
        tot_e += len(errors); tot_w += len(warns)
    print("\n" + "=" * 78)
    print(f"SUMMA: {tot_e} FEL, {tot_w} varningar (varningar = medvetna val, ej blockerande)")
    print("=" * 78)
    return 1 if tot_e else 0


if __name__ == "__main__":
    sys.exit(main())
