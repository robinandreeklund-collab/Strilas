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

- **P4 orienteras USB-C uppåt.**
- **KANTBYTE (2026-06):** mot den RIKTIGA P4-modellen (Fusion) hamnade J1 fel — den dockade
  edge B i stället för edge A. FC-kortet är därför **speglat om långaxeln (y=120)** så att
  J1 (→ edge A) och J2 (3V3-tapp → edge B) byter långsida och dockar rätt (bekräftat i CAD:
  optik→P4→FC monteras korrekt). Speglingen behåller hålbilden (symmetrisk) → samma genomgående
  M2-standoff. **Pin-ORDNINGEN är OFÖRÄNDRAD (original):** FC J1 (B.Cu) möter edge A på P4:ans
  F.Cu = MOTSATT lager, så speglingen + ansikts-flippen tar ut varandra → fysisk J1.k möter
  edge A pin (k+5). Verifierat mot riktig P4-geometri + kalibrerat mot optik↔edge B = 8/8.
- Edge A saknar kraftskena → **3V3 matas via edge-B kraft-tapp (J2)** direkt från P4 edge B.

## J1 — FEMALE socket mot P4 edge A (pin 6–20, 15-pin)

| J1 | P4-pin | GPIO | Funktion |
|---|---|---|---|
| 1 | 6 | GPIO29 | MAGWELL (magasin-närvaro) |
| 2 | 7 | GPIO28 | RECOIL_FAULT (eFuse fault-in) |
| 3 | 8 | GND | |
| 4 | 9 | GPIO50 | **IMU_INT** (IMU U1, 0x69) |
| 5 | 10 | GPIO49 | **IMU_INT** (IMU U2, 0x68) |
| 6 | 11 | GPIO5 | RACK |
| 7 | 12 | GPIO4 | TRIG |
| 8 | 13 | GND | |
| 9 | 14 | GPIO3 | MAG_REL |
| 10 | 15 | GPIO2 | RECOIL_PWM (→ eFuse EN/gate) |
| 11 | 16 | GPIO8 | NFC_SCL (I²C) |
| 12 | 17 | GPIO7 | NFC_SDA (I²C) |
| 13 | 18 | GND | |
| 14 | 19 | GPIO24 | MODE_A (lägesväljare bit 0) |
| 15 | 20 | GPIO25 | MODE_B (lägesväljare bit 1) |

## Komponenter

| Ref | Typ | Funktion |
|---|---|---|
| J1 | PinSocket 1×15 (female) | mot P4 edge A (pin 6–20) |
| J2 | PinSocket 1×3 (female) | edge-B kraft-tapp (3V3+GND direkt från P4) |
| J3–J6 | JST-PH B2B vertikal 2-pin | trigger / rack / mag-release / magwell (interna pull-ups) |
| J7 | JST-PH B3B vertikal 3-pin | recoil-effektkort (PWM/FAULT/GND) |
| J8 | JST-PH B4B vertikal 4-pin | NFC PN532 (SDA/SCL/3V3/GND) |
| J9 | JST-PH B4B vertikal 4-pin | **OLED SSD1306 I²C** (GND/3V3/SCL/SDA) |
| J10 | JST-PH B3B vertikal 3-pin | **4-läges rotarykopplare** (MODE_A/MODE_B/GND) |
| U1 | TDK IIM-42653 (LGA-14) | **extra IMU #1**, I²C 0x69 (AD0 hög), INT=GPIO50 |
| U2 | TDK IIM-42653 (LGA-14) | **extra IMU #2**, I²C 0x68 (AD0 låg), INT=GPIO49 |
| R1/R2 | 4k7 | I²C-pullups (delas av NFC + båda IMU + OLED) |
| R3/R4 | 4k7 | MODE_A / MODE_B pull-ups (pull-up till 3V3, switch drar till GND) |
| C1/C2 | 100nF / 1µF | 3V3-rail/NFC-avkoppling |
| C3/C4 | 100nF | U1 VDD/VDDIO-avkoppling |
| C5/C6 | 100nF | U2 VDD/VDDIO-avkoppling |
| H1–H4 | M2 | i linje med P4-standoffsen → genomgående stack |

> **4-läges rotarykopplare (MODE_A/MODE_B):**
> Switch common=GND, utgång A → MODE_A, utgång B → MODE_B.
> Pull-ups R3/R4 (4k7) håller linjerna höga när switch-positionen är öppen.
> | Läge | MODE_A | MODE_B | Binärkod |
> |------|--------|--------|----------|
> | Safe | H | H | 00 |
> | Single | L | H | 01 |
> | Burst | H | L | 10 |
> | Auto | L | L | 11 |

> **OLED I²C (J9):** SSD1306 adress 0x3C → ingen krock med NFC (0x24/0x48), IMU (0x68/0x69).
> Delar SDA/SCL (GPIO7/8) med NFC + båda IMU:er. Pinout JST: GND / 3V3 / SCL / SDA.

> **2 IMU på delad I²C-buss** (max på en buss — ICM-45686 har bara adress 0x68/0x69).
> Båda: CS hög → I²C-läge; SDO/AD0 sätter adress. Delar SDA/SCL (GPIO7/8) med NFC
> (PN532 = 0x24/0x48) och OLED (0x3C) — ingen adresskrock; egna INT på GPIO50 resp GPIO49.

## Bygg / reproduktion

```
python3 hardware/firecontrol_netlist.py          # SKiDL → firecontrol.net
python3 hardware/receiver_place.py firecontrol   # placering + outline (71×21, PRE-MIRROR)
python3 hardware/firecontrol_flip.py             # J1/J2 → B.Cu (face down mot P4)
python3 hardware/fc_add_ports_v2.py              # speglar + lägger till J9/J10/R3/R4 (KÖRS EJ vid ny plac.)
# DSN → freerouting → ses_apply → GND-pour → gerbers/STEP
python3 hardware/route_firecontrol.py
python3 hardware/fc_route_fixup.py               # VID BEHOV: kopplar U2.1 om maze stängt in den (annars no-op)
```

> **U2.1-fixen (fc_route_fixup.py) — villkorlig:** U2 (IIM-42653, LGA-14) har AD0/SDO = GND (pin 1)
> inne i fotavtrycket. freerouting kör med GND uteslutet (maze-routas separat). Med nuvarande
> placering (J9/J10 borta från U2) når maze U2.1 direkt → skriptet blir en no-op. MEN routning är
> icke-deterministisk; skulle en seed stänga in U2.1 (verify: 1 oroutad GND, ingen via-plats mellan
> +3V3/NFC_SCL i LGA-pitchen 0,5 mm) tar skriptet bort +3V3-väggen söder om paddan, drar en egen
> GND-flykt (F.Cu→via→B.Cu) och routar om C5:s +3V3 med DRC-min keepout (`MAZE_KEEP=0.30`).

> **Placering (trångt 71×21-kort):** överkanten (y114) full → J9 (OLED, 4-pin) i nedre högra hörnet,
> J10 (lägesväljare, 3-pin) i luckan J6→H4 (J3–J6 skjutna 1 mm vänster), R3/R4 i cap-radens luckor.
> 0 courtyard-krock verifierat.

Routning verifierad **ren**: 0 oroutade (inkl. GND-plan), 0 clearance @0,2 mm, 0 courtyard-krock.
Mate mot P4 edge A verifierad: **0 felmatchningar** (15/15 paddar).
