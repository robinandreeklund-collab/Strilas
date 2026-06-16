#!/usr/bin/env python3
"""STRILAS — receiver-kort (väst-patch + hjälm-halo): netlistor i kod (SKiDL → KiCad).
Genererar vest-patch.net + helmet-halo.net. TSOP OR:as via dioder → 1 DATA-linje;
860 nm-konstellation (SFH 4715AS) drivs av N-FET (LED_EN); hjälm har GNSS U.FL. → place + route → Gerbers.

KRAFTARKITEKTUR (verifierad mot datablad):
  J1 bär VBAT (2S, 7,4–8,4 V) → matar BARA konstellations-LED-grenarna (SFH 4715AS, ~0,5 A/gren).
  En lokal LDO (HT7333-A, SOT-89, Vin≤12 V → 2S OK) gör +3V3 som matar TSOP4856 (abs-max VS=6 V!)
  och DATA-pullupen → DATA blir ren 3,3 V-logik mot väst-noden. (TSOP tål EJ 2S direkt — därför LDO.)
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
        LED=mk("SFH4715AS", "D", [(1, "A"), (2, "K")], "strilas:IR_Emitter_OSRAM_OSLON_Black_SFH4725S", "SFH4715AS_860nm"),
        ORD=mk("ORdiode", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SOD-123", "BAT54"),
        NFET=mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400"),
        # 3,3 V LDO för TSOP+logik. SOT-89 pin (Holtek HT73XX datablad): 1=GND 2=VIN(tab) 3=VOUT.
        LDO=mk("HT7333-A", "U", [(1, "GND"), (2, "VIN"), (3, "VOUT")], "Package_TO_SOT_SMD:SOT-89-3", "HT7333-A"),
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
    P3V3 = Net("+3V3")                                                # lokal logik-rail (LDO-utgång)
    J1 = P["J"]()
    J1[1] += VBAT; J1[2] += GND; J1[3] += DATA; J1[4] += LED_EN
    Rpu = P["R"](value="10k"); Rpu[1] += P3V3; Rpu[2] += DATA         # DATA pullup → 3V3 (EJ VBAT) → 3,3 V-logik
    Cb = P["C"](value="10uF", footprint="Capacitor_SMD:C_1206_3216Metric"); Cb[1] += VBAT; Cb[2] += GND  # LED-bulk på VBAT
    # TSOP-array + diod-OR  (TSOP matas från +3V3, EJ VBAT — abs-max VS = 6 V)
    for i in range(n_tsop):
        s = P["TSOP"](); out = Net(f"OUT{i+1}")
        s["VS"] += P3V3; s["GND"] += GND; s["OUT"] += out
        d = P["ORD"](); d["K"] += out; d["A"] += DATA                 # diod-OR (active-low)
        cd = P["C"](); cd[1] += P3V3; cd[2] += GND                    # TSOP-avkoppling på 3V3
    # konstellations-LED + driver
    Q = P["NFET"](); Q["S"] += GND; Q["D"] += LEDC
    Rg = P["R"](value="220R"); Rg[1] += LED_EN; Rg[2] += Q["G"]
    # konstellation = högeffekt 860 nm OSLON SFH 4715AS (Ie 780 mW/sr @1A databl.) för 150 m dagsljus.
    # Serieresistor 10R 2512 → ~0,4–0,5 A/LED vid VBAT 2S. OBS blink-modulerad: max ~50 % duty
    # (annars 2,5 W topp i 2 W-motstånd). LED-näten breddas till 0,4 mm via dsn_power_class.
    for i in range(n_led):
        led = P["LED"](); rl = P["R"](value="10R", footprint="Resistor_SMD:R_2512_6332Metric")
        a = Net(f"LED_A{i+1}")                                        # namngivet LED-anodnät (för power-klass)
        rl[1] += VBAT; rl[2] += a; led["A"] += a; led["K"] += LEDC
    # lokal 3,3 V LDO (HT7333-A): VBAT → +3V3 för TSOP + DATA-pullup. Vin 2S < 12 V abs-max.
    ldo = P["LDO"](); ldo["VIN"] += VBAT; ldo["GND"] += GND; ldo["VOUT"] += P3V3
    cin = P["C"](value="1uF"); cin[1] += VBAT; cin[2] += GND          # LDO-in
    cout = P["C"](value="10uF", footprint="Capacitor_SMD:C_1206_3216Metric"); cout[1] += P3V3; cout[2] += GND  # LDO-ut (stabilitet)
    # GNSS U.FL (hjälm)
    if gnss:
        u = P["UFL"](); u["S"] += Net("GNSS_RF"); u["G"] += GND
    # monteringshål
    for _ in range(4):
        P["MH"]()[1] += GND
    generate_netlist(file_=out_file)
    print(f"  {out_file}: {n_tsop} TSOP, {n_led} LED, LDO HT7333-A" + (", GNSS U.FL" if gnss else ""))


if __name__ == "__main__":
    build(3, 2, False, "hardware/vest-patch.net")     # väst-patch
    build(8, 4, True, "hardware/helmet-halo.net")     # hjälm-halo
