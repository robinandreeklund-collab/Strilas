#!/usr/bin/env python3
"""STRILAS — byt kondensator-PAKET på plats (pcbnew), bevara routning via plan-omfyllning.

Standardisera till in-stock-paket: 100nF → 0805 (CL21B104KBCNNNC), 1uF → 0402 (CL05A105KP5NNNC).
Avkopplings-C ligger på +3V3/GND-PLAN → footprint-byte + zon-omfyllning återkopplar paddarna
automatiskt (ingen diskret omroutning). Signal-nät-C (helmet codec) hanteras separat (re-route).

ETT kort per process (pcbnew-SWIG). Kör: python3 hardware/swap_cap_pkg.py <board>
"""
import sys, re, pcbnew
KI = "/usr/share/kicad/footprints/Capacitor_SMD.pretty"
# Standardisera 100nF & 1uF → 0402 (krympning = ingen clearance-krock; plan-C återkopplas vid omfyllning)
TARGET = {("100nF", "0805"): "C_0402_1005Metric", ("1uF", "0805"): "C_0402_1005Metric"}


def valof(netfile):
    t = open(netfile).read(); out = {}
    for blk in re.split(r'\n\s*\(comp\b', t)[1:]:
        r = re.search(r'\(ref "([^"]+)"\)', blk); v = re.search(r'\(value "([^"]*)"\)', blk)
        if r:
            out[r.group(1)] = v.group(1) if v else ""
    return out


def swap(board_name, only_refs=None):
    pcb = f"hardware/{board_name}.kicad_pcb"; net = f"hardware/{board_name}.net"
    vals = valof(net)
    b = pcbnew.LoadBoard(pcb)
    foots = list(b.GetFootprints())
    done = []
    for f in foots:
        ref = f.GetReference()
        if only_refs is not None and ref not in only_refs:
            continue
        cur = str(f.GetFPID().GetLibItemName()); val = vals.get(ref, "")
        size = "0402" if "0402" in cur else ("0805" if "0805" in cur else "")
        tgt = TARGET.get((val, size))
        if not tgt:
            continue
        pos, orient, flipped = f.GetPosition(), f.GetOrientation(), f.IsFlipped()
        padnets = {p.GetName(): p.GetNet() for p in f.Pads()}
        new = pcbnew.FootprintLoad(KI, tgt)
        new.SetReference(ref); new.SetValue(val); new.SetPosition(pos)
        if flipped:
            new.Flip(pos, False)
        new.SetOrientation(orient)
        new.Reference().SetVisible(f.Reference().IsVisible()); new.Value().SetVisible(False)
        for p in new.Pads():
            n = padnets.get(p.GetName())
            if n is not None:
                p.SetNet(n)
        b.Remove(f); b.Add(new)
        done.append(f"{ref}:{val}->{tgt.split('_')[1]}")
    # fyll om alla zoner (plan-omkoppling till nya paddar)
    if list(b.Zones()):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(pcb, b)
    print(f"  {board_name}: bytte {done}")


if __name__ == "__main__":
    board = sys.argv[1]
    refs = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    swap(board, refs)
