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
EMIT = mk("EmitConn", "J", [(1, "VBAT"), (2, "IR_MOD"), (3, "GND"), (4, "EMIT_HI")],
          "Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal", "→ optik (VBAT·IR_MOD·GND·EMIT_HI; CC-sänka på optik)")
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
PFET = mk("AOD4185", "Q", [(1, "G"), (2, "D"), (3, "S")], "Package_TO_SOT_SMD:TO-252-2", "AOD4185")  # P-ch 40V/40A 15mΩ (delad VBAT-väg ~7A topp)
DFET = mk("AOD4184A", "Q", [(1, "G"), (2, "D"), (3, "S")], "Package_TO_SOT_SMD:TO-252-2", "AOD4184A")
OPAMP = mk("OPA171", "U", [(1, "OUT"), (2, "V-"), (3, "IN+"), (4, "IN-"), (5, "V+")],
           "Package_TO_SOT_SMD:SOT-23-5", "OPA171")
# 2S→5V buck: AP63203WU (Diodes, 3A synkron, 3,8–32V in, integrerade FET). Stift VERIFIERADE mot
# KiCad-symbolbiblioteket: 1=FB 2=EN 3=IN 4=GND 5=SW 6=BST. → induktor + FB-delare + BST-cap externt.
BUCK = mk("AP63203WU", "U", [(1,"FB"),(2,"EN"),(3,"IN"),(4,"GND"),(5,"SW"),(6,"BST")],
          "Package_TO_SOT_SMD:TSOT-23-6", "AP63203WU 2S→5V 3A")
IND = mk("L_buck", "L", [(1, "1"), (2, "2")], "Inductor_SMD:L_Taiyo-Yuden_MD-5050", "2.2uH")  # Sunlord SWPA5040S2R2MT, Isat 4,5A > 3A-buck-topp
ADC = mk("ADS1115", "U", [(1,"ADDR"),(2,"ALERT"),(3,"GND"),(4,"AIN0"),(8,"VDD"),(9,"SDA"),(10,"SCL")],
         "Package_SO:TSSOP-10_3x3mm_P0.5mm", "ADS1115 I²C-ADC 0x48 (batteri-sense)")
