#!/usr/bin/env python3
"""STRILAS — lägg termiska vior under emittrarna FÖRE routning.
Vian sitter inne i emitterns centrala katod-padd (F.Cu) → redan ansluten på F.Cu,
ger värmeväg till baksidan. Placeras före DSN-export så Freerouting håller andra
nät fria från dem (ren DRC). Körs efter receiver_place.py, före ExportSpecctraDSN.
"""
import pcbnew

PCB = "hardware/weapon-module.kicad_pcb"
OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
EMIT = [(-9.0, 22.0, "LED_MID"), (9.0, 22.0, "LED_CATH")]   # emitter-centrum + katod-nät


def main():
    b = pcbnew.LoadBoard(PCB)
    n = 0
    for cx, cy, net in EMIT:
        nc = b.FindNet(net).GetNetCode()
        for dx in (-0.6, 0.6):
            for dy in (-0.7, 0.7):
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(MM(OX + cx + dx), MM(OY - (cy + dy))))
                v.SetWidth(MM(0.7)); v.SetDrill(MM(0.35))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNetCode(nc); b.Add(v); n += 1
    pcbnew.SaveBoard(PCB, b)
    print(f"  {n} termiska vior tillagda (katod-nät) före routning")


if __name__ == "__main__":
    main()
