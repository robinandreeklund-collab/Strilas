# STRILAS vapen-modul — OSLON-omdesign (PÅGÅENDE / WIP)

> ⚠️ **STATUS: EJ fab-färdig.** Detta är en pågående omdesign. Det senast **fullt
> verifierade** kortet (52×80 mm, 0 oroutade, 0 clearance-fel) finns i git-historiken
> (commit `10a1535`) och är det man faller tillbaka på tills detta är klart.

## Vad som är LÅST i den här omdesignen ✅
- **Skott-emitter: OSRAM OSLON Black SFH 4725S** (940 nm, 980 mW @ 1 A) — STEP från ams-osram.
  Footprint: `strilas.pretty/IR_Emitter_OSRAM_OSLON_Black_SFH4725S.kicad_mod` (land E062.3010.91-06).
- **Kollimator: Carclo 10003** — Ø20 mm Narrow Spot TIR, officiellt matchad för SFH 4725S,
  nedladdningsbar STEP + 20 mm-hållare (benmönster). 4 ben (2/lins: topp + ytter).
- **P4-anslutning: RIGID 1×13 kantkontakt** (J1) mot P4:ans högra kantrad
  (VSYS·GND·3V3·GPIO20·GPIO21·GND·GPIO22·GPIO23·GPIO26·GND·GPIO27·GPIO32·GND) — **ingen flex**.
- **P4-standoffs borttagna** (kantkontakt + hölje bär P4:an).
- **Kort krympt till 54×68 mm** (praktiskt minimum för 2× Ø20 + kamera + 1×13-kontakt).
- Kamerafäste (B0332 28×28), trigger- (J3) + batteri- (J2) kontakter, IMU, driver: på plats.

## Den ärliga, OLÖSTA punkten 🛑
**2 emitter-anod-nät routas inte rent:** `N$2` (Rset→D2-anod) och `LED_MID` (D2-katod→D3-anod).
OSLON-anoden (nedre padden) blir inringad av lins-urtaget + kamerahålen + kollimatorbenen, och
Freerouting når dem inte. Manuell dragning hittills korsar `LED_CATH` → clearance-brott.
**Kortet har därför 2 oroutade nät och är inte fab-klart.**

## Återstår (1 fokuserat pass)
1. Flytta emittrarna isär/upp så anod-kanalen nedåt öppnas → ren autoroute, **eller**
2. Förrouta de 2 näten för hand genom mittkanalen (ej höger sida där LED_CATH går),
   med verifierad clearance.
Sedan: kopparplan-fyll, Gerbers, STEP (med Carclo + OSLON 3D), full omverifiering → **lås**.
