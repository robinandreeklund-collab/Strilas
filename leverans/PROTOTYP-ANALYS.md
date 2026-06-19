# STRILAS — komplett prototyp-analys (pinout · krets-sim · beställning)

> Genererad och **maskin-verifierad** mot de faktiska `.net`/`.kicad_pcb`-filerna.
> Återskapa allt: `python3 hardware/verify_p4_pinout.py` · `python3 hardware/sim_circuit.py`
> · `cd hardware && python3 ../vapen-stack/gen_nextpcb.py`

## 0. Sammanfattning — prototyp-status

| Kort | Pinout (P4) | Krets-sim (ström/signal) | Routning | Order-klar |
|---|---|---|---|---|
| **weapon-module (optik)** | ✓ 0 fel | ✓ PASS | 0/0 | ✓ |
| **firecontrol** | ✓ 0 fel | ✓ PASS | 0/0 | ✓ |
| **helmet-mb (Ø96)** | ✓ 0 fel | ✓ PASS | 0/0 | ✓ |
| **vest-mb** | ✓ 0 fel | ✓ PASS | 0/0 | ✓ |
| **vest-patch** | — (ingen P4) | ✓ PASS | 0/0 | ✓ |
| **led-tab** | — (passiv micro-PCB) | — | 0/0 | ✓ |

**0 pinout-fel, 0 krets-fel** över alla kort. Endast medvetna varningar (USB-JTAG, se §1.3).

---

## 1. Pinout-verifiering mot ESP32-P4

ESP32-P4 monteras som stackad **Waveshare ESP32-P4-WIFI6**-modul via 2× kant-kontakt
(edge A = 16 signal-GPIO, edge B = kraft + 11 GPIO). Modulen exponerar bara "säkra"
GPIO på kanten — flash/PSRAM/SDIO-till-C6/USB-HS-PHY är internt och når aldrig kanten.

**Databladsfakta (verifierat juni 2026, Espressif ESP-IDF/datablad):**
55 GPIO (GPIO0–54) · strapping = **GPIO34–38** · USB-Serial-JTAG = **GPIO24/25** ·
**inga input-only-pinnar** (till skillnad från klassiska ESP32).

### 1.1 Nät→GPIO (härlett ur de faktiska .net + kant-geometrin, själv-verifierat mot kraft/GND)

**weapon-module** (edge B, 6 signal-GPIO): GPIO20=IR_MOD, GPIO22=MISO, GPIO23=SCK,
GPIO26=IMU_INT, GPIO27=MOSI, GPIO32=nCS · *(SPI till optik-IMU + 56 kHz IR-modulering)*

**firecontrol** (edge A, 12 signal-GPIO): GPIO2=RECOIL_PWM, GPIO3=MAG_REL, GPIO4=TRIG,
GPIO5=RACK, GPIO7=NFC_SDA, GPIO8=NFC_SCL, GPIO24=MODE_A, GPIO25=MODE_B,
GPIO28=RECOIL_FAULT, GPIO29=MAGWELL, GPIO49=IMU2_INT, GPIO50=IMU3_INT

**helmet-mb** (edge A+B, 18 signal-GPIO): GPIO2=LED_EN, GPIO3=IMU_INT, GPIO4=GNSS_TX,
GPIO5=GNSS_RX, GPIO7=I2C_SDA, GPIO8=I2C_SCL, GPIO20=PTT, GPIO23=I2S_MCLK,
GPIO24=I2S_DIN, GPIO25=AMP_SD, GPIO28=I2S_BCLK, GPIO29–31/51/52=5×DATA,
GPIO49=I2S_DOUT, GPIO50=I2S_LRCK *(edge A helt fullsatt; edge B har 9 lediga GPIO)*

**vest-mb** (edge A+B, 14 signal-GPIO): GPIO52/51/31/30/29/28/50/49/5/4 = 10× patch-DATA,
GPIO3=TPIC_SER, GPIO2=TPIC_SRCK, GPIO8=TPIC_RCK, GPIO7=LED_EN *(GPIO24/25 lediga)*

