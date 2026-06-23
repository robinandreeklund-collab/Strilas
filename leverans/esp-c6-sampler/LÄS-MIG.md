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

## BESLUT (juni 2026): EXTERN ESP via 4-pol JST på HAT:en
Att SMT-placera en C6-modul (bar MINI-1/-1U) ELLER en XIAO-sockel **direkt på HAT:en gick inte att
routa**: framsidan blockeras av kamera-PCB:n + det redan fullpackade toppbandet (buck + 3 IMU + fire-
control), och baksidan av 40-pin-headern. Flera placeringar provades — alla bröt routningen.

**Vald lösning:** en **4-pol JST (J10) på HAT:en** (`+5V·ESP_TX·ESP_RX·GND`, → CM5 GPIO14/15) och en
**extern ESP32-C6-modul** (t.ex. Seeed XIAO ESP32-C6: egen LDO + U.FL-antenn + USB-C för flash) som
monteras separat i huset och ansluts med 4-tråds kabel. Kort **56×41 oförändrat, routar 0/0**. Bara 4
nät → triviell routning, ingen omplacering. Denna sampler står kvar som lager-koll om man i en framtida
HAT-respin vill SMT-placera en bar modul (kräver då layout-omarbetning eller större kort).

## HAT-anslutning (J10, genomförd)
- **JST-pinne:** 1=+5V · 2=ESP_TX (CM5 GPIO14/pin8 → extern C6 RX) · 3=ESP_RX (extern C6 TX → CM5 GPIO15/pin10) · 4=GND.
- **Extern modul:** matas 5V (egen LDO på XIAO), flashas via egen USB-C, antenn via egen U.FL/PCB-antenn ut ur huset.
- **MPN:** J10 = JST `S4B-PH-K-S(LF)(SN)` (maskin-monteras); XIAO ESP32-C6 + kabel = köps separat.
