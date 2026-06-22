# STRILAS — Vapen-modul v2 (Raspberry Pi CM5) — komplett design

> ## ✅ SLUTGILTIG ARKITEKTUR + FÄRDIGA KORT (2026-06)
> **Stack (mot målet →):** CM5 → CM5-carrier (köpt, t.ex. CM5 Nano Base 56×41) → **HAT/FC** →
> *[20 mm; AR0234M @10 mm]* → **OPTIK-PCB**. Hård gräns: alla PCB ≤ **56×41 mm**.
>
> | Kort | Status | Innehåll |
> |---|---|---|
> | **OPTIK-PCB** (`optik_head.py`) | ✅ **ROUTAD 0/0**, leverans klar | 41×56 porträtt; **lins-cutout** topp (AR0234M bakom @10 mm standoff); **2 emittrar + Carclo 10734/10003 SIDA-VID-SIDA** botten; **CC-sänka (OPA171+DPAK+0R2/0R1+15k/1k+gate) på FRAMSIDAN** (enkelsidig SMT = billigare); JST 3-pin (VBAT·IR_MOD·GND) THT bak. |
> | **HAT/FC** (`weapon_hat_netlist.py`) | ✅ **ROUTAD 0/0**, 4-lager, leverans klar | 56×41; **40-pin HONA-sockel i kortets CENTRUM på BAKSIDAN** (trycks rakt ner på carrierns mittstiftlist — *verifierat mot CM5-NANO-B 3D-modell: header dead-center, offset <0,02 mm*); ALL SMT på FRAMSIDAN; kontakter på topp/botten-kant. 2S-batteri **JST-XH** + skydd (PTC/rev-FET/TVS); 2S→5V buck (back-feed); IMU (SPI); batteri-sense (I²C-ADC); FC-IO (trigger/rack/mag/magwell/recoil/NFC/MODE/PTT). |
> | **AR0234M** (VEYE) | köps | 29×29, V4L2-driver på CM5, M12-lins + 860 nm bandpass, FFC→carrier-CSI. |
> | **CM5 + carrier** | köps | **CM5 Lite** (microSD-boot via carrierns SD-slot, inget eMMC) — välj *wireless*-SKU (mesh kräver WiFi5/BT5); bänk: CM5 Nano Base. |
>
> **Nyckeländringar mot tidigare iterationer i denna doc:** (a) carrier-elektroniken blev en **HAT på
> carrier-headern** (ej eget DF40-kort) → bara stock-footprints, routbart. (b) emittrarna **sida-vid-sida**
> (ej över/under). (c) **CC-sänkan flyttad optik→** kortare puls-loop, lägre EMI; HAT skickar bara DC VBAT +
> µA IR_MOD + GND. (d) kamera = **AR0234M** (tillgänglig). (e) batteri **JST-XH** (ej XT30).
>
> **Compute bekräftad (`compute_budget_cm5.py`):** CM5 kör CV-pipelinen på <2 % av EN A76-kärna även i
> värsta dagsljus; MIPI-CSI 4-lane → ingen USB-flaskhals. **Orkar driva allt med stor marginal** (båda
> P4-riskerna borta). Sim/test-svit grön. **AR0234M-hålbild verifierad** mot VEYE-måttritning: modul 29×29 mm,
> 4×Ø2 hörnhål = **20×20-kvadrat** (CAM_PITCH=20) centrerad på optiska axeln → optik-PCB:ns kamera-hål flyttade
> till ±10 mm (in-place, routning bevarad). **Öppet (HIL):** IEC 60825-1-ommätning, bänk-bringup. Avsnitten
> nedan beskriver tidigare designiterationer.