### 1.2 Kontroller som passerar (alla kort)
- **Giltigt intervall** GPIO0–54 ✓
- **Inga dubbel-använda GPIO** (0 konflikter) ✓
- **Strapping (34–38)** används aldrig (exponeras inte ens på kanten) ✓
- **Kraft/GND-integritet:** alla kant-GND-stift på GND, VSYS=VBAT, 3V3-tapp=+3V3 ✓
- **Peripheri-mux:** P4:ans GPIO-matris ruttar I²C/SPI/UART/I²S till ~valfri GPIO →
  alla buss-tilldelningar funktionellt giltiga. Kameran (OV9281) går via modulens
  dedikerade MIPI-CSI-FPC, ej kant-GPIO → ingår ej i dessa nät.

### 1.3 Varningar (medvetna val — ej blockerande)
- **GPIO24/25 = USB-Serial-JTAG.** Används av **firecontrol** (MODE_A/B, läges-ratt) och
  **helmet-mb** (I2S_DIN/AMP_SD). Konsekvens: JTAG-över-USB tappas på de två P4:orna.
  **OK för prototyp** — Waveshare-modulen flashas via USB-C (HS-OTG), inte via USB-JTAG.
  - *Rekommendation (valfri, ej gjort — kräver omroutning):* helmet kan flytta I2S_DIN→edge B
    GPIO22 och AMP_SD→GPIO26 (9 lediga edge-B-GPIO) för att frigöra 24/25; FC kan flytta
    MODE_A/B→edge A GPIO30/31 (lediga). vest-mb använder redan **inte** 24/25.
  - *AMP_SD (GPIO25) boot-puls:* GPIO25 har intern pull-up i USB-JTAG-läge vid reset →
    PAM8302A kan kort aktiveras innan firmware kör (möjligt litet "pop"). Åtgärd om önskat:
    100 kΩ pulldown på AMP_SD, eller acceptera (kort, ofarligt).

---

## 2. Krets-simulering (ström + signaler)

Funktionell krets-sim på nät-nivå (`hardware/sim_circuit.py`) — bygger kraftskenor ur
passningselement, summerar strömbudget mot källkapacitet och kontrollerar varje signalnät.

### 2.1 Kraft / strömbudget

| Kort | VBAT-last (topp) | +3V3-last | +3V3-källa | Marginal |
|---|---|---|---|---|
| weapon-module | ~1002 mA (IR-emitter CC ~1 A topp, gatad) | ~1 mA | P4 onboard-buck 2 A | stor |
| firecontrol | — (matas via P4) | ~2 mA | edge-B kraft-tapp | stor |
| helmet-mb | ~1050 mA (6 OSLON, 3 grenar) + amp 180 mA | ~197 mA | AP63203 2 A | ✓ |
| vest-mb | ~240 mA (3 vibratorer samtidigt) | ~20 mA | P4 onboard-buck | stor |
| vest-patch | ~700 mA (4 OSLON, 2 grenar) | ~4 mA | HT7333 LDO 250 mA | ✓ |

Alla skenor inom källkapacitet. (LED-konstellation är **pulsad/modulerad** → medel långt
under topp; budgeten räknar värsta fall.)

### 2.2 Signaler (per kort, alla PASS)
- **Inga flytande IC-pinnar.** Enda 1-nods-näten är medvetet oanvända *kontakt*-stift
  (helmet F9P-puck PPS/RSV) — flaggas som info, ej fel.
- **I²C-pullups verifierade:** firecontrol (NFC_SDA/SCL) och helmet (I2C_SDA/SCL) har 4k7→+3V3 ✓.
- **Avkoppling:** varje strömförande IC har minst en avkopplings-C på sin skena ✓.
- **Spänningsdomän:** 3,3 V genomgående (P4 + all periferi native 3V3 → **inga level-shifters**).

