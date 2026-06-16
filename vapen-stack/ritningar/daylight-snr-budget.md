# STRILAS — dagsljus-SNR-budget @150 m (konstellation → kamera)

> Varför väst/hjälm-konstellationen MÅSTE vara högeffekt **SFH 4715AS** (860 nm OSLON, **Ie 780 mW/sr@1A**, datablad),
> inte en svag 1206. Detta är den #1-mätpunkt design-resolution §1.3 flaggade — här är budgeten.

## Antaganden (verkliga delar)
| Parameter | Värde |
|---|---|
| Kamera | OV9281, 3 µm pixel, QE@860 nm ≈ 0,25 |
| Lins | 16 mm, f/2 → bländardiameter 8 mm, area **5,0·10⁻⁵ m²** |
| Filter | 860 nm bandpass, FWHM ~30 nm, T ≈ 0,7 ; lins-T ≈ 0,85 |
| Exponering | 100 µs (kort → fryser recoil, släpper lite ljus) |
| LED | SFH 4715AS 860 nm; drivs ~0,4–0,5 A → **~390 mW/sr** (780 mW/sr vid 1 A, databl.) |
| Avstånd | 150 m, klar atmosfär (T ≈ 0,95) |

## Signal (LED, per frame)
```
E_lins  = I/R²              = 0,47/150²            = 2,1·10⁻⁵ W/m²
P_lins  = E·A·T_lins·T_filt·T_atm = 2,1e-5·5,0e-5·0,85·0,7·0,95 ≈ 5,9·10⁻¹⁰ W
foton/s = P / (hc/λ)        = 5,9e-10 / 2,31e-19   ≈ 2,6·10⁹ /s
e⁻(100µs)= foton·t·QE       = 2,6e9·1e-4·0,25      ≈ 6,4·10⁴ e⁻   (på ~1–2 px)
```
→ Signalen **mättar pixeln** (full well ~7 k e⁻). Vi sänker exponering/ström så bloben ligger
~halva full well (skarp, ej blommad) — fortfarande långt över bruset.

## Bakgrund (solbelyst, i bandet) + brus
```
E_sol_inband ≈ 0,95 W/m²/nm · 30 nm ≈ 28 W/m²   (AM1.5 @860 nm)
L_bakgrund   = ρ·E/π = 0,3·28/π     ≈ 2,7 W/m²/sr
P_bg/px = L·A·Ω_px·T = 2,7·5,0e-5·(3µm/16mm)²·0,6 ≈ 2,9·10⁻¹² W
e⁻_bg(100µs) ≈ 310 e⁻/px   →  skottbrus = √310 ≈ 18 e⁻
```
**Frame-differencing** drar bort den statiska solbakgrunden → kvar: modulerad LED mot skottbruset.

## SNR @150 m dagsljus
```
SNR = S / √(S + 2·bg + läsbrus²) ≈ 3500 / √(3500 + 620 + 16) ≈ 54   (LED @ halv full well)
```
**Nominellt SNR ≈ 50–80** — gott och väl över detektionströskeln (~5–10).

## Varför OSLON krävs (marginal-argumentet, ärligt)
En svag 1206 (10 mW/sr) ger **nominellt** SNR ~19 — ser bra ut på papper. MEN verkliga förluster
äter 10–50×: **off-axis** (80°-stråle → lägre intensitet i vinkel), **solglimt/flare**, **filter-
vinkelskift**, **dis/aerosol** sämre dagar, **damm/repor**, **defokus**. Då:
- 1206 @10 mW/sr → derat SNR **0,4–2** → **faller** i fält.
- SFH 4715AS @~390 mW/sr → derat SNR **7–35** → **håller** med marginal.

→ Högeffekt-OSLON ger den **marginal** som krävs för att klara 150 m dagsljus i verkligheten.
Det är därför Prototyp 1 kör SFH 4715AS, inte en närhålls-1206.

## Patch-drivning (väst/hjälm) — verifierad kraftarkitektur
**LED-gren:** VBAT(2S) → **10R 2512 (2W)** → SFH 4715AS → N-FET (LED_EN-modulerad) → GND.
~0,4–0,5 A/LED → ~390 mW/sr. **OBS:** 0,5 A i 10R = 2,5 W topp → kör **max ~50 % duty**
(modulerad konstellation, ej DC) annars överhettas 2 W-motståndet. LED-spår breddade till 0,4 mm.
**Logik-gren (separat):** TSOP4856 (**abs-max VS = 6 V**) + DATA-pullup matas från en lokal
**HT7333-A 3,3 V-LDO** (Vin ≤ 12 V → 2S OK), EJ direkt från VBAT. DATA blir ren 3,3 V mot väst-noden.

## Kvar att mäta (ärligt)
- Bänkmät faktisk blob-SNR @150 m i sol (slutgiltig bekräftelse) — budgeten har stor marginal men
  glimt/off-axis mäts bäst på riktigt.
- Off-axis-täckning: 80°-strålen räcker brett, men verifiera intensiteten vid spelets vinklar.
- Exponering/ström-trim så bloben är skarp (ej blommad) men >> bakgrund.
