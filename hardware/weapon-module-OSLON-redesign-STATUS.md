# STRILAS vapen-modul — OSLON-version: ✅ LÅST & VERIFIERAD

**54×68 mm, 4-lager. 0 oroutade, 0 clearance-brott @0,2 mm, annular OK.**

## Låst hårdvara
- **Skott-emitter:** 2× OSRAM OSLON Black **SFH 4725S** (940 nm, 980 mW @ 1 A) — STEP fr. ams-osram.
- **Kollimator:** 2× **Carclo 10003** Ø20 mm Narrow Spot TIR (officiellt matchad SFH 4725S) + 20 mm-hållare, 2 ben/lins (H8–H11).
- **Kamera:** Arducam **B0332** (OV9281 mono GS, USB-UVC) bakom kortet, lins genom Ø16; **16 mm M12-lins** (verifierat 150 m); kamerafäste M2 28×28 (H4–H7).
- **IMU:** TDK **ICM-45686** (LGA-14, SPI).
- **P4:** ESP32-P4-WIFI6 via **RIGID 1×13 kantkontakt** (J1) mot P4:ans högra kantrad — ingen flex.
- **Kontakter:** J2 batteri-in, J3 trigger-in (kablar via pipan). Driver = Rset hårt strömtak + N-FET 56 kHz.

## Verifierat (kört i container)
| Kontroll | Resultat |
|---|---|
| Oroutade nät | **0** |
| Koppar-clearance @0,2 mm | **0 brott** |
| Via annular | ✅ ≥0,125 mm |
| Komponentkrockar / utanför / lins | 0 |
| Fysik @150 m (FOV·SNR·bäring·range·IMU·skott·ballistik·träff) | **alla ✅** (Carclo narrow @2 A → 218 m, 100 % torso) |
| Firmware-tester | **15/15 ✅** |

## Kvarvarande fysik-steg (kräver fysisk del — normalt)
1. Verifiera footprint-padstack mot köpt dels datablad (DFM).
2. Bänkmät Class 1 / AE per IEC 60825-1 vid driftström (R2/Rset = vakten).
