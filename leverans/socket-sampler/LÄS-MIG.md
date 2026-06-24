# STRILAS — 2.54 HONA-SOCKEL-SAMPLER (DEMO · EJ FÖR TILLVERKNING)

Sista kontakt-kategorin som ännu handlöds: **2.54 mm hona-socklar** (P4-WIFI6 edge-socklar,
kraft-tapp, XIAO/breakout). I kontakt-samplern kom Sullins-MPN tillbaka **Pending** (ej i NextPCB:s
auto-matchnings­bibliotek). Detta kort bär **samma footprints i flera märken** (Ckmtw / Sullins /
Samtec) i de pinantal korten använder → hitta en **auto-matchad In-Stock-hona**, så kan NextPCB
montera även P4-socklarna (då slipper vi handlöda dem).

> **Kortet beställs / tillverkas ALDRIG.** Bara lager-/monteringskoll.

## Filer
`socket-sampler-bom.xls` (11 rader — **filen att ladda upp**) · `socket-sampler-gerbers.zip` ·
`socket-sampler-centroid.csv`. Källa: `hardware/socket_sampler.py`.

## Pinantal som faktiskt sitter på korten
| Footprint | Kort | Antal |
|---|---|---|
| PinSocket_1x03 | firecontrol (kraft-tapp) | 1 |
| PinSocket_1x07 | XIAO/breakout-socklar | 2 |
| PinSocket_1x14 | optik (P4 edge A) | 1 |
| PinSocket_1x15 | firecontrol (P4 edge) | 1 |
| PinSocket_1x20 | helmet-mb + vest-mb (P4-WIFI6 edge A/B) | 4 |

## Kandidater
| Ref | Pinn | MPN | Märke | Roll |
|---|---|---|---|---|
| J1 | 1x3 | DS1023-1x3SF11 | Ckmtw | kinesisk basic-lib |
| J2 | 1x3 | PPTC031LFBN-RC | Sullins | kontroll (var Pending) |
| J3 | 1x7 | DS1023-1x7SF11 | Ckmtw | |
| J4 | 1x7 | PPTC071LFBN-RC | Sullins | kontroll |
| J5 | 1x14 | DS1023-1x14SF11 | Ckmtw | |
| J6 | 1x14 | PPTC141LFBN-RC | Sullins | kontroll |
| J7 | 1x15 | DS1023-1x15SF11 | Ckmtw | |
| J8 | 1x15 | PPTC151LFBN-RC | Sullins | kontroll |
| J9 | 1x20 | DS1023-1x20SF11 | Ckmtw | P4-WIFI6 (mest använd) |
| J10 | 1x20 | PPTC201LFBN-RC | Sullins | kontroll |
| J11 | 1x20 | SSW-120-01-T-S | Samtec | premium-referens |

## LAGER-KOLL RESULTAT (NextPCB, 10/11) + valt MPN

| Pinn | **Ckmtw DS1023** | Sullins | Samtec |
|---|---|---|---|
| 1x3 | ✅ 4–7 d, $0.042 | 7–18 d, $0.46 | — |
| 1x7 | ✅ 4–6 d, $0.072 | 7–18 d, $0.71 | — |
| 1x14 | ✅ 4–6 d, $0.136 | 7–18 d, $1.17 | — |
| 1x15 | ⚠️ Pending | 7–18 d, $1.24 | — |
| 1x20 | ✅ 4–7 d, $0.205 | 7–18 d, $1.55 | 7–18 d, $3.23 |

**Valt: Ckmtw DS1023-serien** — matchad, 4–7 d lead (i linje med övriga BOM), **5–10× billigare**
än Sullins. Sullins (kontroll) matchade nu men dyr/långsam → det var *märket* som saknades i auto-lib,
inte footprinten. Enda luckan: **1x15 = Pending** (mindre vanlig längd; bara firecontrol J1) →
manuell offert (1 dag), Sullins PPTC151LFBN-RC som backup.

## GENOMFÖRT
`gen_nextpcb.py` uppdaterad: placeholder-MPN → Ckmtw DS1023 per storlek (1x3/1x7/1x14/1x15/1x20),
och **`PinSocket` tillagt i `MOUNT_NEEDLES`** → 2.54-hona-socklarna maskin-monteras nu också:

| Kort | Hona-sockel | MPN |
|---|---|---|
| optik | J1 1x14 (P4 edge B) | DS1023-1X14SF11 |
| firecontrol | J1 1x15 (P4 edge A) + J2 1x3 (kraft-tapp) | DS1023-1X15SF11 / -1X3SF11 |
| helmet-mb | J8/J9 1x20 (P4-WIFI6) | DS1023-1X20SF11 |
| vest-mb | J11/J12 1x20 (P4-WIFI6) | DS1023-1X20SF11 |

Alla BOM/centroid regenererade + kopierade till `leverans/` (socklar nu i centroid, Procurement
Type tom = monteras). **Ingen omroutning** (footprint oförändrad). Undantag: optik-PROTOTYP-varianten
behåller J1 handlödd (J1 utesluten ur mount där → BOM=DNP + ej i centroid, konsekvent). Hane-
breakout-headers (1x6/1x7 amp/mik) ej sämplade → fortsatt handlödda.
