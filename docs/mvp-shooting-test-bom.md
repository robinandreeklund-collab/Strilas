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
4. **Riktig räckvidd (100–150 m utomhus):** v1 kör en **kollimerad högström-emitter**
   från start — inget 15 m-bänkbygge som inte bevisar något.

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

## Vapnet — kollimerad högström-emitter (100–150 m)

| # | Del | Antal | ~Pris | Not |
|---|---|---|---|---|
| 1 | **TDK ICM-45686 breakout** (SlimeVR Mumo eller generisk) | 1 | ~$12 | **KÄRNA** — ger siktvektorn till ballistiken; utan den = laser tag |
| 2 | **IR-LED ams-OSRAM SFH 4715AS** (860 nm) eller 940 nm OSLON-syskon | 2 | ~$2 | high-power, tål **1–3 A pulsat**; 940 nm matchar TSOP-toppen |
| 3 | **TIR-kollimator / asfärisk lins ~±5°** (Carclo/LEDiL för OSLON Black) | 1 | ~$3 | **räckviddsspaken** — koncentrerar strålen → 100–150 m |
| 4 | **Logic-level N-MOSFET** AO3400 | 2 | ~$1 | tål 1–3 A korta pulser; gate från RMT (56 kHz) |
| 5 | **Strömsättningsresistor** ~1–3 Ω (effekt) + **reservoarkondensator** 100–470 µF låg-ESR + 220 Ω gate + ¼W-sortiment | 1 sats | ~$6 | resistorn sätter (och hårdvarubegränsar) pulsströmmen; cap:en levererar pulsen |
| 6 | **Mikrobrytare** (snap-action med arm) | 1 | ~$1 | trigger |
| 7 | Perfboard + lödd LED-strömväg + Dupont för signaler | 1 | ~$6 | **löd LED+driver fast** — breadboard tål inte 1–3 A rent |

I²C-IMU:n kopplas till P4-kortets I²C-pinnar; firmwaren gör host-side-fusion
(attityd) och låser siktvektorn vid avtryck. LED:n sitter i lins-fokus (kollimering);
RMT driver gaten på 56 kHz, resistorn + reservoarcap formar pulsströmmen.

## Målet — komponenter att koppla till kit #2

| # | Del | Antal | ~Pris | Not |
|---|---|---|---|---|
| 1 | **Vishay TSOP4856** (56 kHz) | 4 | ~$4 | IR-mottagare, 4 st = täckning/zoner |
| 2 | **860/940 nm bandpass-glasfilter** (matcha emitterns våglängd) | 4 | ~$8 | **krävs för utomhus-räckvidd** — sänker tröskeln i solljus |
| 3 | Status-LED + kablar | 1 | ~$2 | **högtalaren finns i kitet** = träffljud |
| 4 | Fysiskt mål: kartong/foamboard | 1 | – | montera TSOP-arna på |

## ⚠️ Den enda regeln som måste stämma

**Bärvåg = mottagarfrekvens: 56 kHz.** Emittern moduleras på 56 kHz, TSOP**4856**
lyssnar på 56 kHz. Blanda inte 38/56 kHz — då ser målet ingenting.

## ⚠️ Ögonsäkerhet — nu på riktigt (1–3 A kollimerad)

Den här emittern är **inte** trivialt säker som en 100 mA-LED. Att kollimera 1–3 A till
±5° ger hög radians → **du måste beräkna/mäta accessible emission (AE) vid aperturen och
sätta en hårdvaru-strömgräns** (strömsättningsresistorn = vakten, inte firmware).

- En **LED är inkoherent + utsträckt källa** → långt mer förlåtande än en laser, men inte gratis.
- **Sikta 1 A först.** Behöver du mer räckvidd, lös det hellre med bandpassfilter på mottagaren
  än med mer ström.
- **Bänkmät** (eller räkna konservativt per IEC 60825-1) innan du pekar den mot någon.

> *Be om en Class 1-strömbudget-kalkyl (max ström för given strålvinkel + källstorlek) innan bygget.*

## Verktyg

Lödkolv + tenn (**LED-strömvägen ska lödas**, inte breadboardas — 1–3 A), multimeter.
Helst en optisk effektmätare för AE-verifiering.

**Total ~$115** — varav $64 är de två korten du ändå vill ha för projektet.

---

*När korten + komponenterna är hemma skriver jag firmware + adjudikator:*
- *Vapen (P4): IMU-attityd → lås siktvektor vid trigger → sänd FireEvent (riktning,
  tid, IR-kod) över WiFi + skjut kodad 56 kHz-stråle.*
- *Mål (P4): TSOP → IRHit (zon, IR-kod, tid) över WiFi + ljud i högtalaren.*
- *Adjudikator (laptop): ballistik-bana längs siktvektorn → geometri mot målets
  inmätta hitboxes → grinda mot IR-LOS/zon → träff/miss/zon. Nivå-3-loopen i smått.*
