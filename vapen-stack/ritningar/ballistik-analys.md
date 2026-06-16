# STRILAS — ballistik & avståndsmätning (analys)

> Skisser: [`vapen-layout.png`](vapen-layout.png) · [`ballistik-avstand.png`](ballistik-avstand.png)

## Frågan
Skjuter du mot ett mål på 150 m måste du sikta **ovanför** målet (kulfall/kulbana).
Men då ligger inte kamerans centrum på målets centrum. Hur hittar systemet
avståndet, och hur hanteras att man måste hålla över?

## 1. Grundinsikten: ljus faller inte — ballistik måste **beräknas**
En IR-stråle (940 nm-skottet) går rakt; den påverkas inte av gravitation. Vill vi
simulera **riktig kulbana** kan vi alltså INTE låta strålen fysiskt "träffa" målet
och kalla det en träff på långt håll. I stället:

- **Kameran** är sensorn som mäter *var* målet är (vinkel) och *hur långt bort* (avstånd).
- **Firmware** räknar ut kulans bana (fall över avståndet) och avgör träff/miss.
- **IR-LED:n (940 nm)** är **skott-kommunikation** (skytte-ID + skottdata till mål/server),
  inte det som avgör geometrin.

Kulfall (ex. v₀≈900 m/s): `fall ≈ ½·g·(R/v₀)²`. Vid R=150 m → t≈0,167 s →
**fall ≈ 14 cm**, dvs en hållpunkt på `≈ fall/R ≈ 0,9 mrad` (~3 MOA) över målet.

## 2. Hur avståndet R fås — stadiametriskt med kameran
Målet bär **IR-beacons med känd geometri** (t.ex. två beacons med känt avstånd S,
eller en känd kropps-/markörbredd). Kameran mäter deras **vinkelstorlek i pixlar**:

```
R = f · S / (p · n)
   f = brännvidd, p = pixelstorlek (OV9281 = 3 µm), n = pixlar mellan beacons, S = verklig separation
```

Det är exakt samma princip som en mil-dot-kikare. Inget time-of-flight behövs
(skulle kräva ns-timing — ej möjligt med denna hårdvara). IR-LED:n kan **inte**
mäta avstånd tillförlitligt (reflex-intensitet är opålitlig).

**Räkneexempel (150 m):** f≈8,7 mm (~25° HFOV), S=0,4 m →
`n = 8,7e-3·0,4 / (3e-6·150) ≈ 7,7 px`.
- Vinkelupplösning/pixel: `p/f ≈ 0,35 mrad/px`.
- Med **subpixel-centroiding** av beacon-mitten (~0,1 px) → avståndsfel ≈ 0,1/7,7 ≈ **1,3 % → ±2 m @ 150 m**.
- Längre brännvidd eller större S ⇒ bättre noggrannhet (men mindre synfält).

## 3. Varför "kameracentrum ≠ målcentrum" är helt OK
Systemet kräver INTE att mitten ligger på målet. Kameran mäter målets **exakta läge i
bilden** (azimut/elevation relativt boresight) plus avståndet. Firmware gör:

1. boresight-riktning = dit pipan pekar (bildens mitt),
2. avstånd R (steg 2) → **kulfall** → omräknat till en **pixel-hållpunkt** under mitten,
3. **träff om** den simulerade kulbanan (boresight + fall över R) skär målet (inom träffradie).

I praktiken visas en **hållpunkts-retikel** som flyttar sig nedåt med avståndet; du
lägger den på målet. Bildens geometriska mitt får alltså gärna peka över målet —
det är själva poängen med hållpunkten.

## 4. Roller — "punkter av kalkyleringar"
- **Beräkningspunkterna = beacon-centroiderna i kamerabilden.** Ur dem fås både
  vinkel (läge) och avstånd (separation). Det är där "punkterna" görs — i kameran.
- **IR-LED (940 nm):** skickar skottet/ID:t. Eftersom boresight (och 940 nm-strålen)
  pekar *över* målet vid hållover, ska strålen ha en **bred nog kon** ELLER så bär
  strålen bara skott-ID och **träffen adjungeras av skyttens kamera+firmware** och
  rapporteras (till mål/server). Kameran "ser" redan exakt vilket mål och var.
- **Kamera (OV9281, 860 nm-bandpass):** ser målets 860 nm-beacons, avvisar egen
  940 nm-stråle → ingen självbländning.

## 5. Praktiska rekommendationer / designval
- **Beacon-geometri:** minst två beacons med så stor känd separation S som möjligt
  (axelbredd ~0,4–0,5 m) för bäst avståndsupplösning; koda dem (blink-ID) så flera
  mål kan särskiljas.
- **Brännvidd:** välj lins efter max-avstånd vs synfält. 150 m kräver god centroiding;
  ~8–16 mm + subpixel ger ±1–3 m.
- **Ballistikmodell i firmware:** tabell/parametrar per "vapentyp" (v₀, BC) → fall(R);
  enkel `½g(R/v)²` räcker för spel, lägg ev. luftmotstånd om realism krävs.
- **Hit-adjudikering:** låt skyttens enhet räkna träffen (den har vinkel + R exakt) och
  skicka utfallet; 940 nm används för LOS-ID och anti-fusk, inte som "kula".
- **Kalibrering:** boresight↔kamera-mitt kalibreras en gång (parallax pipa↔lins);
  parallaxen är försumbar bortom några meter men korrigeras i tabell för närhåll.

## TL;DR
Avståndet kommer från **kameran** (beacon-separation i pixlar, stadiametriskt) — inte
från LED:n. Firmware räknar kulfallet för det avståndet och lägger en **hållpunkt**;
träff avgörs av om den simulerade banan skär målet. Att sikta över målet är inbyggt i
hållpunkten — kameracentrum behöver aldrig ligga på målet.
