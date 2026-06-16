#!/usr/bin/env python3
"""STRILAS — HJÄLM-MODERKORT ("holo"-kort), v3 m. ESP32-C6-devkit + ljud. SKiDL → 'hardware/helmet-mb.net'.
Centralt hjälm-nav: 4 lösa dubbel-aim-patchar (front/bak/vä/hö) + F9P-puck + batteri + HÖGTALARE/MIK. 4-lager.

ARKITEKTUR (verifierad mot datablad):
  • ESP: stackad ESP32-C6-DevKitC-1 (Waveshare N16, WiFi6 → matchar vapnets P4; 23 GPIO; samma på väst-mb).
    Matas från kortets 3V3. 2× 1x16-header (J1: 3V3/RST/GPIO4-7/0/1/8/10/11/2/3/5V/GND/NC ;
    J3: GND/GPIO16TX/17RX/15/23/22/21/20/19/18/9/GND/13/12/GND/NC). Strapping 8/9/15 + USB 12/13 undviks.
  • 2S-batteri → AP63203-buck → 3,3 V @2A. LED-konstellation på VBAT.
  • ZED-F9P RTK-puck (8-pol JST GH): UART + I²C (config + IST8310-kompass), matas VBAT (3–9 V).
  • IIM-42653 IMU (I²C, delar F9P-bussen + INT) → GNSS/INS-fusion + lokal huvud-attityd.
  • 4 EGNA TSOP4856 (ledade, ben böjs/sprids diagonalt) → diod-OR → 1 DATA. 4 patch-DATA. 23 GPIO → alla 5
    DATA läses DIREKT (ingen 74HC165). 2 topp-konstellations-LED + driver (LED_EN broadcast).
  • LJUD (feedback): MAX98357A-amp-breakout (1x7 + högtalare) + I²S-MEMS-mik-breakout (1x6) → I²S.
GPIO: UART2 + I²C2 + INT1 + LED_EN1 + 5 DATA + I²S4 + amp_SD1 = 16 av 23 (reserv kvar).
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
IMU = mk("IIM-42653", "U", [(i, i) for i in range(1, 15)], "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "IIM-42653")
TSOP = mk("TSOP4856", "U", [(1, "OUT"), (2, "GND"), (3, "VS")], "OptoDevice:Vishay_MOLD-3Pin", "TSOP4856")
LED = mk("SFH4715AS", "D", [(1, "A"), (2, "K")], "strilas:IR_Emitter_OSRAM_OSLON_Black_SFH4725S", "SFH4715AS_860nm")
ORD = mk("ORdiode", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SOD-123", "BAT54")
NFET = mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400")
F9P = mk("ZED-F9P", "J", [(1, "VCC"), (2, "GND"), (3, "TXD"), (4, "RXD"), (5, "SDA"), (6, "SCL"), (7, "PPS"), (8, "RSV")],
         "Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal", "ZED-F9P RTK (UART+I²C)")
SOCK16 = mk("Conn_1x16", "J", [(i, i) for i in range(1, 17)], "Connector_PinSocket_2.54mm:PinSocket_1x16_P2.54mm_Vertical", "ESP32-C6 1x16 sockel")
PATCH = mk("PatchConn", "J", [(1, "VBAT"), (2, "GND"), (3, "DATA"), (4, "LED_EN"), (5, "P3V3")],
           "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical", "Patch: VBAT·GND·DATA·LED_EN·3V3")
HDR = lambda n, lbl: mk(f"Conn_1x0{n}", "J", [(i, i) for i in range(1, n + 1)],
                        f"Connector_PinHeader_2.54mm:PinHeader_1x0{n}_P2.54mm_Vertical", lbl)
BATT = mk("BATT_2S", "J", [(1, "VBAT"), (2, "GND")], "Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal", "2S batteri")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v, fp="Resistor_SMD:R_0805_2012Metric": RES_T(value=v, footprint=fp)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
MH = mk("MH", "H", [(1, "1")], "MountingHole:MountingHole_2.5mm", "M2.5")

# ---------- nät ----------
VBAT, GND, P3V3 = Net("VBAT"), Net("GND"), Net("+3V3")
SW, BST, FB = Net("SW"), Net("BST"), Net("FB")
LED_EN, I2C_SDA, I2C_SCL, IMU_INT = Net("LED_EN"), Net("I2C_SDA"), Net("I2C_SCL"), Net("IMU_INT")
GNSS_TX, GNSS_RX = Net("GNSS_TX"), Net("GNSS_RX")
BCLK, LRCK, I2S_DOUT, I2S_DIN, AMP_SD = (Net(n) for n in ("I2S_BCLK", "I2S_LRCK", "I2S_DOUT", "I2S_DIN", "AMP_SD"))
LEDC, DATA_OB = Net("LED_CATH"), Net("DATA_OB")
DP = [Net(f"DATA_P{i+1}") for i in range(4)]

# ---------- buck 2S → 3,3 V ----------
Ubk = BUCK()
Ubk["VIN"] += VBAT; Ubk["EN"] += VBAT; Ubk["GND"] += GND; Ubk["SW"] += SW; Ubk["BST"] += BST; Ubk["FB"] += FB
L1 = IND(); L1[1] += SW; L1[2] += P3V3
Cbst = CAP("100nF"); Cbst[1] += SW; Cbst[2] += BST
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric"); Cin[1] += VBAT; Cin[2] += GND
Cout = CAP("22uF", "Capacitor_SMD:C_1206_3216Metric"); Cout[1] += P3V3; Cout[2] += GND
Rt = RES("31.6k"); Rb = RES("10k"); Rt[1] += P3V3; Rt[2] += FB; Rb[1] += FB; Rb[2] += GND

# ---------- IIM-42653 IMU (I²C) ----------
U3 = IMU()
U3[8] += P3V3; U3[5] += P3V3; U3[6] += GND; U3[7] += GND; U3[12] += P3V3
U3[1] += GND; U3[13] += I2C_SCL; U3[14] += I2C_SDA; U3[4] += IMU_INT
Ci1 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric"); Ci1[1] += P3V3; Ci1[2] += GND
Ci2 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric"); Ci2[1] += P3V3; Ci2[2] += GND

# ---------- 4 egna TSOP4856 → diod-OR → DATA_OB ----------
Rpu = RES("10k"); Rpu[1] += P3V3; Rpu[2] += DATA_OB
for i in range(4):
    s = TSOP(); out = Net(f"OB_OUT{i+1}")
    s["VS"] += P3V3; s["GND"] += GND; s["OUT"] += out
    d = ORD(); d["K"] += out; d["A"] += DATA_OB
    cd = CAP("100nF"); cd[1] += P3V3; cd[2] += GND

# ---------- 2 topp-konstellations-LED + driver ----------
Q = NFET(); Q["S"] += GND; Q["D"] += LEDC
Rg = RES("220R"); Rg[1] += LED_EN; Rg[2] += Q["G"]
for i in range(2):
    led = LED(); rl = RES("10R", "Resistor_SMD:R_2512_6332Metric")
    a = Net(f"LED_A{i+1}")
    rl[1] += VBAT; rl[2] += a; led["A"] += a; led["K"] += LEDC

# ---------- ZED-F9P + 4 patch-kontakter ----------
Jf = F9P()
Jf["VCC"] += VBAT; Jf["GND"] += GND; Jf["TXD"] += GNSS_TX; Jf["RXD"] += GNSS_RX
Jf["SDA"] += I2C_SDA; Jf["SCL"] += I2C_SCL; Jf["PPS"] += Net("GNSS_PPS"); Jf["RSV"] += Net("F9P_RSV")
for i in range(4):
    jp = PATCH()
    jp["VBAT"] += VBAT; jp["GND"] += GND; jp["DATA"] += DP[i]; jp["LED_EN"] += LED_EN; jp["P3V3"] += P3V3

# ---------- LJUD: MAX98357A-amp-breakout (1x7) + I²S-mik-breakout (1x6) ----------
Ja = HDR(7, "AMP: 3V3·GND·SD·GAIN·DIN·BCLK·LRC")()
Ja[1] += P3V3; Ja[2] += GND; Ja[3] += AMP_SD; Ja[4] += Net("AMP_GAIN"); Ja[5] += I2S_DOUT; Ja[6] += BCLK; Ja[7] += LRCK
Jm = HDR(6, "MIC: 3V3·GND·SD·WS·SCK·LR")()
Jm[1] += P3V3; Jm[2] += GND; Jm[3] += I2S_DIN; Jm[4] += LRCK; Jm[5] += BCLK; Jm[6] += GND  # LR→GND = vänster

# ---------- stackad ESP32-C6-DevKitC-1 (2× 1x16) ----------
# J1: 1=3V3 2=RST 3=GPIO4 4=GPIO5 5=GPIO6 6=GPIO7 7=GPIO0 8=GPIO1 9=GPIO8 10=GPIO10 11=GPIO11 12=GPIO2 13=GPIO3 14=5V 15=GND 16=NC
JC1 = SOCK16()
JC1[1] += P3V3; JC1[15] += GND        # 3V3 (mata C6 via 3V3-stift) + GND
JC1[3] += DP[3]      # GPIO4  → patch-DATA 4
JC1[5] += I2C_SDA    # GPIO6  → I²C SDA (F9P + IMU)
JC1[6] += I2C_SCL    # GPIO7  → I²C SCL
JC1[7] += IMU_INT    # GPIO0  ← IMU INT
JC1[8] += LED_EN     # GPIO1  → konstellation broadcast
JC1[10] += DP[1]     # GPIO10 → patch-DATA 2
JC1[11] += DP[2]     # GPIO11 → patch-DATA 3
JC1[12] += DATA_OB   # GPIO2  → onboard-TSOP-DATA
JC1[13] += DP[0]     # GPIO3  → patch-DATA 1
# pin2(RST), pin4(GPIO5 reserv), pin9(GPIO8 strap), pin14(5V) = NC
JC1[14] += Net("NC_5V")
# J3: 1=GND 2=GPIO16(TX) 3=GPIO17(RX) 4=GPIO15 5=GPIO23 6=GPIO22 7=GPIO21 8=GPIO20 9=GPIO19 10=GPIO18 11=GPIO9 12=GND 13=GPIO13 14=GPIO12 15=GND 16=NC
JC3 = SOCK16()
JC3[1] += GND; JC3[12] += GND; JC3[15] += GND
JC3[2] += GNSS_RX    # GPIO16 TX → F9P RXD
JC3[3] += GNSS_TX    # GPIO17 RX ← F9P TXD
JC3[6] += AMP_SD     # GPIO22 → amp SD
JC3[7] += I2S_DOUT   # GPIO21 → amp DIN
JC3[8] += LRCK       # GPIO20 I²S LR-clock
JC3[9] += BCLK       # GPIO19 I²S bit-clock
JC3[10] += I2S_DIN   # GPIO18 ← mik
# pin4(GPIO15 strap), pin5(GPIO23 reserv), pin11(GPIO9 strap), pin13/14(GPIO13/12 USB) = NC

# ---------- batteri + monteringshål ----------
Jb = BATT(); Jb["VBAT"] += VBAT; Jb["GND"] += GND
for _ in range(4):
    MH()[1] += GND

generate_netlist(file_="hardware/helmet-mb.net")
print("wrote hardware/helmet-mb.net (hjälm-mb v3: ESP32-C6 + buck + F9P + IIM-42653 + 4 TSOP + 2 LED + ljud + 4 patch)")
