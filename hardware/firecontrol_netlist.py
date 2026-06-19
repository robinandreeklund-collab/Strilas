#!/usr/bin/env python3
"""STRILAS — FIRE-CONTROL-KORT (vapen): kretsdefinition i kod (SKiDL → KiCad-netlista).
Genererar 'hardware/firecontrol.net'.

STACKAS rakt ovanpå P4 (samma 71×21-format) och tar P4:ans SIGNALKANT edge A via en
FEMALE socket (P4 bär male-stiften). Fan-out till greppets I/O via STÅENDE JST-PH
(kabel rakt upp). Optikmodulen (edge B, under) förblir ren optik.

ORIENTERING: USB-upp (verifierad). FC-frame = P4-frame (lång axel = x), FC ligger rakt
ovanför P4 i samma orientering → socket-paddar i samma (x,y) som P4 edge-A-stiften.

EDGE A, pin n castellation: P4-x = -31 + (n-1)*2.54, y = +9.28. Använda pin 6..20:
  6 GPIO29  7 GPIO28  8 GND  9 GPIO50  10 GPIO49  11 GPIO5  12 GPIO4
  13 GND  14 GPIO3  15 GPIO2  16 GPIO8(SCL)  17 GPIO7(SDA)
  18 GND  19 GPIO24(MODE_A)  20 GPIO25(MODE_B)
Edge A saknar kraftskena → 3V3 matas via edge-B kraft-tapp (J2) från P4 edge B.
GPIO50 (tidigare reserv) driver IMU2:ns INT (I²C, delar NFC-bussen).
GPIO24/25 driver 4-läges rotarykopplare (MODE_A/MODE_B, binärt kodad).
"""
from skidl import Part, Pin, Net, generate_netlist, SKIDL, TEMPLATE


def mk(name, ref, pins, fp, value=""):
    p = Part(tool=SKIDL, name=name, ref_prefix=ref, dest=TEMPLATE)
    p.add_pins(*[Pin(num=str(n), name=str(nm)) for n, nm in pins])
    p.footprint = fp
    if value:
        p.value = value
    return p


# ---------- parttyper ----------
# FEMALE socket mot P4 edge A (15 stift, pos 6..20). P4 bär male-stiften.
P4A = mk("P4_EDGE_A", "J", [(i, i) for i in range(1, 16)],
         "Connector_PinSocket_2.54mm:PinSocket_1x15_P2.54mm_Vertical", "P4-socket (edge A)")
# FEMALE socket mot P4 EDGE B (kraft-tapp): FC:s bortre långsida sitter över edge B,
# tar 3V3+GND DIREKT därifrån (edge B pin 3=GND, 4=EN(nc), 5=3V3). Ingen kabel/bygel —
# edge B blir en genomgående stackande stiftlist: optik under, FC ovan.
PWRB = mk("PWR_EDGEB", "J", [(1, "GND"), (2, "ENnc"), (3, "P3V3")],
          "Connector_PinSocket_2.54mm:PinSocket_1x03_P2.54mm_Vertical", "edge-B kraft-tapp 3V3+GND")
SW2 = lambda nm: mk(nm, "J", [(1, "SIG"), (2, "GND")],
                    "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", nm)
REC = mk("RECOIL_CTRL", "J", [(1, "PWM"), (2, "FAULT"), (3, "GND")],
         "Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical", "recoil-styrning")
NFC = mk("NFC_PN532", "J", [(1, "SDA"), (2, "SCL"), (3, "3V3"), (4, "GND")],
         "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical", "NFC PN532 (I²C)")
OLED = mk("OLED_I2C", "J", [(1, "GND"), (2, "3V3"), (3, "SCL"), (4, "SDA")],
          "Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical", "OLED SSD1306 (I²C, GND/3V3/SCL/SDA)")
MODE = mk("MODE_SEL", "J", [(1, "MODE_A"), (2, "MODE_B"), (3, "GND")],
          "Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical", "4-läges rotarykopplare (MODE_A/MODE_B/GND)")
