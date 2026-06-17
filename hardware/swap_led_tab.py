#!/usr/bin/env python3
"""STRILAS — byt LED-tab-socklarnas footprint till strilas:LED_Tab PÅ PLATS (pcbnew).

De fyra/sex LED-tab-socklarna (väst-patch D7-D10, hjälm-mb D5-D10) ritades först med en
PLACEHOLDER (PinHeader_1x02_Vertical) vars 3D-modell bara var en naken 2-stiftslist → i
STEP-filen "svävade" tabbarna fel. strilas:LED_Tab är en RIKTIG LED-tab-sockel: identiska
paddar (pad1 rect @0,0, pad2 oval @0,2.54, Ø1 drill 1.7) → DROP-IN, men med korrekt
emissions-pil på silk + 3D-modell (led-tab-3d.step) som visar den STÅENDE tabben med OSLON.

Eftersom paddarna är geometriskt identiska byts footprinten PÅ PLATS (samma läge, vridning
och nät) → BEFINTLIG ROUTING (hjälm-mb: 584 spår) bevaras orörd. Refs som ska bytas läses ur
netlistan (footprint == strilas:LED_Tab) så endast tab-socklarna rörs.

Kör: python3 hardware/swap_led_tab.py
"""
import os, re, sys, pcbnew

LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strilas.pretty")


def tab_refs(netfile):
    """Refs vars footprint i netlistan är strilas:LED_Tab."""
    t = open(netfile).read()
    refs = []
    for m in re.finditer(r'\(comp\s*\(ref "([^"]+)"\).*?\(footprint "([^"]+)"\)', t, re.S):
        if m.group(2) == "strilas:LED_Tab":
            refs.append(m.group(1))
    return refs


def swap(netfile, pcbfile):
    refs = set(tab_refs(netfile))
    board = pcbnew.LoadBoard(pcbfile)
    # iterera GetFootprints() (rätt-typade FOOTPRINT-objekt; FindFootprintByReference
    # ger ett SwigPyObject vars GetFPID() saknar GetLibItemName)
    byref = {f.GetReference(): f for f in board.GetFootprints()}
    done = []
    for ref in sorted(refs):
        old = byref.get(ref)
        if old is None:
            print(f"  !! {ref} saknas på {pcbfile}"); continue
        if str(old.GetFPID().GetLibItemName()) == "LED_Tab":
            done.append(ref + "(redan)"); continue
        pos = old.GetPosition()
        orient = old.GetOrientation()
        flipped = old.IsFlipped()
        padnets = {p.GetName(): p.GetNet() for p in old.Pads()}
        new = pcbnew.FootprintLoad(LOCAL, "LED_Tab")
        if new is None:
            print(f"  !! kan ej ladda strilas:LED_Tab"); sys.exit(1)
        new.SetReference(ref)
        new.SetPosition(pos)
        if flipped:
            new.Flip(pos, False)
        new.SetOrientation(orient)
        for p in new.Pads():
            n = padnets.get(p.GetName())
            if n is not None:
                p.SetNet(n)
        board.Remove(old)
        board.Add(new)
        done.append(ref)
    pcbnew.SaveBoard(pcbfile, board)
    print(f"  {pcbfile}: bytte {done}")


PAIRS = {
    "vest": ("hardware/vest-patch.net", "hardware/vest-patch.kicad_pcb"),
    "helmet": ("hardware/helmet-mb.net", "hardware/helmet-mb.kicad_pcb"),
}

if __name__ == "__main__":
    # ETT kort per process — pcbnew:s SWIG-bindning ger ett otypat board-objekt vid
    # andra LoadBoard() i samma process. Kör: python3 swap_led_tab.py vest|helmet
    for name in (sys.argv[1:] or list(PAIRS)):
        swap(*PAIRS[name])
