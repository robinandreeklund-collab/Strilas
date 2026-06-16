#!/usr/bin/env python3
"""STRILAS — receiver-kort (väst-patch + hjälm-halo): netlistor i kod (SKiDL → KiCad).
Genererar vest-patch.net + helmet-halo.net. TSOP OR:as via dioder → 1 DATA-linje;
850 nm-konstellation drivs av N-FET (LED_EN); hjälm har GNSS U.FL. → place + route → Gerbers.
"""
from skidl import Part, Pin, Net, generate_netlist, SKIDL, TEMPLATE, reset


def mk(name, ref, pins, fp, value=""):
    p = Part(tool=SKIDL, name=name, ref_prefix=ref, dest=TEMPLATE)
    p.add_pins(*[Pin(num=str(n), name=str(nm)) for n, nm in pins])
    p.footprint = fp
    if value: p.value = value
    return p


def defs():
    return dict(
        TSOP=mk("TSOP4856", "U", [(1, "OUT"), (2, "GND"), (3, "VS")], "OptoDevice:Vishay_MINIMOLD-3Pin", "TSOP4856"),
        LED=mk("LED850", "D", [(1, "A"), (2, "K")], "LED_SMD:LED_1206_3216Metric", "850nm"),
        ORD=mk("ORdiode", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SOD-123", "BAT54"),
        NFET=mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400"),
        R=mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric"),
        C=mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric", "100nF"),
        J=mk("Conn_1x04", "J", [(i, i) for i in range(1, 5)], "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "VBAT·GND·DATA·LED_EN"),
        UFL=mk("U.FL", "J", [(1, "S"), (2, "G")], "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", "GNSS"),
        MH=mk("MH", "H", [(1, "1")], "MountingHole:MountingHole_2.5mm", "M2.5"),
    )


def build(n_tsop, n_led, gnss, out_file):
    reset()
    P = defs()
    VBAT, GND, DATA, LED_EN, LEDC = Net("VBAT"), Net("GND"), Net("DATA"), Net("LED_EN"), Net("LED_CATH")
    J1 = P["J"]()
    J1[1] += VBAT; J1[2] += GND; J1[3] += DATA; J1[4] += LED_EN
    Rpu = P["R"](value="10k"); Rpu[1] += VBAT; Rpu[2] += DATA          # DATA pullup
    Cb = P["C"](value="10uF", footprint="Capacitor_SMD:C_1206_3216Metric"); Cb[1] += VBAT; Cb[2] += GND
    # TSOP-array + diod-OR
    for i in range(n_tsop):
        s = P["TSOP"](); out = Net(f"OUT{i+1}")
        s["VS"] += VBAT; s["GND"] += GND; s["OUT"] += out
        d = P["ORD"](); d["K"] += out; d["A"] += DATA                 # diod-OR (active-low)
        cd = P["C"](); cd[1] += VBAT; cd[2] += GND                    # avkoppling/TSOP
    # konstellations-LED + driver
    Q = P["NFET"](); Q["S"] += GND; Q["D"] += LEDC
    Rg = P["R"](value="220R"); Rg[1] += LED_EN; Rg[2] += Q["G"]
    for i in range(n_led):
        led = P["LED"](); rl = P["R"](value="100R")
        rl[1] += VBAT; rl[2] += led["A"]; led["K"] += LEDC
    # GNSS U.FL (hjälm)
    if gnss:
        u = P["UFL"](); u["S"] += Net("GNSS_RF"); u["G"] += GND
    # monteringshål
    for _ in range(4):
        P["MH"]()[1] += GND
    generate_netlist(file_=out_file)
    print(f"  {out_file}: {n_tsop} TSOP, {n_led} LED" + (", GNSS U.FL" if gnss else ""))


if __name__ == "__main__":
    build(3, 2, False, "hardware/vest-patch.net")     # väst-patch
    build(8, 4, True, "hardware/helmet-halo.net")     # hjälm-halo
