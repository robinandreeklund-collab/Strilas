# STRILAS — Vapen-modul: FÄRDIGROUTAD PCB (status)

Hela EDA-kedjan kördes **autonomt** i denna container (KiCad 7 + Freerouting), från
netlistan till en **fullständigt routad, DRC-ren board + Gerbers**. Du behöver inte göra
EDA själv — filerna nedan laddas upp till en fab.

## Vad som producerades

| Fil | Innehåll |
|---|---|
| `weapon-module.kicad_pcb` | **fullständigt routad** 4-lagers board (öppna i KiCad) |
| `weapon-module-gerbers.zip` | **Gerbers + drill** (11 lager + drill, ladda upp till JLCPCB/PCBWay) |
| `weapon-module-routed.png` | visuell render av routningen |
| `strilas.pretty/` | **kund-footprints** (Vishay-emitter + ICM-45686 LGA-14) |

## Verktygskedjan (reproducerbar)

```
weapon_module_netlist.py   → weapon-module.net        (SKiDL: schema/netlista)
make_footprints.py         → strilas.pretty/*.kicad_mod (emitter + IMU, datablads-mått)
receiver_place.py weapon   → weapon-module.kicad_pcb   (placerad, nät, outline, Ø16-linshål, 4 lager)
weapon_thermal_vias.py     → termiska vior under emittrarna FÖRE routning
ExportSpecctraDSN          → weapon-module.dsn
dsn_power_class.py         → effektnät i egen 0,4 mm-klass (rätt clearance)
freerouting (xvfb, headless) → weapon-module.ses       (autoroute ~8 s, 0 oroutade)
ses_apply.py               → spår/vior in i boarden
weapon_finish.py           → kopparplan (In1=GND, In2=VBAT, B=GND, F=GND-fyll) + fyllning
kicad-cli pcb export gerbers/drill → weapon-module-gerbers.zip
render_weapon.py           → weapon-module-routed.png
```

## Routnings-status — KOMPLETT

- **24 komponenter, alla med riktiga footprints** (inga platshållare kvar).
- **176 spårsegment + 25 vior** (varav 8 termiska under emittrarna), 4 lager.
- **0 oroutade förbindelser** — hela nätet draget inkl. 0,5 mm-pitch-IMU:ns SPI-escape.
- **Effektnät 0,4 mm** (VBAT/VBAT_F/N$2/LED_MID/LED_CATH), signal 0,2 mm.
- **Kopparplan:** In1.Cu = GND, In2.Cu = VBAT (effekt), B.Cu = GND-retur, F.Cu = GND-fyll.
- **Termiska vior** (4 per emitter) i katod-padden → baksidans koppar.
- **Ø16 lins-urtag** i mitten hålls fritt från koppar (min 1,6 mm marginal).
- **Kamerafäste H4–H7** (M2, B0332 28×28-mönster) runt linsaxeln; kameran skruvas bakom kortet.
- **P4** ansluts via **J1 (2×6)** + kort kabel (P4-kortet 71×21 mm sitter i vapenkroppen, ej bakom kameran).

## Egenkontroll (kört i container, geometriskt)

| Kontroll | Resultat |
|---|---|
| Komponent-krockar (courtyard) | **0** |
| Delar utanför outline / i linshålet | **0** |
| Koppar-koppar clearance (olika nät) | **0 brott @ 0,2 mm** (JLCPCB-min 0,152 mm) |
| Koppar→kant / koppar→linshål | min **1,55 / 1,62 mm** |
| Via annulär ring | **0,175 mm** (≥ 0,125 mm) |
| Oroutade (connectivity) | **0** |

## Footprints (verifierade mot datablad)

- **D2/D3 — Vishay VSMA1094750X02 (940 nm)**: land per Vishay DocNo 80365 (ritn. 6.550-5366.9-3),
  två sido-paddar (anod/katod) + central termisk katod-slug. 3,4×3,4 mm, 1,5 A DC / 5 A pulsat.
- **U1 — TDK ICM-45686 LGA-14 2,5×3,0 mm, 0,5 mm-pitch**: pinout verifierad mot TDK AN-000483
  Fig. 2 (pin-kompatibel ICM-45605/45686). SPI på pinnar 13/14/1/12 (SCLK/SDI/SDO/CS), INT1 pin 4.

## Det enda som kvarstår (kan inte avgöras utan fysisk del — normalt sista steg)

1. **Verifiera footprint-padstacken mot den köpta delens datablad** innan beställning (standard DFM).
2. **Bänkmät ögonsäkerhet (Class 1 / AE)** per IEC 60825-1 vid driftströmmen — hårdvaru-strömtaket
   (R2/Rset) är vakten; mät innan emittern pekas mot någon.

Allt EDA-arbete (placering, routning, plan, clearance, Gerbers) är klart och granskat i container.
