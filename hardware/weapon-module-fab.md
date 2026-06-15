# STRILAS — Vapen-optikmodul: tillverkningspaket (PCB 1)

Komplett elektrisk design för vapen-modulen, genererad i kod
([`weapon_module_netlist.py`](weapon_module_netlist.py) → [`weapon-module.net`](weapon-module.net),
KiCad-format). Detta är allt en fab behöver **fram till routing**. Sista steget
(routing → Gerbers) görs i KiCad — steg nedan.

> **Driver-val (v1):** enkel + ögonsäker — effektresistor **R2 (Rset)** sätter ett **hårt
> strömtak**, N-FET **Q2** gatar 56 kHz. (Buck-CC = effektivitetsuppgradering, design-resolution §2.)
> **Kameran (OV5647) är MEKANISK** i mitten; dess FFC går direkt till P4 → ingen elektrik här.

## BOM (19 komponenter, riktiga footprints)

| Ref | Värde | Footprint | Roll |
|---|---|---|---|
| J1 | 2×5 2.54 mm | PinHeader_2x05 | → P4: VBAT·GND·IR_MOD·3V3·GND / SCK·MOSI·MISO·nCS·INT |
| F1 | PTC ~1 A | Fuse_1206 | inskydd (över-ström) |
| Q1 | AO3401 (P-FET) | SOT-23 | reverse-polarity-skydd |
| R1 | 100 k | R_0805 | Q1 gate-pulldown |
| D1 | SMBJ12A | D_SMB | TVS-clamp på VBAT |
| C1 | 10 µF | C_1206 | ingångskondensator |
| C2 | 220 µF | CP_Elec_6.3×7.7 | reservoar för IR-pulsen |
| R2 | 3R3 2 W | R_2512 | **Rset — sätter hårt strömtak (ögonsäkerhet)** |
| D2, D3 | SFH 4715AS (940 nm) | LED_3.2×2.8 mm* | 2× IR-emitter i serie |
| Q2 | AO3400 (N-FET) | SOT-23 | 56 kHz-gate |
| R3 | 220 Ω | R_0805 | gate-resistor |
| U1 | ICM-45686 | InvenSense_LGA-14_2.5×3 mm* | IMU (SPI) |
| C3, C4 | 100 nF | C_0402 | IMU-avkoppling |
| C5 | 1 µF | C_0805 | 3V3-bulk |
| H1–H3 | M2.5 | MountingHole | montering (till GND) |

\* *Verifiera/byt footprint mot exakt del: ams-OSRAM OSLON Black (custom-pad) resp. ICM-45686 LGA-14.*

## Nät (konnektivitet — verifierad)

```
VBAT_IN : F1.1 J1.1                    (batteri in)
VBAT_F  : F1.2 Q1.3                    (efter säkring → reverse-FET drain)
VBAT    : C1 C2 D1(TVS) Q1.S R2(Rset)  (skyddad rail)
R2→D2→D3→Q2.D (LED-sträng) ; Q2.S→GND ; Q2.G←R3←IR_MOD   (driver + 56 kHz-gate)
SPI     : SCK/MOSI/MISO/nCS/INT  ↔  U1(ICM-45686)  ↔  J1
+3V3    : U1.VDD/VDDIO + C3/C4/C5 + J1.4
GND     : allt retur + monteringshål
```

## Stackup & designregler (4-lager)

- **4 lager:** Sig / GND / VBAT-pour / Sig. Solid GND-plan; separat effekt-pour för pulsströmmen.
- **Pulslooped** (C2 → R2 → LED → Q2 → GND) **kort & bred**; MLCC nära LED:erna.
- **Termiska vias** under LED-paddarna till baksidans koppar (pulsad effekt).
- **EMI:** håll IR-driverns switchande nod borta från IMU-SPI-spåren.
- DRC: 6/6 mil spår/gap (JLCPCB std), via 0.3/0.6 mm.
- Kort **Ø42×62 mm**; placering enligt [`weapon_emitter_layout.py`](weapon_emitter_layout.py)
  (kamera i mitten, 2 emittrar ovan, IMU + driver i sidoremsorna, J1 nedtill).

## Från netlista → Gerbers (KiCad-steg)

1. **KiCad → Schematic:** `Import Netlist` av `weapon-module.net` *(eller* `kinet2pcb weapon-module.net`
   *för att gå direkt till en .kicad_pcb).*
2. **Tilldela/verifiera footprints** (de flesta satta; verifiera OSLON + ICM-45686-padstacken mot datablad).
3. **Verifiera IC-pinnar** mot datablad (ICM-45686 LGA-14-pinout) — enda osäkra punkten.
4. **Placera** enligt §-layouten ovan; importera kort-outline 42×62 + kamerahål/standoffs.
5. **Routa 4-lager** (effekt brett, SPI matchat-kort, GND-plan helt).
6. **DRC** → noll fel.
7. **Plot Gerbers + drill**; generera **BOM + CPL (centroid)** för JLCPCB SMT.

## Ärlig statusrad

Detta är den **kompletta elektriska designen** (schema/netlista/BOM/footprints/stackup/DRC) —
allt fram till routing. **Routing → Gerbers kräver KiCad på en maskin** (kan inte autoroutas
korrekt i text för ett 4-lagers blandat effekt/analog-kort). Netlistan importeras direkt; sedan
är det placering + routing + DRC + plot. Verifiera ICM-45686-pinout mot datablad innan layout.
