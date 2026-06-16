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
# RIGID 1-rads kantkontakt mot P4:ans SIGNALKANT (edge B). Mappad mot Waveshares
# OFFICIELLA pinout (datablad/silk): edge B i ordning (ESP-änd → USB-änd):
#   VBUS·VSYS·GND·EN·3V3·GPIO20·GPIO21·GND·GPIO22·GPIO23·RUN·GPIO26·GND·GPIO27·GPIO32·...
# Vi använder VSYS..GPIO32 = 14 sammanhängande stift (inkl EN & RUN som lämnas NC).
# FEMALE socket — P4:an bär MALE-stiften, optikkortet tar emot dem (1×14 socket).
P4IF = mk("P4_EDGE", "J", [(i, i) for i in range(1, 15)],
          "Connector_PinSocket_2.54mm:PinSocket_1x14_P2.54mm_Vertical", "P4-socket (edge B)")
BATT = mk("BATT_IN", "J", [(1, "VBAT"), (2, "GND")],
          "Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal", "2S batteri (JST-XH)")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v, fp="Resistor_SMD:R_0805_2012Metric": RES_T(value=v, footprint=fp)
CAP = lambda v, fp="Capacitor_SMD:C_0805_2012Metric": CAP_T(value=v, footprint=fp)
PFET = mk("AO3401", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3401")
NFET = mk("AO3400", "Q", [(1, "G"), (2, "S"), (3, "D")], "Package_TO_SOT_SMD:SOT-23", "AO3400")
PTC = mk("PTC", "F", [(1, "~"), (2, "~")], "Fuse:Fuse_1206_3216Metric", "PTC_1A")
TVS = mk("SMBJ12A", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SMB", "SMBJ12A")
LED = mk("SFH4725S", "D", [(1, "A"), (2, "K")],
         "strilas:IR_Emitter_OSRAM_OSLON_Black_SFH4725S", "SFH4725S_940nm")
# ICM-42670-P LGA-14 — pin-nr enligt TDK DS-000451 / referensschema NW-MOT-ICM42670-P:
# 1 SDO  2 RESV  3 RESV  4 INT1  5 VDDIO  6 GND  7 FSYNC(→GND när oanvänd)
# 8 VDD  9 INT2  10 RESV 11 RESV 12 CS  13 SCLK 14 SDI
# (IN-STOCK hos LCSC/NextPCB; DROP-IN mot 42688/45686 — samma footprint/pinout,
#  enda skillnad pin7 FSYNC istället f. RESV, men "connect to GND if not used" → samma koppling.)
IMU = mk("ICM-42670-P", "U", [(i, i) for i in range(1, 15)],
         "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "ICM-42670-P")
MH = lambda n: mk(f"MH{n}", "H", [(1, "1")], "MountingHole:MountingHole_2.5mm", "M2.5")
# kamera-monteringshål (M2) — matchar Arducam B0332 28×28 mm-mönster
CMH = lambda n: mk(f"CMH{n}", "H", [(1, "1")], "MountingHole:MountingHole_2.2mm_M2", "M2_kamera")
# kollimator-hållarben (Ø1.6) runt varje emitter (generiskt 20 mm TIR-hållarmönster, 3 ben/lins)
CLEG = lambda n: mk(f"CLEG{n}", "H", [(1, "1")], "MountingHole:MountingHole_2.1mm", "Carclo10734-ben_Ø2.1")
# P4-standoffs (M2) — fäster ESP32-P4-WIFI6 (71×21) bakom kortet
PSTD = lambda n: mk(f"PSTD{n}", "H", [(1, "1")], "MountingHole:MountingHole_2.2mm_M2", "M2_P4")
# OBS: trigger/rack/mag-release/recoil-styrning/NFC ligger på SEPARAT fire-control-kort
# (P4 edge A) — INTE här. Optikmodulen = ren optik (IR+IMU+kamera+P4-sync, edge B).

# ---------- nät ----------
VBAT_IN, VBAT_F, VBAT, GND, P3V3 = Net("VBAT_IN"), Net("VBAT_F"), Net("VBAT"), Net("GND"), Net("+3V3")
IR_MOD, SCK, MOSI, MISO, nCS, INT = (Net(n) for n in ("IR_MOD", "SCK", "MOSI", "MISO", "nCS", "IMU_INT"))
STR1, LEDC, IRG = Net("LED_MID"), Net("LED_CATH"), Net("Q1_GATE")

# ---------- instansiera ----------
J1 = P4IF(); J2 = BATT()
F1 = PTC(); Q2 = PFET(); Rg2 = RES("100k"); Dtvs = TVS()
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric")
Cbulk = CAP("100uF", "Capacitor_SMD:C_1210_3225Metric")   # MLCC reservoar (låg-ESR f. 56 kHz-puls)
Rset = RES("6R8", "Resistor_SMD:R_2512_6332Metric")   # Rset = 2× 6R8 1W PARALLELLT (=3.4Ω, 2W tot)
D1, D2 = LED(), LED()
Q1 = NFET(); Rg = RES("220R")
Rset2 = RES("6R8", "Resistor_SMD:R_2512_6332Metric")   # 2:a Rset-resistorn (skapas SIST → ref R4, ingen omnumrering av R3)
U2 = IMU(); Cd1 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric")
Cd2 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric"); Cd3 = CAP("1uF")
H1, H2, H3 = MH(1)(), MH(2)(), MH(3)()
HC = MH(16)()                       # centrum-kort-hål (mellan linserna)
HP1, HP2, HP3 = MH(17)(), MH(18)(), MH(19)()   # 3 P4-standoff (15mm, synk mot P4-hål)
H4, H5, H6, H7 = CMH(4)(), CMH(5)(), CMH(6)(), CMH(7)()   # kamerafäste (B0332)
CL = [CLEG(i)() for i in range(1, 9)]   # 8 ben: Carclo 10734 4-bens-hållare (ritn. 60575), 4/lins
HP4 = MH(20)()                      # 4:e P4-standoff (instansieras SIST → ref H20, ingen ref-omflyttning)

# ---------- J2 = batteri-in (2S) ; J1 = P4-carrier-header ----------
J2["VBAT"] += VBAT_IN; J2["GND"] += GND
# J1 = 14 stift mot P4 edge B, pos2..15 (VSYS..GPIO32), i EXAKT fysisk ordning:
#   stift  P4-pin   funktion        vårt nät
#   J1[1]  VSYS     systemström-in   VBAT  (2S; P4:ans VSYS-buck MP1658 tål ≤16 V)
#   J1[2]  GND                       GND
#   J1[3]  EN       chip-enable      -- NC (P4:ns pull-up; driv ej)
#   J1[4]  3V3      3V3-ut från P4   +3V3  (matar IMU)
#   J1[5]  GPIO20                    IR_MOD (56 kHz till driver)
#   J1[6]  GPIO21                    -- LEDIG GPIO (NC; reserv för Fas 2-hook)
#   J1[7]  GND                       GND
#   J1[8]  GPIO22                    SCK
#   J1[9]  GPIO23                    MOSI
#   J1[10] RUN      reset            -- NC (P4:ns pull-up; driv ej)
#   J1[11] GPIO26                    MISO
#   J1[12] GND                       GND
#   J1[13] GPIO27                    nCS
#   J1[14] GPIO32                    IMU_INT
# SPEGLAD pinout: P4 monteras STACKAD bakom optiken (kort-mot-kort, ansikte-mot-
# ansikte) → pinouten speglas (pad k = forna pad 15-k) så stiften möts rätt fysiskt.
# SIGNAL↔GPIO-PERMUTATION: de 5 IMU/SPI-näten (INT,nCS,MISO,MOSI,SCK) ligger på
# J1-stift {1,2,4,6,7} = P4-GPIO {32,27,26,23,22} — alla generiska GPIO (SPI går via
# P4:ans GPIO-matris, INT är valfri GPIO). Permuterad för PLANÄR (korsningsfri) escape
# IMU→J1 på ett enda lager (F_Cu): annars tvingas ett via-byte (nCS/INT byter Y-ordning).
#   nCS →J1.1(GPIO32) · MOSI→J1.2(GPIO27) · INT→J1.4(GPIO26) · SCK→J1.6(GPIO23) · MISO→J1.7(GPIO22)
J1[1] += nCS; J1[2] += MOSI; J1[3] += GND; J1[4] += INT
J1[6] += SCK; J1[7] += MISO; J1[8] += GND
J1[10] += IR_MOD; J1[11] += P3V3; J1[13] += GND; J1[14] += VBAT
# NC: J1[5]=RUN, J1[9]=GPIO21, J1[12]=EN (drivs ej från vårt kort).

# ---------- kraftinmatning + skydd ----------
F1[1] += VBAT_IN; F1[2] += VBAT_F                 # PTC-säkring
Q2["D"] += VBAT_F; Q2["S"] += VBAT; Q2["G"] += Rg2[1]; Rg2[2] += GND   # reverse-polarity P-FET
Dtvs["K"] += VBAT; Dtvs["A"] += GND               # TVS-clamp
Cin[1] += VBAT; Cin[2] += GND
Cbulk[1] += VBAT; Cbulk[2] += GND                 # reservoar för pulsen

# ---------- IR-emitterdriver (Rset hårt strömtak + 56 kHz-gate) ----------
Rset[1] += VBAT; Rset[2] += D1["A"]               # effektresistor sätter Imax (R2)
Rset2[1] += VBAT; Rset2[2] += D1["A"]             # parallell (R4) → in-stock 1W-par istället f. specialdel 2W
D1["K"] += STR1; D2["A"] += STR1; D2["K"] += LEDC # 2 LED i serie
Q1["D"] += LEDC; Q1["S"] += GND                   # N-FET drar strängen mot GND
Rg[1] += IR_MOD; Rg[2] += IRG; Q1["G"] += IRG     # 56 kHz på gaten

# ---------- IMU (SPI 4-wire) + avkoppling ----------
# pin-nr (TDK AN-000483 Fig.2):  8=VDD 5=VDDIO 6=GND 13=SCLK 14=SDI 1=SDO 12=CS 4=INT1
U2[8] += P3V3; U2[5] += P3V3; U2[6] += GND        # VDD / VDDIO / GND
U2[7] += GND                                      # pin7 FSYNC → GND (oanvänd, ICM-42670-P)
U2[13] += SCK; U2[14] += MOSI; U2[1] += MISO; U2[12] += nCS; U2[4] += INT
# pinnar 2,3,9,10,11 = RESV/INT2/FSYNC -> ej anslutna (NC), enligt datablad
Cd1[1] += P3V3; Cd1[2] += GND; Cd2[1] += P3V3; Cd2[2] += GND; Cd3[1] += P3V3; Cd3[2] += GND

# ---------- mekanik (hål till GND) ----------
for H in (H1, H2, H3, HC, HP1, HP2, HP3, HP4, H4, H5, H6, H7, *CL):
    H[1] += GND

generate_netlist(file_="hardware/weapon-module.net")
print("wrote hardware/weapon-module.net")
