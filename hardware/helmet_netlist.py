#!/usr/bin/env python3
"""STRILAS — HJÄLM-NOD (komplett): kretsdefinition i kod (SKiDL → KiCad-netlista).
Genererar 'hardware/helmet-halo.net'. Fristående nod (egen ESP + batteri, trådlöst mot väst/vapen
— se ritningar/helmet-node.md). Ø100 ring-kort, 4-lager.

ARKITEKTUR (verifierad mot datablad):
  • 2S-batteri (laddas i docka) → AP63203 synk-buck → 3,3 V @2A (matar XIAO-S3 via 3V3-stift +
    TSOP + GNSS + mik + audio). LED-konstellationen drivs DIREKT från 2S (som väst-patchen).
  • Stackad ESP: Seeed XIAO ESP32-S3 (2× 1x7 sockel), matas från kortets 3V3, programmeras via
    egen USB-C. Pinout: D0..D6 (GPIO1-6,43) ena raden; 5V/GND/3V3/D10/D9/D8/D7 andra.
  • 8× TSOP4856 (940 nm skott-RX, 360° huvud) → diod-OR → DATA. 4× SFH4715AS 860 nm-konstellation
    (högt på ringen) + AO3400-driver (10R, blink-modulerad) ← LED_EN.
  • GNSS: ATGM336H-5N-modul (egen antenn) på 1x5-header → XIAO-UART. I²S-ljud: MAX98357A-amp-breakout
    (1x7 + högtalare på modulen) + I²S-MEMS-mik-breakout (1x6) → röst/spel-ljud.
Moduler (XIAO, GNSS, amp, mik) = köpta breakouts på header (samma stack-filosofi som P4/optik) →
inga ogissade QFN/MEMS/RF-footprints; allt verifierbart.
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
TSOP = mk("TSOP4856", "U", [(1, "OUT"), (2, "GND"), (3, "VS")], "OptoDevice:Vishay_MINIMOLD-3Pin", "TSOP4856")
LED = mk("SFH4715AS", "D", [(1, "A"), (2, "K")], "strilas:IR_Emitter_OSRAM_OSLON_Black_SFH4725S", "SFH4715AS_860nm")
ORD = mk("ORdiode", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SOD-123", "BAT54")
NFET = mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400")
# AP63203 synk-buck (TSOT23-6, Diodes DS41326): 1=FB 2=EN 3=VIN 4=GND 5=SW 6=BST. 3,8-32V in, 2A, Vref 0,8V.
BUCK = mk("AP63203", "U", [(1, "FB"), (2, "EN"), (3, "VIN"), (4, "GND"), (5, "SW"), (6, "BST")],
          "Package_TO_SOT_SMD:TSOT-23-6", "AP63203")
IND = mk("L", "L", [(1, "1"), (2, "2")], "Inductor_SMD:L_Changjiang_FNR5040S", "4.7uH")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v, fp="Resistor_SMD:R_0805_2012Metric": RES_T(value=v, footprint=fp)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
SOCK7 = mk("Conn_1x07", "J", [(i, i) for i in range(1, 8)], "Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical", "XIAO-S3 1x7 sockel")
HDR = lambda n, lbl: mk(f"Conn_1x0{n}", "J", [(i, i) for i in range(1, n + 1)],
                        f"Connector_PinHeader_2.54mm:PinHeader_1x0{n}_P2.54mm_Vertical", lbl)
BATT = mk("BATT_2S", "J", [(1, "VBAT"), (2, "GND")], "Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal", "2S batteri")
# ZED-F9P RTK-puck (komplett: F9P + multiband-antenn + IST8310-kompass + metallbas, centrum-monterad).
# 8-pol 1,25 mm låsbar (JST GH). 3–9 V (typ 5 V, 80 mA) → matas från VBAT(2S, inom 3–9 V). UART + I²C(kompass).
# OBS: stift-ORDNINGEN nedan ska MATCHA modulens kabel — verifiera mot säljarens/u-blox pinout (din modul).
F9P = mk("ZED-F9P", "J", [(1, "VCC"), (2, "GND"), (3, "TXD"), (4, "RXD"), (5, "SDA"), (6, "SCL"), (7, "PPS"), (8, "RSV")],
         "Connector_JST:JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal", "ZED-F9P RTK (UART+I²C)")
MH = mk("MH", "H", [(1, "1")], "MountingHole:MountingHole_2.5mm", "M2.5")

# ---------- nät ----------
VBAT, GND, P3V3 = Net("VBAT"), Net("GND"), Net("+3V3")
DATA, LED_EN, LEDC = Net("DATA"), Net("LED_EN"), Net("LED_CATH")
SW, BST, FB = Net("SW"), Net("BST"), Net("FB")
BCLK, LRCK, I2S_DOUT, I2S_DIN = Net("I2S_BCLK"), Net("I2S_LRCK"), Net("I2S_DOUT"), Net("I2S_DIN")
GNSS_TX, GNSS_RX, AMP_SD = Net("GNSS_TX"), Net("GNSS_RX"), Net("AMP_SD")
I2C_SDA, I2C_SCL = Net("I2C_SDA"), Net("I2C_SCL")             # F9P-config + IST8310-kompass

# ---------- buck: 2S → 3,3 V @2A (matar all logik + XIAO) ----------
Ubk = BUCK()
Ubk["VIN"] += VBAT; Ubk["EN"] += VBAT; Ubk["GND"] += GND      # EN→VIN = auto-start
Ubk["SW"] += SW; Ubk["BST"] += BST; Ubk["FB"] += FB
L1 = IND(); L1[1] += SW; L1[2] += P3V3                          # SW → L → 3V3
Cbst = CAP("100nF"); Cbst[1] += SW; Cbst[2] += BST            # boost-cap
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric"); Cin[1] += VBAT; Cin[2] += GND
Cout = CAP("22uF", "Capacitor_SMD:C_1206_3216Metric"); Cout[1] += P3V3; Cout[2] += GND
Rt = RES("31.6k"); Rb = RES("10k")                            # 0,8·(1+31,6/10)=3,33 V
Rt[1] += P3V3; Rt[2] += FB; Rb[1] += FB; Rb[2] += GND

# ---------- 8× TSOP4856 + diod-OR → DATA (3V3-logik) ----------
Rpu = RES("10k"); Rpu[1] += P3V3; Rpu[2] += DATA
for i in range(8):
    s = TSOP(); out = Net(f"OUT{i+1}")
    s["VS"] += P3V3; s["GND"] += GND; s["OUT"] += out
    d = ORD(); d["K"] += out; d["A"] += DATA
    cd = CAP("100nF"); cd[1] += P3V3; cd[2] += GND

# ---------- 4× SFH4715AS 860 nm-konstellation + driver (VBAT 2S, blink-modulerad) ----------
Q = NFET(); Q["S"] += GND; Q["D"] += LEDC
Rg = RES("220R"); Rg[1] += LED_EN; Rg[2] += Q["G"]
for i in range(4):
    led = LED(); rl = RES("10R", "Resistor_SMD:R_2512_6332Metric")
    a = Net(f"LED_A{i+1}")
    rl[1] += VBAT; rl[2] += a; led["A"] += a; led["K"] += LEDC

# ---------- stackad XIAO ESP32-S3 (2× 1x7 sockel) — alla 11 GPIO används ----------
# vänster rad: D0..D6 = GPIO1,2,3,4,5,6,43 ; höger rad: 5V,GND,3V3,D10,D9,D8,D7
JL = SOCK7(); JR = SOCK7()
JL[1] += DATA       # D0  GPIO1  ← skott-DATA
JL[2] += LED_EN     # D1  GPIO2  → konstellation-gate
JL[3] += BCLK       # D2  GPIO3  I²S bit-clock
JL[4] += LRCK       # D3  GPIO4  I²S LR-clock
JL[5] += I2C_SDA    # D4  GPIO5  I²C SDA (F9P-config + IST8310-kompass)
JL[6] += I2C_SCL    # D5  GPIO6  I²C SCL
JL[7] += GNSS_RX    # D6  GPIO43 UART TX → F9P RXD
JR[1] += Net("NC_5V")   # 5V  (XIAO matas via 3V3 → 5V oanvänd)
JR[2] += GND            # GND
JR[3] += P3V3           # 3V3 (matas från kortets buck)
JR[4] += AMP_SD         # D10 GPIO9  → amp SD/mode
JR[5] += I2S_DIN        # D9  GPIO8  I²S data in ← mik
JR[6] += I2S_DOUT       # D8  GPIO7  I²S data ut → amp
JR[7] += GNSS_TX        # D7  GPIO44 UART RX ← F9P TXD

# ---------- ZED-F9P RTK-puck (centrum, egen antenn+kompass) 8-pol JST GH ----------
Jg = F9P()
Jg["VCC"] += VBAT; Jg["GND"] += GND          # 3–9 V → VBAT(2S) OK
Jg["TXD"] += GNSS_TX; Jg["RXD"] += GNSS_RX   # UART → XIAO
Jg["SDA"] += I2C_SDA; Jg["SCL"] += I2C_SCL   # I²C (kompass + config)
Jg["PPS"] += Net("GNSS_PPS"); Jg["RSV"] += Net("F9P_RSV")

# ---------- I²S audio: MAX98357A-amp-breakout (1x7, högtalare på modulen) ----------
Ja = HDR(7, "AMP: 3V3·GND·SD·GAIN·DIN·BCLK·LRC")()
Ja[1] += P3V3; Ja[2] += GND; Ja[3] += AMP_SD; Ja[4] += Net("AMP_GAIN")
Ja[5] += I2S_DOUT; Ja[6] += BCLK; Ja[7] += LRCK

# ---------- I²S MEMS-mik-breakout (1x6) ----------
Jm = HDR(6, "MIC: 3V3·GND·SD·WS·SCK·LR")()
Jm[1] += P3V3; Jm[2] += GND; Jm[3] += I2S_DIN; Jm[4] += LRCK; Jm[5] += BCLK; Jm[6] += GND  # LR→GND = vänster

# ---------- 2S-batteri + monteringshål ----------
Jb = BATT(); Jb["VBAT"] += VBAT; Jb["GND"] += GND
for _ in range(4):
    MH()[1] += GND

generate_netlist(file_="hardware/helmet-halo.net")
print("wrote hardware/helmet-halo.net (komplett hjälm-nod: buck+XIAO-S3+8TSOP+4LED+GNSS+I2S-audio)")
