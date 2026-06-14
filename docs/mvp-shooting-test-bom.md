# STRILAS — v1 skjut-test: exakt inköpslista

> **Detta är version 1 av hur vapnet är TÄNKT att fungera — inte vanlig peka-och-skjut
> laser tag.** Minsta bygget som visar STRILAS-konceptet på riktigt: vapnet fångar sin
> **siktriktning (IMU)** vid avtryck, skickar en **FireEvent** (riktning + tid + IR-kod)
> till en **adjudikator** som modellerar ballistiken och avgör träff — med **IR-strålen
> som siktlinje-ankare + zon**, inte som hela sanningen. **P4-familjen hela vägen.**

## Vad v1 faktiskt visar (skiljer det från laser tag)

1. **Pose-medvetet:** vapnets IMU ger siktvektorn → servern integrerar en (enkel men
   riktig) ballistik-bana längs den, inte bara "stråle in i sensor".
2. **Server-avgjort:** vapen + mål skickar *bevis* (FireEvent / IRHit) över WiFi; en
   liten **adjudikator avgör** — exakt nivå-3-loopen i miniatyr.
3. **IR = ankare, inte domare:** strålen bevisar siktlinje + zon och grindar geometrin.

**Server = din laptop/PC** för v1 (ingen Jetson behövs än). **Målets position** mäts in
med måttband och konfigureras tills UWB/GNSS-lagret kommer — det är den enda genvägen,
och den ändrar inte loopens logik.

## Kort — köp 2× samma kit (minimal variation)

| Antal | Del | Roll | ~Pris |
|---|---|---|---|
| **2** | **ESP32-P4-WIFI6-KIT-A** (P4 + C6 **WiFi 6** + **kamera** + **högtalare** + mic) | 1 = **vapen**, 1 = **mål** | ~$32/st |

Identisk hårdvara i båda → en toolchain (ESP-IDF), en sak att lära sig. Kamera +
högtalare ingår i kitet och stannar i scope (pose-väg + ljud senare).

> *Har du redan ETH-kitet (PoE) kan det bli målet istället — men 2× samma WIFI6-kit
> är enklast.*

## Vapnet — komponenter att koppla till kit #1

| # | Del | Antal | ~Pris | Not |
|---|---|---|---|---|
| 1 | **TDK ICM-45686 breakout** (SlimeVR Mumo eller generisk) | 1 | ~$12 | **KÄRNA** — ger siktvektorn till ballistiken; utan den = laser tag |
| 2 | **IR-LED ams-OSRAM SFH 4715AS** (860 nm) | 2 | ~$2 | skott-emitter (1 + reserv) |
| 3 | **Logic-level N-MOSFET** AO3400 / 2N7000 | 2 | ~$1 | LED-driver |
| 4 | **Motstånd** 33 Ω + 220 Ω + ¼W-sortiment | 1 sats | ~$5 | 33 Ω ⇒ ~100 mA = ögonsäkert + några meter |
| 5 | **Mikrobrytare** (snap-action med arm) | 1 | ~$1 | trigger |
| 6 | Breadboard + Dupont-kablar | 1 | ~$6 | montering utan lödning |

I²C-IMU:n kopplas till P4-kortets I²C-pinnar; firmwaren gör host-side-fusion
(attityd) och låser siktvektorn vid avtryck.

## Målet — komponenter att koppla till kit #2

| # | Del | Antal | ~Pris | Not |
|---|---|---|---|---|
| 1 | **Vishay TSOP4856** (56 kHz) | 4 | ~$4 | IR-mottagare, 4 st = täckning/zoner |
| 2 | Status-LED + kablar | 1 | ~$2 | **högtalaren finns i kitet** = träffljud |
| 3 | Fysiskt mål: kartong/foamboard | 1 | – | montera TSOP-arna på |

## ⚠️ Den enda regeln som måste stämma

**Bärvåg = mottagarfrekvens: 56 kHz.** Emittern moduleras på 56 kHz, TSOP**4856**
lyssnar på 56 kHz. Blanda inte 38/56 kHz — då ser målet ingenting.

## Ögonsäkerhet

Med 33 Ω-motståndet (~100 mA) är en 860 nm-LED trivialt Class 1. Driv den **aldrig**
på ampere utan strömgräns och tryck den inte mot ögat. Resistorn = hårdvaruvakten.

## Verktyg

Lödkolv + tenn (om du vill löda emitter/TSOP fast), multimeter. Allt kan dock
breadboardas utan lödning för första testet.

**Total ~$105** — varav $64 är de två korten du ändå vill ha för projektet.

---

*När korten + komponenterna är hemma skriver jag firmware + adjudikator:*
- *Vapen (P4): IMU-attityd → lås siktvektor vid trigger → sänd FireEvent (riktning,
  tid, IR-kod) över WiFi + skjut kodad 56 kHz-stråle.*
- *Mål (P4): TSOP → IRHit (zon, IR-kod, tid) över WiFi + ljud i högtalaren.*
- *Adjudikator (laptop): ballistik-bana längs siktvektorn → geometri mot målets
  inmätta hitboxes → grinda mot IR-LOS/zon → träff/miss/zon. Nivå-3-loopen i smått.*
