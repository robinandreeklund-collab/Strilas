#!/usr/bin/env python3
"""STRILAS — VAPEN-CARRIER (v2): kretsdefinition i kod (SKiDL → KiCad-netlista).

Carrier-kort för Raspberry Pi CM5 (vapen-noden). Samlar ALL elektronik:
  • CM5-sockel (2× Hirose DF40 100-pin) — CM5 plugar in
  • MIPI-CSI: 22-pin FFC (kamera-ribbon från optik-huvudet) → route → CM5 CAM1
  • CC-sänka (OPA171 + DPAK pass-FET + 0R2 sense, 1 A tak / 3 A DNP) → emitter-JST → optik-huvud
  • IMU (ICM-42688-P, SPI) — re-ankrar attityd per frame
  • Kraft: 2S → 5 V buck (CM5) + VBAT emitter-rail; rev-skydd, TVS, bulk, PTC
  • Batteri-sense via I²C-ADC (CM5 saknar ADC)
  • Fire-control-IO: trigger/rack/mag-release/magwell, recoil-ctrl, NFC, MODE  (= dagens FC-kort)

CM5-parten exponerar de SIGNALER vi använder (namngivna per CM5-funktion); full DF40-pinmappning
sätts vid layout mot CM5-databladet. Optik-huvudet = hardware/optik_head.py (kamera + 2 emittrar).

Kör:  python3 hardware/weapon_carrier_netlist.py  → hardware/weapon-carrier.net
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
# CM5-sockel: vi listar de signaler vi ANSLUTER (CM5-funktionsnamn). Fysisk DF40-pinmappning
# (2× 100-pin) sätts vid layout mot CM5-databladet. Strömstift dubbleras (5V/GND) i verkligheten.
CM5_PINS = [(1,"VDD_5V"),(2,"VDD_5V"),(3,"GND"),(4,"GND"),(5,"GND"),(6,"GND"),
            # CAM1 MIPI (2-lane) + I²C-styrning
            (7,"CAM1_C_N"),(8,"CAM1_C_P"),(9,"CAM1_D0_N"),(10,"CAM1_D0_P"),
            (11,"CAM1_D1_N"),(12,"CAM1_D1_P"),(13,"CAM_SCL"),(14,"CAM_SDA"),
            # IMU SPI + INT
            (15,"SPI_SCLK"),(16,"SPI_MOSI"),(17,"SPI_MISO"),(18,"SPI_CE"),(19,"IMU_INT"),
            # IR-modulering (PWM) + buck-EN
            (20,"IR_MOD"),(21,"BUCK_EN"),
            # I²C (NFC + ADC)
            (22,"I2C_SCL"),(23,"I2C_SDA"),
            # fire-control GPIO
            (24,"TRIG"),(25,"RACK"),(26,"MAGREL"),(27,"MAGWELL"),
            (28,"RECOIL_PWM"),(29,"RECOIL_FAULT"),(30,"MODE0"),(31,"MODE1"),(32,"PTT")]
CM5 = mk("RaspberryPi_CM5", "J", CM5_PINS,
         "Connector_Hirose:Hirose_DF40C-100DS-0.4V_2x50_P0.40mm_Vertical", "CM5 (2× DF40 100-pin)")
# kamera-FFC (22-pin MIPI, ribbon från optik-huvudet)
FFC = mk("CAM_FFC_22", "J", [(i, i) for i in range(1, 23)],
         "Connector_FFC-FPC:Hirose_FH12-22S-0.5SH_1x22-1MP_P0.50mm_Horizontal", "MIPI-kamera 22-pin")
BATT = mk("XT30", "J", [(1, "VBAT"), (2, "GND")], "Connector:XT30", "2S batteri (XT30)")
EMIT = mk("EmitConn", "J", [(1, "VBAT_E"), (2, "DRV")],
          "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", "→ optik-huvud (emitter)")
# fire-control-kontakter (grepp): switchar + recoil + NFC + MODE
SW = lambda n, a, b: mk(f"SW_{n}", "J", [(1, a), (2, b)],
                        "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", n)
RECOIL = mk("RecoilConn", "J", [(1, "VBAT"), (2, "PWM"), (3, "FAULT"), (4, "GND")],
            "Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal", "recoil-driver")
NFC = mk("PN532", "J", [(1, "VCC"), (2, "GND"), (3, "SDA"), (4, "SCL")],
         "Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal", "NFC PN532 (I²C)")

RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v, fp="Resistor_SMD:R_0805_2012Metric": RES_T(value=v, footprint=fp)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
PFET = mk("AO3401", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3401")
DFET = mk("AOD4184A", "Q", [(1, "G"), (2, "D"), (3, "S")], "Package_TO_SOT_SMD:TO-252-2", "AOD4184A")
OPAMP = mk("OPA171", "U", [(1, "OUT"), (2, "V-"), (3, "IN+"), (4, "IN-"), (5, "V+")],
           "Package_TO_SOT_SMD:SOT-23-5", "OPA171")
# 2S→5V buck (modul/IC svartlåda: VIN/EN/GND/5V) — diskret implementering sätts vid layout
BUCK = mk("Buck_5V_3A", "U", [(1, "VIN"), (2, "EN"), (3, "GND"), (4, "VOUT")],
          "Converter_DCDC:Converter_DCDC_left", "2S→5V @≥3A")
ADC = mk("ADS1115", "U", [(1, "VDD"), (2, "GND"), (3, "SCL"), (4, "SDA"), (5, "AIN0")],
         "Package_SO:TSSOP-10_3x3mm_P0.5mm", "I²C-ADC (batteri-sense)")
IMU = mk("ICM-42688-P", "U", [(1,"SDO"),(4,"INT1"),(5,"VDDIO"),(6,"GND"),(8,"VDD"),(12,"CS"),(13,"SCLK"),(14,"SDI")],
         "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "ICM-42688-P")
PTC = mk("PTC", "F", [(1, "~"), (2, "~")], "Fuse:Fuse_1812_4532Metric", "PTC_3A")
TVS = mk("SMBJ12A", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SMB", "SMBJ12A")

# ---------- nät ----------
VBAT_IN, VBAT_F, VBAT, V5, GND = (Net(n) for n in ("VBAT_IN","VBAT_F","VBAT","+5V","GND"))
VBAT_E, LEDC, GATE = Net("VBAT_E"), Net("LED_CATH"), Net("DRV_GATE")
VREF, SENSE, IR_MOD = Net("IDRV_REF"), Net("IDRV_SENSE"), Net("IR_MOD")
SCK, MOSI, MISO, nCS, IMU_INT = (Net(n) for n in ("SCK","MOSI","MISO","nCS","IMU_INT"))
I2C_SCL, I2C_SDA = Net("I2C_SCL"), Net("I2C_SDA")
CAM_SCL, CAM_SDA = Net("CAM_SCL"), Net("CAM_SDA")
VBAT_SENSE = Net("VBAT_SENSE")
# MIPI diff-par
mc_n,mc_p,m0_n,m0_p,m1_n,m1_p = (Net(n) for n in ("CAM_C_N","CAM_C_P","CAM_D0_N","CAM_D0_P","CAM_D1_N","CAM_D1_P"))
# fire-control
TRIG,RACK,MAGREL,MAGWELL,RPWM,RFAULT,MODE0,MODE1,PTT = (Net(n) for n in
    ("TRIG","RACK","MAGREL","MAGWELL","RECOIL_PWM","RECOIL_FAULT","MODE0","MODE1","PTT"))

# ---------- instansiera ----------
U_cm = CM5(); Jf = FFC(); J2 = BATT(); Je = EMIT()
# kraft
F1 = PTC(); Qrp = PFET(); Rg = RES("100k"); Dt = TVS()
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric"); Cbulk = CAP("100uF", "Capacitor_SMD:C_1210_3225Metric")
Ub = BUCK(); Lb_in = CAP("22uF","Capacitor_SMD:C_1210_3225Metric"); Lb_out = CAP("22uF","Capacitor_SMD:C_1210_3225Metric")
# CC-sänka
Uop = OPAMP(); Qd = DFET()
Rsense = RES("0R2", "Resistor_SMD:R_2512_6332Metric")
Rovr = RES("0R1 DNP=1A/montera=3A")
Rda = RES("15k"); Rdb = RES("1k"); Rgate = RES("100R"); Cop = CAP("100nF"); Cc = CAP("100pF")
# IMU
U_imu = IMU(); Ci1 = CAP("100nF","Capacitor_SMD:C_0402_1005Metric"); Ci2 = CAP("1uF")
# batteri-sense (8.4V→100k/47k) + I²C-ADC
U_adc = ADC(); Rsa = RES("100k"); Rsb = RES("47k"); Csns = CAP("100nF"); Cadc = CAP("100nF")
# fire-control
Jt = SW("TRIGGER","TRIG","GND")(); Jr = SW("RACK","RACK","GND")()
Jm = SW("MAGREL","MAGREL","GND")(); Jw = SW("MAGWELL","MAGWELL","GND")()
Jrec = RECOIL(); Jnfc = NFC()
Rmode0 = RES("10k"); Rmode1 = RES("10k")
# pull-ups switchar
Rt = RES("10k"); Rr = RES("10k"); Rm = RES("10k"); Rw = RES("10k")
Ri2c1 = RES("4k7"); Ri2c2 = RES("4k7")   # I²C pull-ups

# ---------- CM5: kraft + signaler ----------
U_cm["VDD_5V"] += V5; U_cm["GND"] += GND
U_cm["CAM1_C_N"]+=mc_n; U_cm["CAM1_C_P"]+=mc_p; U_cm["CAM1_D0_N"]+=m0_n; U_cm["CAM1_D0_P"]+=m0_p
U_cm["CAM1_D1_N"]+=m1_n; U_cm["CAM1_D1_P"]+=m1_p; U_cm["CAM_SCL"]+=CAM_SCL; U_cm["CAM_SDA"]+=CAM_SDA
U_cm["SPI_SCLK"]+=SCK; U_cm["SPI_MOSI"]+=MOSI; U_cm["SPI_MISO"]+=MISO; U_cm["SPI_CE"]+=nCS; U_cm["IMU_INT"]+=IMU_INT
U_cm["IR_MOD"]+=IR_MOD; U_cm["BUCK_EN"]+=Ub["EN"]
U_cm["I2C_SCL"]+=I2C_SCL; U_cm["I2C_SDA"]+=I2C_SDA
U_cm["TRIG"]+=TRIG; U_cm["RACK"]+=RACK; U_cm["MAGREL"]+=MAGREL; U_cm["MAGWELL"]+=MAGWELL
U_cm["RECOIL_PWM"]+=RPWM; U_cm["RECOIL_FAULT"]+=RFAULT; U_cm["MODE0"]+=MODE0; U_cm["MODE1"]+=MODE1; U_cm["PTT"]+=PTT

# ---------- kamera-FFC (22-pin) → CM5 CAM1 ----------
# RPi-CAM-22-pinout (förenklad): GND-skärm + 3 diff-par + I²C + 3V3. Strömmen till kameran tas från CM5/5V via FFC.
Jf[1]+=GND; Jf[2]+=m0_n; Jf[3]+=m0_p; Jf[4]+=GND; Jf[5]+=m1_n; Jf[6]+=m1_p; Jf[7]+=GND
Jf[8]+=mc_n; Jf[9]+=mc_p; Jf[10]+=GND; Jf[15]+=CAM_SCL; Jf[16]+=CAM_SDA; Jf[19]+=GND; Jf[22]+=V5
for p in (11,12,13,14,17,18,20,21): Jf[p] += GND   # reserv/GND/CAM_GPIO (sätts vid layout)

# ---------- kraftväg: 2S → skydd → buck → 5V (CM5) ; VBAT → emitter-rail ----------
J2["VBAT"]+=VBAT_IN; J2["GND"]+=GND
F1[1]+=VBAT_IN; F1[2]+=VBAT_F
Qrp["D"]+=VBAT_F; Qrp["S"]+=VBAT; Qrp["G"]+=Rg[1]; Rg[2]+=GND     # rev-polaritet
Dt["K"]+=VBAT; Dt["A"]+=GND; Cin[1]+=VBAT; Cin[2]+=GND; Cbulk[1]+=VBAT; Cbulk[2]+=GND
Ub["VIN"]+=VBAT; Ub["GND"]+=GND; Ub["VOUT"]+=V5
Lb_in[1]+=VBAT; Lb_in[2]+=GND; Lb_out[1]+=V5; Lb_out[2]+=GND

# ---------- CC-sänka (emitter på huvudet via Je) ----------
# VBAT → Je.VBAT_E → huvud D1.A …serie… D2.K → Je.DRV → LEDC → FET-drain → SENSE → GND
Je["VBAT_E"]+=VBAT; Je["DRV"]+=LEDC
Qd["D"]+=LEDC; Qd["S"]+=SENSE; Qd["G"]+=GATE
Rsense[1]+=SENSE; Rsense[2]+=GND; Rovr[1]+=GND; Rovr[2]+=SENSE
Uop["V+"]+=VBAT; Uop["V-"]+=GND; Uop["IN+"]+=VREF; Uop["IN-"]+=SENSE; Uop["OUT"]+=Rgate[1]; Rgate[2]+=GATE
Rda[1]+=IR_MOD; Rda[2]+=VREF; Rdb[1]+=VREF; Rdb[2]+=GND           # 15k/1k → 0,206 V tak → 1 A
Cc[1]+=Uop["OUT"]; Cc[2]+=SENSE; Cop[1]+=VBAT; Cop[2]+=GND

# ---------- IMU (SPI) ----------
U_imu["VDD"]+=V5; U_imu["VDDIO"]+=V5; U_imu["GND"]+=GND   # OBS: ICM kräver 1.8-3.3V VDDIO → LDO/level vid layout
U_imu["SCLK"]+=SCK; U_imu["SDI"]+=MOSI; U_imu["SDO"]+=MISO; U_imu["CS"]+=nCS; U_imu["INT1"]+=IMU_INT
Ci1[1]+=V5; Ci1[2]+=GND; Ci2[1]+=V5; Ci2[2]+=GND

# ---------- batteri-sense → I²C-ADC ----------
Rsa[1]+=VBAT; Rsa[2]+=VBAT_SENSE; Rsb[1]+=VBAT_SENSE; Rsb[2]+=GND; Csns[1]+=VBAT_SENSE; Csns[2]+=GND
U_adc["VDD"]+=V5; U_adc["GND"]+=GND; U_adc["SCL"]+=I2C_SCL; U_adc["SDA"]+=I2C_SDA; U_adc["AIN0"]+=VBAT_SENSE
Cadc[1]+=V5; Cadc[2]+=GND

# ---------- fire-control ----------
Jt["TRIG"]+=TRIG; Jt["GND"]+=GND; Jr["RACK"]+=RACK; Jr["GND"]+=GND
Jm["MAGREL"]+=MAGREL; Jm["GND"]+=GND; Jw["MAGWELL"]+=MAGWELL; Jw["GND"]+=GND
Rt[1]+=V5; Rt[2]+=TRIG; Rr[1]+=V5; Rr[2]+=RACK; Rm[1]+=V5; Rm[2]+=MAGREL; Rw[1]+=V5; Rw[2]+=MAGWELL
Jrec["VBAT"]+=VBAT; Jrec["PWM"]+=RPWM; Jrec["FAULT"]+=RFAULT; Jrec["GND"]+=GND
Jnfc["VCC"]+=V5; Jnfc["GND"]+=GND; Jnfc["SDA"]+=I2C_SDA; Jnfc["SCL"]+=I2C_SCL
Rmode0[1]+=MODE0; Rmode0[2]+=GND; Rmode1[1]+=MODE1; Rmode1[2]+=GND
Ri2c1[1]+=V5; Ri2c1[2]+=I2C_SCL; Ri2c2[1]+=V5; Ri2c2[2]+=I2C_SDA

generate_netlist(file_="hardware/weapon-carrier.net")
print("wrote hardware/weapon-carrier.net")