# ADS1115 VSSOP-10 (DGS) stift VERIFIERADE mot TI SBAS444: 1=ADDR 2=ALERT 3=GND 4=AIN0 8=VDD 9=SDA 10=SCL.
IMU = mk("ICM-42688-P", "U", [(1,"SDO"),(4,"INT1"),(5,"VDDIO"),(6,"GND"),(7,"RESV7"),(8,"VDD"),(12,"CS"),(13,"SCLK"),(14,"SDI")],
         "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "ICM-42688-P")
# ICM-42688-P stift (DS-000347): 1=SDO/AD0 2,3,10,11=RESV(NC) 4=INT1 5=VDDIO 6=GND 7=RESV→GND
#   8=VDD 9=INT2/FSYNC(NC) 12=CS 13=SCLK 14=SDI. Ingen REGOUT-pinne → VDD/VDDIO-caps räcker.
# 2 EXTRA IMU på I²C — SAMMA ICM-42688-P som IMU1 (i lager hos NextPCB; IIM-42653 hade ~400 d ledtid).
# ICM-42688-P kör I²C lika bra (CS→VDDIO, AD0-adress). Numeriska stift per DS-000347 (samma LGA-14):
#   8=VDD 5=VDDIO 6=GND 7=RESV(→GND) 13=SCL 14=SDA 1=SDO/AD0(adress) 12=CS(→VDDIO=I²C) 4=INT1
#   → 3 IMU totalt på HAT/FC. I²C 0x68/0x69 via AD0 (krockar ej med ADS1115 0x48 el. PN532).
IMU_I2C = mk("ICM-42688-P", "U", [(i, str(i)) for i in range(1, 15)],
             "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "ICM-42688-P")
PTC = mk("PTC", "F", [(1, "~"), (2, "~")], "Fuse:Fuse_1812_4532Metric", "PTC_3A")   # 3A-hold 16V (sampled), slö → ser ~2,5A snitt
TVS = mk("SMBJ12A", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SMB", "SMBJ12A")
TVS5 = mk("SMAJ5.0A", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SMA", "SMAJ5.0A")   # 5V-rail transientskydd
EEPROM = mk("AT24C32", "U", [(1,"A0"),(2,"A1"),(3,"A2"),(4,"GND"),(5,"SDA"),(6,"SCL"),(7,"WP"),(8,"VCC")],
            "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "AT24C32 HAT-ID EEPROM 0x50")
# ESP32-C6 ESP-NOW-brygga: hona-SOCKEL på BAKSIDAN → Seeed XIAO ESP32-C6 daughterboard trycks dit
# (eget LDO + U.FL-antenn + USB-C för flash). Bara 4 nät behövs: +5V, GND, UART (TX/RX) ↔ CM5.
# Pad-numrering (footprint XIAO_ESP32C6_Socket): 1–7 vä = D0..D6/TX, 8–14 hö = 5V,GND,3V3,D10,D9,D8,D7/RX.
XIAO = mk("XIAO_ESP32C6", "J", [(i, str(i)) for i in range(1, 15)],
          "strilas:XIAO_ESP32C6_Socket", "XIAO ESP32-C6 (ESP-NOW-brygga, baksida)")
# AT24C32 standard 24Cxx-pinout: 1-3=A0/A1/A2(→GND=0x50) 4=GND 5=SDA 6=SCL 7=WP(→GND, skrivbar) 8=VCC

# ---------- nät ----------
VBAT_IN, VBAT_F, VBAT, V5, V3, GND = (Net(n) for n in ("VBAT_IN","VBAT_F","VBAT","+5V","+3V3","GND"))
IR_MOD = Net("IR_MOD")
SW_n, BST_n, FB_n = Net("SW_n"), Net("BST_n"), Net("FB_n")   # buck switch/bootstrap/feedback
SCK, MOSI, MISO, nCS, IMU_INT = (Net(n) for n in ("SCK","MOSI","MISO","nCS","IMU_INT"))
IMU2_INT, IMU3_INT = Net("IMU2_INT"), Net("IMU3_INT")
I2C_SCL, I2C_SDA = Net("I2C_SCL"), Net("I2C_SDA")
ID_SD, ID_SC = Net("ID_SD"), Net("ID_SC")              # HAT-ID-EEPROM-buss (GPIO0/1, separat I²C)
VBAT_SENSE = Net("VBAT_SENSE")
TRIG,RACK,MAGREL,MAGWELL,RPWM,RFAULT,MODE0,MODE1,PTT = (Net(n) for n in
    ("TRIG","RACK","MAGREL","MAGWELL","RECOIL_PWM","RECOIL_FAULT","MODE0","MODE1","PTT"))
EMIT_HI = Net("EMIT_HI")          # GPIO13 → optik: hög = 3A-läge (kopplar in parallell-0R1), låg/flytande = 1A
ESP_TX, ESP_RX = Net("ESP_TX"), Net("ESP_RX")   # CM5 UART0 ↔ ESP32-C6-brygga (GPIO14/15)

# ---------- instansiera ----------
H = HDR(); J2 = BATT(); Je = EMIT()
F1 = PTC(); Qrp = PFET(); Rg = RES("100k"); Dt = TVS()
Cin = CAP("10uF","Capacitor_SMD:C_1206_3216Metric"); Cbulk = CAP("100uF","Capacitor_SMD:C_1210_3225Metric")
Ub = BUCK(); Lbi = CAP("22uF","Capacitor_SMD:C_1210_3225Metric"); Lbo = CAP("22uF","Capacitor_SMD:C_1210_3225Metric")
L1 = IND(); Rfb1 = RES("52k3"); Rfb2 = RES("10k")     # buck-induktor + FB-delare (→5,0V)
Cff = CAP("22pF","Capacitor_SMD:C_0402_1005Metric"); Cbst = CAP("100nF","Capacitor_SMD:C_0402_1005Metric")
# CC-sänkan (OPA171+DPAK+sense+delare) FLYTTAD till optik-PCB:n (kortare puls-loop, frigör HAT-yta).
U_imu = IMU(); Ci1 = CAP("100nF","Capacitor_SMD:C_0402_1005Metric"); Ci2 = CAP("1uF")
U_imu2 = IMU_I2C(); U_imu3 = IMU_I2C()                 # 2 extra IMU (I²C) → 3 totalt
Ci3 = CAP("100nF","Capacitor_SMD:C_0402_1005Metric"); Ci4 = CAP("100nF","Capacitor_SMD:C_0402_1005Metric")
Ci5 = CAP("100nF","Capacitor_SMD:C_0402_1005Metric"); Ci6 = CAP("100nF","Capacitor_SMD:C_0402_1005Metric")
U_adc = ADC(); Rsa = RES("100k"); Rsb = RES("47k"); Csns = CAP("100nF"); Cadc = CAP("100nF")
Jt = SW("TRIGGER","TRIG","GND")(); Jr = SW("RACK","RACK","GND")()
Jm = SW("MAGREL","MAGREL","GND")(); Jw = SW("MAGWELL","MAGWELL","GND")()
Jrec = RECOIL(); Jnfc = NFC()
Rmode0 = RES("10k"); Rmode1 = RES("10k")
Rt = RES("10k"); Rr = RES("10k"); Rm = RES("10k"); Rw = RES("10k")
Ri1 = RES("4k7"); Ri2 = RES("4k7")
Dt5 = TVS5(); Cbulk5 = CAP("100uF","Capacitor_SMD:C_1210_3225Metric")   # 5V transientskydd + CM5-bulk
U_eep = EEPROM(); Ceep = CAP("100nF","Capacitor_SMD:C_0402_1005Metric")
Rid1 = RES("3k9"); Rid2 = RES("3k9")                   # ID_SD/ID_SC pull-ups (RPi HAT-spec)
Jc6 = XIAO()                                           # ESP32-C6-brygga-sockel (baksida)

# ---------- 40-pin header: kraft + signaler (RPi-pinout) ----------
H[2] += V5; H[4] += V5                                  # 5V BACK-FEED in i carriern
for p in (6,9,14,20,25,30,34,39): H[p] += GND
H[1] += V3; H[17] += V3                                 # 3V3 från carriern (IMU VDDIO)
H[19] += MOSI; H[21] += MISO; H[23] += SCK; H[24] += nCS; H[22] += IMU_INT   # SPI + INT (IMU1)
H[29] += IMU2_INT; H[31] += IMU3_INT                   # GPIO5/GPIO6 → INT för de 2 I²C-IMU:erna
H[12] += IR_MOD                                         # GPIO18 (HW-PWM) → 56 kHz
H[3] += I2C_SDA; H[5] += I2C_SCL                        # I²C (ADC + NFC)
H[13] += TRIG; H[15] += RACK; H[16] += MAGREL; H[18] += MAGWELL
H[32] += RPWM; H[36] += RFAULT; H[37] += MODE0; H[38] += MODE1; H[40] += PTT
H[27] += ID_SD; H[28] += ID_SC                         # GPIO0/1 = HAT-ID-EEPROM-buss (ID_SD/ID_SC)
H[33] += EMIT_HI                                       # GPIO13 → optikens 3A-väljare (firmware-styrd)
H[8] += ESP_TX; H[10] += ESP_RX                        # GPIO14/15 (UART0 TXD/RXD) → ESP32-C6-brygga

# ---------- kraft: 2S → skydd → buck → 5V (back-feed) ; VBAT → emitter-rail ----------
J2["VBAT"] += VBAT_IN; J2["GND"] += GND
F1[1] += VBAT_IN; F1[2] += VBAT_F
Qrp["D"] += VBAT_F; Qrp["S"] += VBAT; Qrp["G"] += Rg[1]; Rg[2] += GND
Dt["K"] += VBAT; Dt["A"] += GND; Cin[1] += VBAT; Cin[2] += GND; Cbulk[1] += VBAT; Cbulk[2] += GND
Ub["IN"] += VBAT; Ub["EN"] += VBAT; Ub["GND"] += GND   # EN→VBAT = alltid på när batteri finns
Ub["SW"] += SW_n; Ub["BST"] += BST_n; Ub["FB"] += FB_n
L1[1] += SW_n; L1[2] += V5                             # SW → induktor → 5V
Cbst[1] += BST_n; Cbst[2] += SW_n                      # bootstrap-cap
Rfb1[1] += V5; Rfb1[2] += FB_n; Rfb2[1] += FB_n; Rfb2[2] += GND   # FB-delare 52k3/10k → 5,0V (Vref 0,8V)
Cff[1] += V5; Cff[2] += FB_n                           # feedforward-cap (loop-stabilitet)
Lbi[1] += VBAT; Lbi[2] += GND; Lbo[1] += V5; Lbo[2] += GND        # 22µF in/ut
Cbulk5[1] += V5; Cbulk5[2] += GND                      # 100µF output-bulk (CM5-transient)
Dt5["K"] += V5; Dt5["A"] += GND                        # 5V-rail TVS (transient/back-feed-clamp)

# ---------- emitter-kontakt → optik (VBAT + IR_MOD + GND; CC-sänkan sitter på optik-PCB:n) ----------
Je["VBAT"] += VBAT; Je["IR_MOD"] += IR_MOD; Je["GND"] += GND; Je["EMIT_HI"] += EMIT_HI

# ---------- IMU (SPI; VDD/VDDIO = 3V3 från headern) ----------
U_imu["VDD"] += V3; U_imu["VDDIO"] += V3; U_imu["GND"] += GND; U_imu["RESV7"] += GND   # pin7 RESV→GND per DS
U_imu["SCLK"] += SCK; U_imu["SDI"] += MOSI; U_imu["SDO"] += MISO; U_imu["CS"] += nCS; U_imu["INT1"] += IMU_INT
Ci1[1] += V3; Ci1[2] += GND; Ci2[1] += V3; Ci2[2] += GND
# 2 extra IMU på I²C: U_imu2 = 0x69 (AD0=hög), U_imu3 = 0x68 (AD0=låg); CS→3V3 = I²C-läge
U_imu2[8] += V3; U_imu2[5] += V3; U_imu2[6] += GND; U_imu2[7] += GND; U_imu2[12] += V3
U_imu2[1] += V3;  U_imu2[13] += I2C_SCL; U_imu2[14] += I2C_SDA; U_imu2[4] += IMU2_INT
U_imu3[8] += V3; U_imu3[5] += V3; U_imu3[6] += GND; U_imu3[7] += GND; U_imu3[12] += V3
U_imu3[1] += GND; U_imu3[13] += I2C_SCL; U_imu3[14] += I2C_SDA; U_imu3[4] += IMU3_INT
Ci3[1] += V3; Ci3[2] += GND; Ci4[1] += V3; Ci4[2] += GND
Ci5[1] += V3; Ci5[2] += GND; Ci6[1] += V3; Ci6[2] += GND

# ---------- batteri-sense → I²C-ADC ----------
Rsa[1] += VBAT; Rsa[2] += VBAT_SENSE; Rsb[1] += VBAT_SENSE; Rsb[2] += GND; Csns[1] += VBAT_SENSE; Csns[2] += GND
U_adc["VDD"] += V3; U_adc["GND"] += GND; U_adc["SCL"] += I2C_SCL; U_adc["SDA"] += I2C_SDA
U_adc["AIN0"] += VBAT_SENSE; U_adc["ADDR"] += GND      # ADDR→GND = 0x48 (ALERT lämnas NC)
Cadc[1] += V3; Cadc[2] += GND

# ---------- fire-control ----------
Jt["TRIG"] += TRIG; Jt["GND"] += GND; Jr["RACK"] += RACK; Jr["GND"] += GND
Jm["MAGREL"] += MAGREL; Jm["GND"] += GND; Jw["MAGWELL"] += MAGWELL; Jw["GND"] += GND
Rt[1] += V3; Rt[2] += TRIG; Rr[1] += V3; Rr[2] += RACK; Rm[1] += V3; Rm[2] += MAGREL; Rw[1] += V3; Rw[2] += MAGWELL
Jrec["VBAT"] += VBAT; Jrec["PWM"] += RPWM; Jrec["FAULT"] += RFAULT; Jrec["GND"] += GND
Jnfc["VCC"] += V5; Jnfc["GND"] += GND; Jnfc["SDA"] += I2C_SDA; Jnfc["SCL"] += I2C_SCL   # NFC matas från 5V (egen LDO på modulen) → isolerar RF-burst från 3V3
Rmode0[1] += MODE0; Rmode0[2] += GND; Rmode1[1] += MODE1; Rmode1[2] += GND
Ri1[1] += V3; Ri1[2] += I2C_SCL; Ri2[1] += V3; Ri2[2] += I2C_SDA

# ---------- HAT-ID-EEPROM (AT24C32 @0x50 på ID_SD/ID_SC = GPIO0/1) ----------
U_eep["VCC"] += V3; U_eep["GND"] += GND; U_eep["A0"] += GND; U_eep["A1"] += GND; U_eep["A2"] += GND
U_eep["SDA"] += ID_SD; U_eep["SCL"] += ID_SC; U_eep["WP"] += GND      # WP→GND = skrivbar
Ceep[1] += V3; Ceep[2] += GND
Rid1[1] += V3; Rid1[2] += ID_SD; Rid2[1] += V3; Rid2[2] += ID_SC      # ID-buss pull-ups

# ---------- ESP32-C6-brygga (XIAO-sockel, baksida; matas +5V → eget LDO) ----------
Jc6[8] += V5; Jc6[9] += GND                            # XIAO 5V + GND
Jc6[14] += ESP_TX                                      # D7/RX (GPIO17) ← CM5 TX (GPIO14)
Jc6[7] += ESP_RX                                       # D6/TX (GPIO16) → CM5 RX (GPIO15)

generate_netlist(file_="hardware/weapon-hat.net")
print("wrote hardware/weapon-hat.net")
