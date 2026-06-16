#!/usr/bin/env python3
"""STRILAS — HJÄLM-MODERKORT ("holo"-kortet, NYTT): centralt hjälm-nav. SKiDL → 'hardware/helmet-mb.net'.
Ersätter den platta hjälm-ringen. 4 lösa dubbel-aim-patchar (front/bak/vä/hö) pluggas in; F9P-puck +
batteri i centrum. 4-lager.

ARKITEKTUR (verifierad mot datablad):
  • ESP: stackad XIAO ESP32-S3 (samma som väst-moderkortet → enkel sourcing), matas från kortets 3V3.
  • 2S-batteri → AP63203-buck → 3,3 V @2A (XIAO + 165 + IMU + TSOP + F9P-logik). LED-konst. på VBAT.
  • ZED-F9P RTK-puck (8-pol JST GH): UART + I²C (config + IST8310-kompass), matas VBAT (3–9 V).
  • IIM-42653 IMU (I²C, delar F9P-bussen + 1 INT) → GNSS/INS-fusion (bättre RTK) + lokal huvud-attityd.
  • 4 EGNA TSOP4856 (ledade, ben böjs/sprids i bra vinklar som kompletterar patcharna) → diod-OR → 1 DATA.
  • 4 patch-kontakter (1x5: VBAT·GND·DATA·LED_EN·3V3) → 4 patch-DATA. Alla 5 DATA läses via 74HC165 (SPI).
  • 2 topp-konstellations-LED (860 nm) + driver (LED_EN broadcast → patchar + topp-LED).
GPIO (XIAO 11): UART2 + I²C2 + IMU_INT1 + LED_EN1 + 165(SCK/MISO/LD)3 = 9 (2 reserv). Ingen TPIC/haptik/ljud.
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
HC165 = mk("74HC165", "U", [(1, "SHLD"), (2, "CLK"), (3, "H"), (4, "G"), (5, "F"), (6, "E"),
           (7, "QHn"), (8, "GND"), (9, "QH"), (10, "SER"), (11, "A"), (12, "B"), (13, "C"),
           (14, "D"), (15, "CLKINH"), (16, "VCC")], "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", "74HC165")
# IIM-42653 (LGA-14), I²C — samma som fire-control. pin: 8=VDD 5=VDDIO 6/7=GND 12=CS(→VDDIO=I²C)
# 1=SDO/AD0(adress) 13=SCL 14=SDA 4=INT1. (AUX1 2/3/10/11 = NC.)
IMU = mk("IIM-42653", "U", [(i, i) for i in range(1, 15)], "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "IIM-42653")
TSOP = mk("TSOP4856", "U", [(1, "OUT"), (2, "GND"), (3, "VS")], "OptoDevice:Vishay_MOLD-3Pin", "TSOP4856")
LED = mk("SFH4715AS", "D", [(1, "A"), (2, "K")], "strilas:IR_Emitter_OSRAM_OSLON_Black_SFH4725S", "SFH4715AS_860nm")
ORD = mk("ORdiode", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SOD-123", "BAT54")
NFET = mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400")
F9P = mk("ZED-F9P", "J", [(1, "VCC"), (2, "GND"), (3, "TXD"), (4, "RXD"), (5, "SDA"), (6, "SCL"), (7, "PPS"), (8, "RSV")],
         "Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal", "ZED-F9P RTK (UART+I²C)")
SOCK7 = mk("Conn_1x07", "J", [(i, i) for i in range(1, 8)], "Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical", "XIAO-S3 1x7 sockel")
PATCH = mk("PatchConn", "J", [(1, "VBAT"), (2, "GND"), (3, "DATA"), (4, "LED_EN"), (5, "P3V3")],
           "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical", "Patch: VBAT·GND·DATA·LED_EN·3V3")
BATT = mk("BATT_2S", "J", [(1, "VBAT"), (2, "GND")], "Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal", "2S batteri")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v, fp="Resistor_SMD:R_0805_2012Metric": RES_T(value=v, footprint=fp)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
MH = mk("MH", "H", [(1, "1")], "MountingHole:MountingHole_2.5mm", "M2.5")

# ---------- nät ----------
VBAT, GND, P3V3 = Net("VBAT"), Net("GND"), Net("+3V3")
SW, BST, FB = Net("SW"), Net("BST"), Net("FB")
SCK, MISO, LD165, LED_EN = Net("SCK"), Net("MISO"), Net("LD165"), Net("LED_EN")
I2C_SDA, I2C_SCL, IMU_INT = Net("I2C_SDA"), Net("I2C_SCL"), Net("IMU_INT")
GNSS_TX, GNSS_RX = Net("GNSS_TX"), Net("GNSS_RX")
LEDC, DATA_OB = Net("LED_CATH"), Net("DATA_OB")
DP = [Net(f"DATA_P{i+1}") for i in range(4)]                  # 4 patch-DATA

# ---------- buck 2S → 3,3 V ----------
Ubk = BUCK()                                                  # U1
Ubk["VIN"] += VBAT; Ubk["EN"] += VBAT; Ubk["GND"] += GND; Ubk["SW"] += SW; Ubk["BST"] += BST; Ubk["FB"] += FB
L1 = IND(); L1[1] += SW; L1[2] += P3V3
Cbst = CAP("100nF"); Cbst[1] += SW; Cbst[2] += BST
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric"); Cin[1] += VBAT; Cin[2] += GND
Cout = CAP("22uF", "Capacitor_SMD:C_1206_3216Metric"); Cout[1] += P3V3; Cout[2] += GND
Rt = RES("31.6k"); Rb = RES("10k"); Rt[1] += P3V3; Rt[2] += FB; Rb[1] += FB; Rb[2] += GND

# ---------- 74HC165: läs 5 DATA (4 patch + 1 onboard) via SPI ----------
U165 = HC165()                                                # U2
U165["VCC"] += P3V3; U165["GND"] += GND; U165["CLK"] += SCK; U165["SHLD"] += LD165; U165["CLKINH"] += GND
U165["QH"] += MISO; U165["SER"] += GND
U165["A"] += DATA_OB; U165["B"] += DP[0]; U165["C"] += DP[1]; U165["D"] += DP[2]; U165["E"] += DP[3]
for pin in ["F", "G", "H"]: U165[pin] += GND                  # oanvända → GND
Cd165 = CAP("100nF"); Cd165[1] += P3V3; Cd165[2] += GND

# ---------- IIM-42653 IMU (I²C, delar F9P-buss) ----------
U3 = IMU()
U3[8] += P3V3; U3[5] += P3V3; U3[6] += GND; U3[7] += GND; U3[12] += P3V3   # VDD/VDDIO/GND, CS→VDDIO=I²C
U3[1] += GND; U3[13] += I2C_SCL; U3[14] += I2C_SDA; U3[4] += IMU_INT       # AD0 låg → 0x68
Ci1 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric"); Ci1[1] += P3V3; Ci1[2] += GND
Ci2 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric"); Ci2[1] += P3V3; Ci2[2] += GND

# ---------- 4 egna TSOP4856 (utspridda vinklar) → diod-OR → DATA_OB ----------
Rpu = RES("10k"); Rpu[1] += P3V3; Rpu[2] += DATA_OB           # onboard DATA-pullup
for i in range(4):
    s = TSOP(); out = Net(f"OB_OUT{i+1}")
    s["VS"] += P3V3; s["GND"] += GND; s["OUT"] += out
    d = ORD(); d["K"] += out; d["A"] += DATA_OB
    cd = CAP("100nF"); cd[1] += P3V3; cd[2] += GND

# ---------- 2 topp-konstellations-LED + driver (LED_EN broadcast) ----------
Q = NFET(); Q["S"] += GND; Q["D"] += LEDC
Rg = RES("220R"); Rg[1] += LED_EN; Rg[2] += Q["G"]
for i in range(2):
    led = LED(); rl = RES("10R", "Resistor_SMD:R_2512_6332Metric")
    a = Net(f"LED_A{i+1}")
    rl[1] += VBAT; rl[2] += a; led["A"] += a; led["K"] += LEDC

# ---------- ZED-F9P RTK-puck (8-pol GH) ----------
Jf = F9P()
Jf["VCC"] += VBAT; Jf["GND"] += GND; Jf["TXD"] += GNSS_TX; Jf["RXD"] += GNSS_RX
Jf["SDA"] += I2C_SDA; Jf["SCL"] += I2C_SCL; Jf["PPS"] += Net("GNSS_PPS"); Jf["RSV"] += Net("F9P_RSV")

# ---------- 4 patch-kontakter (1x5) ----------
for i in range(4):
    jp = PATCH()
    jp["VBAT"] += VBAT; jp["GND"] += GND; jp["DATA"] += DP[i]; jp["LED_EN"] += LED_EN; jp["P3V3"] += P3V3

# ---------- stackad XIAO ESP32-S3 (2× 1x7) ----------
# vänster D0..D6 = GPIO1,2,3,4,5,6,43 ; höger 5V,GND,3V3,D10,D9,D8,D7
JL = SOCK7(); JR = SOCK7()
JL[1] += LED_EN     # D0  → konstellation broadcast (patchar + topp-LED)
JL[2] += IMU_INT    # D1  ← IMU INT
JL[3] += LD165      # D2  → 165 parallell-laddning
JL[4] += Net("MB_D3")  # D3  reserv
JL[5] += I2C_SDA    # D4  I²C SDA (F9P + IMU)
JL[6] += I2C_SCL    # D5  I²C SCL
JL[7] += GNSS_RX    # D6  GPIO43 UART TX → F9P RXD
JR[1] += Net("NC_5V"); JR[2] += GND; JR[3] += P3V3
JR[4] += Net("MB_D10")  # D10 reserv
JR[5] += MISO       # D9  ← 165 QH
JR[6] += SCK        # D8  → 165 CLK
JR[7] += GNSS_TX    # D7  GPIO44 UART RX ← F9P TXD

# ---------- batteri + monteringshål ----------
Jb = BATT(); Jb["VBAT"] += VBAT; Jb["GND"] += GND
for _ in range(4):
    MH()[1] += GND

generate_netlist(file_="hardware/helmet-mb.net")
print("wrote hardware/helmet-mb.net (hjälm-moderkort: XIAO-S3 + buck + F9P + IIM-42653 + 165 + 4 TSOP + 2 LED + 4 patch)")