# EXTRA IMU — TDK IIM-42653 (LGA-14), samma som optiken men I²C. Pin-nr per DS-000529:
#   8=VDD 5=VDDIO 6=GND 7=RESV(→GND) 13=SCLK(SCL) 14=SDI(SDA) 1=SDO(AD0) 12=CS(→VDDIO=I²C) 4=INT1
# (drop-in: 8 signalstift identiska med 426xx; AUX1 2/3/10/11 = NC. I²C 0x68/0x69 via AD0.)
IMU = mk("ICM-42688-P", "U", [(i, i) for i in range(1, 15)],
         "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "ICM-42688-P")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0402_1005Metric")
RES = lambda v: RES_T(value=v)
CAP = lambda v: CAP_T(value=v)
MH = lambda n: mk(f"MH{n}", "H", [(1, "1")], "strilas:MountingHole_1.7mm", "Ø1.7_P4_standoff")

# ---------- nät ----------
GND, P3V3 = Net("GND"), Net("+3V3")
TRIG, RACK, MAG_REL, MAGWELL = Net("TRIG"), Net("RACK"), Net("MAG_REL"), Net("MAGWELL")
REC_PWM, REC_FLT = Net("RECOIL_PWM"), Net("RECOIL_FAULT")
SDA, SCL = Net("NFC_SDA"), Net("NFC_SCL")
IMU2_INT, IMU3_INT = Net("IMU2_INT"), Net("IMU3_INT")
MODE_A, MODE_B = Net("MODE_A"), Net("MODE_B")

# ---------- instansiera ----------
J1 = P4A(); Jpwr = PWRB()
Jtrig = SW2("TRIGGER")(); Jrack = SW2("RACK_SW")()
Jmag = SW2("MAG_REL_SW")(); Jmagw = SW2("MAGWELL_SW")()
Jrec = REC(); Jnfc = NFC(); Joled = OLED(); Jmode = MODE()
U1 = IMU(); U2 = IMU()
Rsda = RES("4k7"); Rscl = RES("4k7")            # I²C pull-ups (delas av NFC + båda IMU + OLED)
Rma = RES("4k7"); Rmb = RES("4k7")              # MODE_A/MODE_B pull-ups
Cn1 = CAP("100nF"); Cn2 = CAP("1uF")            # 3V3-rail/NFC-avkoppling
Ci1 = CAP("100nF"); Ci2 = CAP("100nF")          # IMU U1 VDD/VDDIO
Ci3 = CAP("100nF"); Ci4 = CAP("100nF")          # IMU U2 VDD/VDDIO
H1, H2, H3, H4 = MH(1)(), MH(2)(), MH(3)(), MH(4)()

# ---------- J1 = P4 edge A pin 6..20 ----------
# FC speglad om långaxeln (y=120) så J1+J2 byter långsida → J1 dockar edge A på RIKTIGA P4.
# OBS pin-ORDNINGEN är OFÖRÄNDRAD (original): FC J1 (B.Cu) möter edge A (P4 F.Cu) = MOTSATT
# lager → speglingen + ansikts-flippen tar ut varandra så fysisk J1.k möter edge A pin (k+5).
# (Verifierat mot riktig P4-geometri + kalibrerat mot optik↔edge B = 8/8.)
#   J1.1  pin6  GPIO29  MAGWELL          J1.7  pin12 GPIO4  TRIG
#   J1.2  pin7  GPIO28  RECOIL_FAULT     J1.8  pin13 GND
#   J1.3  pin8  GND                      J1.9  pin14 GPIO3  MAG_REL
#   J1.4  pin9  GPIO50  IMU2_INT         J1.10 pin15 GPIO2  RECOIL_PWM
#   J1.5  pin10 GPIO49  IMU3_INT         J1.11 pin16 GPIO8  NFC_SCL
#   J1.6  pin11 GPIO5   RACK             J1.12 pin17 GPIO7  NFC_SDA
#   J1.13 pin18 GND
#   J1.14 pin19 GPIO24  MODE_A (lägesväljare bit 0)
#   J1.15 pin20 GPIO25  MODE_B (lägesväljare bit 1)
J1[1] += MAGWELL; J1[2] += REC_FLT; J1[3] += GND; J1[4] += IMU2_INT
J1[5] += IMU3_INT
J1[6] += RACK; J1[7] += TRIG; J1[8] += GND
J1[9] += MAG_REL; J1[10] += REC_PWM; J1[11] += SCL; J1[12] += SDA
J1[13] += GND; J1[14] += MODE_A; J1[15] += MODE_B

