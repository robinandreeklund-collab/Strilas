# STRILAS — väst/hjälm zonschema & hur många zoner

> Figur: [`zonschema.png`](zonschema.png) · jfr [`system-simulering.md`](system-simulering.md)

## Layout (din vision, bekräftad)
- **Väst FRAM:** 5 patchar (4 hörn + 1 centrum). **Väst BAK:** identiskt 5 patchar → 360° täckning.
- Varje patch: **3× TSOP4856** (940 nm skott) + **2× 860 nm** (konstellation) + OR-dioder → 1 DATA-linje.
- **Hjälm-halo:** 8× TSOP radiellt (360° huvud-träff) + **860 nm-konstellation HÖGT på ringen**
  (syns för skyttens kamera från många vinklar) + GNSS i mitten (uppåt).

## Hur många zoner? — två svar (de gör olika saker)

### A) Kamera/P4-zoner (FINA, mjukvara) — **i praktiken obegränsat**
P4:an sitter på **vapnet** och löser PnP ur konstellationen → spelarens **6-DOF-pose**. Den mappar
träffpunkten på spelarens **3D-modell** → du kan dela in kroppen i **vilka zoner du vill** i mjukvara.
Gränsen är bara att zonen måste vara större än bäringsprecisionen:

| Avstånd | bäring 1σ | minsta säkra zon (~3σ) |
|---|---|---|
| 25 m | 0,9 mm | ~3 mm |
| 75 m | 2,6 mm | ~8 mm |
| 150 m | 5,2 mm | ~16 mm |

Kroppszoner är **decimeter**, tröskeln är **millimeter** → **8–16 anatomiska zoner** (huvud, vä/hö
bröst, vä/hö mage, vä/hö arm, ben…) är glasklart särskiljbara hela vägen till 150 m. **P4:an är
alltså INTE begränsningen** — den kan i princip peka ut var som helst på kroppen.

> Verklig gräns för de fina zonerna = **pose-noggrannheten** (hur väl konstellationen syns/ej skyms),
> inte P4:ans compute. Med 5+5 patchar (≈20 konstellations-LED) blir posen mycket robust.

### B) Fysiska TSOP-patch-zoner (LOS-gate + fallback) — satt av patchantal, inte P4
Varje patch = 1 DATA-linje till **väst-noden (ESP32-C5)**. 5 fram + 5 bak + hjälm = **11 DATA-linjer**.
C5 har ~28 GPIO → läser 11 med god marginal (klarar **20+ patchar** om du vill). Dessa ger:
- **LOS/anti-fusk:** strålen nådde faktiskt fram (inte genom vägg).
- **Robust grov-zon** även om kameran tappar konstellationen (fallback).

## Slutsats
- **Antal zoner begränsas inte av P4:an** utan av (a) hur fint du vill dela in 3D-modellen
  (kamera-sidan, mm-precist → 8–16+ zoner lätt) och (b) hur många TSOP-patchar du fysiskt sätter
  (LOS-sidan, C5 klarar 20+).
- Praktisk rekommendation: **10 väst-patchar (5+5) + hjälm-halo** ger 360° täckning, ~20 konstellations-
  punkter för stark pose, och en robust grov-zonkarta — medan kamera/P4 ger den fina träffzonen
  (huvud/bröst/mage vä/hö) ovanpå.
- Helt i linje med tidigare: **väst-nod = ESP32-C5** (inte P4 — ingen kamera på spelaren).

## Mätpunkter (oförändrade)
- Konstellations-synlighet @150 m i dagsljus (störst) · TSOP-räckvidd @150 m · pose-robusthet vid
  delvis skymd konstellation (sätter hur fina zoner som håller i strid).
