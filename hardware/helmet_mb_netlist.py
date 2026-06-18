#!/usr/bin/env python3
"""STRILAS — HJÄLM-MODERKORT ("holo"-kort), v4 m. ESP32-P4-WIFI6 (samma som vapnet) + ljud. SKiDL → 'hardware/helmet-mb.net'.
Centralt hjälm-nav: 4 lösa dubbel-aim-patchar (front/bak/vä/hö) + F9P-puck + batteri + HÖGTALARE/MIK. 4-lager.

ARKITEKTUR (verifierad mot datablad):
  • ESP: stackad ESP32-P4-WIFI6 (samma kort som vapnet; 2× kant-sockel 1x20, edge A+B). Pinout 100%
    verifierad mot Waveshares datablad. P4 självförsörjer via VSYS=VBAT; carrier-buck ger 3V3 till last.
  • 2S-batteri → AP63203-buck → 3,3 V @2A. LED-konstellation på VBAT.
  • ZED-F9P RTK-puck (8-pol JST GH): UART + I²C (config + IST8310-kompass), matas VBAT (3–9 V).
  • IIM-42653 IMU (I²C, delar F9P-bussen + INT) → GNSS/INS-fusion + lokal huvud-attityd.
  • 4 EGNA TSOP4856 (ledade, ben böjs/sprids diagonalt) → diod-OR → 1 DATA. 4 patch-DATA. GPIO → alla 5
    DATA läses DIREKT (ingen 74HC165). 6 konstellations-LED (3 serie-par) + driver (LED_EN broadcast).
  • LJUD/KOMM (riktigt headset): ES8388-codec (QFN-28, 3,3V-native) — analog bom-mik IN + I²S DAC/ADC
    ↔ P4 + I²C-styrning (0x10). Line-ut → PAM8302A klass-D-amp → öronhögtalare. PTT-knapp → GPIO20.
GPIO: UART2 + I²C2 + INT1 + LED_EN1 + 5 DATA + I²S(MCLK/BCLK/LRCK/DOUT/DIN)5 + MCLK + amp_SD1 + PTT1.
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
LED = mk("LED_TAB", "D", [(1, "A"), (2, "K")], "strilas:LED_Tab", "LED-tab (OSLON på micro-PCB med ben → böjs/vinklas; ledad)")
ORD = mk("ORdiode", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SOD-123", "BAT54")
NFET = mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400")
F9P = mk("ZED-F9P", "J", [(1, "VCC"), (2, "GND"), (3, "TXD"), (4, "RXD"), (5, "SDA"), (6, "SCL"), (7, "PPS"), (8, "RSV")],
         "Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal", "ZED-F9P RTK (UART+I²C)")
# ALT RTK-puck (UM980/F9P all-in-one, IST8310, LÅG PROFIL): 6-pol JST-GH 1.25mm. Pinout per databl.:
# 1=VCC 2=RX 3=TX 4=SCL 5=SDA 6=GND. Monteras som ALTERNATIV till 8-pol ZED-F9P (samma puck-fästhål).
F9P6 = mk("RTK_AIO_6P", "J", [(1, "VCC"), (2, "RX"), (3, "TX"), (4, "SCL"), (5, "SDA"), (6, "GND")],
          "Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal", "RTK all-in-one 6-pol GH (UM980/F9P, alt-puck)")
# ESP32-P4-WIFI6 (samma kort som vapnet!) — 2× kant-sockel (1x20). Pinout 100% verifierad mot
# Waveshares datablad (edge A + edge B). P4 självförsörjer via VSYS; carrier-buck ger 3V3 för last.
P4B = mk("P4_EDGE_B", "J", [(1, "VBUS"), (2, "VSYS"), (3, "GND"), (4, "EN"), (5, "P3V3"), (6, "GPIO20"),
         (7, "GPIO21"), (8, "GNDb"), (9, "GPIO22"), (10, "GPIO23"), (11, "RUN"), (12, "GPIO26"),
         (13, "GNDc"), (14, "GPIO27"), (15, "GPIO32"), (16, "GPIO33"), (17, "GPIO46"), (18, "GNDd"),
         (19, "GPIO47"), (20, "GPIO48")], "Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical", "P4-WIFI6 edge B")
P4A = mk("P4_EDGE_A", "J", [(1, "GPIO52"), (2, "GPIO51"), (3, "GND"), (4, "GPIO31"), (5, "GPIO30"),
         (6, "GPIO29"), (7, "GPIO28"), (8, "GNDb"), (9, "GPIO50"), (10, "GPIO49"), (11, "GPIO5"),
         (12, "GPIO4"), (13, "GNDc"), (14, "GPIO3"), (15, "GPIO2"), (16, "GPIO8"), (17, "GPIO7"),
         (18, "GNDd"), (19, "GPIO24"), (20, "GPIO25")], "Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical", "P4-WIFI6 edge A")
PATCH = mk("PatchConn", "J", [(1, "VBAT"), (2, "GND"), (3, "DATA"), (4, "LED_EN"), (5, "P3V3")],
           "Connector_JST:JST_PH_S5B-PH-K_1x05_P2.00mm_Horizontal", "Patch: VBAT·GND·DATA·LED_EN·3V3")
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

# ---------- 6 konstellations-LED via LEDADE TAB-MICRO-PCB (3 grenar × 2 i serie) + driver ----------
# OSLON:en sitter på en egen micro-PCB (led-tab, hardware/led_tab.py) med 2 BEN (wire-legs) som löds in
# i discens 2-håls tab-sockel (D5-D10) → böjs/vinklas RADIELLT UT mot horisonten (kameran i ögonhöjd
# @150 m ser punkterna). Full OSLON-effekt behålls. Serie-par halverar VBAT-strömmen + 3 serieR (2512).
Q = NFET(); Q["S"] += GND; Q["D"] += LEDC
Rg = RES("220R"); Rg[1] += LED_EN; Rg[2] += Q["G"]
for i in range(3):
    rl = RES("10R", "Resistor_SMD:R_2512_6332Metric"); a = Net(f"LED_A{i+1}"); mid = Net(f"LED_M{i+1}")
    rl[1] += VBAT; rl[2] += a
    l1 = LED(); l1["A"] += a; l1["K"] += mid       # gren: VBAT→R→LED1→LED2→LED_CATH(FET)
    l2 = LED(); l2["A"] += mid; l2["K"] += LEDC

# ---------- RTK-puck (8-pol ZED-F9P + 6-pol alt-puck, parallellt) + 4 patch-kontakter ----------
Jf = F9P()
Jf["VCC"] += VBAT; Jf["GND"] += GND; Jf["TXD"] += GNSS_TX; Jf["RXD"] += GNSS_RX
Jf["SDA"] += I2C_SDA; Jf["SCL"] += I2C_SCL; Jf["PPS"] += Net("GNSS_PPS"); Jf["RSV"] += Net("F9P_RSV")
# Alt-puck 6-pol GH PARALLELLT (samma UART/I²C/kraft → montera ENDERA pucken; delar fästhålen H5-H8).
Jf6 = F9P6(); Jf6.ref = "J12"
Jf6["VCC"] += VBAT; Jf6["RX"] += GNSS_RX; Jf6["TX"] += GNSS_TX
Jf6["SCL"] += I2C_SCL; Jf6["SDA"] += I2C_SDA; Jf6["GND"] += GND
for i in range(4):
    jp = PATCH()
    jp["VBAT"] += VBAT; jp["GND"] += GND; jp["DATA"] += DP[i]; jp["LED_EN"] += LED_EN; jp["P3V3"] += P3V3

# ---------- LJUD/KOMM: ES8388-codec (U7) + PAM8302A klass-D-amp (U8) → riktigt headset ----------
# ES8388 QFN-28, 3,3V-native (matchar kortets rail → I²S/I²C DIREKT mot P4, inga level-shifters, ingen
# extra 1,8V-rail). Analog bom-electret-mik IN (LIN1, pin 24) + I²S DAC/ADC ↔ P4 + I²C-styrning
# (CE→GND ⇒ I²C-addr 0x10). Line-ut (LOUT2) → AC-koppling → PAM8302A → öronhögtalare. PTT-knapp → GPIO.
# Pinout verifierad mot Everest ES8388 User Guide (typ-app-schemat). 0,5mm-QFN routar (som IMU:n).
MCLK, PTT = Net("I2S_MCLK"), Net("PTT")
MICIN, LINE_OUT = Net("MIC_HOT"), Net("LINE_OUT")
SPK_P, SPK_N = Net("SPK_P"), Net("SPK_N")
ES = mk("ES8388", "U",
        [(1, "MCLK"), (2, "DVDD"), (3, "PVDD"), (4, "DGND"), (5, "SCLK"), (6, "DSDIN"), (7, "LRCK"),
         (8, "ASDOUT"), (9, "NC1"), (10, "VREF"), (11, "ROUT1"), (12, "LOUT1"), (13, "HPGND"),
         (14, "ROUT2"), (15, "LOUT2"), (16, "HPVDD"), (17, "AVDD"), (18, "AGND"), (19, "DACVREF"),
         (20, "VMID"), (21, "RIN2"), (22, "LIN2"), (23, "RIN1"), (24, "LIN1"), (25, "NC2"),
         (26, "CE"), (27, "CDATA"), (28, "CCLK"), (29, "EP")],
        "strilas:ES8388_QFN-28_4x4mm_P0.5mm", "ES8388")
AMP = mk("PAM8302A", "U", [(1, "SD"), (2, "GND"), (3, "INP"), (4, "INN"), (5, "VOP"), (6, "VDD"), (7, "NC"), (8, "VON")],
         "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "PAM8302A")
J2P = lambda nm: mk(nm, "J", [(1, "1"), (2, "2")], "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", nm)

U7 = ES(); U7.ref = "U7"
U7["MCLK"] += MCLK; U7["SCLK"] += BCLK; U7["LRCK"] += LRCK; U7["DSDIN"] += I2S_DOUT; U7["ASDOUT"] += I2S_DIN
U7["CCLK"] += I2C_SCL; U7["CDATA"] += I2C_SDA; U7["CE"] += GND          # I²C addr 0x10
U7["AVDD"] += P3V3; U7["HPVDD"] += P3V3; U7["DVDD"] += P3V3; U7["PVDD"] += P3V3
U7["DGND"] += GND; U7["AGND"] += GND; U7["HPGND"] += GND; U7["EP"] += GND
Cvref = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric"); Cvref[1] += U7["VREF"]; Cvref[2] += GND
Cvmid = CAP("1uF"); Cvmid[1] += U7["VMID"]; Cvmid[2] += GND
Cdacv = CAP("1uF"); Cdacv[1] += U7["DACVREF"]; Cdacv[2] += GND
Cav1 = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric"); Cav1[1] += P3V3; Cav1[2] += GND
Cav2 = CAP("100nF"); Cav2[1] += P3V3; Cav2[2] += GND
Cdv = CAP("1uF"); Cdv[1] += P3V3; Cdv[2] += GND
Cpv = CAP("100nF"); Cpv[1] += P3V3; Cpv[2] += GND
Chv = CAP("100nF"); Chv[1] += P3V3; Chv[2] += GND
# electret-bom-mik: bias från 3V3, AC-koppling in i LIN1; RIN1 AC till GND (single-ended)
Rmb = RES("2.2k"); Rmb[1] += P3V3; Rmb[2] += MICIN
Cmic = CAP("1uF"); Cmic[1] += MICIN; Cmic[2] += U7["LIN1"]
Crin = CAP("1uF"); Crin[1] += U7["RIN1"]; Crin[2] += GND
Jmic = J2P("MIC_BOOM")(); Jmic.ref = "J6"; Jmic[1] += MICIN; Jmic[2] += GND
# line-ut (LOUT2) → AC-koppling → PAM8302A → högtalare (mono)
Caout = CAP("1uF"); Caout[1] += U7["LOUT2"]; Caout[2] += LINE_OUT
U8 = AMP(); U8.ref = "U8"
U8["INP"] += LINE_OUT; U8["INN"] += GND; U8["SD"] += AMP_SD; U8["VDD"] += P3V3; U8["GND"] += GND
Camp = CAP("1uF"); Camp[1] += P3V3; Camp[2] += GND
U8["VOP"] += SPK_P; U8["VON"] += SPK_N
Jspk = J2P("SPEAKER")(); Jspk.ref = "J7"; Jspk[1] += SPK_P; Jspk[2] += SPK_N
Jptt = J2P("PTT_BTN")(); Jptt.ref = "J11"; Jptt[1] += PTT; Jptt[2] += GND
Rsda = RES("4k7"); Rsda[1] += P3V3; Rsda[2] += I2C_SDA   # I²C pullups (codec+F9P+IMU på 3V3)
Rscl = RES("4k7"); Rscl[1] += P3V3; Rscl[2] += I2C_SCL

# ---------- stackad ESP32-P4-WIFI6 (2× kant-sockel, samma kort som vapnet) ----------
JB = P4B(); JB.ref = "J8"
JB["VSYS"] += VBAT; JB["GND"] += GND; JB["GNDb"] += GND; JB["GNDc"] += GND; JB["GNDd"] += GND
JB["GPIO23"] += MCLK; JB["GPIO20"] += PTT              # edge B: I²S MCLK till codec + PTT-knapp
# Edge A = alla signaler (16 GPIO). I²C på dedikerade GPIO8(SCL)/GPIO7(SDA).
JA = P4A(); JA.ref = "J9"
JA["GND"] += GND; JA["GNDb"] += GND; JA["GNDc"] += GND; JA["GNDd"] += GND
JA["GPIO7"] += I2C_SDA; JA["GPIO8"] += I2C_SCL          # I²C (F9P + IMU + ES8388 @0x10)
JA["GPIO5"] += GNSS_RX; JA["GPIO4"] += GNSS_TX          # UART → F9P
JA["GPIO3"] += IMU_INT; JA["GPIO2"] += LED_EN
JA["GPIO52"] += DATA_OB; JA["GPIO51"] += DP[0]; JA["GPIO31"] += DP[1]; JA["GPIO30"] += DP[2]; JA["GPIO29"] += DP[3]  # 5 DATA
JA["GPIO28"] += BCLK; JA["GPIO50"] += LRCK; JA["GPIO49"] += I2S_DOUT; JA["GPIO24"] += I2S_DIN; JA["GPIO25"] += AMP_SD  # I²S + amp_SD

# ---------- batteri + monteringshål ----------
Jb = BATT(); Jb.ref = "J10"; Jb["VBAT"] += VBAT; Jb["GND"] += GND
# H1-H4 = kort-monteringshål (ring); H5-H8 = ZED-F9P-puckens fäste (M2.5, 20.80×33.90 mm rektangel,
# centrerat) → pucken skruvas direkt på PCB:n med standoffs (puck-bas Ø55, höjd 55, kontakt i syd).
for _ in range(8):
    MH()[1] += GND

generate_netlist(file_="hardware/helmet-mb.net")
print("wrote hardware/helmet-mb.net (hjälm-mb v4: ESP32-P4-WIFI6 + buck + F9P + IIM-42653 + 4 TSOP + 2 LED + ljud + 4 patch)")
