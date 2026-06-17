# STRILAS — leverans (komplett underlag per kort)

Allt samlat på ett ställe per kort: **gerbers + BOM + centroid + STEP (3D)**.
Genererat från exakt routade kort (alla 0 oanslutna / 0 clearance / 0 courtyard-krock,
system-sim 28/28 PASS). Full rapport: [`FORSTA-BATCH.md`](FORSTA-BATCH.md).

| Mapp | Kort | Storlek | Lager | Monteringshål |
|---|---|---|---|---|
| `optik/` | Vapen-optikmodul | 54×74 mm | 4 | 4 + 4 P4-standoff |
| `firecontrol/` | Fire-control (stack på P4) | 71×21 mm | 2 | 4 |
| `vest-patch/` | Väst-/hjälm-patch (×14) | 44×44 mm | 2 | 4 |
| `helmet-mb/` | Hjälm-moderkort (rund) | Ø97 mm | 4 | 4 |
| `vest-mb/` | Väst-moderkort | 100×60 mm | 4 | 4 |
| `led-tab/` | Konstellations-LED på 90°-vinklad micro-PCB (right-angle fot) (6/hjälm) | 6×11 mm | 2 | — |

Per mapp:
- `<kort>-gerbers.zip` — RS-274X gerber + Excellon-borr (det NextPCB tillverkar från).
- `<kort>-bom.xls` — BOM (8-kol NextPCB-mall). TH-kontakter = DNP (kund-löds).
- `<kort>-centroid.csv` / `.xls` — pick-and-place (SMT-placeringar; TH/monteringshål uteslutna).
- `<kort>.step` — 3D-modell (mekanik/passform, ej för tillverkning).

`optik/` innehåller även **PROTOTYP-varianten** (`optik-PROTOTYP-*`): samma kort men IMU obestyckad
(körs på breakout) för första provskjutningen.

> FR-4 1,6 mm, HASL/ENIG. ESP32-P4-WIFI6, ZED-F9P-puck, OV9281+860 nm-filter, amp/mik, vibratorer,
> batterier, TSOP4856 + ams OSRAM OSLON-emitter/LED köps separat (se BOM-noter + FORSTA-BATCH.md).
>
> **OSLON-LED:erna SMT-placeras av NextPCB** (precision, t.ex. emittern under linsen); de ledade
> **TSOP4856 monteras/böjs av kund** (ej i centroid). **Optik-linser (Carclo TIR-kollimator) + hållare
> köps separat och monteras manuellt** över emittrarna. OBS: 940 nm-emittern **SFH 4725S är utgående/EOL**
> men lagerförs ännu — verifiera aktuell 940 nm OSLON-ersättare inför produktion. 860 nm SFH 4715AS = aktiv.
