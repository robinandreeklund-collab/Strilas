# STRILAS — uppdaterad precisionsanalys: IIM-42653 + 120 fps (FÖRSLAG)

> Figur: [`precision-iim42653.png`](precision-iim42653.png) · bygger på [`precision-analys.md`](precision-analys.md)
> **Status:** förhandsanalys av föreslagen ändring; korten bär fortfarande **ICM-42670-P** tills
> bytet görs. **Pinout OCH alla elektriska tal nu LÅSTA mot DS-000529** (gyro/accel-spec-sidorna).
> Inga uppskattningar kvar på IMU-sidan.

## IIM-42653 verifierade tal (DS-000529)
| Gyro | Värde | | Accel | Värde |
|---|---|---|---|---|
| Rate Noise Spectral Density | **0,005 °/s/√Hz** | | brus (X/Y) | 65 µg/√Hz |
| Scale-factor init. tolerans | **±0,5 %** | | scale-factor init. | ±0,5 % |
| Scale-factor över temp | ±0,005 %/°C | | zero-g | ±20 mg |
| ZRO (bias) | ±0,5 °/s, ±0,04 °/s/°C | | FSR | ±4 / 8 / 16 / 32 g |
| Nonlinjäritet / cross-axis | ±0,1 % / ±1,25 % | | | |
| FSR | **±4000 … ±31,25 dps** | | temp / shock | −40…+105 °C / 20 000 g |
| I²C-adress (AD0) | 0x68 / 0x69 | | | bekräftar FC dual-IMU |

*(RNSD 0,005 är något högre än ICM-42688:s 0,0028 — priset för ±4000 dps FSR — men försumbart i
bryggan. Vinsten: ±0,5 % skalfaktor + ±4000 dps + industri-temp/shock.)*

## Pinout — VERIFIERAD drop-in (DS-000529, IIM-42653)
De 8 signalstift vår design använder är **identiska** med ICM-42670/42688-footprinten:
`1=AP_SDO(MISO) · 4=INT1 · 5=VDDIO · 6=GND · 8=VDD · 12=AP_CS · 13=AP_SCLK · 14=AP_SDI(MOSI)`.
Skillnad: stift **2/3/10/11 = AUX1** (sekundär SPI, oanvänd → NC) i stället för RESV; **7=RESV**
(vår pin7→GND giltig); **9=INT2/FSYNC/CLKIN** (NC). I²C på FC oförändrat (12=AP_CS→VDDIO, 1=AD0).
→ **Ingen omdragning** — endast värde/MPN byts. ±4000 dps · ±32g · −40…+105 °C · 20 000 g bekräftat.

## Vad som ändras
| | Nu (på kortet) | Föreslaget |
|---|---|---|
| IMU | ICM-42670-P (verifierad: gyro 0,007 °/s/√Hz, ±2000 dps, ±1 °/s ZRO) | **IIM-42653** (industri/AEC-Q100, **±4000 dps**, ultralågt brus, stram skalfaktor) |
| Kamera | OV9281 (antog 60 fps) | OV9281 **120 fps**, **low-distortion M12** (bekräftat av produktlänk) |

Allt övrigt (16 mm-lins, 0,0107 °/px, PnP-konstellation, arkitektur "kameran = sikte") oförändrat.
Skala: **1° = 2 618 mm @150 m**.

## 1. Steady-state (mål i bild) — var redan litet, blir lite bättre
| Felkälla | nu | föreslaget | not |
|---|---|---|---|
| Centroid-brus (0,1 px) | 2,8 mm | 2,8 mm | SNR-/optikberoende, oförändrat |
| Intrinsisk kalib-rest | 5,2 mm | **3,9 mm** | low-distortion-lins → modellen passar bättre *(uppskattning, kalibreringsberoende)* |
| IMU mellan-frame-brygga | 2,4 mm | **1,2 mm** | 120 fps + RNSD 0,005 °/s/√Hz (LÅST) |
| Avstånd→hållpunkt (±0,9 m) | 1,6 mm | 1,6 mm | d(fall)/dR ≈ 1,8 mm/m |
| **RSS** | **≈ 6,6 mm** | **≈ 5,2 mm** | |