> **Status:** designförslag (2026-06). Vapen-noden = **Raspberry Pi Compute Module 5** (Linux).
> Väst/hjälm = oförändrat ESP32-P4. Mesh:en (firmware/run_mesh.py) är transport-agnostisk → blandade noder OK.
>
> **Plattformsval — varför CM5 (och inte P4/Radxa/Orange Pi):** det avgörande beroendet är
> **GS-NIR-kamerans drivrutin**. Rangordning av kamera-driverstöd: **Raspberry Pi ≫ Rockchip(Radxa) >
> Allwinner(Orange Pi)**. Bara på Raspberry Pi har en global-shutter NIR-kamera (AR0234/Mira220/IMX296)
> en **underhållen, turnkey libcamera-drivrutin**. P4 (esp_cam_sensor) och Radxa/RK3566 (vendor-kärna,
> bara rolling-shutter IMX turnkey) kräver egen driver-port. CM5 är dessutom **carrier-native** (precis
> vår arkitektur), starkast i klassen och bäst long-term-support. → kameran blir ett LÖST problem.

## 1. Arkitektur — optik-huvud + carrier + CM5

```
   ┌──────────────── OPTIK-HUVUD (mini-PCB, "business end") ────────────────┐
   │   [IR-emitter D1 + kollimator]   ← över kameran                        │
   │   [  GS-NIR MIPI-KAMERA (utbytbar M12/C-lins + 860 nm bandpass) ]      │
   │   [IR-emitter D2 + kollimator]   ← under kameran (symmetriskt kring axeln) │
   └──────┬─────────────────────────────────────────────┬──────────────────┘
          │ 22-pin MIPI-CSI FFC (kamera)                 │ 2-tråd JST (emitter-ström, pulsad)
          ▼                                              ▼
   ┌──────────────────── CARRIER-PCB (CM5-native) ──────────────────────────┐
   │  • CM5-sockel: 2× 100-pin Hirose DF40 (BtB) — CM5 plugar in            │
   │  • MIPI-CSI: 22-pin FFC-kontakt → kort impedanskontrollerad route → CM5│
   │  • CC-sänka (OPA171 + DPAK-FET + 0R2 sense, 1 A tak / 3 A DNP) → emitter│
   │  • IMU (ICM-42688-P, SPI), 2S → 5 V buck (CM5) + VBAT emitter-rail     │
   │  • rev-skydd, TVS, bulk; batteri-sense; fire-control-IO (trigger/rack/ │
   │    mag/recoil/NFC) — samlar all elektronik likt dagens FC-kort         │
   └───────────────────────────────────┬────────────────────────────────────┘
                                        │ CM5 DF40 (MIPI/SPI/I²C/PWM/UART/USB/5V)
                                        ▼
                        ┌─────────── RASPBERRY PI CM5 ───────────┐
                        │ BCM2712 quad A76 @2,4 GHz · VideoCore  │
                        │ VII · ≤8/16 GB · **Lite (microSD-boot)**│
                        │ · WiFi5/BT5 · 2× MIPI 4-lane · 55×40 mm │
                        └───────────────────────────────────────┘
```

Med CM5 går kameran **via carriern** (vi äger hela MIPI-vägen: 22-pin FFC-kontakt → kort route → CM5
DF40), och emitter-strömmen i **separat** kabel (pulsad 1–3 A borta från MIPI → låg EMI).

## 2. Compute: Raspberry Pi CM5 (BCM2712)

| | Värde | Not |
|---|---|---|
| CPU | quad Cortex-A76 @2,4 GHz | kör Python+OpenCV+`solvePnP` direkt; CV-pipelinen med stor marginal |
| GPU/video | VideoCore VII + HW-ISP + H.265 | ISP avlastar tröskling/debayer; HW-enkoder för vapen-cam |
| RAM | ≤8/16 GB LPDDR4X | rikligt |
| Lagring | **CM5 Lite → microSD-boot** (carrierns SD-slot) | inget eMMC ombord; använd A1/A2-kort + read-only rootfs mot SD-slitage i vapen |
| Radio | **WiFi5 + BT5** (Lite *wireless*-variant) | mesh kräver WiFi → välj Lite-WiFi-SKU, ej den trådlösa-fria; mesh-trafiken är lätt → gott om marginal |
| Kamera | **2× MIPI-CSI 4-lane** (via DF40) | full-frame GS @120 fps möjligt (4-lane) |
| Anslutning | 2× 100-pin Hirose DF40 | **carrier-native** — vår carrier bär kontakterna |
| Mått | 55×40 mm modul | carrier ~55–65×40 |

