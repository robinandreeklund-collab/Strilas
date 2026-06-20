# VÄST-MB — KONTAKT-MONTERINGSTEST (pris-koll)

Syfte: få NextPCB att offerera vest-mb **med alla JST + XT30 maskin-monterade** (istället för
kund-handlödda), så vi ser **vad THT-kontaktmonteringen kostar**. Är priset rimligt → vi gör
likadant på alla kort.

## Ladda upp dessa till NextPCB (vest-mb PCBA-offert)
| Fil | Roll |
|---|---|
| `vest-mb-gerbers.zip` | kort (oförändrat — samma board) |
| `vest-mb-MONTERAD-bom.xls` | **BOM med JST+XT30 satta FÖR montering** (ej DNP) |
| `vest-mb-MONTERAD-centroid.csv` (el. `.xls`) | placering inkl. de 11 kontakterna |

PCBA Qty t.ex. 5. Jämför totalpris mot den vanliga (handlödda) `vest-mb-bom.xls`.

## Vad är monterat i testet
- **J1–J10** — JST-PH 6p sido `S6B-PH-K-S(LF)(SN)` (zon/patch-kontakter) → maskin-monteras
- **J13** — `XT30PW-M` (2S-batteri in) → maskin-monteras
- **J11/J12** — 1x20 P4-WIFI6-socklar (2.54) → **förblir handlödda** (utanför JST/XT30-scope;
  generisk 2.54 var ändå Pending hos NextPCB → egen MPN-koll om de också ska monteras)

Alla 11 kontakter var **In Stock** i kontakt-samplern (S6B-PH ~$0.072, XT30 ~$0.38), så bara
monterings-/THT-lödkostnaden tillkommer i offerten.

## Efter pris-koll
- **Rimligt pris** → jag aktiverar `mount_refs` på alla kort (helmet/optik/firecontrol/vest-patch)
  och regenererar alla BOM/centroid. Färdigmonterade kort, ingen handlödning.
- **För dyrt** → behåll handlödning; de kanoniska `vest-mb-bom.xls` m.fl. (DNP) gäller.

> De kanoniska filerna (`vest-mb-bom.xls`, `vest-mb-centroid.csv`) är **oförändrade** (handlödd
> variant) — bara XT30 fick äntligen sin MPN (`XT30PW-M`) ifylld som beställningsreferens.
