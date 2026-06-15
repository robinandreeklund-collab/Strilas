# STRILAS — Kameraval (sikteskamera)

Kravet: **ser 860 nm** (måste, för att se målets konstellation), **P4-stödd** (`esp_cam_sensor`),
**billig**, **passar kit:ets kontakt**. Resolution: ≥2 MP räcker gott för blob-konstellationen.

## Beslut: **OV5647 NoIR** ⭐

| Kamera | P4 | Ser 860 nm | Kontakt | ~Pris | Kommentar |
|---|---|---|---|---|---|
| **OV5647 NoIR** ⭐ | ✅ (egen ISP) | ✅ (inget IR-cut) | **= kit (RPi-stil)** | **$10–15** | **drop-in**, 5 MP, P4-native |
| SC2336 (NIR) | ✅ (P4-exempel) | ✅ NIR-native | 24-pin MIPI (verifiera) | $5–10 | billigast, större 1/3″-pixlar = bäst IR-SNR, 2 MP |
| Kit-OV5647 stock | ✅ | ❌ (IR-cut) | kit | (medföljer) | ser ej IR → kan ej användas som sikte utan filterbortagning |
| Mira220 mono (GS) | ✅ | ✅ NIR | eval-kort | ~$141 | global shutter, men dyr — uppgradering, ej v1 |
| IMX296 / Arducam Pivariety | ❌ (Pi) | — | — | — | ingen P4-drivrutin |

## Varför OV5647 NoIR

- **Drop-in:** kit:et tar redan OV5647 → NoIR-versionen = samma kamera utan IR-cut-filter → samma
  kontakt + samma P4-drivrutin, men **ser 860 nm**. Noll integrationsfriktion.
- **Billig** (~$12), 5 MP (gott om marginal).
- **Verifierad:** SNR ≈ 30 + bäring σ ≈ 0,0008° @150 m med denna sensor-klass (`system-verification-report.md`).

## Billigare alternativ: SC2336

Ännu billigare ($5–10), **NIR-native** (säkerhetskamerasensor → ser 860 nm utan filter-pyssel),
**större pixlar (1/3″) → bättre IR-SNR**, 2 MP räcker. **Haken:** ofta 24-pin MIPI-modul →
**verifiera att FFC/kontakten matchar kit:et**. Driver finns i `esp_cam_sensor` + jeff-cn/esp32-p4-cam-exempel.

## Global shutter (senare)

GS undviker pan-smet men kostar: **Mira220 mono** (~$141 eval) är den P4-stödda GS-NIR-vägen.
Skjut på — rolling shutter + **fast-pan-grind** i firmware räcker för v1.

## Åtgärd

Sikteskamera = **OV5647 NoIR** (eller SC2336 om kontakten matchar). Kit:ets stock-OV5647 (med IR-cut)
duger **inte** som sikte — använd den ev. till annat eller gör NoIR genom att ta bort filtret.
