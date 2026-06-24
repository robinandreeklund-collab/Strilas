# STRILAS — KONDENSATOR / LAGER-SAMPLER (DEMO · EJ FÖR TILLVERKNING)

**Syfte:** hitta en **in-stock 100nF 0402-MPN** (annat märke) som ersätter nuvarande
`CL05B104KO5NNNC` — den ligger på **12–20 dagars lager-lead** hos NextPCB och är därmed
schemaflaskhalsen för de 4 moderkorten (weapon/firecontrol/helmet/vest-mb) efter att vi
unifierade alla avkopplings-C till 0402. Vi behåller 0402-footprinten och byter bara MPN →
**inget kort routas om**, leadet kapas.

> **Kortet beställs / tillverkas ALDRIG.** Det finns bara för att ladda upp BOM:en och se vad
> NextPCB har i lager. När en in-stock-MPN är vald → uppdatera `gen_nextpcb.py` och regenerera
> de riktiga kortens BOM. Inga gerbers skickas.

## Filer
`cap-sampler-bom.xls` (23 rader — **filen att ladda upp**) · `cap-sampler-gerbers.zip` ·
`cap-sampler-centroid.csv`. Källa: `hardware/cap_sampler.py` → `hardware/cap-sampler.kicad_pcb`.

## Innehåll

### 14× 100nF 0402 — olika märken/spänningar (huvudsyfte)
| Ref | MPN | Märke | Not |
|---|---|---|---|
| **C1** | CL05B104KO5NNNC | Samsung | **NUVARANDE** — 50V X7R, 12–20 d lead (den vi byter bort) |
| C2 | CL05B104KA5NNNC | Samsung | 25V X7R (lägre V → ofta mer i lager) |
| C3 | CL05B104KP5NNNC | Samsung | 10V X7R basic-lib high-runner |
| C4 | GRM155R71H104KE14D | Murata | 50V X7R |
| C5 | GRM155R71C104KA88D | Murata | 16V X7R high-runner |
| C6 | CC0402KRX7R7BB104 | Yageo | 16V X7R |
| C7 | CC0402KRX7R9BB104 | Yageo | 6.3V X7R (billigast) |
| C8 | 0402B104K500CT | Walsin | 50V X7R basic-lib |
| C9 | C1005X7R1H104K050BB | TDK | 50V X7R |
| C10 | C0402C104K4RACTU | Kemet | 16V X7R |
| C11 | 0402B104K500NT | Fenghua | 50V X7R kinesisk basic-lib (billig — ofta i lager) |
| C12 | GRM155R61A104KA01D | Murata | 10V X5R (litet/billigt) |
| C13 | 04025C104KAT2A | Kyocera AVX | 50V X7R |
| C14 | CL05F104ZO5NNNC | Samsung | 16V Y5V (sista utväg, lös tolerans) |
| **C15** | CL21B104KBCNNNC | Samsung | **100nF 0805 — REDAN IN STOCK** (referens-baslinje) |

**Val-regel:** ta första som är **In Stock** med ≥16V X7R/X5R (avkoppling tål allt ≥6.3V vid
3V3-rail, men ≥16V ger marginal). C7/C11/C12 (billigast/basic-lib) är troligast i lager. Y5V (C14)
bara om inget X5R/X7R finns. Undvik att låsa på en hög-V-50V-del om en 16V ligger i lager billigare.

### Övriga lång-lead / manuellt-offererade delar (passa på att lager-kolla)
| Ref | MPN | Märke | Del |
|---|---|---|---|
| R1 | PE2512FKE070R200L | Yageo | 0R2 2512 (CC-sense) — **manuell offert idag** |
| R2 | WSL2512R2000FEA | Vishay | 0R2 2512 Kelvin — in-stock-alt |
| R3 | CRL2512-FW-R200ELF | Bourns | 0R2 2512 — in-stock-alt |
| R4 | CRCW251210R0FKEGHP | Vishay | 10R 2512 (LED-serie effekt) |
| L1 | FNR5040320R47M | Changjiang | 4.7µH FNR5040 (buck) — **manuell offert idag** |
| L2 | SWPA5040S4R7MT | Sunlord | 4.7µH 5×5 — in-stock-alt |
| FB1 | MF-MSMF300/16-2 | Bourns | PTC 3A 1812 — **manuell offert idag** |
| FB2 | 1812L300/16MR | Littelfuse | PTC 3A 1812 — in-stock-alt |

## LAGER-KOLL RESULTAT (NextPCB, 19/23 auto-matchade) + valda MPN

**100nF 0402 — 9 In-Stock-träffar.** Vald: **C4 Murata `GRM155R71H104KE14D` (50V X7R, In Stock,
$0,0125)** → ersätter Samsung `CL05B104KO5NNNC`. Behåller **exakt** 50V X7R-spec (ingen rail-audit
behövs — vissa 100nF kan sitta på VBAT/2S 8,4 V, då duger inte 10–16 V-varianterna), tier-1-märke,
billigare än nuvarande, lead kapat.

| In-Stock 50V X7R | $ | | Lägre-V In-Stock (ej valt) | spec |
|---|---|---|---|---|
| **C4 Murata GRM155R71H104KE14D ✅VALD** | 0.0125 | | C5 Murata GRM155R71C104KA88D | 16V X7R |
| C8 Walsin 0402B104K500CT | 0.0075 | | C3 Samsung CL05B104KP5NNNC | 10V X7R |
| C11 Fenghua 0402B104K500NT | 0.0072 | | C12 Murata GRM155R61A104KA01D | 10V X5R |
| C13 AVX 04025C104KAT2A | 0.0117 | | C14 Samsung CL05F104ZO5NNNC | 16V **Y5V** undvik |

*(C1 nuvarande Samsung 50V = 4–7 d; C2/C6/C7/C9/C10 = 3–18 d lead.)*

**Övriga delar (de som krävde manuell offert idag):**
| Del | Var | → Valt | Status |
|---|---|---|---|
| 0R2 2512 | R1 Yageo PE2512 (Pending/manuell) | **R2 Vishay WSL2512R2000FEA** | 4–7 d, sourcebar — bonus: precisions-Kelvin-sense |
| 4.7µH FNR5040 | L1 Changjiang FNR5040320R47M (Pending) | **L2 Sunlord SWPA5040S4R7MT** | ✅ In Stock — Isat≈2,8A > 2A ✓ |
| PTC 3A 1812 | FB1 Bourns / FB2 Littelfuse | **ingen ändring** | båda Pending → förblir manuell offert |
| 10R 2512 (LED-serie) | R4 Vishay CRCW2512 | **flagga** | 7–18 d + $0,95/st; ingen in-stock-alt sämplad → egen runda vid behov |

**Gjort:** `gen_nextpcb.py` uppdaterad (`100nF@0402`→Murata, `0R2`→Vishay WSL2512, `4.7uH`→Sunlord);
alla 5 påverkade kort-BOM regenererade + kopierade till `leverans/` (optik, firecontrol, helmet-mb,
vest-mb; vest-patch oförändrat → 100nF 0805). **Ingen omroutning** (footprints oförändrade).
