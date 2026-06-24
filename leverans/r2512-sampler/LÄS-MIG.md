# STRILAS — 10R 2512-SAMPLER (DEMO · EJ FÖR TILLVERKNING)

**Syfte:** hitta en **in-stock 10R 2512-MPN** som ersätter nuvarande Vishay
`CRCW251210R0FKEGHP` (7–18 d lead, ~$0,95/st). 10R är LED-serie-effektmotståndet för
860 nm-konstellationen — **6× på helmet-mb + 6× på vest-mb-patch = 12/kit**, så lead + pris
slår igenom på hela kittet.

> **Kortet beställs / tillverkas ALDRIG.** Bara för att ladda upp BOM:en och se NextPCB-lagret.

## EFFEKT-KRAV (viktigt vid val)
Konstellations-LED: ~**2,5 W topp @0,5 A**, ~50 % duty → ~**1,25 W medel**. Därför:
- **2 W (HP)** = säkert → välj helst en **2W In-Stock**-del.
- **1 W** (vanligaste basic-lib-jellybean) = **marginellt** (1 W < 1,25 W medel) → bara om
  duty hålls lågt, eller använd **2× parallell (20R 1W var)** = 2 W total + halverad ström/del.

## Filer
`r2512-sampler-bom.xls` (11 rader — **filen att ladda upp**) · `r2512-sampler-gerbers.zip` ·
`r2512-sampler-centroid.csv`. Källa: `hardware/r2512_sampler.py`.

## Kandidater (alla 10R, footprint R_2512_6332Metric)
| Ref | MPN | Märke | Effekt | Not |
|---|---|---|---|---|
| **R1** | CRCW251210R0FKEGHP | Vishay | 2W HP 1% | **NUVARANDE** (7–18 d, byts) |
| R2 | CRCW251210R0JNEGHP | Vishay | 2W HP 5% | billigare tolerans, samma effekt |
| R3 | RCV2512100RJNEA | Vishay | 2W 5% | RCV power-serie |
| R4 | PA2512FKF7W10R0L | Yageo | 2W 1% | PA power-serie |
| R5 | ERJ1TRQF10R0U | Panasonic | 2W 1% | anti-surge |
| R6 | CRM2512-FX-10R0ELF | Bourns | 2W 1% | CRM power |
| R7 | RC2512FK-0710RL | Yageo | **1W** 1% | jellybean (in-stock-trolig; 1W marginellt) |
| R8 | RC2512JK-0710RL | Yageo | **1W** 5% | billigast jellybean |
| R9 | 2512WGF10R0T5E | Uniroyal | **1W** 1% | kinesisk basic-lib (billig) |
| R10 | WR12X10R0FTL | Walsin | **1W** 1% | basic-lib |
| R11 | ESR25JZPF10R0 | ROHM | **1W** 1% | — |

## LAGER-KOLL RESULTAT (NextPCB, 7/11 matchade) + valt MPN

| Ref | MPN | Märke | Effekt | Lead | $ |
|---|---|---|---|---|---|
| R1 | CRCW251210R0FKEGHP | Vishay | 2W HP 1% | **31–42 d** ❌ | 0.955 (nuvarande, blev värre) |
| **R2 ✅VALD** | CRCW251210R0JNEGHP | Vishay | **2W HP** 5% | **4–6 d** | 0.401 |
| R6 | CRM2512-FX-10R0ELF | Bourns | (rating osäker) | 4–6 d | 0.268 |
| R7 | RC2512FK-0710RL | Yageo | **1W** 1% | ✅ In Stock | 0.119 |
| R8 | RC2512JK-0710RL | Yageo | **1W** 5% | ✅ In Stock | 0.100 |
| R10 / R11 | WR12X10R0FTL / ESR25JZPF10R0 | Walsin / ROHM | 1W | 7–18 d | 0.040 / 0.261 |
| R3 / R4 / R5 / R9 | — | Vishay/Yageo/Panasonic/Uniroyal | — | Pending | — |

**Valt: R2 Vishay `CRCW251210R0JNEGHP` (2W HP, 5%, 4–6 d, $0,40).** Enda *In Stock* var R7/R8 men
de är **1W < 1,25 W medel** (underdimensionerade). Enda bekräftat 2W-tillgängligt är Vishay HP-familjen;
R1 (nuvarande) är 31–42 d, **R2 = samma 2W-HP-familj på 4–6 d** (i linje med övriga BOM, t.ex. 0R2:s
4–7 d → förlänger ej kritiska vägen) och **−58 % pris**. 5 % tol är irrelevant för ett LED-serie­motstånd.
**Drop-in: ingen omroutning, ingen firmware-ändring, full 2W-marginal behållen.** (R7/R8 1W = skenbesparing
→ skulle kräva sänkt duty eller 2× parallell layout-ändring.)

**Gjort:** `gen_nextpcb.py` `"10R"` → R2; helmet-mb + vest-patch-BOM regenererade + kopierade till
`leverans/` (de två kort som bär 10R; footprint oförändrad → ingen omroutning).
