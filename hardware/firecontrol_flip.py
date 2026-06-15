#!/usr/bin/env python3
"""Flippa FC:ans P4-socket (J1) till UNDERSIDAN (B_Cu) utan att flytta paddarna.
FC stackas OVANPÅ P4 → socketen måste vända NEDÅT för att ta emot edge A-stiften
(som pekar uppåt). Genomgående paddar → flippen påverkar inte routningen.
Körs efter placering, före DSN-export."""
import pcbnew
b = pcbnew.LoadBoard("hardware/firecontrol.kicad_pcb")
for ref in ("J1", "J2"):                    # J1=edge A-socket, J2=edge B kraft-tapp
    f = [g for g in b.GetFootprints() if g.GetReference() == ref][0]
    f.Flip(f.GetPosition(), False)          # row längs x → up-ned-flip behåller paddarna
    print(f"  {ref}-socket → {'BAK (nedåt mot P4)' if f.IsFlipped() else 'FRAM'}")
pcbnew.SaveBoard("hardware/firecontrol.kicad_pcb", b)