**Slutsats oförändrad:** sensorbruset (~5 mm 1σ) är ~27× mindre än hållpunkten (140 mm).
Det är fortfarande **siktet som avgör träff, inte elektroniken** — den önskade "måste-sikta"-känslan.
Steady-state var alltså aldrig problemet; uppgraderingen ger marginal, inte räddning.

## 2. Recoil — här gör IIM-42653 + 120 fps verklig nytta
Det här var systemets svaghet. Tre konkreta vinster:

1. **±4000 dps FSR = ingen gyro-mättning (binär vinst).** En skarp recoil-puls kan toppa
   över ±2000 dps; mättar gyrot blir integrationen under bryggan skräp. ±4000 dps tar bort
   den failure-moden helt. *(Detta är säkert — det är en FSR-siffra, inte en gissning.)*
2. **Stram industri-skalfaktor minskar ur-FOV-dödräkningen.** Felet när målet lämnar bild
   = skalfaktorfel × integrerad vinkel:
   | ur FOV | konsument ~1 % | konsument ~3 % | **industri ~0,5 %** (IIM, låses) |
   |---|---|---|---|
   | 10° | 262 mm | 785 mm | **131 mm** |
   | 20° | 524 mm | 1571 mm | **262 mm** |
   → ~2–6× mindre transient. *(±0,5 % nu LÅST ur DS-000529; över temp endast ±0,005 %/°C extra.)*
3. **120 fps → kortare brygga + halverat oskärpefönster.** Re-ankring var 8,3 ms (mot 16,7);
   målet hålls låst genom mer av recoilen → kortare/ingen dödräkning.

**MEN — ärligt:** ur-FOV-felet **försvinner inte**. En bättre IMU och 120 fps **minskar** det,
men den verkliga fixen är att **hålla målet i bild**: kort exponering (≤100 µs), ev. något
bredare FOV, begränsad recoil-amplitud, och regeln "**skottet landar/adjungeras vid återlås**".
IIM-42653 köper marginal, inte mirakel.

## 3. Det IMU-bytet INTE rör (oförändrade risker)
- **Dagsljus-SNR @150 m (fortfarande #1, overifierad).** Syns målets modulerade 860 nm-konstellation
  mot solsken på 150 m? IMU:n påverkar inte detta alls. **120 fps gör det dessutom något svårare**
  (kortare exponering per frame = mindre ljus) — en avvägning att mäta vid bringup.
- **Kalibrering** (intrinsisk + ev. extrinsisk) — fortfarande en mätpunkt.
- **Recoil-aktuatorn** — obyggd; verkliga rate/amplitud okända.

## 4. Gun-emittern (SFH4725S, 1→3 A) — separat från sikt-precisionen
Viktigt att inte blanda ihop: gun-emittern är **skottet** (940 nm). Den påverkar
- **skott-räckvidd/registrering** (hur säkert målet/servern tar emot skott-ID:t på 150 m) och
- **ögonsäkerhet** (IEC 60825-1) — design-resolution §3: vid 1 A ~54 W/sr, ~2,1 mW in i öga @1 m;
  konservativt Class 1 ~0,1 A full-auto / 0,67 A semi, men utsträckt-källa-relaxation kan tillåta
  1–3 A **om uppmätt**. → Att gå mot 3 A är en **mät- och säkerhetsfråga**, inte en precisionsfråga.

Den påverkar **inte** kamerans bäring/avstånd (det är målets 860 nm-konstellation). Om man vill
köpa **detektionsräckvidd/SNR @150 m** är hävstången målets **konstellations-LED-effekt** +
exponering + FOV — inte gun-emittern.

## TL;DR
IIM-42653 + 120 fps är rätt uppgradering, men av rätt skäl: steady-state var redan bra (~5 mm),
**vinsten ligger i recoil** — ±4000 dps tar bort mättningsrisken (säker vinst), industri-skalfaktor
+ 120 fps minskar ur-FOV-dödräkningen ~2–6×. Den eliminerar den dock inte; att hålla målet i bild
(FOV/exponering/återlås) är fortfarande den verkliga fixen, och **dagsljus-SNR @150 m är kvar som
största overifierade risken** — orörd av IMU-bytet. Exakta IIM-42653-tal + pinout låses mot
databladet innan vi ändrar korten.
