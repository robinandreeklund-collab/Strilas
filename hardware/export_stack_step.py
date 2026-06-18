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


def holepos(b, ref):
    f = [g for g in b.GetFootprints() if g.GetReference() == ref][0]
    return f.GetPosition()


def fit(src_path, src_ref, dst1, dst2, out_pcb, hole_refs=None, hole_dst=None):
    """Stel transform: src_ref:s ändstift → (dst1,dst2). En LINJÄR kontakt är symmetrisk →
    BÅDA ändpunkts-korrespondenserna ger ~0 mm kontaktfel; monteringshålen (hole_refs på src,
    hole_dst-positioner) avgör den FYSISKT korrekta (annars kan P4 hamna kontakt-mötande men
    med standoff-hålen 10-20 mm fel → korten droppar in felplacerade i CAD)."""
    b = pcbnew.LoadBoard(src_path)
    nA, nB = ("1", str(len([0 for _ in [g for g in b.GetFootprints() if g.GetReference()==src_ref][0].Pads()])))
    p1, p2 = pad(b, src_ref, nA), pad(b, src_ref, nB)
    best = None
    for e1, e2 in ((dst1, dst2), (dst2, dst1)):       # prova BÅDA ändpunkts-korrespondenserna
        ang = math.degrees(math.atan2(e2.y-e1.y, e2.x-e1.x) - math.atan2(p2.y-p1.y, p2.x-p1.x))
        for trial in (ang, -ang, ang+180, ang-180):
            b2 = pcbnew.LoadBoard(src_path)
            c = pad(b2, src_ref, nA)
            apply_xform(b2, trial, pcbnew.VECTOR2I(c.x, c.y), pcbnew.VECTOR2I(0, 0))
            q1 = pad(b2, src_ref, nA)
            apply_xform(b2, 0, pcbnew.VECTOR2I(0, 0), pcbnew.VECTOR2I(e1.x-q1.x, e1.y-q1.y))
            cerr = (pad(b2, src_ref, nB) - e2).EuclideanNorm()/1e6
            herr = 0.0
            if hole_refs and hole_dst:
                herr = max(min((holepos(b2, r)-h).EuclideanNorm()/1e6 for h in hole_dst) for r in hole_refs)
            if best is None or (cerr+herr) < best[0]:
                best = (cerr+herr, cerr, b2)
    score, err, b2 = best
    pcbnew.SaveBoard(out_pcb, b2)
    return err, nB, b2


# optik = ankar. Mål för P4 edge B = optik-J1 pad 1 & 14 + de 4 standoff-hålen (HÅL-KONSISTENT).
op = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
dQ1, dQ14 = pad(op, "J1", "1"), pad(op, "J1", "14")
OHOLES = [holepos(op, r) for r in ("HP1", "HP2", "HP3", "HP4")]
e1, nB, p4b = fit("hardware/p4-board.kicad_pcb", "J_B", dQ1, dQ14, "/tmp/p4_stack.kicad_pcb",
                  hole_refs=("MP1", "MP2", "MP3", "MP4"), hole_dst=OHOLES)
print(f"P4→optik: edge B pad{nB}-fel = {e1:.3f} mm  {'✓' if e1<0.2 else '✗'}")

# FC edge A-mål = TRANSFORMERADE P4 J_A pad 1 & 12 + transformerade MP-hål (HÅL-KONSISTENT).
tA1, tA12 = pad(p4b, "J_A", "1"), pad(p4b, "J_A", "12")
P4HOLES = [holepos(p4b, r) for r in ("MP1", "MP2", "MP3", "MP4")]
e2, n12, _ = fit("hardware/firecontrol.kicad_pcb", "J1", tA1, tA12, "/tmp/fc_stack.kicad_pcb",
                 hole_refs=("H1", "H2", "H3", "H4"), hole_dst=P4HOLES)
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
