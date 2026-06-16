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

---

## Byggt kort (2026-06): komplett hjälm-nod
Ø100 mm, **4-lager** (In1=GND-plan, In2=VBAT-plan), routad **rent** (0 oroutade · 0 clearance · 0 oconnected).
Netlista: `hardware/helmet_netlist.py` · placering: `hardware/receiver_place.py` (helmet) · route: `hardware/route_helmet.py`.

**Arkitektur (verifierad mot datablad):**
- **2S-batteri** (laddas i docka) → **AP63203** synk-buck (TSOT23-6, 3.8–32 V in, 2 A; FB-delare 31.6k/10k → 3.33 V).
  Buck-3V3 matar XIAO via dess 3V3-stift + alla sensorer/GNSS/mik/audio. Konstellations-LED:erna drivs DIREKT från 2S.
- **Stackad ESP: XIAO ESP32-S3** (2× 1×7 sockel, centrum) — matas från kortets 3V3, programmeras via egen USB-C.
  GPIO: D0=DATA, D1=LED_EN, D2/D3=I²S BCLK/LRCK, D4=I²S→amp, D5=I²S←mik, D6/D7=GNSS UART, D9=amp SD.
- **8× TSOP4856** (940 nm skott-RX, utåt på ringen, 360°) → 8× BAT54 diod-OR → DATA (3,3 V-logik, 10k pullup).
- **4× SFH4715AS** 860 nm-konstellation (mellan TSOP-paren) + AO3400-driver (10R 2512, blink-modulerad) ← LED_EN.
- **GNSS:** ATGM336H-5N-modul (egen antenn) på 1×5-header → XIAO-UART.
- **I²S-ljud:** MAX98357A-amp-breakout (1×7 + högtalare) + I²S-MEMS-mik-breakout (1×6) → röst/spelljud.

**Köps separat (pluggas på header):** XIAO ESP32-S3, ATGM336H-GNSS-modul, MAX98357A-amp-breakout + högtalare,
I²S-MEMS-mik-breakout, 2S-LiPo. **NextPCB monterar** allt ytmonterat (buck, TSOP, LED, BAT54, NFET, R/C/L);
TH-headers/sockets (J1–J6) löder du själv. Underlag: `nextpcb/helmet-bom.xls` + `helmet-centroid.xls` + `helmet-halo-gerbers.zip`.

**Kvarstår (bänk):** buck-utgång 3,3 V verifieras innan ESP plugg; I²S audio + GNSS-fix bekräftas; konstellations-duty ≤50 %.
