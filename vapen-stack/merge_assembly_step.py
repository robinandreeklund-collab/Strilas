#!/usr/bin/env python3
"""Slå ihop de tre korten till EN assembly-STEP, 12 mm plan-till-plan i Z.
Använder OCCT (cadquery): varje *-stack.step (redan XY-co-orienterad) laddas och
ges en STEL Location i Z — geometrin/komponenterna rörs inte (ingen scattering).
optik z0 · P4 z12 · FC z24. Standoffs läggs in av användaren."""
import cadquery as cq

PARTS = [("weapon-module.step", 0.0),
         ("p4-board-stack.step", 12.0),
         ("firecontrol-stack.step", 24.0)]
OUT = "strilas-assembly.step"

asm = cq.Assembly(name="STRILAS_vapen_stack")
for path, z in PARTS:
    shp = cq.importers.importStep(path)
    asm.add(shp, name=path.replace(".step", ""), loc=cq.Location((0, 0, z)))
    bb = shp.val().BoundingBox()
    print(f"  {path:24} z+{z:<4} → lokal z[{bb.zmin:6.2f},{bb.zmax:6.2f}] → globalt z[{bb.zmin+z:6.2f},{bb.zmax+z:6.2f}]")

asm.export(OUT)
print(f"skrev {OUT}")
