#!/usr/bin/env python3
"""STRILAS — lägg ERM-coin-motorns lim-keepout (MK1) på BAKSIDAN @centrum på väst-patchen.
Footprinten (strilas:ERM_Coin_Keepout_10mm) är pad-lös (ren silk/Fab/courtyard-markering): motorn
(Ø10 coin) fästs med sin 3M-tejp inom ringen, matas via J2 (2-pol JST). 3M-tejpen isolerar motorns
metallhölje från ev. GND-koppar → ingen kopparkeepout behövs (centrum-fronten är full av optik-kluster).
Körs EFTER receiver_place.py vest (placering nollställer kortet → keepout måste återläggas)."""
import os, pcbnew
PCB = "hardware/vest-patch.kicad_pcb"
LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strilas.pretty")
MM = pcbnew.FromMM
OX, OY = 150.0, 120.0

b = pcbnew.LoadBoard(PCB)
# ta bort ev. tidigare MK1 (idempotent)
for f in list(b.GetFootprints()):
    if f.GetReference() == "MK1":
        b.Remove(f)
fp = pcbnew.FootprintLoad(LOCAL, "ERM_Coin_Keepout_10mm")
fp.SetReference("MK1")
fp.SetPosition(pcbnew.VECTOR2I(MM(OX), MM(OY)))   # centrum (0,0)
b.Add(fp)
fp.Flip(fp.GetPosition(), False)                  # → BAKSIDAN (mot kroppen)
pcbnew.SaveBoard(PCB, b)
print(f"  MK1 (ERM_Coin_Keepout_10mm) @ centrum, BAKSIDA — keepout återlagd.")
