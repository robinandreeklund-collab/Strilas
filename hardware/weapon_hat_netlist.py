#!/usr/bin/env python3
"""STRILAS — VAPEN-HAT (v2, förenklad): kretsdefinition i kod (SKiDL → KiCad-netlista).

HAT som pluggar på ett FÄRDIGT CM5-carrier-korts 40-pin GPIO-header (t.ex. CM5 Nano Base).
Carrier-kortet sköter CM5↔DF40 + kamerans 22-pin MIPI-CSI; HAT:en bär resten:
  • CC-sänka (OPA171 + DPAK pass-FET + 0R2 sense, 1 A tak / 3 A DNP) → emitter-JST → optik-huvud
  • IMU (ICM-42688-P, SPI; VDDIO=3V3 från headern)
  • 2S → 5 V buck → BACK-POWER carriern via headerns 5V-stift; VBAT emitter-rail (skild)
  • batteri-sense via I²C-ADC (CM5 saknar ADC)
  • fire-control-IO: trigger/rack/mag-release/magwell, recoil, NFC, MODE, PTT

INGEN DF40, INGEN MIPI på vårt kort → bara stock-footprints → placeras/routas direkt.
Optik-huvud = hardware/optik_head.py. Kameran → carriers CSI (rör ej HAT:en).

Kör:  python3 hardware/weapon_hat_netlist.py  → hardware/weapon-hat.net
"""
from skidl import Part, Pin, Net, generate_netlist, SKIDL, TEMPLATE


def mk(name, ref, pins, fp, value=""):
    p = Part(tool=SKIDL, name=name, ref_prefix=ref, dest=TEMPLATE)
    p.add_pins(*[Pin(num=str(n), name=str(nm)) for n, nm in pins])
    p.footprint = fp
    if value:
        p.value = value
    return p

# ---------- 40-pin RPi-header (HAT ↔ CM5-carrier) — standard RPi-pinout ----------
# HONA-sockel på HAT:ens BAKSIDA i kortets CENTRUM → trycks rakt ner på carrierns
# centrerade 40-pin stiftlist (CM5-NANO-B). Alla övriga komponenter på FRAMSIDAN.
HDR_PINS = [(1,"3V3"),(2,"5V"),(3,"GPIO2_SDA"),(4,"5V"),(5,"GPIO3_SCL"),(6,"GND"),(7,"GPIO4"),
            (8,"GPIO14"),(9,"GND"),(10,"GPIO15"),(11,"GPIO17"),(12,"GPIO18"),(13,"GPIO27"),(14,"GND"),
            (15,"GPIO22"),(16,"GPIO23"),(17,"3V3"),(18,"GPIO24"),(19,"GPIO10_MOSI"),(20,"GND"),
            (21,"GPIO9_MISO"),(22,"GPIO25"),(23,"GPIO11_SCLK"),(24,"GPIO8_CE0"),(25,"GND"),(26,"GPIO7_CE1"),
            (27,"GPIO0"),(28,"GPIO1"),(29,"GPIO5"),(30,"GND"),(31,"GPIO6"),(32,"GPIO12"),(33,"GPIO13"),
            (34,"GND"),(35,"GPIO19"),(36,"GPIO16"),(37,"GPIO26"),(38,"GPIO20"),(39,"GND"),(40,"GPIO21")]
HDR = mk("RPi_40pin", "J", HDR_PINS,
         "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical", "40-pin HONA → CM5-carrier (baksida, centrum)")

BATT = mk("BATT_2S", "J", [(1, "VBAT"), (2, "GND")], "Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal", "2S batteri (JST-XH)")
EMIT = mk("EmitConn", "J", [(1, "VBAT"), (2, "IR_MOD"), (3, "GND")],
          "Connector_JST:JST_PH_S3B-PH-K_1x03_P2.00mm_Horizontal", "→ optik (VBAT·IR_MOD·GND; CC-sänka på optik)")
SW = lambda n, a, b: mk(f"SW_{n}", "J", [(1, a), (2, b)],
                        "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", n)
RECOIL = mk("RecoilConn", "J", [(1, "VBAT"), (2, "PWM"), (3, "FAULT"), (4, "GND")],
            "Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal", "recoil-driver")