# ---------- edge-B kraft-tapp (3V3+GND direkt från P4 edge B) + fan-out ----------
Jpwr["P3V3"] += P3V3; Jpwr["GND"] += GND      # pin2 (ENnc) lämnas NC
Jtrig["SIG"] += TRIG; Jtrig["GND"] += GND
Jrack["SIG"] += RACK; Jrack["GND"] += GND
Jmag["SIG"] += MAG_REL; Jmag["GND"] += GND
Jmagw["SIG"] += MAGWELL; Jmagw["GND"] += GND
Jrec["PWM"] += REC_PWM; Jrec["FAULT"] += REC_FLT; Jrec["GND"] += GND
Jnfc["SDA"] += SDA; Jnfc["SCL"] += SCL; Jnfc["3V3"] += P3V3; Jnfc["GND"] += GND

# ---------- OLED-display (I²C, delar NFC-bussen) ----------
# SSD1306 adress 0x3C/0x3D → ingen krock med NFC 0x24/0x48 eller IMU 0x68/0x69.
# JST-pinout: GND/3V3/SCL/SDA (standardordning på SSD1306-moduler)
Joled["GND"] += GND; Joled["3V3"] += P3V3; Joled["SCL"] += SCL; Joled["SDA"] += SDA

# ---------- 4-läges rotarykopplare (binärt kodad, pull-ups på kort) ----------
# Koppling: switch common=GND, utgång A → MODE_A, utgång B → MODE_B.
# Läge 0 (safe):  MODE_A=H  MODE_B=H  (båda öppna/pull-up)
# Läge 1 (single): MODE_A=L  MODE_B=H  (A → GND)
# Läge 2 (burst): MODE_A=H  MODE_B=L  (B → GND)
# Läge 3 (auto):  MODE_A=L  MODE_B=L  (båda → GND)
Jmode["MODE_A"] += MODE_A; Jmode["MODE_B"] += MODE_B; Jmode["GND"] += GND
Rma[1] += P3V3; Rma[2] += MODE_A
Rmb[1] += P3V3; Rmb[2] += MODE_B

# ---------- 2× extra IMU (I²C, delar NFC-bussen) ----------
# U1 = adress 0x69 (AD0 hög), INT=GPIO50 ; U2 = adress 0x68 (AD0 låg), INT=GPIO49.
# pin: 8=VDD 5=VDDIO 6=GND 12=CS(hög→I²C) 1=SDO/AD0(adress) 13=SCL 14=SDA 4=INT1
U1[8] += P3V3; U1[5] += P3V3; U1[6] += GND; U1[7] += GND; U1[12] += P3V3
U1[1] += P3V3; U1[13] += SCL; U1[14] += SDA; U1[4] += IMU2_INT      # AD0 hög → 0x69
U2[8] += P3V3; U2[5] += P3V3; U2[6] += GND; U2[7] += GND; U2[12] += P3V3
U2[1] += GND;  U2[13] += SCL; U2[14] += SDA; U2[4] += IMU3_INT      # AD0 låg → 0x68
Ci1[1] += P3V3; Ci1[2] += GND; Ci2[1] += P3V3; Ci2[2] += GND
Ci3[1] += P3V3; Ci3[2] += GND; Ci4[1] += P3V3; Ci4[2] += GND

# ---------- I²C pull-ups + 3V3-avkoppling ----------
Rsda[1] += P3V3; Rsda[2] += SDA
Rscl[1] += P3V3; Rscl[2] += SCL
Cn1[1] += P3V3; Cn1[2] += GND
Cn2[1] += P3V3; Cn2[2] += GND

# ---------- mekanik (4 hål i linje med P4-standoffsen → genomgående stack) ----------
for H in (H1, H2, H3, H4):
    H[1] += GND

generate_netlist(file_="hardware/firecontrol.net")
print("wrote hardware/firecontrol.net")
