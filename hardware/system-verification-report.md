# STRILAS — Fysik-verifiering @ 150 m (rapport)

Numerisk end-to-end-verifiering av hela kedjan med **exakta komponenter och datablad-
värden**, inga genvägar. Körs av [`system_physics_verification.py`](system_physics_verification.py)
(Monte Carlo + radiometri + länkbudget + ballistik). Konstellation på kroppsfigur **150 m** bort.

## Antaganden (explicita)

Kamera **OV9281 mono global shutter NoIR** (px 3,0 µm, 1280×800, QE@860≈0,25, FW 8000 e⁻,
läsbrus 3 e⁻) · **12 mm M12-lins**/F2 (18,2° H — se nedan) · 860 nm bandpass (FWHM 12 nm, τ 0,7) ·
konstellation 5× 860 nm @ 0,30 W/sr i kroppsgeometri · sol 0,9 W/m²/nm, scen ρ 0,3 ·
ICM-45686 gyro 3,8 m°/s/√Hz · skott **2× Vishay VSMA1094750X02 (940 nm)** + TIR-kollimator
(räknat konservativt 1,08 W/A; verkligt ≈1,68) · TSOP-tröskel 0,35 mW/m² ×30 sol ÷4 bandpass ·
5.56 v0 880 m/s.

## Resultat

| # | Steg | Utfall | Nyckeltal |
|---|---|---|---|
| 1 | Framing / FOV | ✅ | konstellation 0,12°×0,26° i FOV; vertikal baslinje **18 px** |
| 2 | Kamera-detektion (dagsljus) | ✅ | **SNR 87** @ 30 µs exp (mono+3µm, 6mm-apertur; mättar vid längre → kort exp) |
| 3 | Bäringsprecision (MC) | ✅ | **σ = 0,0009°** ≪ krav 0,076° (huvud) / 0,191° (torso) |
| 4 | PnP-range | ✅ | **σ = 1,0 m** (0,67 %) @ 150 m |
| 5 | IMU inter-frame | ✅ | drift **~0,0005°** @ 60 fps → **1 IMU räcker** (array = ren reserv) |
| 6 | IR-skott → TSOP @ 150 m | ✅* | **VALT: medium TIR @ ~2 A → 153 m** (kompakt 42×62-kort) |
| 7 | Ögonsäkerhet | ⚠️ mätpunkt | pt-källa 18× över; **extended-source täcker** → måste mätas |
| 8 | Ballistik | ✅ | flygtid 188 ms, drop **16 cm**, lead (3 m/s) 56 cm — modelleras |
| 9 | End-to-end träff (MC) | ✅ | **100 % torso**, sidled-RMS **0,2 cm** @ 150 m |

## ⚠️ Linsval: 12 mm krävs för 150 m (inte 6 mm)

Fysiken avslöjar en hård gräns: **OV9281 är 1 MP (1280×800).** Med den tidigare påtänkta
**6 mm-linsen (35,5° FOV)** subtenderar konstellationen bara **~9 px @ 150 m** → LED:erna
hamnar 2–4 px isär och **smälter ihop till en blob** (blob-detektionen hittar 1 i st.f. 5, och
range-baslinjen kollapsar). Det är inte en mjukvarubugg utan informationsbrist i bilden.
**Lösning: 12 mm M12-lins (18,2° FOV)** → ~8 px LED-separation + 18 px vertikal baslinje →
ren blob-detektion och robust PnP. 6 mm duger till robust räckvidd ~80 m; **för 150 m: 12 mm.**
(PCB:t påverkas inte — kameran är mekanisk/USB bakom Ø16-hålet, oberoende av brännvidd.)

## Tolkning

**Precisionskedjan håller med enorm marginal (med 12 mm-linsen).** Den låsta sensorn
(**OV9281 mono global shutter**) ser konstellationen vid 150 m i dagsljus med **SNR 87** vid
kort exponering — mono utan Bayer-filter + 3 µm-pixlar + 6 mm-apertur (12 mm/F2) ger gott om
signal, och global shutter eliminerar pan-smet direkt (ingen mjukvarugrind behövs). Bäringen
blir ~**0,0009°**, ~85× bättre än vad som krävs för att upplösa ett huvud (0,076°). Ballistiken
(drop/lead) modelleras exakt, och Monte Carlo ger **100 % torso-träff** med ~0,2 cm sidled-RMS.
IMU-driften mellan bildrutor är försumbar → bekräftar att **1 IMU räcker** (4-arrayen = ren reserv).

**Emitter/optik-val: 2× Vishay VSMA1094750X02 (940 nm) + medium TIR-kollimator (≤±7,5°),
~2 A pulsat, kompakt 42×62-kort.** Viktig insikt: **ögonexponeringen sätts av räckviddskravet,
inte av linsen.** För 150 m krävs ~Ie 59 W/sr oavsett lins/ström-kombo; medium @ 2 A ger
Ie ≈ 61 → **nära minsta möjliga exponering**. (Narrow @ 1 A ger Ie 72 = mer marginal men
*högre* exponering.) Den valda Vishay-emittern är 940 nm (TSOP-topp + kamerans 860 nm-bandpass
avvisar egen stråle → ingen självbländning) och tål 1,5 A DC / 5 A pulsat → 2 A pulsat ligger
väl inom rating.

**Enda kvarvarande villkoret:** **ögonsäkerhet** — 18× över *punktkälle*-MPE, men **extended-
source-relaxationen (~67×) täcker** → **måste mätas** (skenbar källa/AE per IEC 60825-1).

## Slutsats

Systemet är **fysikaliskt sunt @ 150 m**. Allt som rör *precision* (det som gör det till mer
än laser tag) verifieras med stor marginal med de exakta, låsta komponenterna. Det enda som
inte kan *avgöras* i simulering är **ögonsäkerheten** — den kräver en bänkmätning (utpekad
mätpunkt). Driftpunkt (vald): **2× Vishay 940 nm + medium TIR + ~2 A + kort kameraexp (30 µs)**,
kompakt 42×62-kort.

> Detta är en simulering med trogna modeller — inte ett substitut för bänkmätning av AE,
> dagsljus-SNR och räckvidd. Men varje länk är räknad ur fysik/datablad, inte antagen.
