# STRILAS — v1 skjut-test: exakt inköpslista

> **Detta är version 1 av hur vapnet är TÄNKT att fungera — inte vanlig peka-och-skjut
> laser tag.** Minsta bygget som visar STRILAS-konceptet på riktigt: vapnet fångar sin
> **siktriktning (IMU)** vid avtryck, skickar en **FireEvent** (riktning + tid + IR-kod)
> till en **adjudikator** som modellerar ballistiken och avgör träff — med **IR-strålen
> som siktlinje-ankare + zon**, inte som hela sanningen. **P4-familjen hela vägen.**

## Vad v1 faktiskt visar (skiljer det från laser tag)

1. **PRECIST sikte (kärnan):** sikteskameran mäter bäringen till målets **aktiva
   IR-konstellation** via solvePnP → **sub-0,1°** relativ bäring. IMU:n fyller mellan
   bildrutorna (hög-rate) + rekyl. *Det här* är precisionen — inte strålbredden.
2. **Server-avgjort:** vapen + mål skickar *bevis* (FireEvent / IRHit) över WiFi; en
   liten **adjudikator avgör** — exakt nivå-3-loopen i miniatyr.
3. **IR-skottstråle = LOS + skott-ID, inte hitbox:** bred kon (länkbudget), geometrin
   gör precisionen (se `level3-ballistic-architecture.md` §3.2).
4. **Riktig räckvidd + precision (100–150 m):** kollimerad emitter (räckvidd) +
   **telefoto-sikteskamera + aktiv IR-konstellation** (precis bäring på avstånd) — ingen
   leksak som bara pekar åt rätt håll.

**Server = din laptop/PC** för v1 (ingen Jetson behövs än). **Precisionen är RELATIV**
(kameran mäter vapen→mål direkt) → därför behövs **varken GNSS-heading eller UWB i v1**;
de kommer när spelare rör sig över fält och mål inte alltid är i sikte. Målets grova
position mäts in med måttband.

## Kort — köp 2× samma kit (minimal variation)

| Antal | Del | Roll | ~Pris |
|---|---|---|---|
| **2** | **ESP32-P4-WIFI6-KIT-A** (P4 + C6 **WiFi 6** + **kamera** + **högtalare** + mic) | 1 = **vapen**, 1 = **mål** | ~$32/st |

Identisk hårdvara i båda → en toolchain (ESP-IDF), en sak att lära sig. Kamera +
högtalare ingår i kitet och stannar i scope (pose-väg + ljud senare).

> *Har du redan ETH-kitet (PoE) kan det bli målet istället — men 2× samma WIFI6-kit
> är enklast.*

## Vapnet — emitter (100–150 m) + precis sikteskamera

**A. Skottstråle (räckvidd + LOS):**

| # | Del | Antal | ~Pris | Not |
|---|---|---|---|---|
| 1 | **IR-LED ams-OSRAM SFH 4715AS** (860 nm) | 2 | ~$2 | high-power, tål **1–3 A pulsat** |
| 2 | **TIR-kollimator** (Carclo 10195 ~20 mm, för SFH 4715AS) | 1–4 | ~$3/st | **räckvidd** (bred kon ok — inte precision) |
| 3 | **Logic-level N-MOSFET** AO3400 | 2 | ~$1 | gate från RMT (56 kHz) |
| 4 | **Rsense ~1–3 Ω 2W** + **reservoarcap** 100–470 µF + 220 Ω gate + ¼W-sortiment | 1 sats | ~$6 | resistorn = HW-strömgräns (ögonsäkerhet); cap levererar pulsen |
| 5 | **Mikrobrytare** (trigger) | 1 | ~$1 | |

**B. Precis bäring (det som gör det till mer än en leksak):**

