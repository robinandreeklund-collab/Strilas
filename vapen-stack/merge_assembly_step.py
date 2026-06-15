#!/usr/bin/env python3
"""Slå ihop de tre korten till EN assembly-STEP, 12 mm plan-till-plan i Z.
De två *-stack.step är redan XY-co-orienterade (optikens frame); här Z-förskjuts
P4 (+12) och FC (+24) och all geometri slås ihop till en fil (standoffs läggs in
av användaren). Ren textbearbetning: translatera CARTESIAN_POINT i Z + renumrera
entitets-ID så de inte krockar.  optik z0 · P4 z12 · FC z24."""
import re

PARTS = [("weapon-module.step", 0.0),
         ("p4-board-stack.step", 12.0),
         ("firecontrol-stack.step", 24.0)]
OUT = "strilas-assembly.step"

cp_re = re.compile(r"(CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\()\s*"
                   r"([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*(\))",
                   re.I)

def shift_z(text, dz):
    if dz == 0:
        return text
    def repl(m):
        z = float(m.group(4)) + dz
        return f"{m.group(1)}{m.group(2)},{m.group(3)},{z:.6f}{m.group(5)}"
    return cp_re.sub(repl, text)

def renumber(text, offset):
    if offset == 0:
        return text
    return re.sub(r"#(\d+)", lambda m: f"#{int(m.group(1))+offset}", text)

def maxid(text):
    return max((int(x) for x in re.findall(r"#(\d+)", text)), default=0)

header = None
bodies = []
offset = 0
for path, dz in PARTS:
    t = open(path).read()
    i0 = t.index("DATA;") + len("DATA;")
    i1 = t.rindex("ENDSEC;")
    if header is None:
        header = t[:i0]                      # behåll första filens HEADER + DATA;
    data = t[i0:i1]
    data = shift_z(data, dz)
    data = renumber(data, offset)
    bodies.append(data)
    offset += maxid(data) + 100              # nästa fils ID:n efter denna

merged = header + "\n" + "\n".join(bodies) + "\nENDSEC;\nEND-ISO-10303-21;\n"
open(OUT, "w").write(merged)

# sanity: Z-spann per kort
for path, dz in PARTS:
    t = shift_z(open(path).read(), dz)
    zs = [float(m.group(4)) for m in cp_re.finditer(t)]
    print(f"  {path:24} dz={dz:>4}  →  z [{min(zs):7.2f}, {max(zs):7.2f}]")
print(f"skrev {OUT}  ({len(merged)//1024} kB)")
