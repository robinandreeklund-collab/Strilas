#!/usr/bin/env python3
"""STRILAS — patcha Specctra-DSN: flytta effekt-/pulsnät till egen klass 'power'
med bredare spår (width 400 ~ 0,4 mm) så Freerouting routar dem breda MED korrekt
clearance (ingen efter-breddning som äter avstånd). Körs mellan DSN-export och routning.
Användning: python dsn_power_class.py <board.dsn>
"""
import re, sys

POWER = {"VBAT", "VBAT_F", "VBAT_IN", "N$2", "LED_MID", "LED_CATH"}


def main(dsn):
    t = open(dsn).read()
    m = re.search(r'\(class kicad_default ""\s*(.*?)\s*\(circuit', t, re.S)
    if not m:
        print("  !! hittade ej kicad_default-klassen"); sys.exit(1)
    nets = m.group(1).split()
    keep = [n for n in nets if n not in POWER]
    pwr = [n for n in nets if n in POWER]
    if not pwr:
        print("  (inga effektnät kvar att flytta)"); return
    # ersätt nätlistan i kicad_default med 'keep'
    t = t[:m.start(1)] + " ".join(keep) + "\n      " + t[m.end(1):]
    # lägg in ny power-klass efter kicad_default-klassens avslut
    kc = re.search(r'\(class kicad_default.*?\n      \)\n    \)', t, re.S)
    block = kc.group(0)
    pclass = (
        '\n    (class power "" ' + " ".join(pwr) + '\n'
        '      (circuit\n        (use_via Via[0-3]_600:300_um)\n      )\n'
        '      (rule\n        (width 400)\n        (clearance 200.1)\n      )\n    )'
    )
    t = t[:kc.end()] + pclass + t[kc.end():]
    open(dsn, "w").write(t)
    print(f"  flyttade {len(pwr)} nät till klass 'power' (width 400): {pwr}")


if __name__ == "__main__":
    main(sys.argv[1])
