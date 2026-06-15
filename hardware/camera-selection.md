# STRILAS — Kameraval (sikteskamera)

> ## 🔒 Två nivåer (custom PCB → tänk långsiktigt)
> - **v1-bänk / snabbstart: Arducam 5MP OV5647 NoIR, M12** (B012S6WJOS, ~$15) — drop-in i kit:et,
>   börja CV-utvecklingen direkt.
> - **Custom-PCB (långsiktigt optimalt): SC2336** (2MP MIPI) — **NIR-native** (ser 860 nm utan
>   filter-pyssel), **större 1/3″-pixlar → bäst IR-SNR** av de billiga, **P4-stödd** (esp_cam_sensor
>   + jeff-cn-exempel), ~$5–10. Designa kortets kamera-urtag/kontakt för SC2336-modulen.
> - **Global shutter** (ideal mot pan-smet) skjuts på: ingen *billig* GS-sensor har P4-drivrutin
>   (OV9281/OV2311/AR0234 = egen drivrutin krävs; Mira220 = dyr eval). Rolling shutter + fast-pan-grind räcker.

### USB-vägen (P4 har USB OTG 2.0 HS) — enda billiga global-shutter-vägen

P4:an har **USB 2.0 HS host** + Espressifs **UVC-host-drivrutin** + **HW-JPEG-avkodare** → en
**USB UVC-kamera fungerar**. Det låser upp **global shutter (OV9281, ~$30)** plug-and-play utan
MIPI-drivrutin — GS tar bort rolling-shutter/pan-smet, den verkliga vinsten för ett rörligt vapen.
Pris: USB-kabel (klumpigare än FFC) + JPEG-avkod-latens (litet med HW-JPEG) + mer firmware
(USB-host+UVC). **OV9281 måste vara NoIR** (ser 860 nm). Ändrar EJ det routade kortet (kameran =
mekanisk + kabelval).

**Gaffel efter prioritet:** GS-precision på rörligt mål → **USB OV9281 GS**; enklast/lägst latens →
**MIPI SC2336/OV5647 NoIR** (rolling + fast-pan-grind).

Kravet: **ser 860 nm** (måste), **billig**. Resolution: ≥1–2 MP räcker för blob-konstellationen.

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

## Åtgärd — och köp inte en kamera du inte kan använda

Kit:ets stock-OV5647 (med IR-cut) duger **inte** som sikte som den är. Två rena vägar:

1. **Köp kit UTAN kamera + OV5647 NoIR separat (~$12)** — om "utan kamera"-varianten är billigare
   med ungefär kamerans pris. Garanterat, ingen mod-risk. **(rekommenderas)**
2. **Köp kit med kamera + konvertera till NoIR** — RPi Cam Model B har justerbar M12-lins;
   IR-cut-filtret sitter i linshållaren och kan tas bort → NoIR. Gratis, ~10 min, viss risk.

P4 + C6 + högtalare behövs oavsett — frågan gäller bara kameran. SC2336 ($5–10 NIR-native) är
billigast om dess 24-pin-kontakt matchar kit:et.
