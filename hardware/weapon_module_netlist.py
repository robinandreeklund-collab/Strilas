#!/usr/bin/env python3
"""STRILAS — VAPEN-OPTIKMODUL: kretsdefinition i kod (SKiDL → KiCad-netlista).
Genererar 'hardware/weapon-module.net' (importeras i KiCad/kinet2pcb för layout→Gerbers).

Driver = AKTIV KONSTANTSTRÖMS-SÄNKA (op-amp OPA171 + DPAK pass-FET + sense-resistor):
I = Vref/Rsense, BATTERI-OBEROENDE (passiv Rset gav 0,3–0,6 A som sjönk med batteriet).
Sense-resistorn + 3,3 V-referensdelaren = HÅRT HW-strömtak (~1,0 A) → realiserar
eye-safety design-regel #1 ("ögonsäkerhet i hårdvara"). IR_MOD gatar referensen → 56 kHz.
Skalbar till 3 A endast via avsiktligt Rsense-byte + IEC 60825-1-ommätning (eye-safety-budget.md).
Sikteskamera = USB OV9281 GS NoIR — sitter MEKANISKT bakom kortet (lins genom Ø16-hål),
ansluts till P4 via USB-kabel → finns INTE elektriskt på detta kort.

Skottstråle-emitter = ams OSRAM SFH 4725S/4725CS (940 nm, OSLON Black) — SAMMA leverantör/paket
som patchens/hjälmens konstellations-LED (SFH 4715AS, 860 nm OSLON Black) → enhetlig optik-sourcing.
IMU = TDK InvenSense IIM-42653 (industri-IMU, LGA-14 2.5×3 mm). Kund-footprints i strilas.pretty.
IMU-pinout verifierad mot TDK DS-000529 (IIM-42653).
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
# Pass-FET för konstantströms-sänkan: DPAK (TO-252) logic-level N-FET, pin 1=G 2=D(tab) 3=S.
# Linjär drift vid låg Vds (~1,4–1,8 V) → 1,8–4,2 W puls @1–3 A; DPAK + kopparplan klarar skurar.
DFET = mk("AOD4184A", "Q", [(1, "G"), (2, "D"), (3, "S")], "Package_TO_SOT_SMD:TO-252-2", "AOD4184A")
# OPA171 (SOT-23-5 DBV) pin (TI-datablad SBOS516H Fig.4-2): 1=OUT 2=V- 3=IN+ 4=IN- 5=V+.
# 2,7–36 V matning (drivs från VBAT), in-CM inkl. V- (kan känna 0,2 V shunt), RR-utgång (gate-drive).
OPAMP = mk("OPA171", "U", [(1, "OUT"), (2, "V-"), (3, "IN+"), (4, "IN-"), (5, "V+")],
           "Package_TO_SOT_SMD:SOT-23-5", "OPA171")
PTC = mk("PTC", "F", [(1, "~"), (2, "~")], "Fuse:Fuse_1206_3216Metric", "PTC_3A")  # 3A-hold f. 3A-skala
TVS = mk("SMBJ12A", "D", [(1, "K"), (2, "A")], "Diode_SMD:D_SMB", "SMBJ12A")
# IR-emitter: SFH 4725AS (aktiv efterföljare till utgångna 4725S). Paket C63062-A4141 IDENTISKT
# (samma footprint/dome/80°/1x1-chip) → strilas-footprinten oförändrad. Bin 13 = 940 nm (930-950).
LED = mk("SFH4725AS", "D", [(1, "A"), (2, "K")],
         "strilas:IR_Emitter_OSRAM_OSLON_Black_SFH4725S", "SFH4725AS_940nm_bin13")
# 3A-override = MONTERA-FÖR-3A-motstånd (DNP). Rp(0R1) parallellt över Rsense(R2,0R2) → 0,2||0,1=0,067Ω
# → I 1A→3A. Default OBESTYCKAT (DNP) = 1A (säker, fail-safe); montera Rp = 3A (medvetet, lab).
# (Optikkortet är för tätt för en separat bygel vid sense-noden — ett DNP-motstånd är platsfritt och precist.)
# IIM-42653 LGA-14 — pin-nr enligt TDK DS-000529 (industri-IMU, verifierad mot databladet):
# 1 SDO  2 AUX1_SDIO  3 AUX1_SCLK  4 INT1  5 VDDIO  6 GND  7 RESV(→GND)
# 8 VDD  9 INT2/FSYNC  10 AUX1_CS  11 AUX1_SDO  12 CS  13 SCLK 14 SDI
# (de 8 stift vi använder: 1/4/5/6/8/12/13/14 = identiska med 426xx-footprinten → DROP-IN.
#  AUX1 (2/3/10/11) = oanvänd sekundär-SPI → NC. ±4000 dps, ±0,5% SF, -40..+105°C, 20000g.)
IMU = mk("IIM-42653", "U", [(i, i) for i in range(1, 15)],
         "strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx", "IIM-42653")
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
STR1, LEDC, GATE = Net("LED_MID"), Net("LED_CATH"), Net("DRV_GATE")
VREF, SENSE = Net("IDRV_REF"), Net("IDRV_SENSE")   # CC-sänka: gatad referens + ström-sense

# ---------- instansiera ----------
J1 = P4IF(); J2 = BATT()
F1 = PTC(); Q2 = PFET(); Rg2 = RES("100k"); Dtvs = TVS()
Cin = CAP("10uF", "Capacitor_SMD:C_1206_3216Metric")
Cbulk = CAP("100uF", "Capacitor_SMD:C_1210_3225Metric")   # MLCC reservoar (låg-ESR f. 56 kHz-puls)
D1, D2 = LED(), LED()
U2 = IMU(); Cd1 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric")
Cd2 = CAP("100nF", "Capacitor_SMD:C_0402_1005Metric"); Cd3 = CAP("1uF")
# ---- aktiv konstantströms-sänka (ersätter passiv Rset) — instansieras EFTER IMU så IMU=U1 ----
Uop = OPAMP()                                              # U2 = OPA171
Qd = DFET()                                                # Q2 = DPAK pass-FET
Rsense = RES("0R2", "Resistor_SMD:R_2512_6332Metric")      # I=Vref/Rsense; 0,2Ω → 1A (säker default)
Rp_ovr = RES("0R1 DNP=1A/montera=3A", "Resistor_SMD:R_0805_2012Metric")  # DNP-override parallellt över R2: 0,2||0,1=0,067Ω → 3A
Rdiv_a = RES("15k"); Rdiv_b = RES("1k")                    # IR_MOD → ~0,206 V referens (3,3/16)
Rgate = RES("100R")                                        # gate-isolering (pol m. FET Ciss)
Cop = CAP("100nF"); Ccomp = CAP("100pF")                   # op-amp-avkoppling + slingkompensering
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
#   J1[8]  GPIO22                    MISO
#   J1[9]  GPIO23                    SCK
#   J1[10] RUN      reset            -- NC (P4:ns pull-up; driv ej)
#   J1[11] GPIO26                    IMU_INT
#   J1[12] GND                       GND
#   J1[13] GPIO27                    MOSI
#   J1[14] GPIO32                    nCS
# SPEGLAD pinout: P4 monteras STACKAD bakom optiken (kort-mot-kort, ansikte-mot-
# ansikte) → pinouten MÅSTE speglas (pad k = forna pad 15-k) så att BÅDE kontaktstiften
# OCH de 4 standoff-hålen (HP1-4) möts fysiskt. Näten tilldelas därför J1-paddarna i
# spegelvänd ordning nedan; varje signal når SAMMA P4-GPIO som förr (GPIO32/27/26/23/22).
# (Tidigare bug: speglingen var dokumenterad men EJ applicerad på nät-tilldelningen, så
#  hålen passade bara i den orientering där kontakten gick baklänges — nCS→VSYS m.fl.)
#   nCS→J1.14(GPIO32) · MOSI→J1.13(GPIO27) · INT→J1.11(GPIO26) · SCK→J1.9(GPIO23) · MISO→J1.8(GPIO22)
J1[14] += nCS; J1[13] += MOSI; J1[12] += GND; J1[11] += INT
J1[9]  += SCK; J1[8]  += MISO; J1[7]  += GND
J1[5]  += IR_MOD; J1[4] += P3V3; J1[2] += GND; J1[1] += VBAT
# NC: J1[10]=RUN, J1[6]=GPIO21, J1[3]=EN (drivs ej från vårt kort).

# ---------- kraftinmatning + skydd ----------
F1[1] += VBAT_IN; F1[2] += VBAT_F                 # PTC-säkring
Q2["D"] += VBAT_F; Q2["S"] += VBAT; Q2["G"] += Rg2[1]; Rg2[2] += GND   # reverse-polarity P-FET
Dtvs["K"] += VBAT; Dtvs["A"] += GND               # TVS-clamp
Cin[1] += VBAT; Cin[2] += GND
Cbulk[1] += VBAT; Cbulk[2] += GND                 # reservoar för pulsen

# ---------- IR-emitterdriver: AKTIV KONSTANTSTRÖMS-SÄNKA, 56 kHz-gatad ----------
# Battery-OBEROENDE: op-amp håller SENSE = VREF → I = VREF/Rsense, oavsett VBAT (så länge
# headroom finns, dvs VBAT > 2·Vf + Vsense ≈ 6,9 V → kör 7,0 V lågspänningsspärr i firmware).
# Modulation: IR_MOD (3,3 V logik) → spänningsdelare → VREF ~0,206 V vid hög → I≈1,0 A; vid låg
# → VREF=0 → op-amp drar gaten låg → FET av. (Skalbar till 3 A: minska Rsense / öka VREF.)
D1["A"] += VBAT; D1["K"] += STR1; D2["A"] += STR1; D2["K"] += LEDC   # 2× 940 nm i serie, anod på VBAT
Qd["D"] += LEDC; Qd["S"] += SENSE; Qd["G"] += GATE                   # pass-FET (DPAK)
Rsense[1] += SENSE; Rsense[2] += GND                                 # ström-sense 0,2 Ω → 1 A @0,206 V
# 3A-override: Rp_ovr (0,1 Ω) MONTERA-FÖR-3A (DNP), parallellt direkt över Rsense (SENSE↔GND lokalt vid R2).
# DNP/obestyckat = 1 A (säker fail-safe default); montera Rp_ovr = 3 A (medvetet labbeslut + förnyad mätning).
Rp_ovr[1] += GND; Rp_ovr[2] += SENSE   # pad1=GND (via), pad2=IDRV_SENSE (spår→R2.1) — matchar boardens R3
Uop["V+"] += VBAT; Uop["V-"] += GND                                  # op-amp matas från VBAT
Uop["IN+"] += VREF; Uop["IN-"] += SENSE; Uop["OUT"] += Rgate[1]; Rgate[2] += GATE
Rdiv_a[1] += IR_MOD; Rdiv_a[2] += VREF; Rdiv_b[1] += VREF; Rdiv_b[2] += GND   # 15k/1k → 0,206 V
Ccomp[1] += Uop["OUT"]; Ccomp[2] += SENSE                            # slingkomp (Miller; bänktrimma)
Cop[1] += VBAT; Cop[2] += GND                                       # op-amp-avkoppling

# ---------- IMU (SPI 4-wire) + avkoppling ----------
# pin-nr (TDK AN-000483 Fig.2):  8=VDD 5=VDDIO 6=GND 13=SCLK 14=SDI 1=SDO 12=CS 4=INT1
U2[8] += P3V3; U2[5] += P3V3; U2[6] += GND        # VDD / VDDIO / GND
U2[7] += GND                                      # pin7 RESV → GND (IIM-42653)
U2[13] += SCK; U2[14] += MOSI; U2[1] += MISO; U2[12] += nCS; U2[4] += INT
# pinnar 2,3,9,10,11 = RESV/INT2/FSYNC -> ej anslutna (NC), enligt datablad
Cd1[1] += P3V3; Cd1[2] += GND; Cd2[1] += P3V3; Cd2[2] += GND; Cd3[1] += P3V3; Cd3[2] += GND

# ---------- mekanik (hål till GND) ----------
for H in (H1, H2, H3, HC, HP1, HP2, HP3, HP4, H4, H5, H6, H7, *CL):
    H[1] += GND

generate_netlist(file_="hardware/weapon-module.net")
print("wrote hardware/weapon-module.net")
