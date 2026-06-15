#!/usr/bin/env python3
"""STRILAS — exportera P4 + FC som STEP FÖR-ROTERade till optikens frame, så att de tre
korten droppar in CO-ORIENTERADE i Fusion (rätt rader möts: optik↔edge B 14↔14,
FC↔edge A 12↔12). Optiken är ankar-frame; P4 och FC transformeras dit via
2-punkts stel transform ur faktiska padd-positioner. Verifierar innan export.

Lämnar fab-filerna (*.kicad_pcb) i sina naturliga frames; skriver *-stack.step.
Z bakas INTE — lyft P4 ~11 mm och FC ~11 mm till i Fusion (socket+header-höjd)."""
import math, pcbnew

OUT = {"p4": "hardware/p4-board-stack.step", "fc": "hardware/firecontrol-stack.step"}


def pad(board, ref, name):
    f = [g for g in board.GetFootprints() if g.GetReference() == ref][0]
    p = [q for q in f.Pads() if q.GetName() == name][0]
    return p.GetPosition()


def items(b):
    return list(b.GetFootprints()) + list(b.GetDrawings()) + list(b.GetTracks()) + list(b.Zones())


def apply_xform(b, ang_deg, center, offset):
    ea = pcbnew.EDA_ANGLE(ang_deg, pcbnew.DEGREES_T)
    for it in items(b):
        it.Rotate(center, ea)
    for it in items(b):
        it.Move(offset)


def fit(src_path, src_ref, dst1, dst2, out_pcb):
    """Stel transform: src_ref pad 'A'→dst1, pad 'B'→dst2. Auto-korrigerar rotationstecken."""
    b = pcbnew.LoadBoard(src_path)
    nA, nB = ("1", str(len([0 for _ in [g for g in b.GetFootprints() if g.GetReference()==src_ref][0].Pads()])))
    p1, p2 = pad(b, src_ref, nA), pad(b, src_ref, nB)
    ang = math.degrees(math.atan2(dst2.y-dst1.y, dst2.x-dst1.x) - math.atan2(p2.y-p1.y, p2.x-p1.x))
    best = None
    for trial in (ang, -ang, ang+180, ang-180):
        b2 = pcbnew.LoadBoard(src_path)
        c = pad(b2, src_ref, nA)
        apply_xform(b2, trial, pcbnew.VECTOR2I(c.x, c.y), pcbnew.VECTOR2I(0, 0))
        q1 = pad(b2, src_ref, nA)
        apply_xform(b2, 0, pcbnew.VECTOR2I(0, 0), pcbnew.VECTOR2I(dst1.x-q1.x, dst1.y-q1.y))
        e = (pad(b2, src_ref, nB) - dst2).EuclideanNorm()/1e6
        if best is None or e < best[0]:
            best = (e, trial, b2)
    err, trial, b2 = best
    pcbnew.SaveBoard(out_pcb, b2)
    return err, nB, b2


# optik = ankar. Mål för P4 edge B = optik-J1 pad 1 & 14.
op = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
dQ1, dQ14 = pad(op, "J1", "1"), pad(op, "J1", "14")
e1, nB, p4b = fit("hardware/p4-board.kicad_pcb", "J_B", dQ1, dQ14, "/tmp/p4_stack.kicad_pcb")
print(f"P4→optik: edge B pad{nB}-fel = {e1:.3f} mm  {'✓' if e1<0.2 else '✗'}")

# FC edge A-mål = TRANSFORMERADE P4 J_A pad 1 & 12.
tA1, tA12 = pad(p4b, "J_A", "1"), pad(p4b, "J_A", "12")
e2, n12, _ = fit("hardware/firecontrol.kicad_pcb", "J1", tA1, tA12, "/tmp/fc_stack.kicad_pcb")
print(f"FC→P4:   socket pad{n12}-fel = {e2:.3f} mm  {'✓' if e2<0.2 else '✗'}")

if e1 < 0.2 and e2 < 0.2:
    import subprocess
    for src, key in (("/tmp/p4_stack.kicad_pcb", "p4"), ("/tmp/fc_stack.kicad_pcb", "fc")):
        subprocess.run(["kicad-cli", "pcb", "export", "step", "-f", "--subst-models",
                        "-o", OUT[key], src], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("skrev", OUT["p4"], "och", OUT["fc"])
else:
    print("!! transform ej ren — exporterar EJ")
