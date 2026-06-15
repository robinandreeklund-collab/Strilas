# STRILAS — Fysik-verifiering @ 150 m (rapport)

Numerisk end-to-end-verifiering av hela kedjan med **exakta komponenter och datablad-
värden**, inga genvägar. Körs av [`system_physics_verification.py`](system_physics_verification.py)
(Monte Carlo + radiometri + länkbudget + ballistik). Konstellation på kroppsfigur **150 m** bort.

## Antaganden (explicita)

OV5647 (px 1,4 µm, 2592×1944, QE@860≈0,12, FW 6000 e⁻, läsbrus 3 e⁻) · M12 6mm/F2 (~33° H, NoIR-krav) ·
860 nm bandpass (FWHM 12 nm, τ 0,7) · konstellation 5× 860 nm @ 0,30 W/sr i kroppsgeometri ·
sol 0,9 W/m²/nm, scen ρ 0,3 · ICM-45686 gyro 3,8 m°/s/√Hz · skott 2× 940 nm OSLON + Carclo · TSOP
tröskel 0,35 mW/m² ×30 sol ÷4 bandpass · 5.56 v0 880 m/s.

## Resultat

| # | Steg | Utfall | Nyckeltal |
|---|---|---|---|
| 1 | Framing / FOV | ✅ | konstellation 0,12°×0,26° i FOV; vertikal baslinje **37 px** |
| 2 | Kamera-detektion (dagsljus) | ✅ | **SNR 30** @ 30 µs exp (mättar vid längre → kort exp = ingen rolling-smet) |
| 3 | Bäringsprecision (MC) | ✅ | **σ = 0,0008°** ≪ krav 0,076° (huvud) / 0,191° (torso) |
| 4 | PnP-range | ✅ | **σ = 0,49 m** (0,33 %) @ 150 m |
| 5 | IMU inter-frame | ✅ | drift **0,0005°** @ 60 fps → **1 IMU räcker** (array = ren reserv) |
| 6 | IR-skott → TSOP @ 150 m | ✅* | **VALT: medium 10195 @ ~2 A → 153 m** (kompakt 42×62-kort) |
| 7 | Ögonsäkerhet | ⚠️ mätpunkt | pt-källa 18× över; **extended-source täcker** → måste mätas |
| 8 | Ballistik | ✅ | flygtid 188 ms, drop **16 cm**, lead (3 m/s) 56 cm — modelleras |
| 9 | End-to-end träff (MC) | ✅ | **100 % torso**, sidled-RMS **0,1 cm** @ 150 m |

## Tolkning

**Precisionskedjan håller med enorm marginal.** Kameran ser konstellationen vid 150 m i
dagsljus (SNR ≫, så stark att man kör *kort* exponering → eliminerar rolling-shutter-smet
— en oväntad synergi som gör OV5647 mer än tillräcklig). Bäringen blir ~0,0008°, ~95× bättre
än vad som krävs för att upplösa ett huvud. Ballistiken (drop/lead) modelleras exakt, och
Monte Carlo ger 100 % torso-träff med 1 mm sidled-RMS. IMU-driften mellan bildrutor är
försumbar → bekräftar att **1 IMU räcker** (4-arrayen är ren reserv).

**Lins/kort-val: B — medium Carclo 10195 (Ø20), kompakt 42×62-kort, ~2 A för 150 m.**
Viktig insikt: **ögonexponeringen sätts av räckviddskravet, inte av linsen.** För 150 m krävs
~Ie 59 W/sr oavsett lins/ström-kombo; medium @ 2 A ger Ie ≈ 61 → **nära minsta möjliga
exponering**. (Narrow @ 1 A ger Ie 72 = mer marginal men *högre* exponering.) Så B ger kompakt
kort **och** nära-minimal ögonexponering.

**Enda kvarvarande villkoret:** **ögonsäkerhet** — 18× över *punktkälle*-MPE, men **extended-
source-relaxationen (~67×) täcker** → **måste mätas** (skenbar källa/AE per IEC 60825-1).

## Slutsats

Systemet är **fysikaliskt sunt @ 150 m**. Allt som rör *precision* (det som gör det till mer
än laser tag) verifieras med stor marginal med de exakta komponenterna. Det enda som inte kan
*avgöras* i simulering är **ögonsäkerheten** — den kräver en bänkmätning (utpekad mätpunkt).
Driftpunkt (vald): **medium Carclo 10195 + ~2 A + kort kameraexp (30 µs)**, kompakt 42×62-kort.

> Detta är en simulering med trogna modeller — inte ett substitut för bänkmätning av AE,
> dagsljus-SNR och räckvidd. Men varje länk är räknad ur fysik/datablad, inte antagen.
