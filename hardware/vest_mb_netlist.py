#!/usr/bin/env python3
"""STRILAS — VÄST-MODERKORT (väst-nod): kretsdefinition i kod (SKiDL → KiCad-netlista).
Genererar 'hardware/vest-mb.net'. Fristående väst-nod: alla 10 patchar + 10 zon-vibratorer
pluggas in; trådlöst mot vapnets P4 (ESP-NOW/WiFi). 4-lager.

ARKITEKTUR (verifierad mot datablad):
  • Samma ESP som hjälmen för enkel sourcing: stackad XIAO ESP32-S3 (2× 1x7 sockel).
  • 2S-batteri (laddas i docka) → AP63203-buck → 3,3 V @2A (matar XIAO + 74HC165 + ERM-motorer).
    VBAT(2S) distribueras till varje patch (konstellations-LED). ERM-motorer matas från 3V3.
  • 10× DATA (skott-hit per patch, aktiv-låg 3,3 V) läses via 2× 74HC165 (parallel-in→SPI):
    XIAO har bara 11 GPIO → shift-register sparar stift. (SH/LD + delad SCK + QH→MISO.)
  • 10× VIB (zon-vibrator) drivs av 2× TPIC6B595 power-shift-register (open-drain 150 mA/kanal,
    inbyggd flyback): MOSI→SERIN, delad SRCK, RCK-latch. Motor: 3V3→motor→DRAIN→GND (PWM=intensitet).
  • LED_EN broadcast (1 GPIO) → alla patchars konstellation blinkar synkront (torso = 1 stel kropp).
  • Zon-kontakt 1x6: VBAT·GND·DATA·LED_EN·3V3·VIB (patch pins 1-4, motor pins 5-6).
XIAO/patchar/motorer köps separat och pluggas; allt ytmonterat (buck,165,TPIC,R/C/L) av NextPCB.
"""
from skidl import Part, Pin, Net, generate_netlist, SKIDL, TEMPLATE, reset


def mk(name, ref, pins, fp, value=""):
    p = Part(tool=SKIDL, name=name, ref_prefix=ref, dest=TEMPLATE)
    p.add_pins(*[Pin(num=str(n), name=str(nm)) for n, nm in pins])
    p.footprint = fp
    if value: p.value = value
    return p


reset()
# ---------- parttyper ----------
BUCK = mk("AP63203", "U", [(1, "FB"), (2, "EN"), (3, "VIN"), (4, "GND"), (5, "SW"), (6, "BST")],
          "Package_TO_SOT_SMD:TSOT-23-6", "AP63203")
IND = mk("L", "L", [(1, "1"), (2, "2")], "Inductor_SMD:L_Changjiang_FNR5040S", "4.7uH")
# 74HC165 PISO (SOIC-16, Nexperia datablad): in A=11 B=12 C=13 D=14 E=6 F=5 G=4 H=3, SH/LD=1 CLK=2
#  QH'=7 GND=8 QH=9 SER=10 CLK_INH=15 VCC=16.
HC165 = mk("74HC165", "U", [(1, "SHLD"), (2, "CLK"), (3, "H"), (4, "G"), (5, "F"), (6, "E"),
           (7, "QHn"), (8, "GND"), (9, "QH"), (10, "SER"), (11, "A"), (12, "B"), (13, "C"),
           (14, "D"), (15, "CLKINH"), (16, "VCC")], "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", "74HC165")
# TPIC6B595 power-shift (SOIC-20W DW, TI SLIS032D): 2=VCC 3=SERIN 4-7=D0-3 8=/SRCLR 9=/G 10/11/19=GND
#  12=RCK 13=SRCK 14-17=D4-7 18=SEROUT 1/20=NC.
TPIC = mk("TPIC6B595", "U", [(1, "NC1"), (2, "VCC"), (3, "SERIN"), (4, "D0"), (5, "D1"), (6, "D2"),
          (7, "D3"), (8, "SRCLRn"), (9, "Gn"), (10, "GND"), (11, "GND2"), (12, "RCK"), (13, "SRCK"),
          (14, "D4"), (15, "D5"), (16, "D6"), (17, "D7"), (18, "SEROUT"), (19, "GND3"), (20, "NC2")],
          "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm", "TPIC6B595")
SOCK7 = mk("Conn_1x07", "J", [(i, i) for i in range(1, 8)],
           "Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical", "XIAO-S3 1x7 sockel")
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
SCK, MOSI, MISO, LD165, RCK, LED_EN = (Net(n) for n in ("SCK", "MOSI", "MISO", "LD165", "RCK", "LED_EN"))
DATA = [Net(f"DATA{i+1}") for i in range(10)]
VIB = [Net(f"VIB{i+1}") for i in range(10)]
CHAIN165, CHAINTPIC = Net("HC165_CHAIN"), Net("TPIC_CHAIN")

