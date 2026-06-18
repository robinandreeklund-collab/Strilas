# STRILAS — Class 1-ögonsäkerhets-strömbudget (skott-emitter, 940 nm)

> **Ingenjörsestimat** för att sätta konservativ start-/HW-tak-ström. **Ersätter inte**
> en formell IEC 60825-1-mätning — slutlig Class 1 kräver uppmätt accessible emission vid
> aperturen, vid låst pulsformat. Beräknad av [`eye_safety_budget.py`](eye_safety_budget.py)
> (parametrisk — stoppa in dina uppmätta värden).

## Antaganden

2× LED, 80 % lins-effektivitet, ±7,5° kon (Carclo 10195), eval @ **100 mm** (IEC Condition 3),
7 mm pupill. Pulsduty: **semi 1,4 %**, **full-auto 9,1 %** (56 kHz-bärvåg × paket × repetition).
λ = 940 nm → C4 = 3,02. Konservativ punktkälle-MPE ≈ **30,6 W/m²** (medel, ~10 s).

## Resultat (konservativ punktkälla, C6 = 1)

| Ström | Ie [W/sr] | E@100 mm | Eavg full-auto | verdikt |
|---|---|---|---|---|
| 0,25 A | 8,3 | 834 | 76 | 2,5× över |
| 0,50 A | 16,5 | 1648 | 150 | 4,9× över |
| 1,0 A | 32,1 | 3215 | 293 | 9,6× över |
| 3,0 A | 86,8 | 8680 | 790 | 25,8× över |

**Max ström för Class 1 (punktkälla):** full-auto **~0,10 A**, semi **~0,67 A**.

## Den avgörande nyansen: utsträckt källa (C6)

Punktkälle-antagandet är **worst case** och dödar räckvidd. Men en **LED + lins är en
utsträckt källa**. Om den uppmätta **skenbara källan ≥ α_max (100 mrad)** relaxeras taket
**~67×** → då blir **1–3 A Class 1 med marginal** (full-auto-tak ~6,7 A, semi ~44 A).

→ **Svaret hänger helt på den skenbara källstorleken.** Det är därför mätning krävs:
- Skenbar källa = liten LED-die imagead → nära punktkälla → restriktivt.
- Skenbar källa = fylld linsöppning (Ø20 @ 100 mm = 200 mrad) → full relaxation.

## Design-regler (beslutade)

1. **HW-strömtak** via sense-resistor (firmware kan bara gå lägre) — "ögonsäkerhet i hårdvara".
   **REALISERAT** (2026-06): aktiv CC-sänka (U2=OPA171 + DPAK-FET + R2=0R2 sense) i optik-netlistan.
   Hård gräns I = Vref/Rsense; Vref ≤ 0,206 V (3,3 V-delaren 15k/1k) → **default I_max ≈ 1,0 A** (R2=0R2).
   **3A-OVERRIDE (2026-06):** låg solder-jumper JP1 (default OPEN = säker) bryggas → parallellkopplar
   Rp=0R1 över R2 → Rsense 0,2→0,067 Ω → I_max ≈ **3,0 A**. Kraft-HW (Rp, F1=PTC_3A, spår) 3A-klassad;
   jumpern **fail-safe** (obryggad/tappad = 1 A). 3 A kräver **medveten bryggning + förnyad mätning**.
   - **Headroom (2S, 2 emittrar i SERIE):** 3 A behöver VBAT > 2·Vf(3A)+Vsense ≈ 7,1 V → håller bara i
     övre 2S-delen; firmware-LV-spärr ~7,5 V @3 A (~6,9 V @1 A).
   - **Emitter:** SFH 4725S utgången → **SFH 4725AS** (samma paket/footprint/optik, drop-in; puls-max
     3 A @ tp≤800µs; vårt ~9µs/≤9,1% duty ligger inom kurvan, men 3 A = emitterns abs-tak).
2. **Börja på 0,5–1 A** vid bringup.
3. **Cap full-auto-duty** i firmware (semi är ~6–7× snällare).
4. **2 separata emittrar** = 2 skenbara källor → var och en lägre exponering.
5. **MÄT** AE + skenbar källa per IEC 60825-1 (inkl. enkelpuls + pulståg-N^(-1/4)) **innan**
   modulen riktas mot människor. Köp räckvidd med mottagar-bandpass före mer ström.

## Slutsats

Med konservativ punktkälla är vi **inte** Class 1 vid räckviddsström — men extended-source-
relaxationen täcker troligen 1–3 A. **Det måste mätas**, inte antas. HW-taket + duty-cap +
2-emitter-splitten är de hårda skyddsbarriärerna oavsett mätutfall.
