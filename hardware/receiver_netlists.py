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
        # TSOP4856 = LEDAD (genomplåt) 3-bens IR-mottagare (Vishay doc 82459, 6,0×6,95×5,6, AGC2).
        # MOLD-footprint (rätt storlek). Benen BÖJS för att rikta domen (3 åt sidan + 1 rakt upp/patch).
        TSOP=mk("TSOP4856", "U", [(1, "OUT"), (2, "GND"), (3, "VS")], "OptoDevice:Vishay_MOLD-3Pin", "TSOP4856"),
        LED=mk("L1I0", "D", [(1, "A"), (2, "K")], "strilas:L1I0_IR", "L1I0-0850090200000"),
        LEDTAB=mk("LED_TAB", "D", [(1, "A"), (2, "K")], "strilas:LED_Tab", "LED-tab (L1I0-micro-PCB, ben böjs 40° UT som TSOP)"),
        ORD=mk("ORdiode", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SOD-123", "BAT54"),
        NFET=mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400"),
        # OPA171 (SOT-23-5 DBV) konstantströms-op-amp (TI SBOS516H): 1=OUT 2=V- 3=IN+ 4=IN- 5=V+.
        OPAMP=mk("OPA171", "U", [(1, "OUT"), (2, "V-"), (3, "IN+"), (4, "IN-"), (5, "V+")],
                 "Package_TO_SOT_SMD:SOT-23-5", "OPA171"),
        # 3,3 V LDO för TSOP+logik. SOT-89 pin (Holtek HT73XX datablad): 1=GND 2=VIN(tab) 3=VOUT.
        LDO=mk("HT7333-A", "U", [(1, "GND"), (2, "VIN"), (3, "VOUT")], "Package_TO_SOT_SMD:SOT-89-3", "HT7333-A"),
        R=mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric"),
        C=mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric", "100nF"),
        J=mk("Conn_1x06", "J", [(i, i) for i in range(1, 7)], "Connector_JST:JST_PH_S6B-PH-K_1x06_P2.00mm_Horizontal", "VBAT·GND·DATA·LED_EN·3V3·VIB"),
        MOT=mk("Motor_2pin", "J", [(1, "+"), (2, "-")], "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", "ERM-motor 2-pol JST (+3V3/VIB)"),
        UFL=mk("U.FL", "J", [(1, "S"), (2, "G")], "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", "GNSS"),
        MH=mk("MH", "H", [(1, "1")], "MountingHole:MountingHole_2.2mm_M2", "M2"),
    )


