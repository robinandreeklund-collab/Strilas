# STRILAS — Fysik-verifiering @ 150 m (rapport)

Numerisk end-to-end-verifiering av hela kedjan med **exakta komponenter och datablad-
värden**, inga genvägar. Körs av [`system_physics_verification.py`](system_physics_verification.py)
(Monte Carlo + radiometri + länkbudget + ballistik). Konstellation på kroppsfigur **150 m** bort.

## Antaganden (explicita)

OV5640 (px 1,4 µm, 2592×1944, QE@860≈0,12, FW 6000 e⁻, läsbrus 3 e⁻) · M12 FOV 18° (f≈11,5 mm) F/2 ·
860 nm bandpass (FWHM 12 nm, τ 0,7) · konstellation 5× 860 nm @ 0,30 W/sr i kroppsgeometri ·
sol 0,9 W/m²/nm, scen ρ 0,3 · ICM-45686 gyro 3,8 m°/s/√Hz · skott 2× 940 nm OSLON + Carclo · TSOP
tröskel 0,35 mW/m² ×30 sol ÷4 bandpass · 5.56 v0 880 m/s.

## Resultat

| # | Steg | Utfall | Nyckeltal |
|---|---|---|---|
| 1 | Framing / FOV | ✅ | konstellation 0,12°×0,26° i FOV; vertikal baslinje **37 px** |
| 2 | Kamera-detektion (dagsljus) | ✅ | **SNR 58** @ 30 µs exp (mättar vid längre → kort exp = ingen rolling-smet) |
| 3 | Bäringsprecision (MC) | ✅ | **σ = 0,0004°** ≪ krav 0,076° (huvud) / 0,191° (torso) |
| 4 | PnP-range | ✅ | **σ = 0,49 m** (0,33 %) @ 150 m |
| 5 | IMU inter-frame | ✅ | drift **0,0005°** @ 60 fps → **1 IMU räcker** (array = ren reserv) |
| 6 | IR-skott → TSOP @ 150 m | ✅* | **narrow Carclo @ 1 A → 166 m** (medium/1 A når bara 111 m) |
| 7 | Ögonsäkerhet | ⚠️ mätpunkt | pt-källa 22× över; **extended-source täcker** → måste mätas |
| 8 | Ballistik | ✅ | flygtid 188 ms, drop **16 cm**, lead (3 m/s) 56 cm — modelleras |
| 9 | End-to-end träff (MC) | ✅ | **100 % torso**, sidled-RMS **0,1 cm** @ 150 m |

## Tolkning

**Precisionskedjan håller med enorm marginal.** Kameran ser konstellationen vid 150 m i
dagsljus (SNR ≫, så stark att man kör *kort* exponering → eliminerar rolling-shutter-smet
— en oväntad synergi som gör OV5640 mer än tillräcklig). Bäringen blir ~0,0004°, ~500× bättre
än vad som krävs för att upplösa ett huvud. Ballistiken (drop/lead) modelleras exakt, och
Monte Carlo ger 100 % torso-träff med 1 mm sidled-RMS. IMU-driften mellan bildrutor är
försumbar → bekräftar att **1 IMU räcker** (4-arrayen är ren reserv).

**De två kopplade villkoren** (samma som hela tiden):
1. **IR-skottets räckvidd @ 150 m** kräver **narrow-lins (Carclo 10048)** — då räcker **~1 A**
   (166 m). Medium-lins/1 A når bara 111 m. → välj narrow-lins, håll strömmen låg.
2. **Ögonsäkerhet** vid den strömmen: 22× över *punktkälle*-MPE, men **extended-source-
   relaxationen (~67×) täcker** — vilket **måste mätas** (skenbar källa/AE per IEC 60825-1).

## Slutsats

Systemet är **fysikaliskt sunt @ 150 m**. Allt som rör *precision* (det som gör det till mer
än laser tag) verifieras med stor marginal med de exakta komponenterna. Det enda som inte kan
*avgöras* i simulering är **ögonsäkerheten** — den kräver en bänkmätning (utpekad mätpunkt).
Rekommenderad driftpunkt: **narrow Carclo + ~1 A + kort kameraexp (30 µs)**.

> Detta är en simulering med trogna modeller — inte ett substitut för bänkmätning av AE,
> dagsljus-SNR och räckvidd. Men varje länk är räknad ur fysik/datablad, inte antagen.