# ---------- buck: 2S → 3,3 V @2A ----------
Ubk = BUCK()                                                  # U1
Ubk["VIN"] += VBAT; Ubk["EN"] += VBAT; Ubk["GND"] += GND; Ubk["SW"] += SW; Ubk["BST"] += BST; Ubk["FB"] += FB
L1 = IND(); L1[1] += SW; L1[2] += P3V3
Cbst = CAP("100nF"); Cbst[1] += SW; Cbst[2] += BST
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric"); Cin[1] += VBAT; Cin[2] += GND
Cout = CAP("22uF", "Capacitor_SMD:C_1206_3216Metric"); Cout[1] += P3V3; Cout[2] += GND
Rt = RES("31.6k"); Rb = RES("10k"); Rt[1] += P3V3; Rt[2] += FB; Rb[1] += FB; Rb[2] += GND
Cbulk = CAP("100uF", "Capacitor_SMD:C_1210_3225Metric"); Cbulk[1] += P3V3; Cbulk[2] += GND  # ERM-pulsreservoar

# ---------- 2× 74HC165: läs 10 DATA (parallel-in → SPI) ----------
U165a = HC165(); U165b = HC165()                              # U2 (DATA1-8), U3 (DATA9-10)
for u in (U165a, U165b):
    u["VCC"] += P3V3; u["GND"] += GND; u["CLK"] += SCK; u["SHLD"] += LD165; u["CLKINH"] += GND
for i, pin in enumerate(["A", "B", "C", "D", "E", "F", "G", "H"]):
    U165a[pin] += DATA[i]                                     # DATA1..8
U165b["A"] += DATA[8]; U165b["B"] += DATA[9]                  # DATA9,10
for pin in ["C", "D", "E", "F", "G", "H"]: U165b[pin] += GND  # oanvända in → GND
U165a["QH"] += MISO; U165a["SER"] += CHAIN165; U165b["QH"] += CHAIN165; U165b["SER"] += GND
Cd165a = CAP("100nF"); Cd165a[1] += P3V3; Cd165a[2] += GND
Cd165b = CAP("100nF"); Cd165b[1] += P3V3; Cd165b[2] += GND

# ---------- 2× TPIC6B595: driv 10 VIB (open-drain power-shift) ----------
Ut1 = TPIC(); Ut2 = TPIC()                                    # U4 (VIB1-8), U5 (VIB9-10)
for u in (Ut1, Ut2):
    u["VCC"] += P3V3; u["GND"] += GND; u["GND2"] += GND; u["GND3"] += GND
    u["SRCK"] += SCK; u["RCK"] += RCK; u["Gn"] += GND; u["SRCLRn"] += P3V3   # /G=låg(på), /SRCLR=hög
for i, pin in enumerate(["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]):
    Ut1[pin] += VIB[i]                                        # VIB1..8
Ut2["D0"] += VIB[8]; Ut2["D1"] += VIB[9]                      # VIB9,10 (D2-7 = NC open-drain)
Ut1["SERIN"] += MOSI; Ut1["SEROUT"] += CHAINTPIC; Ut2["SERIN"] += CHAINTPIC
Cdt1 = CAP("100nF"); Cdt1[1] += P3V3; Cdt1[2] += GND
Cdt2 = CAP("100nF"); Cdt2[1] += P3V3; Cdt2[2] += GND

# ---------- 10× zon-kontakt (patch + vibrator) ----------
for i in range(10):
    z = ZONE()
    z["VBAT"] += VBAT; z["GND"] += GND; z["DATA"] += DATA[i]
    z["LED_EN"] += LED_EN; z["P3V3"] += P3V3; z["VIB"] += VIB[i]

# ---------- stackad XIAO ESP32-S3 (2× 1x7 sockel) ----------
# vänster: D0..D6 (GPIO1,2,3,4,5,6,43) ; höger: 5V,GND,3V3,D10,D9(MISO),D8(SCK),D7(MOSI? -> se nedan)
JL = SOCK7(); JR = SOCK7()                                    # J11 (vänster), J12 (höger)
JL[1] += LD165      # D0  → 74HC165 SH/LD (parallell-laddning)
JL[2] += RCK        # D1  → TPIC RCK (latch)
JL[3] += LED_EN     # D2  → konstellation broadcast
JL[4] += Net("MB_D3"); JL[5] += Net("MB_D4"); JL[6] += Net("MB_D5")  # reserv-GPIO
JL[7] += Net("MB_D6")
JR[1] += Net("NC_5V")   # 5V (matas via 3V3)
JR[2] += GND
JR[3] += P3V3
JR[4] += Net("MB_D10")  # reserv
JR[5] += MISO           # D9  MISO ← 74HC165 QH
JR[6] += SCK            # D8  SCK  → delad shift-clock (165 CLK + TPIC SRCK)
JR[7] += MOSI           # D7  MOSI → TPIC SER IN

# ---------- batteri + monteringshål ----------
Jb = BATT(); Jb["VBAT"] += VBAT; Jb["GND"] += GND
for _ in range(4):
    MH()[1] += GND

generate_netlist(file_="hardware/vest-mb.net")
print("wrote hardware/vest-mb.net (väst-moderkort: XIAO-S3 + buck + 2×74HC165 + 2×TPIC6B595 + 10 zon-kontakter)")
