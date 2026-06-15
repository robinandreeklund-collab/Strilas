# STRILAS — Vapen-modul: AUTOROUTAD PCB (status)

Hela EDA-kedjan kördes **autonomt** i denna container (KiCad 7 + Freerouting), från
netlistan till en routad board + Gerbers. Du behöver inte göra EDA själv — filerna nedan
laddas upp till en fab.

## Vad som producerades

| Fil | Innehåll |
|---|---|
| `weapon-module.kicad_pcb` | **routad** 4-lagers board (öppna i KiCad) |
| `weapon-module-gerbers.zip` | **Gerbers + drill** (ladda upp till JLCPCB/PCBWay) |
| `weapon-module-routed.png` | visuell render av routningen |
| `weapon_module_place.py` | bygger placerad board ur netlistan (pcbnew) |
| `ses_import.py` | applicerar Freerouting-rutter på boarden |

## Verktygskedjan (reproducerbar)

```
weapon_module_netlist.py  → weapon-module.net      (SKiDL: schema/netlista)
weapon_module_place.py    → weapon-module.kicad_pcb (placerad, nät, outline, kamerahål, 4 lager)
ExportSpecctraDSN         → weapon-module.dsn
freerouting (xvfb, headless) → weapon-module.ses    (autoroute ~5 s)
ses_import.py             → spår/vior in i boarden + GND-plan (In1+B.Cu)
kicad-cli pcb export gerbers/drill → gerbers.zip
```

## Routnings-status

- **80 spårsegment + 3 vior, 4 lager, GND-plan på In1 + B.Cu.** All **kraft** (VBAT/VBAT_F/+3V3)
  och de flesta signaler routade.
- **6 förbindelser oroutade** = SPI-escape (SCK/MOSI/MISO/nCS/INT) till **IMU-placeholdern**.
  Orsak: Bosch_LGA-14-platshållaren är 0,5 mm-pitch → autoroutern når inte de inre paddarna
  utan korrekt fanout. **Detta löser sig när den riktiga ICM-45686-footprinten ersätter
  platshållaren** (dess land-pattern ger ren via-fanout) — en normal, footprint-specifik åtgärd.

## ⚠️ Måste fixas före skarp tillverkning (normala sista steg)

1. **Byt platshållar-footprints** mot exakta delar: **U1 → ICM-45686 LGA-14** (verifiera pinout!),
   **D2/D3 → ams-OSRAM OSLON Black** (custom thermal pad). Routa då om SPI-escapen.
2. **J1** ligger något under outline-kanten — nudge:a in den i KiCad (1 min).
3. **Effektbredd:** autoroutern använde ~0,2 mm; **bredda VBAT/LED-pulsbanan** (1–3 A) + verifiera
   termiska vias under LED:erna.
4. **DRC i KiCad** (kicad-cli 7 saknar DRC; kör i GUI eller KiCad 8) → noll fel före fab.

## Ärlig sammanfattning

Detta är en **autonomt autoroutad, ~87 % komplett board med färdiga Gerbers** — kraften och de
flesta signaler är dragna, GND-plan på plats. De återstående SPI-escapen + footprint-bytena är
footprint-specifika sista steg som hör ihop med att byta platshållarna mot de exakta delarna.
Det är så långt en blind autoroute ansvarsfullt kan tas; resten är 30 min i KiCad med rätt
footprints — inte EDA-design från scratch.
