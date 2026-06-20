#!/usr/bin/env python3
"""STRILAS — VÄST-MODERKORT (väst-nod), v3 m. ESP32-P4-WIFI6. SKiDL → 'hardware/vest-mb.net'.
Alla 10 patchar + 10 zon-vibratorer pluggas in; trådlöst mot vapnets P4 (WiFi6). 4-lager.

ARKITEKTUR (verifierad mot datablad):
  • ESP: stackad ESP32-P4-WIFI6 (Waveshare) — SAMMA kort som vapnet + hjälm-mb → en enda source,
    enkelt underhåll. 2× 1x20 kant-sockel (edge A = signaler, edge B = kraft-tapp). P4 självförsörjer
    via VSYS=VBAT (onboard MP1658-buck). ~40 GPIO → gott om plats för 10 DATA direkt + TPIC.
  • 2S-batteri → AP63203 carrier-buck → 3,3 V @2A (TPIC-logik + ERM-motorer + patchars 3V3-rail).
    P4 matas separat via edge-B VSYS=VBAT.
  • 10× patch-DATA (aktiv-låg) läses DIREKT på P4-GPIO (rikligt med GPIO → ingen 74HC165 behövs).
  • 10× VIB (zon-vibrator) via 2× TPIC6B595 power-shift (open-drain 150 mA/kanal): SER/SRCK/RCK (3 GPIO).
  • LED_EN broadcast (1 GPIO) → alla patchars konstellation. Ingen haptik-mik/ljud (väst = vibratorer).
  • Zon-kontakt 1x6: VBAT·GND·DATA·LED_EN·3V3·VIB. GPIO: 10 DATA + 3 TPIC + LED_EN = 14 (edge A: 16 sign).
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
# ESP32-P4-WIFI6 (Waveshare) — 2× 1x20 kant-sockel. Pinout verifierad mot Waveshares datablad.
# P4 självförsörjer via VSYS; carrier-buck ger 3V3 för last (TPIC/ERM/patch-rail).
P4B = mk("P4_EDGE_B", "J", [(1, "VBUS"), (2, "VSYS"), (3, "GND"), (4, "EN"), (5, "P3V3"), (6, "GPIO20"),
         (7, "GPIO21"), (8, "GNDb"), (9, "GPIO22"), (10, "GPIO23"), (11, "RUN"), (12, "GPIO26"),
         (13, "GNDc"), (14, "GPIO27"), (15, "GPIO32"), (16, "GPIO33"), (17, "GPIO46"), (18, "GNDd"),
         (19, "GPIO47"), (20, "GPIO48")], "Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical", "P4-WIFI6 edge B")
P4A = mk("P4_EDGE_A", "J", [(1, "GPIO52"), (2, "GPIO51"), (3, "GND"), (4, "GPIO31"), (5, "GPIO30"),
         (6, "GPIO29"), (7, "GPIO28"), (8, "GNDb"), (9, "GPIO50"), (10, "GPIO49"), (11, "GPIO5"),
         (12, "GPIO4"), (13, "GNDc"), (14, "GPIO3"), (15, "GPIO2"), (16, "GPIO8"), (17, "GPIO7"),
         (18, "GNDd"), (19, "GPIO24"), (20, "GPIO25")], "Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical", "P4-WIFI6 edge A")
ZONE = mk("Zone_1x06", "J", [(1, "VBAT"), (2, "GND"), (3, "DATA"), (4, "LED_EN"), (5, "P3V3"), (6, "VIB")],
          "Connector_JST:JST_PH_S6B-PH-K_1x06_P2.00mm_Horizontal", "Zon: VBAT·GND·DATA·LED_EN·3V3·VIB")
# OBS POLARITET: AMASS XT30PW-M-footprinten har pin 1 = "−" (rect-pad, silk −) och pin 2 = "+" (silk +).
# Därför pin1=GND, pin2=VBAT — annars kopplas batteriets plus till minus-terminalen (omvänd polaritet).
BATT = mk("BATT_2S", "J", [(1, "GND"), (2, "VBAT")], "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal", "2S batteri XT30 (≥15A)")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v: RES_T(value=v)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
MH = mk("MH", "H", [(1, "1")], "MountingHole:MountingHole_2.5mm", "M2.5")
PFET = mk("AOD4185", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:TO-252-2", "AOD4185A")
TVS  = mk("SMBJ12A", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SMB", "SMBJ12A")
PWRSW = mk("PWR_SW", "J", [(1, "GATE"), (2, "GND")], "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", "Strombrytare (extern SPST)")
TP   = mk("TestPoint", "TP", [(1, "1")], "TestPoint:TestPoint_Pad_D1.5mm", "TP")

# ---------- nät ----------
VBAT, GND, P3V3 = Net("VBAT"), Net("GND"), Net("+3V3")
SW, BST, FB = Net("SW"), Net("BST"), Net("FB")
TSER, TSRCK, TRCK, LED_EN = Net("TPIC_SER"), Net("TPIC_SRCK"), Net("TPIC_RCK"), Net("LED_EN")
DATA = [Net(f"DATA{i+1}") for i in range(10)]
VIB = [Net(f"VIB{i+1}") for i in range(10)]
CHAINTPIC = Net("TPIC_CHAIN")
VBAT_RAW, PGATE, VBAT_SENSE = Net("VBAT_RAW"), Net("PGATE"), Net("VBAT_SENSE")

# ---------- carrier-buck 2S → 3,3 V (TPIC/ERM/patch-rail; P4 självförsörjer via VSYS) ----------
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

# ---------- stackad ESP32-P4-WIFI6 (2× 1x20 kant-sockel) ----------
# Edge B = kraft-tapp: VSYS=VBAT (P4:ans buck självförsörjer), GND. Övriga edge-B-stift NC.
JB = P4B()
JB["VSYS"] += VBAT; JB["GND"] += GND; JB["GNDb"] += GND; JB["GNDc"] += GND; JB["GNDd"] += GND
JB["GPIO20"] += VBAT_SENSE
# Edge A = alla signaler (14 av 16): 10 DATA direkt + 3 TPIC-ctrl + LED_EN broadcast.
JA = P4A()
JA["GND"] += GND; JA["GNDb"] += GND; JA["GNDc"] += GND; JA["GNDd"] += GND
JA["GPIO52"] += DATA[0]; JA["GPIO51"] += DATA[1]; JA["GPIO31"] += DATA[2]; JA["GPIO30"] += DATA[3]
JA["GPIO29"] += DATA[4]; JA["GPIO28"] += DATA[5]; JA["GPIO50"] += DATA[6]; JA["GPIO49"] += DATA[7]
JA["GPIO5"] += DATA[8]; JA["GPIO4"] += DATA[9]                       # 10 DATA direkt
JA["GPIO3"] += TSER; JA["GPIO2"] += TSRCK; JA["GPIO8"] += TRCK       # TPIC SER/SRCK/RCK
JA["GPIO7"] += LED_EN                                                # konstellation broadcast
# (GPIO24/GPIO25 reserv)

# ---------- batteri-in + ingangsskydd + strombrytare ----------
Jb = BATT(); Jb["GND"] += GND; Jb["VBAT"] += VBAT_RAW
Qp = PFET(); Qp["D"] += VBAT_RAW; Qp["S"] += VBAT; Qp["G"] += PGATE
Rgate = RES("100k"); Rgate[1] += PGATE; Rgate[2] += VBAT_RAW
Jsw = PWRSW(); Jsw["GATE"] += PGATE; Jsw["GND"] += GND
Dtvs = TVS(); Dtvs["K"] += VBAT; Dtvs["A"] += GND
# ---------- batteri-sense (8.4V -> 100k/47k -> 2.69V pa GPIO20/ADC1) ----------
Rst = RES("100k"); Rsb = RES("47k"); Csns = CAP("100nF")
Rst[1] += VBAT; Rst[2] += VBAT_SENSE; Rsb[1] += VBAT_SENSE; Rsb[2] += GND
Csns[1] += VBAT_SENSE; Csns[2] += GND
# ---------- test points ----------
for _net in (VBAT, P3V3, GND, DATA[0]):
    TP()[1] += _net
for _ in range(4):
    MH()[1] += GND

generate_netlist(file_="hardware/vest-mb.net")
print("wrote hardware/vest-mb.net (väst-mb v3: ESP32-P4-WIFI6 + buck + 2×TPIC6B595 + 10 zon-kontakter, DATA direkt)")
