#!/usr/bin/env python3
"""STRILAS — VAPEN-OPTIKMODUL: kretsdefinition i kod (SKiDL → KiCad-netlista).
Genererar 'hardware/weapon-module.net' (importeras i KiCad/kinet2pcb för layout→Gerbers).

Driver för v1 = enkel, ögonsäker: effektresistor (Rset) sätter HÅRT strömtak,
N-FET (Q1) gatar 56 kHz. (Buck-CC = effektivitetsuppgradering, se design-resolution §2.)
Sikteskamera = USB OV9281 GS NoIR — sitter MEKANISKT bakom kortet (lins genom Ø16-hål),
ansluts till P4 via USB-kabel → finns INTE elektriskt på detta kort.

Skottstråle-emitter = Vishay VSMA1094750X02 (940 nm). IMU = TDK ICM-45686 (LGA-14).
Bägge har kund-footprints i hardware/strilas.pretty (verifierade mot datablad).
IMU-pinout verifierad mot TDK AN-000483 Fig.2 (pin-kompatibel ICM-45605/45686).
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
P4IF = mk("P4_IFACE", "J", [(i, i) for i in range(1, 13)],
          "Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical", "P4-carrier-header")
BATT = mk("BATT_IN", "J", [(1, "VBAT"), (2, "GND")],
          "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "2S batteri")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v, fp="Resistor_SMD:R_0805_2012Metric": RES_T(value=v, footprint=fp)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
PFET = mk("AO3401", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3401")
NFET = mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400")
PTC = mk("PTC", "F", [(1, "~"), (2, "~")], "Fuse:Fuse_1206_3216Metric", "PTC_1A")
TVS = mk("SMBJ12A", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SMB", "SMBJ12A")
LED = mk("VSMA1094750", "D", [(1, "A"), (2, "K")],
         "strilas:IR_Emitter_Vishay_VSMA1094750", "VSMA1094750X02_940nm")
# ICM-45686 LGA-14 — pin-nr enligt TDK AN-000483 Fig.2:
# 1 SDO  2 RESV  3 RESV  4 INT1  5 VDDIO  6 GND  7 RESV
# 8 VDD  9 INT2  10 RESV 11 RESV 12 CS  13 SCLK 14 SDI
IMU = mk("ICM-45686", "U", [(i, i) for i in range(1, 15)],
         "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "ICM-45686")
MH = lambda n: mk(f"MH{n}", "H", [(1, "1")], "MountingHole:MountingHole_2.5mm", "M2.5")

# ---------- nät ----------
VBAT_IN, VBAT_F, VBAT, GND, P3V3 = Net("VBAT_IN"), Net("VBAT_F"), Net("VBAT"), Net("GND"), Net("+3V3")
IR_MOD, SCK, MOSI, MISO, nCS, INT = (Net(n) for n in ("IR_MOD", "SCK", "MOSI", "MISO", "nCS", "IMU_INT"))
STR1, LEDC, IRG = Net("LED_MID"), Net("LED_CATH"), Net("Q1_GATE")

# ---------- instansiera ----------
J1 = P4IF(); J2 = BATT()
F1 = PTC(); Q2 = PFET(); Rg2 = RES("100k"); Dtvs = TVS()
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric")
Cbulk = CAP("220uF", "Capacitor_SMD:CP_Elec_6.3x7.7")
Rset = RES("3R3_2W", "Resistor_SMD:R_2512_6332Metric")
D1, D2 = LED(), LED()
Q1 = NFET(); Rg = RES("220R")
U2 = IMU(); Cd1 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric")
Cd2 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric"); Cd3 = CAP("1uF")
H1, H2, H3 = MH(1)(), MH(2)(), MH(3)()

# ---------- J2 = batteri-in (2S) ; J1 = P4-carrier-header ----------
J2["VBAT"] += VBAT_IN; J2["GND"] += GND
# J1 till P4: VSYS(=VBAT) ut till P4, 3V3 in från P4, signaler till P4-GPIO
J1[1] += VBAT; J1[2] += P3V3; J1[3] += GND; J1[4] += IR_MOD       # VSYS / 3V3 / GND / IR_MOD(GPIO20)
J1[5] += SCK; J1[6] += MOSI; J1[7] += MISO; J1[8] += nCS          # SPI (GPIO22/23/26/27)
J1[9] += INT; J1[10] += GND; J1[11] += GND; J1[12] += GND         # INT(GPIO32) + GND

# ---------- kraftinmatning + skydd ----------
F1[1] += VBAT_IN; F1[2] += VBAT_F                 # PTC-säkring
Q2["D"] += VBAT_F; Q2["S"] += VBAT; Q2["G"] += Rg2[1]; Rg2[2] += GND   # reverse-polarity P-FET
Dtvs["K"] += VBAT; Dtvs["A"] += GND               # TVS-clamp
Cin[1] += VBAT; Cin[2] += GND
Cbulk[1] += VBAT; Cbulk[2] += GND                 # reservoar för pulsen

# ---------- IR-emitterdriver (Rset hårt strömtak + 56 kHz-gate) ----------
Rset[1] += VBAT; Rset[2] += D1["A"]               # effektresistor sätter Imax
D1["K"] += STR1; D2["A"] += STR1; D2["K"] += LEDC # 2 LED i serie
Q1["D"] += LEDC; Q1["S"] += GND                   # N-FET drar strängen mot GND
Rg[1] += IR_MOD; Rg[2] += IRG; Q1["G"] += IRG     # 56 kHz på gaten

# ---------- IMU (SPI 4-wire) + avkoppling ----------
# pin-nr (TDK AN-000483 Fig.2):  8=VDD 5=VDDIO 6=GND 13=SCLK 14=SDI 1=SDO 12=CS 4=INT1
U2[8] += P3V3; U2[5] += P3V3; U2[6] += GND        # VDD / VDDIO / GND
U2[13] += SCK; U2[14] += MOSI; U2[1] += MISO; U2[12] += nCS; U2[4] += INT
# pinnar 2,3,7,9,10,11 = RESV/INT2 -> ej anslutna (NC), enligt datablad
Cd1[1] += P3V3; Cd1[2] += GND; Cd2[1] += P3V3; Cd2[2] += GND; Cd3[1] += P3V3; Cd3[2] += GND

# ---------- mekanik (hål till GND) ----------
for H in (H1, H2, H3):
    H[1] += GND

generate_netlist(file_="hardware/weapon-module.net")
print("wrote hardware/weapon-module.net")
