# STRILAS — Första batch: tillverkningsberedskap & verifiering

Datum: 2026-06-16. Alla kort på **samma ESP32-P4-WIFI6** (P4 + onboard C6 WiFi6).
Autonom genomgång kort-för-kort inför första beställning. Allt nedan är maskinverifierat
(`hardware/verify_board.py`, `hardware/sim_system.py`, courtyard/clearance-kontroller).

## Kort i batchen (5 tillverkade kort)
| Kort (order-namn) | Storlek | Lager | Routning | Anslutet | Clearance@0.2 |
|---|---|---|---|---|---|
| Optik/vapen (`optik`) | 54×74 mm | 4 | seed-ren | 0 oanslutna | 0 |
| Fire-control (`firecontrol`) | 71×21 mm | 2 | ren | 0 | 0 |
| Väst-patch (`vest-patch`) | **37×37 mm** | 2 | ren | 0 | 0 |
| Hjälm-mb (`helmet-mb`) | **RUND Ø104 mm** | 4 | ren | 0 | 0 |
| Väst-mb (`vest-mb`) | 100×60 mm | 4 | ren | 0 | 0 |

(Gammalt ring-hjälmkort `helmet`/`helmet-halo` är **utgånget** och borttaget ur order-paketet.)

## Verifiering (alla kort)
- **Footprints:** varje komponent på kortet matchar netlistans footprint; alla custom-footprints
  (OSLON-emitter/LED 2-pad, InvenSense LGA-14 14-pad, ZED-F9P GH 8-pad) har rätt pad-antal.
- **Paddar/anslutningar:** varje net-nod har en matchande pad; **0 oanslutna** (ratsnest efter
  kopparplan) på alla 5 kort. Enda "icke-pad"-noder är mekaniska monteringshål (GND-tilldelning =
  no-op, avsiktligt; ej elektriskt grundade standoffs).
- **Routing dubbelkollad:** 0 clearance-överträdelser @0.2 mm; 0 courtyard-krockar; inget utanför
  kortkant (rund hjälm-mb radiellt verifierad).

## P4 (c6) pinout — 100 % verifierad
- **Internt identisk** över alla fyra kort som möter P4 (optik edge B, fire-control edge A,
  hjälm-mb + väst-mb edge A+B): varje fysisk P4-pin → samma signal. Byte-för-byte identiska defs.
- **Mot Waveshares officiella dok:** I²C-default SCL=GPIO8 / SDA=GPIO7 bekräftad (matchar edge A
  pin16/17). GPIO-uppsättningen (GPIO2-52) matchar P4:ans exponerade 2×20-stift.
- Mekanik (71.05×21, pin1@4.52 mm, rader ±9.28, 4× M2-hål) uppmätt mot Waveshares måttritning.

## Optik — samma leverantör (verifierat)
- **Vapnets skott-emitter:** ams OSRAM **SFH 4725S** (940 nm, OSLON Black, 980 mW@1A). **UTGÅENDE/EOL**
  (databl. 2023) men lagerförs ännu (RS/Farnell/DigiKey, last-time-buy) → OK för första batchen;
  **verifiera aktuell 940 nm OSLON-ersättare inför produktion** (tidigare angiven "SFH 4725CS" är ej bekräftad).
- **Patchens/hjälmens konstellations-LED:** ams OSRAM **SFH 4715AS** (860 nm, OSLON Black) — **aktiv/tillgänglig**.
- Samma leverantör (ams OSRAM) och **samma OSLON Black-paket/footprint** → enhetlig sourcing.

