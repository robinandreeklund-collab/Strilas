# STRILAS — Kameraval (sikteskamera)

> ## ⚠️ KORRIGERING (juni 2026) — B0332 UTGÅR: linsen går INTE att byta
> Arducams datablad för **B0332**: *"assembled with a 70°(H) low distortion M12 lens … The lens is
> **fixed (non-interchangeable)**."* Den tidigare "låsningen" nedan byggde på att **byta** stock-linsen
> mot en 16 mm → det är **omöjligt** på B0332. Med fast 70° H når siktet bara ~25–30 m, inte 150 m.
> **→ B0332 är därmed ELIMINERAD.** (Samma fälla: Waveshare OV9281-110 = fast 110°; Arducams OV9281-
> M12-moduler = fabrikslimmad lins, ej användarbytbar.)
>
> **HÅRT KRAV som vinnaren måste uppfylla (annars 150 m omöjligt):**
> 1. **Utbytbart linsfäste** (riktig M12-hållare / CS / C-mount) ELLER fabriksvald ~16 mm-ekv. lins →
>    måste ge **~13,7° H FOV** på sin sensor (config.py-målet: ~14 px LED-sep + 24 px baslinje @150 m).
> 2. **Ser 860 nm** (NoIR / inget IR-cut) + plats för 850/860 nm-bandpass.
> 3. **Mono global shutter** (ingen pan-smet), ≥1 MP.
> 4. **P4-väg:** USB-UVC (ingen drivrutin) **eller** `esp_cam_sensor`-MIPI-drivare (ov9281/sc2336/mira220).
>    AR0234-**MIPI**/Pivariety = ingen P4-driver → köp INTE.
>
> **Kandidater (alla har en ÖPPEN verifieringspunkt — inget låses förrän den är klar):**
> | # | Kandidat | Styrka | ÖPPET att verifiera |
> |---|---|---|---|
> | 1 | **DECXIN AR0234 USB-UVC** (2,3 MP mono GS) + 25 mm M12 | USB → ingen driver; 28 mm-hål = som B0332; 2,3 MP | **utbytbar lins?** + 860 nm-känslighet (AR0234 NIR-QE lägre) |
> | 2 | **ams Mira220 mono** (`MIRA220MINI`, MIPI) | **NIR-enhanced (bäst 860 nm), samma leverantör som OSLON**, P4-repo finns | drivrutins-mognad + eval-bräda → MIPI-adapter/FFC + kontakt mot P4 + linsfäste |
> | 3 | **Industriell OV9281/AR0234 C-/CS-mount** (e-con/Vision Components/Leopard) | äkta utbytbar optik + IR-bandpass i gänga; OV9281 har esp_cam_sensor-driver | storlek/vikt + kontakt mot P4 + pris |
>
> **Board-påverkan (optik-kortet):** kameran är mekanisk (mount + Ø16-lins-hål, ingen routning), men
> monteringsmönstret (idag B0332 28×28 M2) + lins-aperturen måste **anpassas till vald modul**. → optik-
> kortet är **INTE beställningsklart** förrän kameran är vald. Mjukvaran (Fas 0–3) är opåverkad.
>
> **Nästa steg:** verifiera punkt 1 (DECXIN lins-swap + NIR). Håller den → enklast (USB, samma mount).
> Annars Mira220 (bäst optiskt/NIR, mer firmware) eller industriell C-mount.

> ## ❌ OGILTIG (fast lins — se KORRIGERING ovan): tidigare "🔒 LÅST" Arducam B0332 + 16 mm M12-lins
> | Del | Exakt | ~Pris | Not |
> |---|---|---|---|
> | **Modul** | **Arducam B0332** — 1 MP OV9281 **mono global shutter**, **USB-UVC 2.0**, M12-fäste | ~$30 | UVC → P4:ans USB OTG 2.0 HS, ingen drivrutin; sensorn ser NIR (850 nm) i grunden |
> | **Lins** | **16 mm M12, F/2** (t.ex. Arducam M2016ZH01) → på 1/4″ OV9281 = **13,7° H FOV** | ~$8 | byt mot stock-vidvinkeln; M12-barrel Ø12 mm går genom Ø16-hålet |
> | **Filter** | **M12 850/860 nm IR-pass/bandpass** | ~$8 | dagsljus-avvisning + ser bara 860 nm-konstellationen |
>
> **Varför 16 mm (inte 6 mm):** OV9281 är 1 MP. Vid 6 mm (35,5° FOV) subtenderar konstellationen
> bara ~9 px @150 m → LED:erna smälter ihop. **16 mm (13,7°) ger ~24 px baslinje + ~14 px LED-
> separation → robust PnP @150 m med marginal** (verifierat, se [`system-verification-report.md`](system-verification-report.md),
> brännvidds-svep). Scen @150 m = 36 m bred → gott om plats att hitta mål. *(12 mm = vidare FOV men
> knappare marginal; 6 mm = bara ~80 m.)*
> **MÅSTE se 860 nm:** OV9281-sensorn är NIR-känslig utan IR-cut; välj 16 mm-lins **utan IR-cut**
> + IR-pass-filtret ovan. (Stock-B0332-linsen har redan 850 nm-pass — vid linsbyte tillförs filtret separat.)
> Kameran sitter mekaniskt **bakom** optikkortet, linsen genom Ø16-hålet; ansluts till P4 via **USB-kabel**.
> P4 mounteras som **carrier** (header-mount). **PCB:t är oberoende av brännvidd** (kameran är mekanisk/USB).
>
> ### P4-carrier pin-map (J1 → P4-GPIO)
> | Signal | P4-pin | | Signal | P4-pin |
> |---|---|---|---|---|
> | VSYS (batteri→P4) | VSYS | | SCK | GPIO22 |
> | 3V3 (P4→logik) | 3V3 | | MOSI | GPIO23 |
> | IR_MOD | GPIO20 (RMT) | | MISO | GPIO26 |
> | IMU INT | GPIO32 | | nCS | GPIO27 |
> *(Batteri matas in på optikkortet J2 → VSYS till P4 + emitter-rail; trigger → egen P4-GPIO på greppet.)*

