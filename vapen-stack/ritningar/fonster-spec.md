# STRILAS — skyddsruta / IR-fönster för mål-korten (väst-patch, hjälm-nod)

Korten monteras i en **svart 3D-printad låda** med ett **transparent IR-skydd** över optiken.
Det skyddar mot smuts/repor/regn, döljer elektroniken och ser rent ut — men måste släppa igenom IR
åt **båda håll**: **940 nm IN** (skottet → TSOP4856) och **860 nm UT** (konstellation → skyttens kamera).

## 1. Materialval — mörk **IR-pass** (long-pass >800 nm)
Använd ett fönster som **ser svart/mörkrött ut för ögat men släpper igenom nära-IR**. Samma princip
som IR-fönstret på en TV-fjärr/IR-mottagare.

| Alternativ | T @860/940 nm | Kommentar |
|---|---|---|
| **IR-pass-akryl (long-pass >800 nm)** ⭐ | ~0,88–0,92 | t.ex. Evonik PLEXIGLAS IR-transmitting; döljer elektronik, matchar svart låda |
| Klar PMMA (akryl) | ~0,92 | syns igenom (visar LED), billigast |
| Klar polykarbonat (PC) | ~0,88 | slagtålig (tåligt skydd), syns igenom |

- **KRAV: bred long-pass (>800 nm)** — INTE ett smalt 850 nm-bandpass (det skulle kapa 940 nm-skottet).
- Tjocklek **1–2 mm**. Matt/AR-yta om möjligt (mindre reflexer).

> **Skillnad mot vapnet:** skyttens **kamera** har ett *smalt* 860 nm-bandpass (ser konstellationen,
> avvisar 940 nm). **Mål-rutan** (väst/hjälm) ska vara **bred long-pass** så att 860 ut OCH 940 in
> båda passerar. Blanda inte ihop dem.

## 2. ⚠️ PLATT över konstellations-LED:erna — INTE kupa
Kameran kör **PnP på LED:ernas exakta positioner**. En **välvd kupa fungerar som en lins** → bryter
ljuset → **förskjuter/suddar LED:ens skenbara läge** → pose/bäring-fel @150 m.
- **Konstellations-LED (860 nm, SFH 4715AS): PLATT fönster** (bevarar geometrin). Obligatoriskt.
- **TSOP-zon (940 nm, bara mottagning): kupa OK** (riktning spelar ingen roll för mottagning).
- Vill man ha kupa estetiskt: gör den **platt just över LED-zonen**, eller håll LED:erna nära
  kupans optiska axel/centrum där brytningen är minimal.

## 3. Reflexer / spökbilder (kamera-sidan)
Rutan kan reflektera LED:ens eget ljus → **falska blobbar** som stör blob-detektionen.
- **Matt svart kant/bländare runt varje LED** (absorberar interna reflexer).
- Håll **rutan nära optiken** (liten luftspalt, t.ex. 2–5 mm) → mindre ljusledning/parallax.
- Ev. **lätt vinklad ruta (~5°)** så direktreflexen inte går rakt tillbaka i kamerans riktning.
- AR-yta hjälper. Svart låda absorberar ströljus → mindre flare (bättre SNR).

## 4. Optisk budget — påverkan
- **Transmissionsförlust ~12 %** (T ≈ 0,88: 2× Fresnel-reflex ~8 % + absorption). Inräknad i
  `daylight-snr-budget.md`: nominellt SNR ~54 → ~50; derat-lågänden ~7 → ~6 (över tröskel ~5–10).
- **Återvinns lätt:** SFH 4715AS körs på 0,4–0,5 A av sina **1,5 A** → bumpa mot ~0,6 A (inom rating
  + duty-tak) tar tillbaka rut-förlusten. Trimmas vid bringup.

## 5. Mekanik
- **Luftspalt** optik↔ruta ~2–5 mm (TSOP + OSLON har breda kon-vinklar → ingen vinjettering).
- **Tätning:** o-ring/packning eller lim-spår i lådan om utomhus/regn (IP-klass efter behov).
- **Värme:** pulsade LED + 2512-motstånd ger lite värme i sluten låda; lågt medel (blink-modulerat,
  ≤50 % duty) → normalt OK. Lämna luftspalt/termisk väg om hög repetition.
- **Infästning:** kortet lim/kardborre-fäst i lådan (väst-patch saknar skruvhål); lådan på väst/hjälm.

## 6. Per kort
| Kort | Under rutan | Fönstertyp |
|---|---|---|
| **Väst-patch** (38×28) | 3× TSOP4856 (940 in) + 2× SFH 4715AS (860 ut) | **platt** IR-pass over LED-zonen |
| **Hjälm-nod** (Ø100) | 8× TSOP runt ringen + 4× SFH 4715AS | **platt** över LED:erna; ringens TSOP-zon kan vara kupa |
| Vapen-optik | kamera (M12-lins) + 2× 940 nm-emitter | egen vapen-kåpa; kamera har eget 860 nm-bandpass (ej denna spec) |

## TL;DR
**Svart låda + platt, mörk IR-pass-ruta (long-pass >800 nm)** över optiken. Skyddar, ser rent ut,
släpper igenom 860 ut + 940 in. **Platt** över konstellations-LED (kupa förskjuter PnP). ~12 % förlust
inräknad, återvinns med lite mer LED-ström. Matt kant + nära ruta mot spökreflexer. Mät T + spökbilder
på bänk.
