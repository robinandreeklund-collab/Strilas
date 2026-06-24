# STRILAS — väst-/hjälm-patch: optimal TSOP-sikte (täckningsberäkning)

> Hör ihop med `hardware/receiver_place.py` (`vest_pos`) och `hardware/receiver_netlists.py` (`build`).

## Frågan
Patchen har **4 ledade TSOP4856** (940 nm skott-mottagare). Hur ska de riktas för
**maximal träfftäckning** över framåt-hemisfären, samtidigt som layouten är **symmetrisk**
(patchen ska kunna klistras var som helst på västen, i valfri vridning)?

## Modell
TSOP4856 vinkelkänslighet (databl.): ~1,0 rakt fram, **halva vid ±45°**, ~0 bortom ±90°.
Modellerad som `respons(θ) = cos²(θ)` (ger 0,5 vid 45°, 0,25 vid 60°). En skott-riktning
räknas **täckt** om någon mottagare har respons ≥ 0,25 (inom ~60° av sin axel → adekvat SNR).
Hela framåt-hemisfären samplas, **solid-vinkel-viktat**. (`/tmp/cov.py`-metoden.)

## Resultat (jämförda symmetriska konfigurationer)
| Konfig | Hemisfär-täckning | Rakt-fram-summa* | Täckning ≤60° zenit |
|---|---|---|---|
| 1 center + 3 lutade 45° (3-falds) | 97,2 % | 2,50 | 100 % |
| **4 @ 90°, lutade 40° (4-falds)** | **99,5 %** | **2,35** | **100 %** |
| 4 @ 90°, lutade 35° | 97,8 % | 2,68 | 100 % |
| 4 @ 90°, lutade 45° | 100,0 % | 2,00 | 100 % |

\* "Rakt-fram-summa" = summerad respons rakt fram = hur många mottagare som ser ett
frontalskott samtidigt (redundans/SNR-marginal).

## Vald lösning: 4 TSOP @ 90°, lutade ~40° utåt
- **4 mottagare jämnt 90° isär** (diamant NÖ/NV/SV/SÖ på kortet), var och en med benen
  **böjda ~40° utåt** från kortets normal (silkscreen-pil "LUTA 40 UT" + NÖ/NV/SV/SÖ).
- **99,5 % av framåt-hemisfären** täckt, **100 % inom 60° zenit** (där så gott som alla skott
  kommer), ~**2,3 mottagare** ser ett frontalskott (bra redundans).
- **Full 4-falds symmetri** → patchen funkar lika bra i vilken rotation som helst på kroppen
  (bröst/rygg/axlar) — ingen "rätt väg upp" att tänka på vid montering.
- 40° valt framför 45° (full täckning men svagare rakt fram) och 35° (starkare fram men 97,8 %)
  som bästa avvägning täckning↔frontal-SNR.

## Layout (symmetrisk, ej "klump")
- 4 TSOP i diamant, domer radiellt utåt mot hörnen.
- **Varje TSOP har sin egen OR-diod + avkopplings-C bredvid sig** → 4 identiska kluster.
- Delade delar (kontakt J1, N-FET, DATA-pullup, gate-R, bulk-C) **centrerade** i Ö–V-bandet.
- **Konstellations-LED ≠ per-TSOP.** De 2× SFH4715AS (860 nm) är **kamera-markörer** (skyttens
  kamera ser dem för pose/PnP), en helt annan funktion än skott-mottagningen. De sitter
  symmetriskt på N/S-axeln. Antal LED styrs av konstellations-/pose-behov, inte av antal TSOP.

## Att bekräfta på bänk
Modellen antar cos²-lob och 60°-tröskel. Verifiera verklig vinkelrespons + SNR @150 m dagsljus
(se `daylight-snr-budget.md`); justera lutningen (35–45°) om verklig lob avviker.
