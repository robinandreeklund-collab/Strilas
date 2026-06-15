# STRILAS — Fire-control-kort (vapen)

Litet breakout-kort (50 × 42 mm, 2-lager) som matar **ESP32-P4-WIFI6:s signalkant
"edge A" (vänsterkanten) STELT** — speglar hur optikmodulen matar edge B. Det fanar
ut vapnets fire-control-I/O till greppet via JST-PH-kontakter. Optikmodulen
(pip-monterad: IR + IMU + kamera + P4-sync på edge B) förblir **ren optik**.

## Varför ett eget kort

Optikmodulen sitter i pipan och dess J1 (edge B, 1×14) är full. Vapnets
fire-control-I/O (avtryckare, rack, mag-release, magasin-NFC, recoil-styrning)
ligger på P4:ans **andra** kant (edge A) och hör fysiskt hemma vid greppet/lådan,
inte vid pipan. Recoil-**effekt** (TPS25983 eFuse + cap-bank + aktuator, matad av
magasinets LiPo) ligger på ett **separat recoil-effektkort** vid magasinet — hit
går bara logik-signaler. Recoil-**känning** (mynningsklättring) görs av IMU:n på
optikmodulen.

## Edge-A pinout (verifierad mot Waveshares OFFICIELLA pinout-diagram)

ESP32-P4-WIFI6 (Pico-format) edge A, topp→botten:

```
GPIO52 GPIO51 GND GPIO31 GPIO30 GPIO29 GPIO28 GND GPIO50 GPIO49
GPIO5  GPIO4  GND GPIO3  GPIO2  SCL/GPIO8 SDA/GPIO7 GND DM/GPIO24 DP/GPIO25
```

- GPIO24/25 = USB D-/D+ → **undviks**.
- Default-I²C = **SCL/GPIO8 + SDA/GPIO7** → används direkt för NFC.
- Edge A har **GND men ingen kraftskena** (VBUS/VSYS/3V3 ligger på edge B) → NFC-läsaren
  matas via separat **3V3-mata (J2)** från optikkortet/P4 edge B.

## J1 — stel kantkontakt mot edge A (1×12, sammanhängande pos 6–17)

| FC-stift | edge A-pos | P4-pin | Nät | Funktion |
|---|---|---|---|---|
| J1.1 | 6 | GPIO29 | MAGWELL | magasin-närvaro (brytare) |
| J1.2 | 7 | GPIO28 | RECOIL_FAULT | eFuse fault-in (open-drain, intern pull-up) |
| J1.3 | 8 | GND | GND | |
| J1.4 | 9 | GPIO50 | — | ledig (NC, Fas 2-hook) |
| J1.5 | 10 | GPIO49 | — | ledig (NC, Fas 2-hook) |
| J1.6 | 11 | GPIO5 | RACK | charging-handle (brytare) |
| J1.7 | 12 | GPIO4 | TRIG | avtryckare (brytare) |
| J1.8 | 13 | GND | GND | |
| J1.9 | 14 | GPIO3 | MAG_REL | mag-release-spak (brytare) |
| J1.10 | 15 | GPIO2 | RECOIL_PWM | recoil-styrning ut (→ eFuse EN/gate) |
| J1.11 | 16 | GPIO8 | NFC_SCL | I²C-klocka |
| J1.12 | 17 | GPIO7 | NFC_SDA | I²C-data |

> Brytarna använder P4:s **interna pull-ups** (inga R behövs). I²C har 4k7-pullups
> (R1/R2) till 3V3 på kortet + 100 nF/1 µF avkoppling (C1/C2).

## Fan-out-kontakter (JST-PH, mot greppets kabelstam)

| Ref | Typ | Stift | Till |
|---|---|---|---|
| J2 | PH 1×02 | 3V3, GND | 3V3-mata från optikkort/P4 edge B |
| J3 | PH 1×02 | TRIG, GND | avtryckar-mikrobrytare |
| J4 | PH 1×02 | RACK, GND | rack/charging-handle-brytare |
| J5 | PH 1×02 | MAG_REL, GND | mag-release-brytare |
| J6 | PH 1×02 | MAGWELL, GND | magasin-närvaro-brytare |
| J7 | PH 1×03 | PWM, FAULT, GND | recoil-**effektkort** (eFuse EN + fault) |
| J8 | PH 1×04 | SDA, SCL, 3V3, GND | NFC-läsare PN532 |

## Bygg / reproduktion

```
python3 hardware/firecontrol_netlist.py     # SKiDL → firecontrol.net
python3 hardware/receiver_place.py firecontrol   # placering + outline
# DSN → freerouting → ses_apply → GND-pour → gerbers/STEP (se historik)
python3 hardware/render_firecontrol.py      # placeringsvy
```

Routning verifierad **ren**: 0 oroutade (inkl. GND-plan), 0 clearance-brott @0,2 mm.
