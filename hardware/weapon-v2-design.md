# STRILAS — Vapen-modul v2 (Radxa Zero 3W) — komplett design

> **Status:** designförslag (2026-06). Ersätter den ESP32-P4-baserade optik+fire-control-stacken
> efter beslut: **Radxa Zero 3W** (RK3566, Linux) på vapen-noden. Väst/hjälm = oförändrat (ESP32-P4).
> Mesh:en (firmware/run_mesh.py) är transport-agnostisk → blandade noder OK.

## 1. Varför detta omtag

Tre drivkrafter sammanföll: (a) alla billiga fast-lins-kameror föll på 150 m-kravet (B0332 m.fl.),
(b) ESP32-P4:s `esp_cam_sensor` stödde för få sensorer, (c) önskan om mindre/enklare kort. **Linux på
vapen-noden** löser (a)+(b): libcamera/Rockchip-kärnan stödjer brett av MIPI-sensorer, och den
befintliga **Python-firmwaren körs direkt** (ingen ESP-IDF-port på vapnet). Optiken bryts ut till ett
litet **optik-huvud** på kabel → resten blir ett **carrier-kort** likt dagens fire-control.

## 2. Arkitektur — 2 kort + Radxa

```
   ┌─────────────────── OPTIK-HUVUD (mini-PCB, "business end") ───────────────────┐
   │   [IR-emitter D1 + kollimator]   ← över kameran                               │
   │   [  MIPI-KAMERA (GS, NIR, M12 16/25 mm + 860 nm bandpass)  ]  ← på axeln     │
   │   [IR-emitter D2 + kollimator]   ← under kameran (symmetriskt kring axeln)    │
   └───────┬───────────────────────────────────────────────┬─────────────────────┘
           │ 22-pin MIPI-CSI FFC (kamera)                   │ 2-tråd JST (emitter-ström, pulsad)
           │  (rakt till Radxa CSI — EMI-separerad)         │
           ▼                                                ▼
   ┌──────────────────────────── CARRIER-PCB (på Radxa 40-pin header) ────────────┐
   │  • CC-sänka (OPA171 + DPAK-FET + 0R2 sense, 1 A tak / 3 A DNP) → emitter      │
   │  • IMU (ICM-42688-P / IIM-42653, SPI)                                          │
   │  • Kraft: 2S → 5 V buck (Radxa) + VBAT emitter-rail; rev-skydd, TVS, bulk     │
   │  • Batteri-sense (ADC), trigger/rack/mag-switchar, recoil-ctrl, NFC (= FC)    │
   │  • Kontakter: optik-emitter-kabel, batteri (XT30/JST), grepp-signaler          │
   └──────────────────────────────────┬───────────────────────────────────────────┘
                                       │ 40-pin GPIO header (SPI/I²C/PWM/UART/5V/GND)
                                       ▼
                         ┌─────────── RADXA ZERO 3W ───────────┐
                         │ RK3566 quad A55 1,6 GHz · ≤8 GB ·    │
                         │ 0,8 TOPS NPU · ISP · WiFi6/BT5 ·     │
                         │ 22-pin MIPI-CSI · 65×30 mm          │
                         └─────────────────────────────────────┘
```

**Varför kameran går RAKT till Radxa-CSI (ej via carriern):** MIPI-CSI är impedanskontrollerade
differentialpar — att dra dem genom en extra kontakt + carrier-spår adderar risk. Kamerans 22-pin FFC
är redan en "kabel" → låt den vara kabeln. Emitter-strömmen (pulsad 1–3 A, 56 kHz) går i en **separat**
2-trådskabel → håller EMI borta från MIPI.

## 3. Compute: Radxa Zero 3W (RK3566)

