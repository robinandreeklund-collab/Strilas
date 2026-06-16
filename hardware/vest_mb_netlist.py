#!/usr/bin/env python3
"""STRILAS — VÄST-MODERKORT (väst-nod), v2 m. ESP32-C6-devkit. SKiDL → 'hardware/vest-mb.net'.
Alla 10 patchar + 10 zon-vibratorer pluggas in; trådlöst mot vapnets P4 (WiFi6). 4-lager.

ARKITEKTUR (verifierad mot datablad):
  • ESP: stackad ESP32-C6-DevKitC-1 (Waveshare N16, samma som hjälm-mb → WiFi6 genomgående, enkel source;
    23 GPIO). 2× 1x16-header (samma pinout som hjälm-mb). Matas från kortets 3V3.
  • 2S-batteri → AP63203-buck → 3,3 V @2A (C6 + ERM-motorer). VBAT(2S) → patchar (konstellation-LED).
  • 10× patch-DATA (aktiv-låg) läses DIREKT på C6-GPIO (23 GPIO → ingen 74HC165 behövs).
  • 10× VIB (zon-vibrator) via 2× TPIC6B595 power-shift (open-drain 150 mA/kanal): SER/SRCK/RCK (3 GPIO).
  • LED_EN broadcast (1 GPIO) → alla patchars konstellation. Ingen haptik-mik/ljud (väst = vibratorer).
  • Zon-kontakt 1x6: VBAT·GND·DATA·LED_EN·3V3·VIB. GPIO: 10 DATA + TPIC3 + LED_EN1 = 14 av 23.
"""
from skidl import Part, Pin, Net, generate_netlist, SKIDL, TEMPLATE, reset


def mk(name, ref, pins, fp, value=""):
    p = Part(tool=SKIDL, name=name, ref_prefix=ref, dest=TEMPLATE)
    p.add_pins(*[Pin(num=str(n), name=str(nm)) for n, nm in pins])
    p.footprint = fp
    if value: p.value = value
    return p


reset()
BUCK = mk("AP63203", "U", [(1, "FB"), (2, "EN"), (3, "VIN"), (4, "GND"), (5, "SW"), (6, "BST")],
          "Package_TO_SOT_SMD:TSOT-23-6", "AP63203")
IND = mk("L", "L", [(1, "1"), (2, "2")], "Inductor_SMD:L_Changjiang_FNR5040S", "4.7uH")
TPIC = mk("TPIC6B595", "U", [(1, "NC1"), (2, "VCC"), (3, "SERIN"), (4, "D0"), (5, "D1"), (6, "D2"),
          (7, "D3"), (8, "SRCLRn"), (9, "Gn"), (10, "GND"), (11, "GND2"), (12, "RCK"), (13, "SRCK"),
          (14, "D4"), (15, "D5"), (16, "D6"), (17, "D7"), (18, "SEROUT"), (19, "GND3"), (20, "NC2")],
          "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm", "TPIC6B595")
SOCK16 = mk("Conn_1x16", "J", [(i, i) for i in range(1, 17)], "Connector_PinSocket_2.54mm:PinSocket_1x16_P2.54mm_Vertical", "ESP32-C6 1x16 sockel")
ZONE = mk("Zone_1x06", "J", [(1, "VBAT"), (2, "GND"), (3, "DATA"), (4, "LED_EN"), (5, "P3V3"), (6, "VIB")],
          "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", "Zon: VBAT·GND·DATA·LED_EN·3V3·VIB")
BATT = mk("BATT_2S", "J", [(1, "VBAT"), (2, "GND")], "Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal", "2S batteri")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v: RES_T(value=v)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
MH = mk("MH", "H", [(1, "1")], "MountingHole:MountingHole_2.5mm", "M2.5")

# ---------- nät ----------
VBAT, GND, P3V3 = Net("VBAT"), Net("GND"), Net("+3V3")
SW, BST, FB = Net("SW"), Net("BST"), Net("FB")
TSER, TSRCK, TRCK, LED_EN = Net("TPIC_SER"), Net("TPIC_SRCK"), Net("TPIC_RCK"), Net("LED_EN")
DATA = [Net(f"DATA{i+1}") for i in range(10)]
VIB = [Net(f"VIB{i+1}") for i in range(10)]
CHAINTPIC = Net("TPIC_CHAIN")

