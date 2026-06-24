#!/usr/bin/env python3
"""STRILAS — lagg till globala fiducials (Ø1 mm, 2 mm mask) pa ett FARDIGROUTAT kort utan
omroutning. Fiducials har INGET nat -> paverkar ej koppar/DRC; behovs for NextPCB SMT pick-and-place.
Anvandning: python3 hardware/add_fiducials.py <board.kicad_pcb> x1,y1 x2,y2 x3,y3 ...
Koordinater i mm i board-koord (x hoger+, y upp+), origo = kortcentrum (OX,OY=150,120).
Hoppar over en position om den krockar (pad-bbox) med befintlig footprint."""
import sys, pcbnew

OX, OY = 150.0, 120.0
MM = pcbnew.FromMM
FID = ("Fiducial", "Fiducial_1mm_Mask2mm")
FPDIR = "/usr/share/kicad/footprints"


def V(x, y): return pcbnew.VECTOR2I(MM(OX + x), MM(OY - y))


def main():
    pcb = sys.argv[1]
    pts = [tuple(float(v) for v in a.split(",")) for a in sys.argv[2:]]
    b = pcbnew.LoadBoard(pcb)
    # befintliga pad-bboxar (for krock-koll)
    boxes = [f.GetBoundingBox(False, False) for f in b.GetFootprints()]
    n = 0
    existing = [f.GetReference() for f in b.GetFootprints() if f.GetReference().startswith("FID")]
    idx = len(existing) + 1
    for (x, y) in pts:
        f = pcbnew.FootprintLoad(f"{FPDIR}/{FID[0]}.pretty", FID[1])
        if f is None:
            print(f"  !! kan ej ladda {FID}"); continue
        f.SetReference(f"FID{idx}")
        f.SetPosition(V(x, y))
        bb = f.GetBoundingBox(False, False)
        if any(bb.Intersects(o) for o in boxes):
            print(f"  FID{idx} @({x},{y}) KROCKAR -> hoppar over"); continue
        b.Add(f); boxes.append(bb)
        print(f"  FID{idx} @({x},{y}) tillagd"); idx += 1; n += 1
    if n and list(b.Zones()):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())   # fyll om plan -> rensar koppar runt no-net-fiducials
        print("  kopparplan omfyllda runt fiducials")
    pcbnew.SaveBoard(pcb, b)
    print(f"{pcb}: {n} fiducials tillagda")


if __name__ == "__main__":
    main()