## System-simulering (signalflöde end-to-end) — 28/28 PASS
Korten "uppkopplade" i en logisk flödessimulering (`sim_system.py`), kabel-bryggor position-
matchade. Verifierade kedjor: skott-RX (patch-TSOP→DATA→kabel→moderkort→P4), konstellation
(P4→LED_EN→patch-FET→OSLON), kraft (batteri→buck→3V3 + VBAT→P4 VSYS), I²C (IMU+F9P+P4),
GNSS-UART (F9P↔P4), vibratorer (P4→TPIC→zon-VIB), ljud (P4 I²S↔amp/mik), vapnets CC-emitter
(OPA171+sense+pass-FET), samt kraftintegritet (varje IC:s matningsstift på rätt skena).

## Beställnings-underlag (per kort i `nextpcb/`)
`<kort>-gerbers.zip` (regenererade från exakt routade kort) · `<kort>-bom.xls` · `<kort>-centroid.csv/.xls`.
STEP (3D) i `hardware/<kort>.step`. **Alla MPN ifyllda** (0 saknade) — passiva = representativa,
verifiera mot NextPCB:s basbibliotek.

### Kund-lödda (NextPCB monterar endast SMT)
- **Alla 2.54 mm TH-kontakter** löds av kund: P4-kant-socklar (1×20/1×14/1×12), patch-/zon-headers
  (1×5/1×6), amp/mik-headers (1×7/1×6), batteri-JST (XH). Markerade DNP i BOM, uteslutna ur centroid.
- ZED-F9P GH (SMD) monteras av NextPCB.
- Köps separat: ESP32-P4-WIFI6 (×3, en per moderkort + vapen), ZED-F9P-puck, OV9281-kamera +
  860 nm IR-pass, MAX98357A-amp + högtalare, MEMS-mik, ERM-vibratorer ×10, 2S-batterier, TSOP4856
  (ledade, böjs 40° utåt på patchen), OSLON-emitter/LED (ams OSRAM, kund-levererade).
- **Hjälm-konstellation: 45°-omriktningshållare/optik (köps separat, MONTERAS MANUELLT):** per disc-LED
  (6 st) — viker OSLON-strålen 90° RADIELLT UT mot horisonten (kameran ser punkterna i ögonhöjd @150 m;
  rakt-upp-LED syns ej). LED:erna maskinplaceras platt vid kanten; hållaren riktar ut. Källa = bänk-item.
- **Optik-linser + hållare (köps separat, MONTERAS MANUELLT):** Carclo TIR-kollimatorlins för OSLON Black
  (t.ex. Carclo 10003-serien, vald stråle/spridning för 150 m) + Carclo-lenshållare per emitter. Klistras/
  snäpps över emittrarna efter SMT (kort-fästbenen H12–H19 finns). Sätter den faktiska strålvinkeln —
  välj spridning vid optik-bringup. Eye-safety (IEC 60825-1) ommäts med vald lins monterad.

## Bänk-bekräftas (ej fångbart i layout-verifiering)
- Dagsljus-SNR @150 m (LED-effekt/exponering, ≤50 % LED-duty) — `daylight-snr-budget.md`.
- TSOP-vinkellob vs cos²-modell (justera 40°-lutning om verklig lob avviker) — `patch-sikte.md`.
- Buck 3,33 V innan P4 pluggas; CC-sänkans ~1 A skott-ström (eye-safety HW-tak).
- Induktor-mättnadsström >2 A; 2512 LED-serieR ≤50 % duty (2,5 W topp).
- **IMU-footprint:** LGA-14 2.5×3 mm-mönstret är namngivet `ICM-456xx` men används för IIM-42653
  (net→pad-mappning enligt IIM-42653 DS-000529). Båda är TDK 14-pin LGA 2.5×3 mm; bekräfta att
  pad-layouten är identisk mot IIM-42653-paketritningen innan produktionsbestyckning av hjälm-mb.
- **NC-stift (avsiktligt):** IMU AUX1-SPI (pin 2/3/9/10/11), P4 edge-B oanvända GPIO + VBUS/EN/RUN/
  3V3-ut (vi matar laster från egen carrier-buck, ej P4:ans 3V3-ut). P4 GND+VSYS+signaler anslutna.