NFC = mk("PN532", "J", [(1, "VCC"), (2, "GND"), (3, "SDA"), (4, "SCL")],
         "Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal", "NFC (I²C)")

RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v, fp="Resistor_SMD:R_0805_2012Metric": RES_T(value=v, footprint=fp)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
PFET = mk("AO3401", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3401")
DFET = mk("AOD4184A", "Q", [(1, "G"), (2, "D"), (3, "S")], "Package_TO_SOT_SMD:TO-252-2", "AOD4184A")
OPAMP = mk("OPA171", "U", [(1, "OUT"), (2, "V-"), (3, "IN+"), (4, "IN-"), (5, "V+")],
           "Package_TO_SOT_SMD:SOT-23-5", "OPA171")
BUCK = mk("Buck_5V_3A", "U", [(1, "VIN"), (2, "EN"), (3, "GND"), (4, "VOUT")],
          "Package_TO_SOT_SMD:TO-263-7_TabPin8", "2S→5V @≥3A (modul/IC)")
ADC = mk("ADS1115", "U", [(1, "VDD"), (2, "GND"), (3, "SCL"), (4, "SDA"), (5, "AIN0")],
         "Package_SO:TSSOP-10_3x3mm_P0.5mm", "I²C-ADC (batteri-sense)")
IMU = mk("ICM-42688-P", "U", [(1,"SDO"),(4,"INT1"),(5,"VDDIO"),(6,"GND"),(8,"VDD"),(12,"CS"),(13,"SCLK"),(14,"SDI")],
         "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "ICM-42688-P")
PTC = mk("PTC", "F", [(1, "~"), (2, "~")], "Fuse:Fuse_1812_4532Metric", "PTC_3A")
TVS = mk("SMBJ12A", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SMB", "SMBJ12A")

# ---------- nät ----------
VBAT_IN, VBAT_F, VBAT, V5, V3, GND = (Net(n) for n in ("VBAT_IN","VBAT_F","VBAT","+5V","+3V3","GND"))
IR_MOD = Net("IR_MOD")
SCK, MOSI, MISO, nCS, IMU_INT = (Net(n) for n in ("SCK","MOSI","MISO","nCS","IMU_INT"))
I2C_SCL, I2C_SDA = Net("I2C_SCL"), Net("I2C_SDA")
VBAT_SENSE = Net("VBAT_SENSE")
TRIG,RACK,MAGREL,MAGWELL,RPWM,RFAULT,MODE0,MODE1,PTT = (Net(n) for n in
    ("TRIG","RACK","MAGREL","MAGWELL","RECOIL_PWM","RECOIL_FAULT","MODE0","MODE1","PTT"))

# ---------- instansiera ----------
H = HDR(); J2 = BATT(); Je = EMIT()
F1 = PTC(); Qrp = PFET(); Rg = RES("100k"); Dt = TVS()
Cin = CAP("10uF","Capacitor_SMD:C_1206_3216Metric"); Cbulk = CAP("100uF","Capacitor_SMD:C_1210_3225Metric")
Ub = BUCK(); Lbi = CAP("22uF","Capacitor_SMD:C_1210_3225Metric"); Lbo = CAP("22uF","Capacitor_SMD:C_1210_3225Metric")
# CC-sänkan (OPA171+DPAK+sense+delare) FLYTTAD till optik-PCB:n (kortare puls-loop, frigör HAT-yta).
U_imu = IMU(); Ci1 = CAP("100nF","Capacitor_SMD:C_0402_1005Metric"); Ci2 = CAP("1uF")
U_adc = ADC(); Rsa = RES("100k"); Rsb = RES("47k"); Csns = CAP("100nF"); Cadc = CAP("100nF")
Jt = SW("TRIGGER","TRIG","GND")(); Jr = SW("RACK","RACK","GND")()
Jm = SW("MAGREL","MAGREL","GND")(); Jw = SW("MAGWELL","MAGWELL","GND")()
Jrec = RECOIL(); Jnfc = NFC()
Rmode0 = RES("10k"); Rmode1 = RES("10k")
Rt = RES("10k"); Rr = RES("10k"); Rm = RES("10k"); Rw = RES("10k")
Ri1 = RES("4k7"); Ri2 = RES("4k7")

# ---------- 40-pin header: kraft + signaler (RPi-pinout) ----------
H[2] += V5; H[4] += V5                                  # 5V BACK-FEED in i carriern
for p in (6,9,14,20,25,30,34,39): H[p] += GND
H[1] += V3; H[17] += V3                                 # 3V3 från carriern (IMU VDDIO)
H[19] += MOSI; H[21] += MISO; H[23] += SCK; H[24] += nCS; H[22] += IMU_INT   # SPI + INT
H[12] += IR_MOD                                         # GPIO18 (HW-PWM) → 56 kHz
H[3] += I2C_SDA; H[5] += I2C_SCL                        # I²C (ADC + NFC)
H[13] += TRIG; H[15] += RACK; H[16] += MAGREL; H[18] += MAGWELL
H[32] += RPWM; H[36] += RFAULT; H[37] += MODE0; H[38] += MODE1; H[40] += PTT

# ---------- kraft: 2S → skydd → buck → 5V (back-feed) ; VBAT → emitter-rail ----------
J2["VBAT"] += VBAT_IN; J2["GND"] += GND
F1[1] += VBAT_IN; F1[2] += VBAT_F
Qrp["D"] += VBAT_F; Qrp["S"] += VBAT; Qrp["G"] += Rg[1]; Rg[2] += GND
Dt["K"] += VBAT; Dt["A"] += GND; Cin[1] += VBAT; Cin[2] += GND; Cbulk[1] += VBAT; Cbulk[2] += GND
Ub["VIN"] += VBAT; Ub["EN"] += VBAT; Ub["GND"] += GND; Ub["VOUT"] += V5
Lbi[1] += VBAT; Lbi[2] += GND; Lbo[1] += V5; Lbo[2] += GND

# ---------- emitter-kontakt → optik (VBAT + IR_MOD + GND; CC-sänkan sitter på optik-PCB:n) ----------
Je["VBAT"] += VBAT; Je["IR_MOD"] += IR_MOD; Je["GND"] += GND

# ---------- IMU (SPI; VDD/VDDIO = 3V3 från headern) ----------
U_imu["VDD"] += V3; U_imu["VDDIO"] += V3; U_imu["GND"] += GND
U_imu["SCLK"] += SCK; U_imu["SDI"] += MOSI; U_imu["SDO"] += MISO; U_imu["CS"] += nCS; U_imu["INT1"] += IMU_INT
Ci1[1] += V3; Ci1[2] += GND; Ci2[1] += V3; Ci2[2] += GND

# ---------- batteri-sense → I²C-ADC ----------
Rsa[1] += VBAT; Rsa[2] += VBAT_SENSE; Rsb[1] += VBAT_SENSE; Rsb[2] += GND; Csns[1] += VBAT_SENSE; Csns[2] += GND
U_adc["VDD"] += V3; U_adc["GND"] += GND; U_adc["SCL"] += I2C_SCL; U_adc["SDA"] += I2C_SDA; U_adc["AIN0"] += VBAT_SENSE
Cadc[1] += V3; Cadc[2] += GND

# ---------- fire-control ----------
Jt["TRIG"] += TRIG; Jt["GND"] += GND; Jr["RACK"] += RACK; Jr["GND"] += GND
Jm["MAGREL"] += MAGREL; Jm["GND"] += GND; Jw["MAGWELL"] += MAGWELL; Jw["GND"] += GND
Rt[1] += V3; Rt[2] += TRIG; Rr[1] += V3; Rr[2] += RACK; Rm[1] += V3; Rm[2] += MAGREL; Rw[1] += V3; Rw[2] += MAGWELL
Jrec["VBAT"] += VBAT; Jrec["PWM"] += RPWM; Jrec["FAULT"] += RFAULT; Jrec["GND"] += GND
Jnfc["VCC"] += V3; Jnfc["GND"] += GND; Jnfc["SDA"] += I2C_SDA; Jnfc["SCL"] += I2C_SCL
Rmode0[1] += MODE0; Rmode0[2] += GND; Rmode1[1] += MODE1; Rmode1[2] += GND
Ri1[1] += V3; Ri1[2] += I2C_SCL; Ri2[1] += V3; Ri2[2] += I2C_SDA

generate_netlist(file_="hardware/weapon-hat.net")
print("wrote hardware/weapon-hat.net")
