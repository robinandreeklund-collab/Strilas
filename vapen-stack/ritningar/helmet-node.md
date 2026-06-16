# STRILAS — egen ESP i hjälmen? (ja) + högtalare/kom

> Figur: [`spelare-topologi.png`](spelare-topologi.png)

## Svar: JA — ge hjälmen en egen ESP, trådlöst mot västen
Skäl (ärligt):
1. **Ingen kabel hjälm↔väst.** En kabel över nacken snor sig, går av och låser huvudrörelsen.
   Egen ESP + litet batteri i hjälmen → helt fristående, ren UX.
2. **Högtalare + mik hör hemma i hjälmen** (vid öron/mun). Med egen ESP drivs ljudet lokalt och
   skickas över radio → ingen ljudkabel ner till västen.
3. **GNSS sitter redan i hjälmen** (bäst sky-view) → läses lokalt och skickas vidare, inte rå-data
   genom en kabel.

## Vad hjälm-noden blir
ESP + litet LiPo · **8× TSOP4856** (360° huvud-träff) · **4× 860 nm**-konstellation (högt på ringen)
· **GNSS** · **I²S-ljud: liten förstärkare + högtalare + MEMS-mik** (spelljud + lagröst) · WiFi6/ESP-NOW.

## Frame-sync är INTE ett problem
Man kan tro att hjälmens och västens konstellation måste blinka exakt synkat. Det behövs inte:
**huvudet och torson är separata stela kroppar** (nacken rör sig) → skyttens kamera kör PnP på dem
**var för sig** ändå (torso-pose + huvud-pose). Varje grupp blinkar sitt eget ID-kodade mönster och
kameran frame-differensar dem oberoende. Hjälmen kan alltså vara helt självständig.

## ESP-val för hjälm-noden
- **ESP32-S3** — bäst för **ljud/röst** (dubbelkärna, beprövat audio-ekosystem, Opus-codec). WiFi4+BLE.
- **ESP32-C6** — om du vill hålla **WiFi6/BLE**-familjen genomgående och ljudet är lätt (enkel codec).
- Båda parar trådlöst med vapnets P4 och väst-C5 (samma Espressif-stack). **Rekommendation: S3** om
  röst-comms är en huvudfunktion; annars C6.

## Per-spelare-topologi (uppdaterad)
| Nod | MCU | Jobb | Länk |
|---|---|---|---|
| Vapenlåda | ESP32-P4-WIFI6 | kamera·IR·sikte/ballistik | WiFi6/ESP-NOW |
| Väst-nod | ESP32-C5 | 10 patchar·hit-zoner·konstellation | WiFi6/ESP-NOW |
| **Hjälm-nod** | **ESP32-S3/C6** | head-TSOP·GNSS·**högtalare+mik** | WiFi6/ESP-NOW |
| Magasin | (passiv) NFC + rekyl-batt | ammo + rekylström | magwell (fysiskt) |

## Pris att betala (ärligt)
- **Fler batterier att ladda:** huvud (vapen) + rekyl (magasin) + väst + hjälm = 4/spelare.
  Mildra med en **gemensam laddningsdocka** (håller alla fyra). Väst-/hjälm-batterierna är små
  (lågeffektsnoder) → lång drifttid.
- En radio till + en ljud-kedja → lite mer kostnad/komplexitet, men löser kabel + comms på köpet.

## TL;DR
Egen ESP i hjälmen = **rätt val**: slipper nack-kabeln och får högtalare/röst-comms trådlöst på köpet.
Frame-sync är inget hinder (huvud/torso är separata pose-kroppar ändå). Välj **S3** för seriöst ljud,
annars **C6**. Priset är ett extra litet batteri per spelare — lös med gemensam laddningsdocka.