# ---------- buck 2S → 3,3 V ----------
Ubk = BUCK()
Ubk["VIN"] += VBAT; Ubk["EN"] += VBAT; Ubk["GND"] += GND; Ubk["SW"] += SW; Ubk["BST"] += BST; Ubk["FB"] += FB
L1 = IND(); L1[1] += SW; L1[2] += P3V3
Cbst = CAP("100nF"); Cbst[1] += SW; Cbst[2] += BST
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric"); Cin[1] += VBAT; Cin[2] += GND
Cout = CAP("22uF", "Capacitor_SMD:C_1206_3216Metric"); Cout[1] += P3V3; Cout[2] += GND
Rt = RES("31.6k"); Rb = RES("10k"); Rt[1] += P3V3; Rt[2] += FB; Rb[1] += FB; Rb[2] += GND
Cbulk = CAP("100uF", "Capacitor_SMD:C_1210_3225Metric"); Cbulk[1] += P3V3; Cbulk[2] += GND  # ERM-pulsreservoar

# ---------- 2× TPIC6B595: driv 10 VIB ----------
Ut1 = TPIC(); Ut2 = TPIC()
for u in (Ut1, Ut2):
    u["VCC"] += P3V3; u["GND"] += GND; u["GND2"] += GND; u["GND3"] += GND
    u["SRCK"] += TSRCK; u["RCK"] += TRCK; u["Gn"] += GND; u["SRCLRn"] += P3V3
for i, pin in enumerate(["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]):
    Ut1[pin] += VIB[i]
Ut2["D0"] += VIB[8]; Ut2["D1"] += VIB[9]
Ut1["SERIN"] += TSER; Ut1["SEROUT"] += CHAINTPIC; Ut2["SERIN"] += CHAINTPIC
Cdt1 = CAP("100nF"); Cdt1[1] += P3V3; Cdt1[2] += GND
Cdt2 = CAP("100nF"); Cdt2[1] += P3V3; Cdt2[2] += GND

# ---------- 10× zon-kontakt (patch + vibrator) ----------
for i in range(10):
    z = ZONE()
    z["VBAT"] += VBAT; z["GND"] += GND; z["DATA"] += DATA[i]
    z["LED_EN"] += LED_EN; z["P3V3"] += P3V3; z["VIB"] += VIB[i]

# ---------- stackad ESP32-C6-DevKitC-1 (2× 1x16) ----------
# J1: 1=3V3 2=RST 3=GPIO4 4=GPIO5 5=GPIO6 6=GPIO7 7=GPIO0 8=GPIO1 9=GPIO8(strap) 10=GPIO10 11=GPIO11 12=GPIO2 13=GPIO3 14=5V 15=GND 16=NC
JC1 = SOCK16()
JC1[1] += P3V3; JC1[15] += GND; JC1[14] += Net("NC_5V")
JC1[3] += DATA[0]; JC1[4] += DATA[1]; JC1[5] += DATA[2]; JC1[6] += DATA[3]   # GPIO4/5/6/7
JC1[7] += DATA[4]; JC1[8] += DATA[5]; JC1[10] += DATA[6]; JC1[11] += DATA[7]  # GPIO0/1/10/11
JC1[12] += DATA[8]; JC1[13] += DATA[9]                                       # GPIO2/3  (10 DATA direkt)
# J3: 1=GND 2=GPIO16(TX) 3=GPIO17(RX) 4=GPIO15(strap) 5=GPIO23 6=GPIO22 7=GPIO21 8=GPIO20 9=GPIO19 10=GPIO18 11=GPIO9(strap) 12=GND 13=GPIO13(USB) 14=GPIO12(USB) 15=GND 16=NC
JC3 = SOCK16()
JC3[1] += GND; JC3[12] += GND; JC3[15] += GND
JC3[2] += TSER     # GPIO16 → TPIC SER
JC3[3] += TSRCK    # GPIO17 → TPIC SRCK
JC3[5] += TRCK     # GPIO23 → TPIC RCK
JC3[6] += LED_EN   # GPIO22 → konstellation broadcast

# ---------- batteri + monteringshål ----------
Jb = BATT(); Jb["VBAT"] += VBAT; Jb["GND"] += GND
for _ in range(4):
    MH()[1] += GND

generate_netlist(file_="hardware/vest-mb.net")
print("wrote hardware/vest-mb.net (väst-mb v2: ESP32-C6 + buck + 2×TPIC6B595 + 10 zon-kontakter, DATA direkt)")