> ## ✅ KAMERA-BESLUT (juni 2026) — B0332 NU, AR0234-USB som framtida uppgrade
> **P4 = LÅST: Waveshare ESP32-P4-WIFI6.** Kameran kopplas på P4-kortets **4-pin MX1.25 USB-OTG**.
> Verifierat ur Waveshare-schemat: stiften = **USB0_5V (5 V/VBUS, TVS-skyddad), USBD_P (D+),
> USBD_N (D−), GND** — kortet kan **källa 5 V i host-läge** (DCDC + switch). Carriern bär ej
> kamerasignal → **kameran = mekanik + USB-kabel, NOLL PCB-ändring.** (Verifiera pin-ordning mot silk +
> aktivera host-mode VBUS i firmware. Kamera drar ~150–250 mA @5 V → inom VBUS-budget.)
>
> **NU (vald): Arducam B0332** = OV9281 1 MP mono global shutter **USB-UVC**, M12 (~$30) +
> **16 mm M12-lins** (13,7° → 150 m) + **850/860 nm bandpass** (~$16). UVC → ingen drivrutin.
> Kabel: kamera-USB → P4 MX1.25 (5V/D+/D−/GND). **Räcker för 150 m** (verifierat, ~24 px konstellation).
>
> **FRAMTID (drop-in-uppgrade): DECXIN AR0234 1/2.6″ mono GS USB-UVC** (2,3 MP, ~$78) + **25 mm M12**
> (13° på större sensor) + 850 nm. **Mekanisk + elektrisk drop-in:** 38×38 mm kort med **28 mm fäst-hål
> = samma som B0332**, M12-fäste, USB (5-pin-1.25 → P4 MX1.25). 2,3× upplösning → mer 150 m-marginal.
> Bänk-verifiera UVC-enum + 860 nm-känslighet vid leverans. (AR0234:s NIR-QE < OV9281 → bandpass +
> LED-modulering bär; B0332 = fallback om NIR/UVC sviktar.)
>
> **⚠ VIKTIG distinktion AR0234:** funkar **bara via USB-UVC** (DECXIN ovan — egen ISP, syns som webbkamera).
> AR0234 via **MIPI** funkar EJ på P4 (ingen `esp_cam_sensor`-driver), och **Pivariety/Jetson-AR0234**
> (Arducam B0353, Camemake) är Pi-/Jetson-låsta → köp INTE dem.
>
> **Max-NIR-alternativ (ej planerat): ams Mira220 mono** (`MIRA220MINI-SENSOR-BOARD-MONO`, ~$92, 2,2 MP
> NIR-*enhanced*) via MIPI-CSI — bäst 860 nm, har officiellt P4-exempel (ams-OSRAM), men kräver MIPI-
> adapter till P4:ans CSI + firmware-port. Bara om USB-AR0234 inte räcker.
>
> **❌ Köp INTE:** AR0234-**MIPI**/Pivariety (B0353), allt *"Pivariety / for Raspberry Pi / libcamera"*,
> Sony **IMX** = Raspberry-Pi-låsta. Tumregel: "raw MIPI/bare sensor" i `esp_cam_sensor` (ov9281, sc2336,
> mira220, ov5647) → ja; "Pivariety/Pi/libcamera" → nej; **USB-UVC (webbkamera) → ja oavsett sensor.**

> ## (Bakgrund) Två nivåer (custom PCB → tänk långsiktigt)
> - **v1-bänk / snabbstart: Arducam 5MP OV5647 NoIR, M12** (B012S6WJOS, ~$15) — drop-in i kit:et,
>   börja CV-utvecklingen direkt.
> - **Custom-PCB (långsiktigt optimalt): SC2336** (2MP MIPI) — **NIR-native** (ser 860 nm utan
>   filter-pyssel), **större 1/3″-pixlar → bäst IR-SNR** av de billiga, **P4-stödd** (esp_cam_sensor
>   + jeff-cn-exempel), ~$5–10. Designa kortets kamera-urtag/kontakt för SC2336-modulen.
> - **Global shutter** (ideal mot pan-smet): **OV9281 HAR P4-drivrutin** (`esp_cam_sensor`, MIPI) +
>   fungerar via **USB-UVC** (B0332, ingen driver) → GS är fullt möjligt. (AR0234 saknar P4-driver;
>   Mira220 har P4-exempel men dyr/eval.) Se KÖP-KLARA MODULER ovan. *(Äldre not: trodde fel att ingen
>   billig GS hade P4-stöd — OV9281 finns i esp_cam_sensor.)*

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