Mjukvara: **libcamera** → `cv_pose`/`fire_control` (Python, redan paritetstestade) körs direkt;
mesh via `run_mesh`-transporten över WiFi5. **Ingen C-port på vapnet** (Fas 3-C-kärnan kvarstår för
väst/hjälm-P4 + som referens).

## 3. Kamera — driver LÖST av plattformen; lås sensorn

Interfacet: 22-pin MIPI-CSI FFC + **utbytbart M12/C-fäste** + 860 nm bandpass + lins för ~13,7° FOV.
På CM5/RPi har dessa **underhållna libcamera-drivrutiner** (inte längre en öppen fråga):

| Sensor | GS | NIR@860 | Upplösn. | Utbytbar lins | RPi-driver | Rekommendation |
|---|---|---|---|---|---|---|
| **ams Mira220** ⭐ | ✅ | ✅✅ NIR-*enhanced* | 2,2 MP | linsoption/holder | `ams_rpi_kernel` (alla Mira) | **bäst dagsljus-SNR + samma leverantör som OSLON-emittrarna** |
| **Arducam AR0234** | ✅ | ✅ | 2,3 MP | M12/C (Pivariety/industri) | Pivariety libcamera | mognast/enklast libcamera-väg |
| RPi Global Shutter Cam (IMX296) | ✅ | (färg, IR-cut) | 1,6 MP | **C/CS-mount** | native | referens-GS, men färg/IR-cut → mindre lämplig |

**Lins:** ~13,7° H FOV → **16 mm M12** på 1/4″-sensor, **~25 mm** på större 1/2,6″ (AR0234/Mira220).
+ **850/860 nm bandpass** (dagsljus-rejektion — avgörande enligt `ir_link_budget.py`).

**Sub-val kvar:** Mira220 (bäst NIR/SNR, leverantörs-konsolidering m. OSLON) vs AR0234 (enklast libcamera).
Driverproblemet är borta oavsett vilken.

## 4. Bänk-bringup (innan custom-carrier)

**CM5 Nano Base IO Board** (Electrokit, 55×40 mm, 22-pin CSI, USB-C, microSD, ~219 kr, i lager) →
validera CM5 + vald kamera + CV-pipeline + libcamera snabbt och billigt **innan** vi spinnar carriern.
Det är dev-kortet; vapen-carriern nedan är produkten.

## 5. IR-emittrar — 2 st ÖVER+UNDER kameran

- **Symmetriskt kring optiska axeln** → strålarnas tyngdpunkt på siktlinjen (bättre än side-by-side).
- **2× SFH 4725AS (940 nm) i SERIE**, drivna av **CC-sänkan på carriern** (1 A default, 3 A DNP) →
  optik-huvudet bär bara dioder + kollimatorer, ingen aktiv elektronik → litet, robust, lågt EMI.
- **Räckvidd (`ir_link_budget.py`):** 2 emittrar @1 A + bandpass = **~2,9× marginal @153 m** (robust).
- Eye-safety: per apertur = samma 1 A; 2 aperturer = designregel #4. **IEC 60825-1-ommätning vid bringup.**

## 6. Carrier-PCB (CM5-native — samlar all elektronik)

- **CM5-sockel:** 2× 100-pin Hirose DF40C-100DS (standard CM5-interface).
- **MIPI-CSI:** 22-pin FFC-kontakt → kort impedanskontrollerad route (90 Ω diff) → CM5 DF40.
- **CC-sänka:** OPA171 + AOD4184A DPAK + 0R2 sense (1 A) + 0R1 DNP (3 A) + 15k/1k + gate-R + komp —
  **identisk beprövad topologi**. IR_MOD från CM5 PWM-GPIO (56 kHz).
