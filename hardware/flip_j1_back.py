#!/usr/bin/env python3
"""Flippa alla kontakter (J1, J2, J3) till BAKSIDAN efter routning utan att flytta paddarna.
Flip-axeln måste vara PARALLELL med paddraden: J1 (lodrät rad, rot0) → vänster-höger (True);
J2/J3 (vågrät rad, rot90) → topp-botten (False). Då står paddarna kvar → spår bevaras.
Körs efter ses_apply, före finish."""
import pcbnew
b = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
axis = {"J1": True, "J2": False, "J3": False}
for f in b.GetFootprints():
    r = f.GetReference()
    if r in axis:
        f.Flip(f.GetPosition(), axis[r])
pcbnew.SaveBoard("hardware/weapon-module.kicad_pcb", b)
b.BuildConnectivity()
try: un = b.GetConnectivity().GetUnconnectedCount(True)
except TypeError: un = b.GetConnectivity().GetUnconnectedCount()
sides = {f.GetReference(): ("BAK" if f.IsFlipped() else "FRAM")
         for f in b.GetFootprints() if f.GetReference() in axis}
print(f"  kontakter: {sides}; oroutade efter flip = {un}")
