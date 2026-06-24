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
   **3A-OVERRIDE (2026-06):** montera-för-3A-motstånd **R3 (Rp=0R1, 0805, DNP)** parallellt direkt
   över R2 (sense) → Rsense 0,2→0,067 Ω → I_max ≈ **3,0 A**. Kraft-HW (Rp, F1=PTC_3A, spår) 3A-klassad;
   default **DNP/obestyckat = 1 A** (säker fail-safe — kortet levereras som 1 A). 3 A kräver **medveten
   montering av R3 + förnyad mätning**. (Optikkortet är för tätt för en separat bygel vid sense-noden;
   ett DNP-motstånd är platsfritt, ligger >4,6 mm från linshålskanten och täcker inte kamera-aperturen.)
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

---

# Konstellations-emitter (850 nm Lumileds L1I0, väst-patch + hjälm-mb) — FIRMWARE-TRIMBAR CC-sänka

> Separat hazard från skott-emittern: **850 nm, 90° vidvinkel** (kamera-markör, LUXEON IR Domed).
> Ingen lins-koncentration → irradiansen vid given ström är **mycket lägre** än den kollimerade
> skott-strålen. Men 850 nm är näIR-näthinnefarligt vid hög effekt → samma HW-tak-princip gäller.
>
> **⚠️ LED-BYTE VSMY98545 → Lumileds L1I0-0850090200000 (2026-06):** L1I0 ger **~750 mW/sr@1A ≈ 2× VSMY:s
> 380 mW/sr**. Det betyder att **den ögonsäkra strömmen ungefär HALVERAS** mot VSMY-budgeten nedan — det HÅRDA
> 1 A-taket står kvar (säkert), men den uppmätta säkra DRIFTPUNKTEN blir lägre. *Netto positivt för räckvidd:*
> du når samma räckvidd som VSMY vid ~halva strömmen → större eye-safety-marginal. L1I0 tål 1,5 A DC / 5 A puls
> (200000-variant), Vf~3,2 V@1A (tightare 2S-headroom → firmware-LV-spärr ~7,2 V). **Kräver förnyad IEC 60825-1-
> mätning med L1I0 innan modulen riktas mot människor** — siffrorna nedan är VSMY-baserade och konservativa nu.
>
> **STATUS:** Realiserat på BÅDA korten — **väst-patch** (×14; U5/Q1/R6 etc.) OCH **hjälm-mb:s egna 6
> navmarkör-LED** (U9/Q1/R14 etc.). Hjälm-mb routades INKREMENTELLT (`hardware/helmet_cc_sink.py`,
> bevarar de 886 befintliga spåren) eftersom full freerouting hänger på det tätt routade 4-lagers-kortet.

## Topologi (2026-06, ersätter passiv 10R-strömsättning)

Samma aktiva CC-sänka som skott-emittern, men **referensen är nu FIRMWARE-STYRD**:
- **U5 = OPA171** + **Q1 pass-FET (AO3400)** + **R6 = 0R2 sense** → I = Vref/Rsense.
- **Vref = LED_EN** (moderkortets broadcast-GPIO) körd som **FILTRERAD LEDC-PWM**: R8(15k)/R9(1k)-
  delare + C6(100nF) → RC ~94 µs släpper blink (≤120 Hz kamera-fps) men filtrerar PWM-bärvågen.
- **Delaren 15k/1k är SAMTIDIGT det HÅRDA TAKET:** Vref_max = 3,3·1/16 = 0,206 V → **I_max = 1,0 A**
  (R6 = 0R2). Firmware sätter PWM-duty 0–100 % → I **0–1,0 A STEGLÖST** men kan **ALDRIG** överstiga
  taket (eye-safety-regel #1 i HÅRDVARA — firmware-bugg/full duty ger fortfarande ≤1 A).
- **3A-override:** montera DNP **R7 = 0R1** parallellt över R6 → 0,2∥0,1 = 0,067 Ω → I_max ≈ 3 A.
  Default **DNP/obestyckat = 1 A** (säker fail-safe, levereras så). 3 A = medvetet labbeslut, kräver
  **förnyad IEC 60825-1-mätning + branch-balans-R-termik-koll** (R3-R5 = 1R 1206: 1 A/gren → 1 W → uppgradera).

## ⚠️ FIRMWARE-KONTRAKT — LED_EN är nu ANALOG setpunkt, EJ digital enable

`LED_EN` (vest-mb GPIO7 / helmet-mb GPIO2, broadcast till alla konstellations-drivare) drivs nu som
**LEDC-PWM**, INTE en på/av-GPIO. **Ström ∝ PWM-duty** (filtrerad). Blink/identifiering görs genom att
släppa duty till 0 i blink-takten (RC släpper ≤120 Hz). PWM-bärvåg ≥100 kHz (filtreras av RC). Varje
kort har egen CC-sänka → **självreglerar oavsett kabellängd** (ingen kalibrering per patch).

## Design-regler (konstellation)

1. **Börja LÅGT** (duty f. ~0,3 A) vid bringup; öka stegvis och **MÄT** accessible emission + skenbar
   källa per IEC 60825-1 **innan** patchar/hjälmar bärs mot människor.
2. HW-taket (R6 + 15k/1k) = hård barriär; firmware kan bara gå lägre. 3 A endast via medveten R7-montering.
3. L1I0 (~2× VSMY mW/sr) når räckvidd vid LÄGRE ström — **varje strömnivå/LED-byte kräver ommätning**
   (OSLON 0,5A → VSMY → L1I0: Ie/A ökar nu kraftigt → KÖR LÄGRE ström, mät om den säkra punkten).
