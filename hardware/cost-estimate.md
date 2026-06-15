# STRILAS — PCB-kostnadsuppskattning (prototyp)

> Grova 2026-priser (JLCPCB/PCBWay-klass, frakt till EU). Varierar med fab/region/datum.
> Tre delar: **bart kort** (billigt) · **komponenter** (mellan) · **montering** (störst för fin-pitch).

## 1. Bart kort (fab, 5 st = minsta order)

| Kort | Storlek | Lager | ~Pris/5 st |
|---|---|---|---|
| Vapen-optikmodul | 42×62 mm | **4** | $20–40 |
| Väst-detektor-patch | 58×42 mm | 2 | $2–5 |
| Hjälm-halo | Ø100 mm | 2 | $10–20 |
| Frakt (EU) | — | — | ~$20 |

**Bara korten (alla tre, 5 st var + frakt): ~$50–85.** Själva kortet är alltså *billigt* —
4-lagret + frakten dominerar.

## 2. Komponenter (per monterat kort)

| Kort | Delar (utöver P4-kit/kamera) | ~Pris |
|---|---|---|
| **Vapen-modul** | 2× 940 nm-LED $4 · 2× Carclo 10195 $6 · ICM-45686 $8 · buck-CC + L1 + caps + FET + diod + skydd $12 · kontakter $4 · passiva $3 | **~$37** |
| **Väst-patch** | 3× TSOP4856 $3 · 2× IR-LED $1 · OR-dioder/driver $1 · 940 nm-filter ×3 $6 · kontakt+passiva $2 | **~$13** |
| **Hjälm-halo** | 8× TSOP $8 · 4× IR-LED $2 · GNSS-patch-antenn $8 · 940 nm-filter ×8 $16 · kontakt+passiva $3 | **~$37** |

*(GNSS-mottagaren ZED-X20 (~$280) sitter på väst-noden, ej på halon, och är full-system — ej v1.)*

## 3. Montering — här är den verkliga frågan

- **Hand-lödning (din tid = gratis):** TSOP, LED, kontakter går fint för hand. **Men**
  ICM-45686 (LGA), buck-driver-IC (QFN) och kamera-FFC är **fin-pitch** → svårt utan
  hetluft/stencil.
- **Fab-montering (JLCPCB SMT):** ~$8 setup + deras delar + ~per-joint → **+$30–60/kort**
  vid små serier. Rekommenderas för IMU + driver.

## 4. Realistiska totaler

| Scenario | Kostnad |
|---|---|
| **v1 skjut-test** (vapen-modul + 1 väst-patch, hand-lödd) | **~$95–150** |
| Full sats (vapen + väst + halo), hand-lödd | ~$130–190 |
| Samma, med fab-montering av fin-pitch | +$50–120 |

*(Utöver de 2× ESP32-P4-WIFI6-kit ~$64 du redan räknat.)*

## Ärliga noter

- **Korten är inte dyra** — fin-pitch-**monteringen** (IMU/driver/kamera) är det som kostar tid/pengar.
- **Frakt dominerar** små order → beställ alla kort i en order.
- **Volym:** vid 16–32 spelare faller kort-pris till ~$1–3/st och montering amorteras; **komponenterna** står still.
- **Full per-spelare-system** (vapen + väst + hjälm + magasin + batteri + ev. GNSS/rekyl/HUD) är en
  större siffra — storleksordning **$200–500/spelare** beroende på tillval. Men *att göra själva
  PCB:n* är den billiga biten.
