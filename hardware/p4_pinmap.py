#!/usr/bin/env python3
"""STRILAS — gemensam P4-pinmap + .net-parser (källa för pinout-verifiering och krets-sim).

Den ENDA sanningskällan för "vilket nät sitter på vilken ESP32-P4-GPIO" är de fysiska
korten: .net-filen ger nät↔(ref,pin) och kant-kontakten landar på en känd Waveshare-stift
(P4A/P4B-tabellerna nedan, identiska för alla kort = samma modul). Vi härleder nät→GPIO ur
.net + kontakt-geometrin och själv-verifierar (VSYS→VBAT, GND→GND osv).

Waveshare ESP32-P4-WIFI6 officiella kant-pinout (verifierad mot datablad/silk; se pinmap_proof.py):
  edge A/B 1-indexerade stift 1..20.
"""
import re

# kanonisk stift→funktion (1-indexerat, samma modul överallt)
EDGE_B = {1: "VBUS", 2: "VSYS", 3: "GND", 4: "EN", 5: "3V3", 6: "GPIO20", 7: "GPIO21",
          8: "GND", 9: "GPIO22", 10: "GPIO23", 11: "RUN", 12: "GPIO26", 13: "GND",
          14: "GPIO27", 15: "GPIO32", 16: "GPIO33", 17: "GPIO46", 18: "GND", 19: "GPIO47", 20: "GPIO48"}
EDGE_A = {1: "GPIO52", 2: "GPIO51", 3: "GND", 4: "GPIO31", 5: "GPIO30", 6: "GPIO29", 7: "GPIO28",
          8: "GND", 9: "GPIO50", 10: "GPIO49", 11: "GPIO5", 12: "GPIO4", 13: "GND", 14: "GPIO3",
          15: "GPIO2", 16: "GPIO8", 17: "GPIO7", 18: "GND", 19: "GPIO24", 20: "GPIO25"}

# ESP32-P4-databladsfakta (verifierat juni 2026 mot Espressif ESP-IDF/datablad):
P4_GPIO_RANGE = range(0, 55)                 # GPIO0..GPIO54 (55 st)
P4_STRAPPING = {34, 35, 36, 37, 38}          # boot-strapping (35/36/37/38 styr bootläge)
P4_USB_JTAG = {24, 25}                        # USB-Serial-JTAG D-/D+ (default). SEKUNDÄRT USB-IF.
P4_USB_OTG_FS = {26, 27}                       # USB-OTG Full-Speed D-/D+ (default). SEKUNDÄRT USB-IF.
# P4:ans PRIMÄRA USB = HS-OTG på DEDIKERADE PHY-stift (ej GPIO-matris) → modulens USB-C för
# programmering/debug påverkas EJ av att GPIO24-27 nyttjas som vanliga GPIO (matrisen tillåter det).
P4_INPUT_ONLY = set()                         # P4 har INGA input-only-pinnar (till skillnad fr klassiska ESP32)
# RESERVED (flash/PSRAM) exponeras EJ på Waveshare-modulens kant → ej i EDGE_A/EDGE_B.

# per kort: vilken kontakt-ref bär vilken kant, och pad k → kant-stift (offset för del-kontakter)
#   full 1x20: pad k → pin k.  weapon (1x14, edge B pin 2..15): pad k → pin k+1.
#   firecontrol (1x15, edge A pin 6..20): pad k → pin k+5.
BOARD_EDGE = {
    "weapon-module": [("J1", EDGE_B, lambda k: k + 1)],
    "firecontrol":   [("J1", EDGE_A, lambda k: k + 5)],
    "helmet-mb":     [("J8", EDGE_B, lambda k: k), ("J9", EDGE_A, lambda k: k)],
    "vest-mb":       [("JA_EDGEB", EDGE_B, lambda k: k), ("JA_EDGEA", EDGE_A, lambda k: k)],
}


def parse_net(path):
    """KiCad .net → (comps, nets). comps[ref]=(value,footprint). nets[name]=[(ref,pin),...]."""
    txt = open(path).read()
    comps = {}
    for block in re.split(r'\n\s*\(comp\b', txt)[1:]:
        ref = re.search(r'\(ref "([^"]+)"\)', block)
        if not ref:
            continue
        val = re.search(r'\(value "([^"]*)"\)', block)
        fp = re.search(r'\(footprint "([^"]*)"\)', block)
        comps[ref.group(1)] = (val.group(1) if val else "", fp.group(1) if fp else "")
    nets = {}
    for block in re.split(r'\n\s*\(net\b', txt)[1:]:
        name = re.search(r'\(name "([^"]+)"\)', block)
        if not name:
            continue
        nodes = re.findall(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', block)
        nets[name.group(1)] = nodes
    return comps, nets


def edge_refs(board, comps):
    """Hitta faktiska kant-kontakt-refs (värdet innehåller 'edge A'/'edge B')."""
    out = {}
    for ref, (val, fp) in comps.items():
        v = val.lower()
        if "edge a" in v:
            out.setdefault("A", []).append(ref)
        elif "edge b" in v and "kraft" not in v:
            out.setdefault("B", []).append(ref)
    return out


def net_to_gpio(board, comps, nets):
    """→ {net: [(ref,pad,pin,func)]} för alla nät som når en P4-kant-GPIO/kraftstift."""
    # bygg ref→pad→net
    refpad = {}
    for net, nodes in nets.items():
        for ref, pin in nodes:
            refpad.setdefault(ref, {})[pin] = net
    er = edge_refs(board, comps)
    cfg = []
    if board == "weapon-module":
        for r in er.get("B", []):
            cfg.append((r, EDGE_B, lambda k: k + 1))
    elif board == "firecontrol":
        for r in er.get("A", []):
            cfg.append((r, EDGE_A, lambda k: k + 5))
    else:  # helmet-mb / vest-mb: full 1x20 A + B
        for r in er.get("A", []):
            cfg.append((r, EDGE_A, lambda k: k))
        for r in er.get("B", []):
            cfg.append((r, EDGE_B, lambda k: k))
    res = {}
    for ref, table, off in cfg:
        pads = refpad.get(ref, {})
        for padstr, net in pads.items():
            try:
                pin = off(int(padstr))
            except ValueError:
                continue
            func = table.get(pin)
            if func:
                res.setdefault(net, []).append((ref, padstr, pin, func))
    return res


if __name__ == "__main__":
    for board in BOARD_EDGE:
        comps, nets = parse_net(f"hardware/{board}.net")
        n2g = net_to_gpio(board, comps, nets)
        print(f"\n===== {board}  ({len(comps)} comps, {len(nets)} nets) =====")
        for net in sorted(n2g):
            for ref, pad, pin, func in n2g[net]:
                print(f"  {func:8} ({ref}.{pad}, pin{pin:>2})  ←  {net}")