def build(n_tsop, n_led, gnss, out_file, n_tab=0):
    reset()
    P = defs()
    VBAT, GND, DATA, LED_EN, LEDC = Net("VBAT"), Net("GND"), Net("DATA"), Net("LED_EN"), Net("LED_CATH")
    P3V3 = Net("+3V3")                                                # 3,3 V från moderkortet (via kontakt)
    VIB = Net("VIB")                                                  # vibrator-retur (moderkortets TPIC låg-sida)
    J1 = P["J"]()                                                    # 6-pol → matchar moderkortets zon-kontakt
    J1[1] += VBAT; J1[2] += GND; J1[3] += DATA; J1[4] += LED_EN; J1[5] += P3V3; J1[6] += VIB  # 3V3+VIB från moderkort
    # ERM-coin-vibrationsmotor (3 V): pluggas in via 2-pol JST (J2) — EJ SMD-lödd. + → 3V3 (EJ VBAT/8,4V!),
    # − → VIB. Moderkortets TPIC6B595 drar VIB→GND (PWM=styrka); TPIC:ns inbyggda klampdiod tar flyback.
    # Motorkroppen (Ø10 coin) fästs med sin 3M-tejp inom keepout-ringen på BAKSIDAN (mekanisk markering,
    # ingen koppar under → höljet kortsluts ej). DELAD PATCH (×14): VÄST pluggar in motorn + 6-trådskabel
    # (VIB driven). HJÄLM = SAMMA kort, J2 obestyckad/tom + VIB-pin NC (5-tråds kabel) → hjälm-mb oförändrad.
    J2 = P["MOT"](); J2.ref = "J2"; J2["+"] += P3V3; J2["-"] += VIB
    Rpu = P["R"](value="10k"); Rpu[1] += P3V3; Rpu[2] += DATA         # DATA pullup → 3V3 → 3,3 V-logik
    Cb = P["C"](value="10uF", footprint="Capacitor_SMD:C_1206_3216Metric"); Cb[1] += VBAT; Cb[2] += GND  # LED-bulk på VBAT
    # TSOP-array + diod-OR  (TSOP matas från +3V3, EJ VBAT — abs-max VS = 6 V)
    for i in range(n_tsop):
        s = P["TSOP"](); out = Net(f"OUT{i+1}")
        s["VS"] += P3V3; s["GND"] += GND; s["OUT"] += out
        d = P["ORD"](); d["K"] += out; d["A"] += DATA                 # diod-OR (active-low)
        cd = P["C"](); cd[1] += P3V3; cd[2] += GND                    # TSOP-avkoppling på 3V3
    # konstellations-LED + FIRMWARE-TRIMBAR AKTIV KONSTANTSTRÖMS-SÄNKA (samma topologi som vapnet).
    # I = Vref/Rsense, BATTERI-OBEROENDE. Vref kommer från LED_EN (moderkortets broadcast-GPIO) som
    # nu körs som FILTRERAD LEDC-PWM: RC (R8·15k ∥ R9·1k + C6·100nF, ~94µs) släpper blink (≤120 Hz,
    # kamera-fps) men filtrerar PWM-bärvågen → analog setpunkt. Delaren 15k/1k SKALAR + är HÅRT TAK:
    # Vref_max = 3,3·1/16 = 0,206 V → I_max = 0,206/Rsense. R6=0R2 → 1,0 A (säker default, levereras så).
    # Firmware sätter PWM-duty 0–100 % → I 0–1,0 A STEGLÖST (kan ALDRIG överstiga taket → eye-safety-
    # regel #1 i HÅRDVARA). 3A-OVERRIDE: montera DNP R7=0R1 parallellt över R6 → 0,2∥0,1=0,067 Ω →
    # I_max ≈ 3 A (medvetet, lab; kräver IEC 60825-1-ommätning + branch-R-termik-koll, se eye-safety-budget.md).
    # 850 nm Lumileds L1I0-0850090200000 (LUXEON IR Domed, 90°, ~750 mW/sr@1A ≈ 2× VSMY, 1,5 A DC-rating,
    # Vf ~3,2 V@1A) — kamera-markör. Starkare än VSMY → når räckvidd vid lägre ström (eye-safe-marginal).
    Uop = P["OPAMP"]()                                               # U5 = OPA171 (CC-op-amp)
    SENSE = Net("IDRV_SENSE"); GATE = Net("LED_GATE"); VREF = Net("IDRV_REF")
    Q = P["NFET"](); Q["D"] += LEDC; Q["S"] += SENSE; Q["G"] += GATE  # Q1 = pass-FET (låg-sida)
    Uop["IN+"] += VREF; Uop["IN-"] += SENSE; Uop["V+"] += VBAT; Uop["V-"] += GND
    Rg = P["R"](value="100R"); Rg[1] += Uop["OUT"]; Rg[2] += GATE    # R2 = gate-R (stabilitet)
    # LED-grenar (serie-par): VBAT → Rbal → LED → LED → LED_CATH → Q1(pass-FET) → SENSE → R6 → GND.
    # CC-sänkan sätter TOTAL ström; Rbal (R3-R5, 1R 1206) balanserar bara grenarna (ej strömsättning).
    leds = [P["LED"]() for _ in range(n_led)] + [P["LEDTAB"]() for _ in range(n_tab)]
    for i in range(0, len(leds) - 1, 2):
        rl = P["R"](value="1R", footprint="Resistor_SMD:R_1206_3216Metric")
        a = Net(f"LED_A{i//2+1}"); mid = Net(f"LED_M{i//2+1}")
        rl[1] += VBAT; rl[2] += a
        leds[i]["A"] += a;   leds[i]["K"] += mid
        leds[i+1]["A"] += mid; leds[i+1]["K"] += LEDC
    if len(leds) % 2:                                                # udda LED → egen gren
        rl = P["R"](value="1R", footprint="Resistor_SMD:R_1206_3216Metric")
        a = Net(f"LED_A{len(leds)//2+1}"); rl[1] += VBAT; rl[2] += a
        leds[-1]["A"] += a; leds[-1]["K"] += LEDC
    # CC-sänkans sense + referens (instansieras EFTER branch-R → branch = R3-R5, dessa R6-R9)
    Rsense = P["R"](value="0R2", footprint="Resistor_SMD:R_1206_3216Metric"); Rsense[1] += SENSE; Rsense[2] += GND  # R6: I=Vref/0R2 → 1A@0,206V
    Rovr = P["R"](value="0R1 DNP=1A/montera=3A"); Rovr[1] += GND; Rovr[2] += SENSE   # R7: 3A-override (DNP, parallellt över R6)
    Rda = P["R"](value="15k"); Rda[1] += LED_EN; Rda[2] += VREF      # R8: skal/tak-delare topp (LED_EN-PWM in)
    Rdb = P["R"](value="1k"); Rdb[1] += VREF; Rdb[2] += GND          # R9: skal/tak-delare botten → Vref=LED_EN·1/16
    Cf = P["C"](value="100nF"); Cf[1] += VREF; Cf[2] += GND          # C6: RC-filter (PWM→analog setpunkt)
    # (Ingen LDO — 3,3 V från moderkortet.) 4 monteringshål (M2.5) i hörnen → skruv/standoff-fäste
    # som komplement till lim/kardborre (t.ex. patch skruvad mot hjälmskal/styv platta).
    for _ in range(4):
        P["MH"]()[1] += GND
    generate_netlist(file_=out_file)
    print(f"  {out_file}: {n_tsop} TSOP, {n_led} fasta LED + {n_tab} LED-tabbar, 4 monteringshål")


if __name__ == "__main__":
    # väst-patch: 4 TSOP (hörn, 40° ut) + 2 fasta LED (centralt, inåt) + 4 böjbara LED-tabbar
    # (kanter N/S/Ö/V, böjs 40° ut som TSOP) → allround konstellation från alla vinklar.
    build(4, 2, False, "hardware/vest-patch.net", n_tab=4)
    # hjälm-noden byggs nu av hardware/helmet_netlist.py (komplett nod: buck+XIAO-S3+GNSS+audio)
