#!/usr/bin/env python3
"""STRILAS — patcha Specctra-DSN: flytta effekt-/pulsnät till egen klass 'power'
med bredare spår (width 400 ~ 0,4 mm) så Freerouting routar dem breda MED korrekt
clearance (ingen efter-breddning som äter avstånd). Körs mellan DSN-export och routning.
Användning: python dsn_power_class.py <board.dsn>
"""
import re, sys

# Effekt-/LED-nät (vapen + väst/hjälm). LED_A* = väst/hjälm konstellations-grenar.
POWER = {"VBAT", "VBAT_F", "VBAT_IN", "VBAT_RAW", "VBAT_PROT", "N$2", "LED_MID", "LED_CATH", "IDRV_SENSE",
         "SW", "LED_A1", "LED_A2", "LED_A3", "LED_A4",
         "LED_M1", "LED_M2", "LED_M3"}   # FIX: LED-mid-noder bär samma ~0,5A som grenarna (var 0,2mm)


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
    # auto-detektera via-padstack (4-lager: Via[0-3]_..., 2-lager: Via[0-1]_...) → funkar för båda
    vm = re.search(r'\b(Via\[0-\d\]_\d+:\d+_um)\b', t)
    circuit = f'\n      (circuit\n        (use_via {vm.group(1)})\n      )' if vm else ''
    pclass = (
        '\n    (class power "" ' + " ".join(pwr) + circuit + '\n'
        '      (rule\n        (width 500)\n        (clearance 200.1)\n      )\n    )'
    )
    t = t[:kc.end()] + pclass + t[kc.end():]
    open(dsn, "w").write(t)
    print(f"  flyttade {len(pwr)} nät till klass 'power' (width 500): {pwr}")


if __name__ == "__main__":
    main(sys.argv[1])
