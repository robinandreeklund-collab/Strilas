#!/usr/bin/env python3
"""Flippa J1 (P4-kantkontakt, 1-kolumns THT) till BAKSIDAN efter routning.
Vänster-höger-flip (aFlipLeftRight=True) → enkolumns-paddar står kvar → spår förblir
anslutna. Körs efter ses_apply, före finish."""
import pcbnew
b = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
for f in b.GetFootprints():
    if f.GetReference() == "J1":
        f.Flip(f.GetPosition(), True)
pcbnew.SaveBoard("hardware/weapon-module.kicad_pcb", b)
b.BuildConnectivity()
try: un = b.GetConnectivity().GetUnconnectedCount(True)
except TypeError: un = b.GetConnectivity().GetUnconnectedCount()
j1 = [f for f in b.GetFootprints() if f.GetReference()=="J1"][0]
print(f"  J1 -> {'BAKSIDA' if j1.IsFlipped() else 'FRAM'}; oroutade efter flip = {un}")