| | Värde | Not |
|---|---|---|
| CPU | quad Cortex-A55 @1,6 GHz | kör Python+OpenCV direkt; CV-pipelinen ryms med marginal |
| NPU | 0,8 TOPS | tillgänglig om vi vill ML-klassa blink-ID senare (ej krävt nu) |
| ISP | hårdvaru-ISP | tröskling/debayer/gain i HW → avlastar CPU |
| RAM | ≤8 GB LPDDR4 | rikligt |
| Radio | **WiFi6 + BT5** | mesh mot väst/hjälm/server |
| Kamera | **22-pin MIPI-CSI 0,5 mm** | standard-FFC |
| GPIO | 40-pin Pi-kompatibel header (SPI/2×I²C/6×PWM/5×UART) | carrier-interface |
| Mått | 65×30 mm, Pi-Zero-hålbild | carriern matchar |
| Mat | 2× 5 V in | 2S→5 V buck på carriern |

Mjukvara: **libcamera/V4L2** → `cv_pose`/`fire_control` (Python, redan paritetstestade) körs direkt;
mesh via `run_mesh`-transporten över WiFi6. Ingen C-port behövs på vapnet (Fas 3-C-kärnan kvarstår
för väst/hjälm-P4 + som referens).

## 4. Kamera — KAMERA-AGNOSTISKT interface, kandidat-shortlist

Kortet låser **interfacet** (22-pin MIPI-CSI FFC + M12/C-fäste + 860 nm bandpass + utbytbar lins för
~13,7° FOV), inte sensorn. Slutval efter driver-verifiering på Zero 3W:

| Sensor | GS | NIR@860 | Upplösn. | Utbytbar lins | RK3566-driver | Kommentar |
|---|---|---|---|---|---|---|
| **OV9281** ⭐ | ✅ | ✅ (NoIR) | 1 MP | M12-hållare/industri | **Rockchip-BSP har ov9281** (verifiera Zero 3W-image) | ledande: GS+driver mest troligt turnkey |
| AR0234 | ✅ | ✅ | 2,3 MP | M12/C (VEYE/industri) | osäker på RK3566 (VEYE-Radxa = bara IMX) → verifiera/kernel-jobb | bäst PnP om driver löser sig |
| ams Mira220 | ✅ | ✅✅ (NIR-enh., samma lev. som OSLON) | 2,2 MP | linsoption | RPi-driver finns → trolig RK-port | bäst dagsljus-SNR, mer integ. |
| IMX462/OV5647-NoIR | ❌ rolling | ✅ | 2–5 MP | M12 | **mogen** (libcamera/VEYE) | fallback: rolling + fast-pan-grind om GS-driver strular |

**Lins:** ~13,7° H FOV. På 1/4″ OV9281 = **16 mm M12**; på större 1/2,6″ AR0234 = **~25 mm**. + **850/860 nm
bandpass** (dagsljus-rejektion — bekräftat avgörande i `ir_link_budget.py`). Kravet "utbytbart fäste"
(M12-hållare/C-mount) står kvar — köp INTE fast-lins-moduler.

**Öppet (HIL):** verifiera GS-sensorns driver på Zero 3W-image + libcamera-pipeline + verklig fps/lanes.

## 5. IR-emittrar — 2 st ÖVER+UNDER kameran (din idé — och optiskt bättre)

- **Symmetriskt kring optiska axeln** → strålarnas gemensamma tyngdpunkt ligger **på siktlinjen**
  (side-by-side-ovanför ger en offset). Båda kollimerade framåt; vertikal placering påverkar ej
  träffpunkten på avstånd.
- **2× SFH 4725AS (940 nm) i SERIE**, drivna av **CC-sänkan på carriern** (1 A default, 3 A DNP) →
  optik-huvudet bär bara dioder + kollimatorer, **ingen aktiv elektronik** → litet, robust, lågt EMI.
- **Räckvidd (ir_link_budget.py):** 2 emittrar @1 A + bandpass = **~2,9× marginal @153 m** (robust);
  1 emitter ~1,5× (tunt). Med 2 emittrar håller du marginal **och** redundans — värt den extra
  kollimatorn här eftersom huvudet ändå är en vertikal remsa.
