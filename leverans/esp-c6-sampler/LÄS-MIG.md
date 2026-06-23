# STRILAS — ESP32-C6-SAMPLER (DEMO · EJ FÖR TILLVERKNING)

Vapnet kör nu **CM5** (Broadcom-radio) men väst/hjälm kör **ESP32-P4 + ESP32-C6** och pratar
**ESP-NOW**. CM5:an kan inte tala ESP-NOW direkt → vi lägger en **ESP32-C6 som UART-brygga på
HAT:en** (samma radio-familj → exakt samma ESP-NOW/firmware). Innan vi binder upp HAT-respinnen vill
vi veta **vilken C6-modul NextPCB faktiskt har i lager och kan SMT-montera**.

Detta kort bär kandidat-modulerna i de **footprints** vi vill montera, över flash-/temp-varianter →
ladda upp BOM, se vad som är **In Stock**, välj MPN → då monterar NextPCB C6:an direkt på HAT:en
(slipper handlöda eller hänga en USB-dongle på carriern).

> **Kortet beställs / tillverkas ALDRIG.** Bara lager- + monteringskoll.

## Filer
`esp-c6-sampler-bom.xls` (8 rader — **filen att ladda upp**) · `esp-c6-sampler-gerbers.zip` ·
`esp-c6-sampler-centroid.csv` (alla 8 med, Top — alla ska monteras). Källa: `hardware/esp_c6_sampler.py`.
Footprints: `hardware/gen_esp_c6_footprint.py` (MINI-1U/-1, härledda ur databladet) + KiCad
`RF_Module` (WROOM).

## Kandidater (Espressif Systems)
| Ref | Modul | Antenn | Flash / Temp | Footprint | Roll |
|---|---|---|---|---|---|
| **U1** | **ESP32-C6-MINI-1U-N4** | **U.FL** | 4 MB / 85 °C | strilas:ESP32-C6-MINI-1U | **PRIMÄRVAL** (antenn ut ur vapenhus) |
| U2 | ESP32-C6-MINI-1U-H4 | U.FL | 4 MB / 105 °C | strilas:ESP32-C6-MINI-1U | hög-temp |
| U3 | ESP32-C6-MINI-1U-H8 | U.FL | 8 MB / 105 °C | strilas:ESP32-C6-MINI-1U | mer flash |
| U4 | ESP32-C6-MINI-1-N4 | PCB | 4 MB / 85 °C | strilas:ESP32-C6-MINI-1 | reserv (modul vid kortkant) |
| U5 | ESP32-C6-MINI-1-H4 | PCB | 4 MB / 105 °C | strilas:ESP32-C6-MINI-1 | hög-temp |
| U6 | ESP32-C6-MINI-1-H8 | PCB | 8 MB / 105 °C | strilas:ESP32-C6-MINI-1 | mer flash |
| U7 | ESP32-C6-WROOM-1U-N4 | U.FL | 4 MB | RF_Module:ESP32-S3-WROOM-1U | större reserv-footprint (18×25,5) |
| U8 | ESP32-C6-WROOM-1-N8 | PCB | 8 MB | RF_Module:ESP32-S3-WROOM-1 | större reserv-footprint (18×25,5) |

**Antenn:** STRILAS-vapnet sitter i metall/sluten kropp + IR-kupa → onboard-PCB-antenn dämpas hårt.
Därför är **U.FL-varianterna (-1U) primärval** med extern antenn ut ur huset. PCB-antenn-varianterna
(-1) finns med ifall modulen får sitta fritt vid en kortkant med plastfönster.

> **Footprint-not:** MINI-1 och MINI-1U delar **exakt samma land pattern** (13,20 mm bred, 47 perimeter-
> pads pitch 0,80 + 4 hörn-GND + center-termik); bara kropps-längden skiljer (16,60 mm med PCB-antenn /
> 12,50 mm med U.FL). WROOM-footprinten lånas från KiCad:s `ESP32-S3-WROOM-1(U)` som är land-pattern-
> kompatibel med C6-WROOM-1(U). Validera vald footprint mot Espressifs officiella KiCad-bibliotek
> innan HAT-respinnen committas.

## Så här används resultatet
1. Ladda upp `esp-c6-sampler-bom.xls` på NextPCB → notera vilka MPN som är **In Stock** + pris + ledtid.
2. Välj helst en **In-Stock MINI-1U** (minst flash som räcker = N4/4 MB räcker gott för en UART-brygga).
3. Då drar jag in den modulen i `weapon_hat_netlist.py` (UART GPIO14/15 + EN/IO9 + lokal 3V3-LDO från +5V),
   placerar om och routar HAT:en på nytt + regenererar `leverans/weapon-hat/`.

## BESLUT (juni 2026): socklad XIAO-daughterboard i stället för naken modul
Den nakna C6-modulen fick **inte plats** på 56×41-HAT:en (40-pin-headern äter mitten; inget 13×17-hål
ledigt). Vald lösning: **hona-sockel på HAT:ens BAKSIDA (J10) + en Seeed XIAO ESP32-C6** som trycks dit
(eget LDO + U.FL-antenn + USB-C). 14 hål trådas mellan fram-SMT:n, DRC 0/0, ingen kort-förstoring, ingen
carrier-krock (baksidan sticker ut i fri luft där). Denna sampler står kvar som lager-koll om man ändå
vill SMT-placera en naken modul senare. Footprint: `strilas:XIAO_ESP32C6_Socket`.

## HAT-integration (genomförd)
- **UART-brygga:** CM5 GPIO14 (pin 8, TXD0)→C6 RXD, GPIO15 (pin 10, RXD0)→C6 TXD. Konsol flyttas till USB.
- **Flash/reset:** CM5 GPIO4 (pin 7)→C6 EN, GPIO17 (pin 11)→C6 IO9 (CM5 kan flasha C6 över UART).
- **Kraft:** egen 3V3-LDO (t.ex. AP2112K-3.3, 600 mA) från HAT:ens +5V + bulk (22µF/100µF) för WiFi-TX-
  toppar (~470 mA). Häng INTE C6 på headerns strömbegränsade 3V3.
- **Antenn:** U.FL → extern antenn monterad utanför metallhuset.
