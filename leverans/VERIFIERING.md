# STRILAS — FULL KORT-VERIFIERING (alla 6 kort)

Föranledd av XT30-polaritetsbuggen på vest-mb. Verktyg: `hardware/audit_board.py` (ETT kort/process).
Kör om när som helst: `python3 hardware/audit_board.py <kort>`.

## Sammanfattning

| Kort | Lager | DRC clr/uncon | PCB↔.net | Kontakt-pol | Diod/LED-pol | P4-pinout |
|---|---|---|---|---|---|---|
| weapon-module | 4 | **0 / 0** ✓ | 0 mismatch ✓ | — | ✓ | VSYS→VBAT, 3V3, GND ✓ |
| firecontrol | 2 | **0 / 0** ✓ | 0 mismatch ✓ | — | — | GND ✓, inga konflikter |
| helmet-mb | 4 | **0 / 0** ✓ | 0 mismatch ✓ | — | ✓ | VSYS→VBAT, GND ✓ |
| vest-mb | 4 | **0 / 0** ✓ | 0 mismatch ✓ | **XT30 ✓ (fixad)** | — | VSYS→VBAT, GND ✓ |
| vest-patch | 2 | **0 / 0** ✓ | 0 mismatch ✓ | — | ✓ | (ej P4-kort) |
| led-tab | 2 | **0 / 0** ✓ | — | — | — | (mikro-PCB) |

**Resultat: alla kort rena.** Den enda funna felet (XT30 omvänd polaritet på vest-mb) är åtgärdat
och omverifierat. Inga ytterligare fel.

## Vad som verifierades (per kort)

1. **DRC** — clearance@0.2 mm + unconnected (samma kontroll som route-skripten). Alla 0/0.
2. **PCB↔.net-konsistens** — varje pad-nät i `.kicad_pcb` jämförs mot `.net`. **0 mismatch på alla
   kort** → PCB och netlista är överens (just den klass av bugg där de glider isär). Detta är den
   starkaste garanten mot "tyst" felkoppling.
3. **Kontakt-polaritet** — inneboende-polariserade (keyade) kontakter mot footprint-silk:
   - **vest-mb J13 XT30PW-M**: pin1=GND(−), pin2=VBAT(+) ✓ — matchar footprintens silk (pin1=−,
     pin2=+). *(Var pin1=VBAT/pin2=GND → batteri bakvänt; fixat i `vest_mb_netlist.py` + omroutat.)*
   - JST-XH/PH/GH är **ej** inneboende-polariserade (symmetrisk husning, polaritet via kabel) → ingen
     XT30-liknande risk. XH-batterikontakter ändå konsistens-kollade: weapon J2 + helmet J10 båda
     **pin1=VBAT, pin2=GND** → samma batterikabel funkar på båda.
4. **Diod/LED/emitter-polaritet** — rätt anod/katod per footprint (källa: SKiDL-part-templates +
   `make_footprints.py` land E062.3010.91-06):
   - **IR-emitter SFH4725S/4715AS** (pad1=anod): anod→VBAT högsida, katod→sänka. Serie-sträng
     VBAT→emitter→emitter→LED_CATH→CC-sänka→GND ✓
   - **LED_Tab konstellation** (pad1=anod): VBAT→10R→anod→LED→LED→katod→N-FET→GND ✓
   - **BAT54 diod-OR** (D_SOD-123, pad1=katod): aktiv-låg OR, DATA-pullup→3V3; TSOP drar katod låg
     → diod leder → DATA låg ✓
   - **TVS SMBJ12A** (D_SMB, pad1=katod): katod→VBAT, anod→GND, unidirektionell matningsklamp ✓
5. **P4-pinout** (mot `p4_pinmap.py` + ESP32-P4-databladsregler):
   - Kraftstift rätt: **VSYS→VBAT, 3V3→+3V3, GND→GND** på alla P4-kort.
   - **Inga GPIO-konflikter** (samma kant-stift med >1 nät) på något kort.
   - **Inga ogiltiga GPIO-nummer** (alla inom GPIO0–54).
   - **Inga strapping-pinnar** (34–38) belastade.
   - INFO: USB-Serial-JTAG-pinnar (GPIO24/25) används som vanlig GPIO — firecontrol (MODE_A/B),
     helmet (I²S_DIN/AMP_SD). Medvetet val → man tappar USB-JTAG-debug men kan flasha via OTG-USB/UART.
     Inget fel, men noterat.

## Not
`audit_board.py` är nu det stående verifierings-verktyget. Kör det efter VARJE board-ändring
(placering/routning/netlist) som komplement till route-skriptens egna DRC-grind.