- Eye-safety: per apertur = samma 1 A som idag; 2 separata aperturer = designregel #4 bevarad.
  **Kräver IEC 60825-1-ommätning vid bringup** (oförändrat).

## 6. Carrier-PCB (samlar all elektronik — "FC + optik-driver" i ett)

- **CC-sänka:** OPA171 + AOD4184A DPAK + R(0R2 sense, 1 A) + R(0R1 DNP, 3 A) + 15k/1k + gate-R + komp —
  **identisk beprövad topologi** från dagens optik-netlist. IR_MOD från Radxa PWM-GPIO (56 kHz).
- **IMU:** ICM-42688-P / IIM-42653 på Radxa-SPI (header). Re-ankrar attityd per frame.
- **Kraft:** 2S (XT30) → **5 V buck** (≥2 A, matar Radxa) + **VBAT emitter-rail**; rev-polaritet P-FET,
  TVS, bulk-MLCC för 56 kHz-pulsen, PTC (3 A-skala). Batteri-sense → Radxa ADC (eller I²C-ADC).
- **Fire-control (som dagens FC-kort):** trigger/rack/mag-release/magwell-switchar, recoil-PWM+FAULT,
  NFC (PN532 I²C), MODE-väljare. Make-ready-state-maskin i Python.
- **Kontakter:** optik-emitter-kabel (JST 2-pol), batteri (XT30), grepp-signaler (JST), ev. headset.
- Monteras på Radxa 40-pin header (board-to-board) + Pi-Zero-standoffs.

## 7. Effekt & drifttid (2S 2200 mAh = 16,3 Wh)

| Last | Effekt | Not |
|---|---|---|
| Radxa RK3566 (CV+WiFi6) | ~2,5–3,5 W | @5 V via buck (~0,9 verkningsgrad) |
| 2× emitter (1 A, ~9 % duty) | ~1,5 W medel-peak | VBAT-rail |
| IMU + sense + misc | ~0,2 W | |
| **Totalt** | **~4–5 W** | → **~3–4 h** drifttid |

Likt dagens budget. Boot: Linux ~sek → håll i suspend för "instant ready" (RK3566 har snabb resume).

## 8. Storlek

- **Optik-huvud:** vertikal remsa ~**30 × 65 mm** (kollimator Ø~20 + kamera ~25 + kollimator Ø~20).
  Krymper med mindre kollimator-optik (Ø10–15 lenslets) → ~25×50. Sitter längs skena/under pipa.
- **Carrier:** ~**65 × 35 mm** (Radxa-fotavtryck + lite), stackad på Radxa.
- Jämfört med dagens 54×74 optik + separat FC: optiken blir ett litet huvud, all elektronik ett kort.

## 9. Öppna punkter att verifiera innan layout

1. **Kamera-driver på Zero 3W** (GS-sensor: OV9281 i Rockchip-BSP? annars kernel-jobb) + libcamera-fps/lanes.
2. **Lins-focal för 13,7°** på vald sensor (16 mm OV9281 / 25 mm AR0234) + 860 nm-bandpass-passning.
3. **5 V-buck-dimensionering** mot Radxa peak-ström (mät verkligt under CV-last).
4. **Emitter-puls över kabel** (EMI/induktans) — kort tvinnad 2-tråd; CC-sänkan reglerar.
5. **IEC 60825-1-ommätning** för 2-emitter-configen.
6. **MIPI-FFC-längd** huvud→Radxa-CSI (håll < ~20–30 cm).

## 10. Nästa steg

1. Lås kameran (verifiera OV9281-på-Zero-3W-driver → annars Mira220/industri-AR0234).
2. Rita **optik-huvudet** (SKiDL-netlist + pcbnew-placering: 2 emitter + kollimator-hålbild + kamera-mount + FFC + JST).
3. Rita **carriern** (CC-sänka + IMU + buck + FC-IO + Radxa-header) — återanvänd dagens optik/FC-netlistor.
4. Uppdatera `firmware/config.py` (sensor/lins/F_PX för vald kamera) + `hardware/camera-selection.md`.
