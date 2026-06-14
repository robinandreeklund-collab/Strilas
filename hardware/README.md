# STRILAS — Hårdvaruritningar

## Detektor-ring: 8× TSOP4856 + central P4-kamera

![Detektor-ring](detector-ring-8x-tsop4856.png)

En rund detektormodul (mål-/sensornod) som du skjuter mot: **8 IR-mottagare i ring
runt en central kamera** som delar blickriktning. Genereras av
[`detector_ring_layout.py`](detector_ring_layout.py) (mått-/placeringsritning, topvy —
inte fab-färdiga Gerbers).

### Mått

| Mått | Värde |
|---|---|
| Kort-diameter | Ø76 mm |
| TSOP bult-cirkel | Ø54 mm (8 st, 45° isär) |
| Central lins-öppning | Ø16 mm |
| Kamera-hålbild | 20 mm fyrkant (4× M2) |
| Monteringshål | 4× M2.5 (Ø~2.8) på Ø68 |
| Kontakt | 2×5, 2.54 mm (8× OUT + 3V3 + GND) |

### Elektriskt (per Vishay app-note)

- Varje **TSOP4856**: `VS`→3V3, `GND`→GND, `OUT`→egen P4-GPIO.
- **100 nF** avkoppling nära varje VS + **100 Ω serie + 0.1–1 µF** RC mot
  matnings-/störningstransienter.
- **8 separata OUT** behåller zon/riktningsinfo (vilken sensor som tog strålen).
  OR:a ihop till en enda linje endast om du nöjer dig med ren ja/nej-träff.
- ESP32-P4 har gott om GPIO för 8 ingångar + I²C/MIPI till kameran.

### Optik / täckning

- Domerna pekar **framåt** (ut ur kortet), samma riktning som kameran → tät
  överlappande framåttäckning + redundans + grov träffposition (starkaste sensorn).
- För **äkta 360°/sidotäckning** måste TSOP-arna **vinklas på facetter** — det är en
  separat mekanisk design (böjda ben eller ett facetterat hus), inte detta plana kort.
- **860/940 nm bandpass-glas** över domerna för utomhus-räckvidd (matcha emitterns
  våglängd).

### ⚠️ Verifiera innan tillverkning

Den centrala öppningen + hålbilden är ett **generiskt riktmått** — **matcha exakt mot
din P4-kameramodul** (OV5640 i ESP32-P4-WIFI6-kitet). Mät linsdiameter, hålavstånd och
FFC-kontaktens läge och uppdatera `CAM_SQ`, `CAM_HOLE`, `LENS_R` i skriptet.

### Nästa steg mot riktig PCB

Den här ritningen → KiCad: importera TSOP4856-footprint (Vishay), lägg kameramodulens
footprint i mitten, dra OUT→header. Säg till så genererar jag KiCad-footprintsen.
