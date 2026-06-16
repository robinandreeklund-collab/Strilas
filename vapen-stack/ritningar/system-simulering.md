# STRILAS — systemsimulering: skytt ↔ mål, hitbox & rörligt mål

> Ritningar: [`system-helhet.png`](system-helhet.png) (skytt↔mål-loopen) ·
> [`hitbox-simulering.png`](hitbox-simulering.png) (hitbox/avstånd/lead) ·
> [`system-oversikt.png`](system-oversikt.png) (vapnets insida + magasin/laddstation)

## 1. Korten stämmer ihop (våglängdssplit verifierad)
| Funktion | Vapen | Väst + hjälm | OK |
|---|---|---|---|
| Skott | sänder **940 nm** (SFH4725S, 56 kHz, kodad) | tar emot **940 nm** (TSOP4856, 56 kHz) | ✓ |
| Synas/sikte | kamera **860 nm-bandpass** | sänder **860 nm**-konstellation | ✓ |

- **Väst-patch:** 3× TSOP4856 (OR:as via BAT54 → 1 DATA-linje = zon) · 2× 860 nm · Q1-driver · J1 4-pol (VBAT·GND·DATA·LED_EN).
- **Hjälm-halo:** 8× TSOP (360°) · 4× 860 nm · GNSS (U.FL) · J1 4-pol.
- Båda → **väst-nod (ESP32-C5)**. Konsekvent med vapnet; inga våglängdskrockar.

## 2. Hur hela loopen funkar (vem avgör träff)
Två IR-länkar, två olika jobb:

1. **860 nm-konstellation (mål → skyttens kamera):** geometrin. Kameran löser PnP → målets
   **avstånd + bäring + zon**. Detta — plus ballistik (fall) och lead — **avgör TRÄFFEN** (precis, mm-klass).
2. **940 nm-skott (skytt → målets TSOP, bred kon, kodad):** **LOS + skytt-ID**. TSOP:en bekräftar
   att strålen fysiskt nådde fram (anti-fusk: kan ej skjuta genom vägg) och vem som sköt.

> **TRÄFF = (kamerans ballistik/lead-lösning landar på målets siluett, rätt zon) OCH (TSOP bekräftar 940 nm-LOS).**
> Den breda 940 nm-konen **ensam ≠ träff** — annars hade det blivit "spreja & be". Det är kameran +
> ditt sikte (hållover + lead) som bestämmer om du träffar. **Därför aldrig point-and-shoot.**

## 3. Hitbox vid olika avstånd (beräknat)
Mål: torso 50×60 cm (väst-zoner), huvud Ø20 cm (hjälm). Kamera 16 mm, 0,0107 °/px.

| Avstånd | torso i bild | huvud i bild | hållpunkt (fall) | sensor-precision | zon upplöst? |
|---|---|---|---|---|---|
| **25 m** | 107 px | 43 px | **4 mm** (~0 %) | 0,9 mm | JA |
| **75 m** | 36 px | 14 px | **34 mm** (~6 %) | 2,6 mm | JA |
| **150 m** | 18 px | 7 px | **136 mm** (~23 % av torsohöjd) | 5,2 mm | JA |

**Två saker syns direkt:**
- **Sensorprecisionen (mm) är ≪ zonstorleken (dm) på ALLA avstånd** → systemet kan alltid avgöra
  *vilken* zon (huvud/torso) du träffar — så länge konstellationen syns (dagsljus-mätpunkten).
- **Hållpunkten växer kraftigt med avstånd:** på 25 m siktar du ~mitt på; på 150 m måste du hålla
  **~en huvudhöjd över** torson. Det är detta som gör att du **måste sikta**.

## 4. Rörligt mål (lead) — beräknat
Lead-vinkel = **v_mål / v0** (oberoende av avstånd); lead-distans = v_mål × R / v0:

| Målfart | lead-vinkel | lead @25 m | @75 m | @150 m |
|---|---|---|---|---|
| 5 m/s | 0,32° | 139 mm | 417 mm | 833 mm |
| 10 m/s | 0,64° | 278 mm | 833 mm | 1667 mm |

Mekanik (uppskjuten flygtids-bedömning): skottlinjen låses i världsram vid avtryck (IMU håller den
fast under recoil), kameran spårar målet under flygtiden (~167 ms @150 m = 20 frames @120 fps),
**träff om linjen skär målets verkliga läge när kulan anländer**. Siktar du där målet *är* → miss;
leder du rätt → träff. Lead-vinkeln är liten (≪ FOV) så målet lämnar aldrig bild pga lead.

## 5. Svar: ska västen ha samma kort (ESP32-P4-WIFI6)?
**Nej — rekommendation: väst-noden = ESP32-C5 (eller C6), INTE P4.** Ärliga skäl:
- **Västen har ingen kamera/vision** → P4:ans tunga compute (120 fps-bildbehandling, PnP) är bortkastad.
- **ESP32-P4 har ingen egen WiFi-radio** — "P4-WIFI6"-modulen lägger till WiFi via en **ESP32-C6-
  medprocessor**. Att sätta P4 på västen = bära P4 + C6 för ett jobb som en ensam **C5/C6 gör nativt**.
- Västen är en **bärbar batterienhet** → vill ha litet, billigt, lågeffekt. C5 ≈ $1–2, P4-modul ≈ $10–15
  och 1–2 W. Fel verktyg för en väst.
- **Auto-parning funkar ändå:** ESP-NOW / WiFi6 parar vapnets P4(+C6) med västens C5 **oberoende av
  att det är olika kisel** — samma Espressif-radiostack. Du behöver alltså inte samma chip för att de
  ska hitta varandra automatiskt.

Västens jobb (OR:a TSOP-DATA = zon, blinka LED_EN = konstellations-ID/frame-synk, GNSS, WiFi-comms)
är lätt → **C5 räcker med marginal**. (Vill du ha EN gemensam radiokod/toolchain är C6 ett alternativ;
samma slutsats — inte P4.)

## 6. Ärliga mätpunkter (oförändrade)
- **Dagsljus-SNR @150 m** för 860 nm-konstellationen — störst; allt hänger på den.
- **TSOP-räckvidd @150 m** i sol (940 nm bandpass) — bänk/fält.
- **Zon-granularitet** (antal väst-patchar) vs önskad upplösning.
- **Recoil-aktuator + latens/spårning** under flygtidsfönstret (lead-robusthet).

## TL;DR
Korten passar ihop (940 nm skott ↔ TSOP, 860 nm konstellation ↔ kamera). Träffen avgörs av **kameran +
ditt sikte** (hållover växer från ~0 @25 m till ~en huvudhöjd @150 m; lead krävs för rörliga mål) —
den breda skott-strålen gatar bara LOS. Sensorn är mm-precis (ser alltid zonen); **du** är begränsningen.
Västen ska köra **ESP32-C5/C6, inte P4** — den parar ändå automatiskt med vapnet över WiFi6/ESP-NOW.