- **IMU:** ICM-42688-P / IIM-42653 på CM5-SPI.
- **Kraft:** 2S (JST-XH) → **5 V buck ≥3 A** (CM5 drar mer än P4/Radxa) + VBAT emitter-rail; rev-polaritet
  P-FET, TVS, bulk-MLCC (56 kHz-puls), PTC. Batteri-sense → ADC (I²C-ADC el. CM5).
- **Fire-control:** trigger/rack/mag-release/magwell-switchar, recoil-PWM+FAULT, NFC (PN532 I²C),
  MODE-väljare. Make-ready-state-maskin i Python.
- **Kontakter:** optik-emitter-kabel (JST 2-pol), batteri (JST-XH), grepp-signaler, ev. headset.

## 7. Effekt & drifttid (2S 2200 mAh = 16,3 Wh)

| Last | Effekt | Not |
|---|---|---|
| CM5 (BCM2712, CV+WiFi) | ~4–6 W | **starkare = törstigare** än P4/Radxa; underklocka v.b. |
| 2× emitter (1 A, ~9 % duty) | ~1,5 W medel-peak | VBAT-rail |
| IMU + sense + misc | ~0,2 W | |
| **Totalt** | **~6–8 W** | → **~2–2,7 h** drifttid |

**Ärlig avvägning:** CM5 är klart kraftfullare men drar mer → kortare drifttid än Radxa (~3–4 h).
Räcker för en speltid; större batteri (3S/3000 mAh) eller underklockning förlänger. Detta är priset för
turnkey-kameran + mest compute.

## 8. Storlek

- **Optik-huvud:** vertikal remsa ~**30 × 65 mm** (kollimator + kamera + kollimator); krymper med mindre
  lenslets. Sitter längs skena/under pipa.
- **Carrier:** ~**55–65 × 40 mm** (CM5-fotavtryck + kringkomponenter). CM5 stackad ovanpå.

## 9. Öppna punkter inför layout

1. **Lås sensorn:** Mira220 vs AR0234 (dagsljus-SNR vs enklaste libcamera) — bekräfta lins-focal + bandpass.
2. **5 V-buck:** dimensionera mot CM5 peak (mät under CV-last; ≥3 A).
3. **MIPI-route på carriern:** 90 Ω diff, längdmatchad, FFC → DF40 (CM5-carrier-referensdesign finns).
4. **Emitter-puls över kabel** (EMI/induktans) — kort tvinnad 2-tråd; CC-sänkan reglerar.
5. **IEC 60825-1-ommätning** för 2-emitter-configen.
6. **Drifttid:** acceptera ~2,5 h ELLER större batteri/underklock.

## 10. Optik-huvud — KLART (hardware/optik_head.py)

`optik-head.kicad_pcb`: 32×66 mm, 2× SFH4725AS i serie över/under kameran, Carclo-ben, **M12-linshållar-
mount (2× M2 @18 mm)** — kameran (Mira220-board + M12-lins) bultas på framsidan, RPi-CSI-FFC → carrier.
0 oanslutna / 0 clearance. Leverans (gerbers+STEP+BOM+centroid) i `leverans/optik-head/`.
⚠️ M12-hållarens 18 mm-pitch: bekräfta mot vald hållare (NPTH, triv. justering).

## 11. PRIMÄR VÄG: HAT på färdigt CM5-carrier-kort (`weapon_hat_netlist.py`)

Enklaste och snabbaste vägen till fungerande vapen: **en HAT som pluggar på ett FÄRDIGT CM5-carrier-korts
40-pin GPIO-header** (t.ex. CM5 Nano Base). Carrier-kortet sköter CM5↔DF40 + kamerans 22-pin MIPI-CSI;
HAT:en bär CC-sänka + IMU + buck + FC-IO + emitter-JST. **Ingen DF40, ingen MIPI på vårt kort → bara
stock-footprints → placeras/routas direkt.**

