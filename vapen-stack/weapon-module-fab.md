# STRILAS — Vapen-optikmodul: tillverkningspaket (PCB 1)

Komplett elektrisk design för vapen-modulen, genererad i kod
([`weapon_module_netlist.py`](weapon_module_netlist.py) → [`weapon-module.net`](weapon-module.net),
KiCad-format). Kortet är **färdigroutat** (4-lager) med Gerbers — se status nedan.

> **Driver-val (v1):** enkel + ögonsäker — effektresistor **R2 (Rset)** sätter ett **hårt
> strömtak**, N-FET **Q1** gatar 56 kHz. (Buck-CC = effektivitetsuppgradering, design-resolution §2.)
> **Sikteskameran (USB OV9281 GS NoIR) är MEKANISK** bakom kortet (lins genom Ø16-hålet),
> ansluts till P4 via **USB-kabel** → ingen kamera-elektrik på detta kort.

## BOM (24 komponenter, riktiga footprints — inga platshållare)

| Ref | Värde / del | Footprint | Roll |
|---|---|---|---|
| J1 | **P4-carrier-header (2×6)** — VSYS·3V3·GND·IR_MOD·SCK·MOSI·MISO·nCS·INT | PinHeader_2x06 | **P4-anslutning** (kort kabel till P4:ans GPIO) |
| J2 | 2S batteri-in | PinHeader_1x02 | matar VSYS + emitter-rail |
| F1 | PTC ~1 A | Fuse_1206 | inskydd (över-ström) |
| Q2 | AO3401 (P-FET) | SOT-23 | reverse-polarity-skydd |
| R1 | 100 k | R_0805 | Q2 gate-pulldown |
| D1 | SMBJ12A | D_SMB | TVS-clamp på VBAT |
| C1 | 10 µF | C_1206 | ingångskondensator |
| C2 | 100 µF | C_1210 (MLCC) | reservoar för IR-pulsen (låg-ESR @56 kHz) |
| R2 | 3R3 2 W | R_2512 | **Rset — sätter hårt strömtak (ögonsäkerhet)** |
| D2, D3 | **Vishay VSMA1094750X02 (940 nm)** | `strilas:IR_Emitter_Vishay_VSMA1094750` | 2× IR-skott-emitter i serie (1,5 A DC / 5 A puls) |
| Q1 | AO3400 (N-FET) | SOT-23 | 56 kHz-gate |
| R3 | 220 Ω | R_0805 | gate-resistor |
| U1 | **TDK ICM-45686** | `strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx` | IMU (SPI 4-wire) |
| C3, C4 | 100 nF | C_0402 | IMU-avkoppling |
| C5 | 1 µF | C_0805 | 3V3-bulk |
| H1–H3 | M2.5 | MountingHole_2.5mm | kort-montering (till GND) |
| **H8–H15** | Ø3,2 | MountingHole_3.2mm | **kollimatorfäste — Carclo 60475 4-bens-hållare**, 4 hål/lins, 9,5×16,45 mm-rektangel (R2,4 ben-clearance) |
| **H4–H7** | **M2** | MountingHole_2.2mm_M2 | **kamerafäste — Arducam B0332 28×28-mönster**; **6 mm M2-standoff** (DigiKey 9488532) → kamera bakom, lins genom Ø16 |

Footprints för D2/D3 och U1 ligger i [`strilas.pretty/`](strilas.pretty/) och är ritade mot
datablad (Vishay DocNo 80365; TDK AN-000483 Fig. 2). **Standard DFM:** verifiera padstacken mot
den köpta delens datablad innan beställning.

> **Våglängd:** skottstrålen är **940 nm** (TSOP-topp + kamerans 860 nm-bandpass avvisar egen
> stråle → ingen självbländning). Vishay VSMA1094750X02 = äkta 940 nm (945 nm topp). *(Tidigare
> dokument angav felaktigt "SFH 4715AS 940 nm" — OSLON "AS" är 850/860 nm; rättat här.)*

> **Kamerafäste:** kameran (Arducam B0332, 38×38 mm, OV9281 USB) skruvas fast **bakom** kortet
> via **H4–H7 (M2, 28×28 mm)** — matchar B0332:s hålbild; linsen går genom Ø16-hålet. (B0332 stödjer
> 28×28 och 34×34; vi använder 28×28 = mest inåt, fritt från komponenter.)
> **P4-anslutning:** **J1 (2×6)** för en kort kabel till ESP32-P4-WIFI6:ans GPIO (P4-kortet 71×21 mm
> monteras i vapenkroppen — det får inte plats bakom kortet där kameran sitter). Se routed-doc.

## Nät (konnektivitet — verifierad)

```
VBAT_IN : F1.1 J1.1                    (batteri in)
VBAT_F  : F1.2 Q1.3                    (efter säkring → reverse-FET drain)
VBAT    : C1 C2 D1(TVS) Q2.S R2(Rset)  (skyddad rail; Q2 = reverse-P-FET)
R2→D2→D3→Q1.D (LED-sträng) ; Q1.S→GND ; Q1.G←R3←IR_MOD   (driver + 56 kHz-gate, Q1 = N-FET)
SPI     : SCK(13)/MOSI(14)/MISO(1)/nCS(12)/INT1(4)  ↔  U1(ICM-45686)  ↔  J1
+3V3    : U1.VDD(8)/VDDIO(5) + C3/C4/C5 + J1.2
GND     : U1.GND(6) + allt retur + monteringshål   (IMU RESV 2,3,7,9,10,11 = NC per datablad)
```

## Stackup & designregler (4-lager)

- **4 lager:** Sig / GND / VBAT-pour / Sig. Solid GND-plan; separat effekt-pour för pulsströmmen.
- **Pulslooped** (C2 → R2 → LED → Q1 → GND) **kort & bred**; MLCC nära LED:erna.
- **Termiska vias** under LED-paddarna till baksidans koppar (pulsad effekt).
- **EMI:** håll IR-driverns switchande nod borta från IMU-SPI-spåren.
- DRC: 6/6 mil spår/gap (JLCPCB std), via 0.3/0.6 mm.
- Kort **52×80 mm** (stackad box: P4 bakom); placering enligt [`weapon_emitter_layout.py`](weapon_emitter_layout.py)
  (kamera i mitten, 2 emittrar ovan, IMU + driver i sidoremsorna, J1 nedtill).

## Status: FÄRDIGROUTAD — Gerbers klara

Hela kedjan (placering → routning → kopparplan → Gerbers) kördes autonomt i container; se `../hardware/build_weapon.sh` för stegen och egenkontrollen.
**35 komponenter, 166 spår + 22 vior, 0 oroutade, 0 clearance-brott @ 0,2 mm.** Färdiga filer:

- **`weapon-module-gerbers.zip`** → ladda upp direkt till JLCPCB/PCBWay (4-lager, 1,6 mm).
- **`weapon-module.kicad_pcb`** → öppna i KiCad för granskning / GUI-DRC.

> **DRC-not:** clearance/connectivity är kontrollerade geometriskt i container (kicad-cli 7
> saknar `pcb drc`). Öppna gärna i KiCad 8 GUI för en formell DRC-stämpel — inga fel väntas.

## Två kvarvarande fysik-steg (kräver den fysiska delen — normalt)

1. **Verifiera footprint-padstacken** mot den köpta delens datablad innan beställning (standard DFM).
2. **Bänkmät ögonsäkerhet (Class 1 / AE)** per IEC 60825-1 vid driftströmmen — R2/Rset är vakten.
