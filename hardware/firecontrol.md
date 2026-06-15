# STRILAS — Fire-control-kort (vapen)

Litet kort (**71 × 21 mm, samma format som ESP32-P4-WIFI6**, 2-lager) som **stackas rakt
ovanpå P4** och tar dess SIGNALKANT **edge A** via en **FEMALE socket** (P4 bär
male-stiften). Fan-out till greppets I/O via **stående JST-PH** (kabel rakt upp).
Bär även en **extra IMU** (I²C). Optikmodulen (edge B, under P4) förblir ren optik.

## Stack & orientering

```
   FC-kort        (socket ↓ mot P4 edge A, stående JST ↑)
   ───────────  ← genomgående M2-standoff (4 st, P4:ans hål)
   P4 (USB-upp)   (male header edge A ↑ / edge B ↓)
   ───────────
   Optikmodul     (female socket ↑ mot P4 edge B)
   ───────────
   IR + lins + kamera (under)
```

- **P4 orienteras USB-C uppåt** (verifierat: overlay J1↔edge B = 0 felmatchningar).
- FC-frame = P4-frame (lång axel = x). FC ligger rakt ovanför P4 i samma orientering →
  socket-paddarna hamnar i exakt samma (x,y) som P4:ans edge-A-stift (rak stack, ingen
  spegelvändning). **Mate-overlay verifierad: 0 felmatchningar.**
- Edge A saknar kraftskena → **3V3 matas via egen stående JST (J2)** från optikens +3V3-rail.

## J1 — FEMALE socket mot P4 edge A (pin 6–17)

| J1 | P4-pin | GPIO | Funktion |
|---|---|---|---|
| 1 | 6 | GPIO29 | MAGWELL (magasin-närvaro) |
| 2 | 7 | GPIO28 | RECOIL_FAULT (eFuse fault-in) |
| 3 | 8 | GND | |
| 4 | 9 | GPIO50 | **IMU2_INT** (extra IMU) |
| 5 | 10 | GPIO49 | reserv (NC) |
| 6 | 11 | GPIO5 | RACK |
| 7 | 12 | GPIO4 | TRIG |
| 8 | 13 | GND | |
| 9 | 14 | GPIO3 | MAG_REL |
| 10 | 15 | GPIO2 | RECOIL_PWM (→ eFuse EN/gate) |
| 11 | 16 | GPIO8 | NFC_SCL (I²C) |
| 12 | 17 | GPIO7 | NFC_SDA (I²C) |

## Komponenter

| Ref | Typ | Funktion |
|---|---|---|
| J1 | PinSocket 1×12 (female) | mot P4 edge A |
| J2 | JST-PH B2B vertikal 2-pin | 3V3-mata från optikens rail |
| J3–J6 | JST-PH B2B vertikal 2-pin | trigger / rack / mag-release / magwell (interna pull-ups) |
| J7 | JST-PH B3B vertikal 3-pin | recoil-effektkort (PWM/FAULT/GND) |
| J8 | JST-PH B4B vertikal 4-pin | NFC PN532 (SDA/SCL/3V3/GND) |
| U1 | TDK ICM-45686 (LGA-14) | **extra IMU på I²C** (delar NFC-bussen, adr 0x69, INT=GPIO50) |
| R1/R2 | 4k7 | I²C-pullups |
| C1/C2 | 100nF / 1µF | 3V3-rail/NFC-avkoppling |
| C3/C4 | 100nF | IMU VDD/VDDIO-avkoppling |
| H1–H4 | M2 | i linje med P4-standoffsen → genomgående stack |

> Extra IMU: CS hög → I²C-läge, SDO/AD0 hög → adress 0x69 (skild från PN532). Delar
> SDA/SCL (GPIO7/8) med NFC; egen INT på GPIO50 (tidigare reservstift).

## Bygg / reproduktion

```
python3 hardware/firecontrol_netlist.py          # SKiDL → firecontrol.net
python3 hardware/receiver_place.py firecontrol   # placering + outline (71×21)
# DSN → freerouting → ses_apply → GND-pour → gerbers/STEP
python3 hardware/render_firecontrol.py
```

Routning verifierad **ren**: 0 oroutade (inkl. GND-plan), 0 clearance @0,2 mm.
Mate mot P4 edge A verifierad: **0 felmatchningar**.