| # | Del | Antal | ~Pris | Not |
|---|---|---|---|---|
| 6 | **TDK ICM-45686 breakout** | 1 | ~$12 | hög-rate attityd + rekyl, fyller mellan kamerabildrutor |
| 7 | **Telefoto M12-lins** (~10–15° FOV) till sikteskameran | 1 | ~$15 | **vinkelupplösning + räckvidd** — annars för liten konstellation @150 m |
| 8 | **860 nm IR-pass/bandpass-filter** för sikteskameran | 1 | ~$8 | ser bara konstellationen → robust dag/natt |
| 9 | Perfboard + lödd LED-strömväg + Dupont | 1 | ~$6 | **löd LED+driver fast** — breadboard tål inte 1–3 A |

> **Sikteskameran = OV5647 (NoIR) i kitet** för v1 — gratis, mogen P4-drivrutin. Rolling shutter
> hanteras med fast-pan-grind i firmware (IMU flaggar snabb panorering). GS-uppgradering = ams-OSRAM
> MIRA220MINI MONO (~$141 eval) *om* grinden blir för begränsande. CV-firmwaren skriver jag.

IMU på I²C; RMT driver gaten på 56 kHz; kameran via FFC till P4 MIPI-CSI.

## Målet — komponenter att koppla till kit #2

Målet gör nu **två** saker: **syns** (IR-konstellation som vapnets kamera pose:ar på) +
**registrerar skott** (TSOP avkodar strålen).

| # | Del | Antal | ~Pris | Not |
|---|---|---|---|---|
| 1 | **IR-LED 860 nm (vidvinkel)** för **konstellationen** | 4 | ~$3 | i **känd geometri** (PnP-mål) — mät basen exakt, t.ex. ~0,5 m |
| 2 | Liten MOSFET/transistor-driver för konstellationen | 1 | ~$1 | P4 modulerar (blink-ID + skiljer från bakgrund/sol) |
| 3 | **Vishay TSOP4856** (56 kHz) | 4 | ~$4 | tar emot skottstrålen (zon/täckning) |
| 4 | **860 nm bandpass-glasfilter** | 4 | ~$8 | TSOP utomhus-räckvidd i solljus |
| 5 | Status-LED + kablar | 1 | ~$2 | **högtalaren finns i kitet** = träffljud |
| 6 | Fysiskt mål: kartong/foamboard | 1 | – | montera TSOP + konstellation; LED:erna bör ~rama in hitbox-arean |

## Precisionsmekanism (varför detta inte är en leksak)

1. Målets **IR-konstellation** (4 LED i känd geometri) lyser; vapnets **NoIR + IR-pass-
   kamera** ser dem som ljuspunkter (funkar dag/natt, på avstånd).
2. **solvePnP** på de 4 punkterna → målets **3D-pose relativt vapnet** (riktning + avstånd).
3. **Boresight = kamerans optiska axel** (kalibrerad). Servern skjuter ballistik-banan
   längs boresight och kollar om den (med drop) skär målets **hitbox-kapslar**, definierade
   *relativt konstellationen*. Allt i relativ ram → **ingen GNSS/UWB behövs**.
4. **IMU** predikterar mellan kamerabildrutor (16–33 ms) + ger rekyl/tilt.

Vinkelprecision: telefoto-kamera ger sub-pixel-bäring ≪ 0,1° → upplöser torso (0,19° @150 m)
och nästan huvud (0,076°). **Bringup-tips:** börja CV:n med en stor tryckt **ArUco** på kort
håll (enklast), byt till aktiv IR-konstellation för full räckvidd/mörker.

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

**Total ~$145** — varav $64 är de två korten du ändå vill ha för projektet.

---

*När korten + komponenterna är hemma skriver jag firmware + adjudikator:*
- *Vapen (P4): **kamera → IR-blob-detektion → solvePnP mot konstellationen → relativ
  bäring (sub-0,1°)**; IMU fyller mellan bildrutor; vid trigger → FireEvent (bäring +
  pose + tid + IR-kod) över WiFi + skjut kodad 56 kHz-stråle. Kamerakalibrering en gång.*
- *Mål (P4): driv IR-konstellationen (blink-ID) + TSOP → IRHit (zon, IR-kod, tid) → ljud.*
- *Adjudikator (laptop): ballistik-bana längs kamerabäringen → geometri mot målets
  hitbox-kapslar → grinda mot IR-LOS → träff/miss/zon. Nivå-3-loopen i smått.*
