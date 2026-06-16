# STRILAS — ballistik & avståndsmätning (analys)

> Skisser: [`vapen-layout.png`](vapen-layout.png) · [`ballistik-avstand.png`](ballistik-avstand.png)
> Bygger på de låsta optikbesluten i [`../../hardware/weapon-module-design-resolution.md`](../../hardware/weapon-module-design-resolution.md) §1 & §6.
> *(Rättat: en tidigare version här använde naiv 2-beacon-stadiametri + 8,7 mm-lins och
> underdrev precisionen grovt. Systemet använder aktiv konstellation + PnP + 16 mm-lins.)*

## Frågan
Skjuter du mot ett mål på 150 m måste du sikta **ovanför** målet (kulfall). Men då
ligger inte kamerans centrum på målets centrum. Hur hittar systemet avståndet, och
hur hanteras hållover?

## 1. Grundinsikt: ljus faller inte → ballistik **beräknas**
940 nm-skottstrålen går rakt. Riktig kulbana kan därför inte fås fysiskt — den
**beräknas i firmware**, vilket kräver **avstånd R**. Kulfall (v₀≈900 m/s) vid 150 m:
`½·g·(R/v)² ≈ 14 cm`, dvs en hållpunkt ≈ 0,9 mrad (~3 MOA) över målet.

## 2. Avståndet kommer ur **PnP på en aktiv IR-konstellation** (inte LED:n, inte stadiametri)
Målet bär en **aktiv konstellation** av modulerade 860 nm-LED i ett **känt 3D-mönster**.
Kameran tar punkternas 2D-projektion och löser **PnP (Perspective-n-Point)** → hela
posen: **avstånd R + bäring + orientering** på en gång (robustare än 2-punkts
stadiametri, som bara ger avstånd ur en baslinje).

**Varför aktiv konstellation:** modulerade LED + **frame-differencing** + 860 nm-bandpass
→ rena ljuspunkter (blobbar) även i dagsljus; **global shutter** (OV9281) → ingen
rörelsesmet. Det räcker med få pixlar per punkt + subpixel-centroidering — till skillnad
från passiva ArUco-markörer som kräver ~20–30 px för avkodning.

**Optik (låst):** Arducam B0332 (OV9281, 1280×800, **3 µm**, global shutter) + IR-pass-filter,
**lins 16 mm M12 (~13,7° FOV)**. Vid 150 m: ~14 px LED-separation + **~24 px baslinje** → robust PnP.

## 3. Precision @150 m (rätt siffror)
| Storhet | Värde @150 m | Hur |
|---|---|---|
| Vinkelskala | **0,0107 °/px** | p/f = 3 µm / 16 mm |
| **Bäring** (mål-läge) | **≈ 0,001° → ≈ 2,8 mm** | subpixel-centroid ~0,1 px; ≪ kravet 0,19° |
| **Avstånd R** (PnP) | **±0,3–0,9 m** (sub-meter) | ~24 px baslinje, modulerade blobbar 0,05–0,1 px; konstellation (≥4 LED, minsta-kvadrat) ≈ ±0,3 m |
| IMU inter-frame-drift | 0,0005° @60 fps | kameran re-ankrar attityden varje frame |

Bäringen (~mm-klass) är det som avgör om träffpunkten hamnar på målet. Avståndet matar
**bara** ballistik-hållpunkten — och den är **mycket** okänslig för R-fel:

```
d(kulfall)/dR ≈ 1,8 mm per meter R-fel  @150 m
→  ±0,9 m avståndsfel  ⇒  ±1,6 mm hållpunktsfel   (försumbart)
```

Så även om avståndet skulle vara dåligt blir det knappt något siktfel. Den tidigare
"±2 m"-siffran var dels fel metod/lins, dels skulle den ändå bara gett ±3,6 mm hållpunkt.

## 4. Varför "kameracentrum ≠ målcentrum" är avsiktligt
Kameran mäter målets exakta läge i bilden (ur konstellationens centroider) **plus** R.
Firmware:
1. boresight = bildmitt (dit pipan pekar),
2. R → kulfall → **hållpunkts-prick** under mitten (pixel-offset),
3. **träff om** simulerad bana (boresight + fall över R) skär målet inom träffradie.

En hållpunkts-retikel flyttar sig nedåt med avståndet; du lägger konstellationen på den.
Bildmitten får peka över målet — det är poängen.

## 5. Roller — "punkter av kalkyleringar"
- **Beräkningspunkterna = konstellationens LED-centroider i kamerabilden.** Ur dem löser
  PnP både bäring och avstånd. Där görs "punkterna" — i kameran.
- **IR-LED (940 nm):** skott-ID/LOS + anti-fusk; **inte** geometrin (och inte avståndet).
  Eftersom boresight pekar över målet vid hållover bär strålen skottdata och träffen
  adjungeras av skyttens kamera+firmware (som har bäring + R exakt) och rapporteras.
- **Kamera (860 nm-pass):** ser konstellationen, avvisar egen 940 nm-stråle (ingen självbländning).
- **IMU (ICM-42670-P):** stel mot optiska axeln; kameran re-ankrar varje frame.

## 6. Designval / kvar att verifiera
- **FOV/brännvidd** sätts egentligen av §1.3-testet (syns konstellationen @150 m i dagsljus?).
  16 mm = trolig landning; 6 mm räcker bara ~80 m. Smalare FOV = bättre dagsljus-SNR.
- **Konstellationsgeometri:** ≥4 LED i känt 3D-mönster (icke-koplanärt) → entydig, robust PnP;
  koda blink-ID per mål för flera samtidiga mål.
- **Kalibrering:** kamera-intrinsics (schackruta) + extrinsics IMU↔kameraram en gång;
  boresight↔kameramitt-parallax tabelleras för närhåll.
- **Ballistikmodell:** `½g(R/v)²` räcker för spel; lägg luftmotstånd/BC vid behov.

## TL;DR
Avståndet kommer ur **PnP på den aktiva IR-konstellationen i kameran** (16 mm-lins),
inte ur LED:n eller naiv stadiametri. Bäring ≈ **mm-klass** @150 m, avstånd **sub-meter**,
och ballistik-hållpunkten är så okänslig för avståndsfel (~1,8 mm/m) att precisionen är
gott och väl tillräcklig. Att sikta över målet ligger i den beräknade hållpunkten.
