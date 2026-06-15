#!/usr/bin/env python3
"""Flippa FC:ans P4-socket (J1) till UNDERSIDAN (B_Cu) utan att flytta paddarna.
FC stackas OVANPÅ P4 → socketen måste vända NEDÅT för att ta emot edge A-stiften
(som pekar uppåt). Genomgående paddar → flippen påverkar inte routningen.
Körs efter placering, före DSN-export."""
import pcbnew
b = pcbnew.LoadBoard("hardware/firecontrol.kicad_pcb")
J1 = [f for f in b.GetFootprints() if f.GetReference() == "J1"][0]
J1.Flip(J1.GetPosition(), False)            # row längs x → up-ned-flip behåller paddarna
pcbnew.SaveBoard("hardware/firecontrol.kicad_pcb", b)
print(f"  J1-socket → {'BAK (nedåt mot P4)' if J1.IsFlipped() else 'FRAM'}")
