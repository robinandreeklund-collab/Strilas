# STRILAS — KONTAKT / HEADER-SAMPLER (DEMO · EJ FÖR TILLVERKNING)

Inventerar **alla gemensamma kontakter** över de 6 korten i de **exakta footprints** korten
använder. Två syften:

1. **Lager-koll** — ladda upp `kontakt-sampler-bom.xls` → se vilka NextPCB har i lager.
2. **MONTERINGSTEST** — kontakterna är här markerade **FÖR montering (ej DNP)** → vi ser om
   NextPCB kan **sourca + montera** (våg/selektiv THT-lödning) kontakterna åt oss. Funkar det
   → vi slipper handlöda dem på de riktiga korten (idag är de DNP/kund-lödda).

> **Kortet beställs / tillverkas ALDRIG.** Bara lager- + monteringskoll.

## Filer
`kontakt-sampler-bom.xls` (17 rader — **filen att ladda upp**) · `kontakt-sampler-gerbers.zip` ·
`kontakt-sampler-centroid.csv` (alla 17 med — eftersom alla ska monteras). Källa:
`hardware/connector_sampler.py`. Footprints inventerade ur `hardware/*.net`.

## Inventering (antal = förekomster över alla kort)
| Ref | Footprint | MPN | Märke | Används till | Antal |
|---|---|---|---|---|---|
| **2.54 mm hona-socklar (THT)** ||||||
| J1 | PinSocket_1x03 | PPTC031LFBN-RC | Sullins | kraft-tapp 3V3/GND | 1 |
| J2 | PinSocket_1x07 | PPTC071LFBN-RC | Sullins | XIAO-S3 / amp-/mik-breakout | 2 |
| J3 | PinSocket_1x14 | PPTC141LFBN-RC | Sullins | P4 edge A | 1 |
| J4 | PinSocket_1x15 | PPTC151LFBN-RC | Sullins | P4 edge | 1 |
| J5 | PinSocket_1x20 | PPTC201LFBN-RC | Sullins | P4-WIFI6 edge A/B | 4 |
| **2.54 mm stift-headers (THT)** ||||||
| J6 | PinHeader_1x06 | PREC006SAAN-RC | Sullins | I²S MEMS-mik-breakout | 1 |
| J7 | PinHeader_1x07 | PREC007SAAN-RC | Sullins | MAX98357A-amp-breakout | 1 |
| **JST-PH 2.0 mm vertikal (B-typ)** ||||||
| J8 | JST_PH_B2B-PH-K 1x02 | B2B-PH-K-S(LF)(SN) | JST | trigger/rack/mag-switchar | 4 |
| J9 | JST_PH_B3B-PH-K 1x03 | B3B-PH-K-S(LF)(SN) | JST | recoil-styrning | 2 |
| J10 | JST_PH_B4B-PH-K 1x04 | B4B-PH-K-S(LF)(SN) | JST | NFC PN532 I²C | 2 |
| **JST-PH 2.0 mm sido (S-typ, låg höjd)** ||||||
| J11 | JST_PH_S2B-PH-K 1x02 | S2B-PH-K-S(LF)(SN) | JST | högtalare/PTT/bom-mik | 3 |
| J12 | JST_PH_S5B-PH-K 1x05 | S5B-PH-K-S(LF)(SN) | JST | aim-patch | 5 |
| J13 | JST_PH_S6B-PH-K 1x06 | S6B-PH-K-S(LF)(SN) | JST | zon/patch | 10 |
| **JST-XH 2.5 mm** ||||||
| J14 | JST_XH_S2B-XH-A 1x02 | S2B-XH-A(LF)(SN) | JST | 2S-batteri | 3 |
| **JST-GH 1.25 mm SMD** (redan SMT-placerad på korten) ||||||
| J15 | JST_GH_SM06B-GHS-TB 1x06 | SM06B-GHS-TB(LF)(SN) | JST | RTK-puck (helmet J1) | 1 |
| J16 | JST_GH_SM08B-GHS-TB 1x08 | SM08B-GHS-TB(LF)(SN) | JST | ZED-F9P RTK | 2 |
| **Kraft** ||||||
| J17 | AMASS_XT30PW-M 1x02 | XT30PW-M | AMASS | batteri-in | 1 |

## LAGER-/MONTERINGSKOLL RESULTAT (NextPCB, 10/17 matchade)

| Del | MPN | Lager | $/st | Slutsats |
|---|---|---|---|---|
| J8 PH 2p vert | B2B-PH-K-S(LF)(SN) | ✅ In Stock | 0.035 | sourca+montera OK |
| J9 PH 3p vert | B3B-PH-K-S(LF)(SN) | ✅ In Stock | 0.041 | OK |
| J10 PH 4p vert | B4B-PH-K-S(LF)(SN) | ✅ In Stock | 0.046 | OK |
| J11 PH 2p sido | S2B-PH-K-S(LF)(SN) | ✅ In Stock | 0.039 | OK |
| J12 PH 5p sido | S5B-PH-K-S(LF)(SN) | ✅ In Stock | 0.076 | OK |
| J13 PH 6p sido | S6B-PH-K-S(LF)(SN) | ✅ In Stock | 0.072 | OK |
| J14 XH 2p | S2B-XH-A(LF)(SN) | ✅ In Stock | 0.072 | OK |
| J15 GH 6p SMD | SM06B-GHS-TB(LF)(SN) | ✅ In Stock | 0.457 | (redan SMD) |
| J16 GH 8p SMD | SM08B-GHS-TB(LF)(SN) | ✅ In Stock | 0.553 | (redan SMD) |
| J17 XT30 | XT30PW-M | ✅ In Stock | 0.383 | OK |
| J1–J7 2.54 headers | Sullins PPTC/PREC | ⚠️ Pending | — | Sullins ej i auto-lib; manual-offert / byt MPN |

**Slutsats:** **alla JST-PH/XH/GH + XT30 är In Stock och togs FÖR montering (ej DNP, prissatta)** →
NextPCB kan **sourca + genomplåts-montera** dem åt oss. De 7 Pending är bara 2.54-headerna (Sullins-
MPN matchar ej deras lib; generiska 2.54-hona/stift finns dock överallt → manual-offert 1 dag, eller
byt till NextPCB-lagerförd MPN).

## Nästa steg (kräver beslut — kostnad/process-avvägning)
- **Aktivera maskin-montering** på de riktiga korten = ändra `is_conn()`/`cust_refs` i
  `gen_nextpcb.py` så JST/XT30 får montering istället för DNP, regenerera alla BOM/centroid.
  Vinst: färdiga kort, ingen handlödning. Kostnad: NextPCB tar betalt för THT-montering (selektiv/
  våg) per kontakt + ev. setup; hjälm-kortet är redan dubbelsidigt.
- **2.54 P4-socklar/headers:** byt placeholder-/Sullins-MPN → NextPCB-lagerförd generisk 2.54 (kräver
  egen liten lager-koll eller manual-offert) om de också ska maskin-monteras.
