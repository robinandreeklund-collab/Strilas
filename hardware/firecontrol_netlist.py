#!/usr/bin/env python3
"""STRILAS — FIRE-CONTROL-KORT (vapen): kretsdefinition i kod (SKiDL → KiCad-netlista).
Genererar 'hardware/firecontrol.net'.

Separat litet breakout-kort som matar ESP32-P4-WIFI6:s SIGNALKANT 'edge A'
(VÄNSTERkanten) STELT — speglar hur optikmodulen matar edge B. Fan-out till
greppets I/O via JST-PH. Optikmodulen förblir ren optik (edge B).

EDGE A (verifierad mot Waveshares OFFICIELLA pinout-diagram, topp→botten):
  GPIO52 GPIO51 GND GPIO31 GPIO30 GPIO29 GPIO28 GND GPIO50 GPIO49
  GPIO5 GPIO4 GND GPIO3 GPIO2 SCL/GPIO8 SDA/GPIO7 GND DM/GPIO24 DP/GPIO25
  (GPIO24/25 = USB D-/D+ → undviks. Default-I²C = SCL/GPIO8 + SDA/GPIO7.)
  OBS: edge A har GND men INGEN kraftskena (VBUS/VSYS/3V3 ligger på edge B) →
  NFC-läsaren matas via separat 3V3-mata (J_PWR) från optikkortet/P4 edge B.

Vi matar ett SAMMANHÄNGANDE block av 12 stift = edge A-pos 6..17 (GPIO29..GPIO7).
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
# STEL kantkontakt mot P4 edge A (12 sammanhängande stift, pos 6..17).
P4A = mk("P4_EDGE_A", "J", [(i, i) for i in range(1, 13)],
         "Connector_PinHeader_2.54mm:PinHeader_1x12_P2.54mm_Vertical", "P4-kantkontakt (edge A)")
# 3V3-mata in (från optikkort/P4 edge B) — edge A saknar kraftskena
PWR = mk("PWR_IN", "J", [(1, "3V3"), (2, "GND")],
         "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", "3V3-mata (från edge B)")
# brytar-fan-out (mikrobrytare → GPIO, P4:s interna pull-up; ingen R behövs)
SW2 = lambda nm, sig: mk(nm, "J", [(1, sig), (2, "GND")],
                         "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", nm)
# recoil-styrning → separat recoil-effektkort (eFuse EN/PWM ut, FAULT in, GND)
REC = mk("RECOIL_CTRL", "J", [(1, "PWM"), (2, "FAULT"), (3, "GND")],
         "Connector_JST:JST_PH_S3B-PH-K_1x03_P2.00mm_Horizontal", "recoil-styrning")
# NFC-läsare (PN532, I²C) — SDA/SCL/3V3/GND
NFC = mk("NFC_PN532", "J", [(1, "SDA"), (2, "SCL"), (3, "3V3"), (4, "GND")],
         "Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal", "NFC PN532 (I²C)")
RES_T = mk("R", "R", [(1, "~"), (2, "~")], "Resistor_SMD:R_0805_2012Metric")
CAP_T = mk("C", "C", [(1, "~"), (2, "~")], "Capacitor_SMD:C_0805_2012Metric")
RES = lambda v: RES_T(value=v)
CAP = lambda v: CAP_T(value=v)
MH = lambda n: mk(f"MH{n}", "H", [(1, "1")], "MountingHole:MountingHole_2.2mm_M2", "M2")

# ---------- nät ----------
GND, P3V3 = Net("GND"), Net("+3V3")
TRIG, RACK, MAG_REL, MAGWELL = Net("TRIG"), Net("RACK"), Net("MAG_REL"), Net("MAGWELL")
REC_PWM, REC_FLT = Net("RECOIL_PWM"), Net("RECOIL_FAULT")
SDA, SCL = Net("NFC_SDA"), Net("NFC_SCL")

# ---------- instansiera ----------
J1 = P4A(); Jpwr = PWR()
Jtrig = SW2("TRIGGER", "SIG")(); Jrack = SW2("RACK_SW", "SIG")()
Jmag = SW2("MAG_REL_SW", "SIG")(); Jmagw = SW2("MAGWELL_SW", "SIG")()
Jrec = REC(); Jnfc = NFC()
Rsda = RES("4k7"); Rscl = RES("4k7")            # I²C pull-ups till 3V3
Cd1 = CAP("100nF"); Cd2 = CAP("1uF")            # 3V3-avkoppling vid NFC
H1, H2, H3 = MH(1)(), MH(2)(), MH(3)()

# ---------- J1 = P4 edge A (pos 6..17), verifierad mot officiell pinout ----------
#   FC-stift  edge A-pos  P4-pin   nät
#   J1[1]     6           GPIO29   MAGWELL  (magasin-närvaro)
#   J1[2]     7           GPIO28   RECOIL_FAULT (in, eFuse open-drain → intern pull-up)
#   J1[3]     8           GND      GND
#   J1[4]     9           GPIO50   -- LEDIG (NC, Fas 2-hook)
#   J1[5]     10          GPIO49   -- LEDIG (NC, Fas 2-hook)
#   J1[6]     11          GPIO5    RACK     (charging-handle)
#   J1[7]     12          GPIO4    TRIG     (avtryckare)
#   J1[8]     13          GND      GND
#   J1[9]     14          GPIO3    MAG_REL  (mag-release-spak)
#   J1[10]    15          GPIO2    RECOIL_PWM (ut → eFuse EN/gate)
#   J1[11]    16          GPIO8    NFC_SCL
#   J1[12]    17          GPIO7    NFC_SDA
J1[1] += MAGWELL; J1[2] += REC_FLT; J1[3] += GND
J1[6] += RACK; J1[7] += TRIG; J1[8] += GND
J1[9] += MAG_REL; J1[10] += REC_PWM; J1[11] += SCL; J1[12] += SDA
# J1[4]=GPIO50, J1[5]=GPIO49 lämnas NC (reserv-GPIO).

# ---------- 3V3-mata (edge A saknar kraftskena) ----------
Jpwr["3V3"] += P3V3; Jpwr["GND"] += GND

# ---------- fan-out till greppets I/O ----------
Jtrig["SIG"] += TRIG; Jtrig["GND"] += GND
Jrack["SIG"] += RACK; Jrack["GND"] += GND
Jmag["SIG"] += MAG_REL; Jmag["GND"] += GND
Jmagw["SIG"] += MAGWELL; Jmagw["GND"] += GND
Jrec["PWM"] += REC_PWM; Jrec["FAULT"] += REC_FLT; Jrec["GND"] += GND
Jnfc["SDA"] += SDA; Jnfc["SCL"] += SCL; Jnfc["3V3"] += P3V3; Jnfc["GND"] += GND

# ---------- I²C pull-ups + 3V3-avkoppling ----------
Rsda[1] += P3V3; Rsda[2] += SDA
Rscl[1] += P3V3; Rscl[2] += SCL
Cd1[1] += P3V3; Cd1[2] += GND
Cd2[1] += P3V3; Cd2[2] += GND

# ---------- mekanik (hål till GND) ----------
for H in (H1, H2, H3):
    H[1] += GND

generate_netlist(file_="hardware/firecontrol.net")
print("wrote hardware/firecontrol.net")
