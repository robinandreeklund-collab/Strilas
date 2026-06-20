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

## Efter lager-koll
1. Hitta märket som är **In Stock** (troligast Ckmtw / kinesisk basic-lib) i 1x20 (+ helst alla pinn).
2. Lägg in dess MPN per pinantal i `gen_nextpcb.py` MPN-dicten (ersätt placeholder `2.54-1xNN-FH`
   för `P4-socket …` / `P4-WIFI6 edge …` / kraft-tapp-nycklarna).
3. Lägg P4-sock-refsen i `mount_refs`-logiken (t.ex. utöka `MOUNT_NEEDLES`/`conn_refs` till att
   även ta `PinSocket`, eller addera refsen explicit), regenerera alla BOM/centroid → P4-socklarna
   maskin-monteras också. **Ingen omroutning** (footprint oförändrad).
- Finns inget auto-matchat i lager → NextPCB manual-offererar (1 dag); välj billigaste In-Stock-hona.