---

## 3. Beställnings-plan (DNP / vad NextPCB placerar vs vad du löder själv)

**Princip (din regel):** allt som är lätt att handlöda — stiftlistar, socklar, JST-PH/XH/EH,
batteri-kontakter, knappar — sätts **DNP** (står kvar i BOM som beställningsreferens men
NextPCB placerar **inte**, och de utesluts ur centroid). Du beställer och löder dem själv.
Finpitch-SMD (JST-GH 1,25 mm puck-kontakt, ES8388-codec, PAM8302A-amp, IMU) **placeras av NextPCB**.

| Kort | NextPCB placerar (SMT) | DU beställer + handlöder (DNP) |
|---|---|---|
| **weapon-module** | 16 delar | J1 (P4-sockel edge B), J2 (batteri-XH). *Prototyp:* U1+C3/C4/C5 (IMU på breakout), R3 (1A fail-safe) |
| **firecontrol** | 10 delar | J1 (P4-sockel A), J2 (kraft-tapp), J3 TRIG, J4 RACK, J5 MAG_REL, J6 MAGWELL, J7 recoil, J8 NFC, J9 OLED, J10 läges-ratt. *Prototyp:* U1/U2 (IMU) |
| **helmet-mb** | 43 delar (inkl F9P-GH-puck J1/J12, ES8388, PAM8302A, IMU) | J8/J9 (P4-socklar), J2–J5 (patch-PH), J6/J7/J11 (mik/högt/PTT-PH), J10 (batteri-XH), U3–U6 (4 ledade TSOP), D5–D10 (6 LED-tab) |
| **vest-mb** | 12 delar (TPIC ×2 m.m.) | J11/J12 (P4-socklar), J1–J10 (zon-PH-headers), J13 (XT30-batteri) |
| **vest-patch** | 17 delar (860 nm-LED, BAT54, HT7333) | J1 (patch-PH), U1–U4 (4 ledade TSOP), D7–D10 (4 LED-tab) |
| **led-tab** | OSLON (NextPCB) | — (löds in i moderkortets tab-sockel av dig) |

**Beställnings-artefakter per kort** finns i `leverans/<kort>/`: `*-gerbers.zip`, `*-bom.xls`
(DNP-kolumn ifylld), `*-centroid.csv`+`.xls` (endast SMT-placerade), `*.step`.

### Du måste själv beställa (utöver PCB+SMT):
- 3× **Waveshare ESP32-P4-WIFI6**-moduler (weapon-stack, helmet, vest).
- Alla **JST-kontakter + kabel** (PH/XH/GH-honor till puck/patch/headset/batteri), stiftsocklar
  (2,54 mm 1×14/1×15/1×20) till P4-stackarna, knappar/rotary, XT30-kontakt (väst).
- **ZED-F9P RTK-puck** (el. alt UM980/F9P Ø86), **electret-mik + öronhögtalare** (helmet),
  **ERM-vibratorer** (väst), **Carclo 10195-lins + 10734-hållare** (optik, över emittern).
- Ledade **TSOP4856** + **OSLON LED-tab**-micro-PCB (handlöds i sina socklar).

---

## 4. Återskapa verifieringen
```sh
python3 hardware/verify_p4_pinout.py     # pinout mot P4-datablad  → 0 fel
python3 hardware/sim_circuit.py          # ström+signal ALLA kort  → ALLA PASS (enhetlig efterföljare
                                         #   till äldre hardware/system_sim.py som bara täckte vapen-stacken)
cd hardware && python3 ../vapen-stack/gen_nextpcb.py   # BOM+centroid (DNP)
```

> *Not:* `hardware/system_sim.py` är en äldre vapen-stack-specifik flödes-sim som inte uppdaterats
> till nuvarande CC-emitterdrivare/15-stifts edge A — använd `sim_circuit.py` (täcker alla kort korrekt).