```
Optik-huvud ──FFC──► [CM5 Nano Base: CM5 + 22-pin CSI + 40-pin header + USB-C]
                                            │ 40-pin header
                         [VÅR HAT] ─────────┘  (CC-sänka, IMU, buck, FC-IO, emitter-JST)
```
- 40-pin headern bär allt HAT:en behöver: **SPI (IMU), I²C (ADC/NFC), PWM GPIO18 (IR_MOD), GPIO (FC), 5V, 3V3, GND.**
  **3V3 från headern matar IMU:ns VDDIO** (löser den öppna punkten).
- **Kraft:** 2S → buck → **5V matas IN i headerns 5V-stift (back-power)**. Emitter-strömmen (puls) på HAT:en, ej headern.
- `weapon-hat.net`: ~85 komp, 0 errors, CC-sänka verifierad. RPi-40-pin-mappning i netlistan.
- **Avvägning:** 3 kort i stacken (CM5+carrier+HAT) → högre + carriern bär oanvänt I/O. Bra för snabb bringup;
  det integrerade DF40-kortet (§12) är produkt-optimalt senare.

## 12. PRODUKT-OPTIMAL (senare): integrerat DF40-carrier — floorplan + byggväg

`weapon-carrier.net` (90 komp, 0 errors) är **schema-komplett**. Att routa kortet kräver **Raspberry Pis
officiella CM5-carrier-KiCad-referens** (DF40-footprints + rekommenderad MIPI/kraft-routning) som grund —
CM5:s 2× DF40C-100DS-kontakter ska INTE handritas. Byggväg:

1. Hämta **RPi CM5 carrier-referensdesign** (KiCad) → ärv DF40-footprints + 5 V/kraft + MIPI-stackup.
2. Importera `weapon-carrier.net`-blocken (`kinet2pcb`) ovanpå referensen.
3. Routa **inkrementellt** (ej freerouting): MIPI först (90 Ω diff, kort, längdmatchad, FFC↔CM5 CSI),
   sen kraft (VBAT/5 V-plan), sen CC-sänka + IMU + FC-IO.

**Floorplan (≈60×45 mm, 4-lager — MIPI + kraftplan):**
```
        ┌──────────────────── 60 × 45 mm, 4-lager ────────────────────┐
   kant │ [JST-XH] [PTC][rev-FET]    ┌─────── CM5 (DF40×2) ───────┐  [FC- │ ← grepp-kablar
   kraft│ [buck 2S→5V][bulk]       │  55×40 modul ovanpå        │   IO: │   (trig/rack/
        │ [ADC+batt-sense]         │                            │  trig │    mag/recoil/
        │                          └────────────────────────────┘  rack │    NFC/MODE)
        │ [CC-sänka: OPA171+DPAK    [IMU]  (nära CM5 SPI)         mag  │
        │  +sense+delare] → [JST→huvud]   [CAM-FFC 22p] ← KORT MIPI →CM5│
        └──────────────────────────────────────────────────────────────┘
```
- **CAM-FFC** placeras intill CM5:s CSI-stift → kortast möjliga MIPI-route (kritiskt).
- **CC-sänka** vid emitter-JST-kanten → emitter-kabeln ut rent, pulsad ström kort.
- **Kraft** (JST-XH→buck) i ett hörn; VBAT-plan matar emitter-rail + buck.
- **FC-IO-kontakter** längs en kant → kablar till greppet.

**Footprints som saknas i miljön (sourcas vid layout):** CM5 DF40 (RPi-referens), 2S→5 V-buck (modul/IC),
JST-XH. Övriga (FFC, OPA171, DPAK, ICM-456xx, JST, R/C) finns.

## 12. Nästa steg

1. **Bänk:** CM5 Nano Base + Mira220 → validera libcamera + CV + range.
2. **Carrier-layout:** hämta RPi CM5-referens → importera `weapon-carrier.net` → inkrementell routning.
3. Bekräfta M12-hållarens mått + MIRA220MINI-mekanik (ams-support) vid mekanik-integration.
