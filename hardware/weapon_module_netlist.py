#!/usr/bin/env python3
"""STRILAS — VAPEN-OPTIKMODUL: kretsdefinition i kod (SKiDL → KiCad-netlista).
Genererar 'hardware/weapon-module.net' (importeras i KiCad/kinet2pcb för layout→Gerbers).

Driver för v1 = enkel, ögonsäker: effektresistor (Rset) sätter HÅRT strömtak,
N-FET (Q1) gatar 56 kHz. (Buck-CC = effektivitetsuppgradering, se design-resolution §2.)
Kameran (OV5640) sitter MEKANISKT i mitten; dess FFC går direkt till P4 → ej elektriskt här.

OBS: IC-pinnar (IMU) ska verifieras mot datablad innan layout — netlistan = BOM + konnektivitet.
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
HDR = mk("Conn_2x05", "J", [(i, i) for i in range(1, 11)],
         "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", "STRILAS_J1")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v, fp="Resistor_SMD:R_0805_2012Metric": RES_T(value=v, footprint=fp)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
PFET = mk("AO3401", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3401")
NFET = mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400")
PTC = mk("PTC", "F", [(1, "~"), (2, "~")], "Fuse:Fuse_1206_3216Metric", "PTC_1A")
TVS = mk("SMBJ12A", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SMB", "SMBJ12A")
LED = mk("SFH4715AS_940", "D", [(1, "A"), (2, "K")], "LED_SMD:LED_3.2x2.8mm", "940nm_OSLON")
IMU = mk("ICM-45686", "U", [(1, "VDD"), (2, "VDDIO"), (3, "GND"), (4, "SCLK"),
                            (5, "SDI"), (6, "SDO"), (7, "nCS"), (8, "INT1")],
         "Sensor_Motion:InvenSense_ICM-426xx_LGA-14_2.5x3mm", "ICM-45686")
MH = lambda n: mk(f"MH{n}", "H", [(1, "1")], "MountingHole:MountingHole_2.5mm", "M2.5")

# ---------- nät ----------
VBAT_IN, VBAT_F, VBAT, GND, P3V3 = Net("VBAT_IN"), Net("VBAT_F"), Net("VBAT"), Net("GND"), Net("+3V3")
IR_MOD, SCK, MOSI, MISO, nCS, INT = (Net(n) for n in ("IR_MOD", "SCK", "MOSI", "MISO", "nCS", "IMU_INT"))
STR1, LEDC, IRG = Net("LED_MID"), Net("LED_CATH"), Net("Q1_GATE")

# ---------- instansiera ----------
J1 = HDR()
F1 = PTC(); Q2 = PFET(); Rg2 = RES("100k"); Dtvs = TVS()
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric")
Cbulk = CAP("220uF", "Capacitor_SMD:CP_Elec_6.3x7.7")
Rset = RES("3R3_2W", "Resistor_SMD:R_2512_6332Metric")
D1, D2 = LED(), LED()
Q1 = NFET(); Rg = RES("220R")
U2 = IMU(); Cd1 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric")
Cd2 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric"); Cd3 = CAP("1uF")
H1, H2, H3 = MH(1)(), MH(2)(), MH(3)()

# ---------- J1 (2x5) pinmappning ----------
J1[1] += VBAT_IN; J1[2] += GND; J1[3] += IR_MOD; J1[4] += P3V3; J1[5] += GND
J1[6] += SCK; J1[7] += MOSI; J1[8] += MISO; J1[9] += nCS; J1[10] += INT

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

# ---------- IMU (SPI) + avkoppling ----------
U2["VDD"] += P3V3; U2["VDDIO"] += P3V3; U2["GND"] += GND
U2["SCLK"] += SCK; U2["SDI"] += MOSI; U2["SDO"] += MISO; U2["nCS"] += nCS; U2["INT1"] += INT
Cd1[1] += P3V3; Cd1[2] += GND; Cd2[1] += P3V3; Cd2[2] += GND; Cd3[1] += P3V3; Cd3[2] += GND

# ---------- mekanik (hål till GND) ----------
for H in (H1, H2, H3):
    H[1] += GND

generate_netlist(file_="hardware/weapon-module.net")
print("wrote hardware/weapon-module.net")
