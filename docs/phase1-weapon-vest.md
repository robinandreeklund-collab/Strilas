# STRILAS — Fas 1: Komplett byggskiss för Vapen + Väst

> **Mål:** en självständig spelarsats — **vapen + väst/hjälm + magasin** — som spelar en komplett force-on-force-/MILES-match **lokalt**, utan UWB-ankare, central server eller vapenkamera. Allt som behövs för att "ett vapen ska funka precis som tänkt" finns här. Fas 2-lagren (UWB-positionering, server-baserad ballistik-/flygtidsadjudikation, live-cam, AAR) **pluggas in senare utan omdesign** tack vare hooks som specas i Del 11.
>
> Bygger vidare på `docs/hardware-analysis.md`. Säkerhetskraven (IR Class 1 i hårdvara, cold-mate-kontakter, BMS-laddning) är icke förhandlingsbara.

---

## 0. Den viktigaste designsanningen i Fas 1

README:ns kärna är **central, positionsbaserad adjudikation** (servern avgör träff utifrån båda spelarnas position + IMU + simulerad flygtid). **Det är ett Fas 2-funktion** — det kräver UWB.

I Fas 1 avgörs träff **lokalt och direkt**, precis som riktig MILES och all kommersiell laser-tag: *träffar IR-strålen din motståndares detektor, så registreras en träff med den skadekod paketet bär.* Det här är **inte en nedgradering** — det är ett fullständigt, rättvist och roligt spel.

**Och det viktigaste:** eftersom **IR-emittern är borrlinjerad (fast monterad i pipan)** så klättrar strålen fysiskt med mynningen vid rekyl. Det betyder att **okontrollerade serier vandrar av målet helt av sig själv** — recoil-to-aim-loopen fungerar "gratis" via fysiken redan i Fas 1. IMU:n loggar klättringen (för Fas 2-adjudikation) och kan valfritt lägga på en eldhastighets-/stabilitetspenalty. Den fulla IMU-matade trajektorie-adjudikationen är en **förfining** i Fas 2, inte en förutsättning.

| Funktion | Fas 1 (lokal) | Fas 2 (server/UWB) |
|---|---|---|
| Träffdetektering | Direkt stråle + skadekod | + positionell flygtidsadjudikation |
| Recoil-to-aim | Fysisk (borrlinjerad stråle klättrar) + IMU-logg | IMU matar nästa skotts simulerade bana |
| Ballistik | Vapenprofil (RoF-cap, skada, mag) lokalt | + muzzle velocity, drag, drop, time-of-flight |
| Poäng/hälsa | Lokalt i väst, peer-delning via ESP-NOW | + central telemetri-DB, live-karta, AAR |
| Position | — | UWB + GNSS + IMU-fusion |

### Plattformsbeslut: bygg på Fas 2-plattformen direkt

Vi bygger Fas 1 **direkt på ESP32-P4 PICO** (P4 + C6 ombord) istället för ESP32-S3 — för att slippa en firmware-port (Xtensa→RISC-V) senare. P4:s Fas 2-gränssnitt (**MIPI-CSI-kamera + HW H.264 1080p30, MIPI-DSI för AR-HUD, ljud in/ut, WiFi 6**) finns redan på kortet och ligger **vilande** i Fas 1 — de aktiveras i Fas 2 utan hårdvarubyte. Dual-core låter oss pinna IR/rekyl/trigger-timing på en kärna och låta C6 sköta radion. **Avvägning:** P4-ekosystemet (ESP-IDF) är nyare och drar mer ström än S3 — men Fas 1-perifererna (RMT, MCPWM/LEDC, SPI, I²C, GPIO, TWAI/CAN) är väl stödda; de avancerade bitarna (MIPI/H.264) rör bara Fas 2. Västen kör **ESP32-C6** (RMT-avkodning + Thread-mesh-väg).

---

## 1. Systemöversikt — spelarsats (Fas 1)

```
                       PLAYER KIT  (självständig, ingen infrastruktur)
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│   VAPENENHET (ESP32-P4 PICO)                     VÄST + HJÄLM (ESP32-C6)   │
│   ┌───────────────────────────┐   ESP-NOW        ┌──────────────────────┐  │
│   │ Fire-control FSM           │◄═══════════════►│ Hit/health FSM        │  │
│   │ IR-TX (RMT, 56 kHz kodad)  │   (på kroppen)   │ IR-RX zon-avkodning   │  │
│   │ Recoil-styrning (load-sw)  │                  │ Zoner: hjälm 360°,    │  │
│   │ IMU (mynningsklättring)    │                  │  bröst/rygg/vä/hö     │  │
│   │ NFC (magasin-ammo)         │                  │ Feedback: LED/haptik/ │  │
│   │ HUD (OLED: ammo/träff/state)│                 │  ljud, "KIA"-indikator │  │
│   │ Avtryckare/rack/mag-release │                 │ Egen 1S-cell + buck   │  │
│   │ Logikcell + buck            │                 └──────────────────────┘  │
│   └──────────┬─────────────┬───┘                                            │
│              │ kall-mate    │ IR-stråle (borrlinjerad, lins ~±15°)          │
│              │ kraftkontakt  └──────────────►  (mot motståndarens väst)      │
│   ┌──────────▼──────────┐                                                   │
│   │ MAGASIN              │                                                   │
│   │  NFC-tag (ammo)      │                                                   │
│   │  Rekyl-LiPo          │                                                   │
│   │  Kraftkontakter >25A │                                                   │
│   └─────────────────────┘                                                   │
└──────────────────────────────────────────────────────────────────────────┘

   Admin/medic-enhet (valfri): en enkel IR-sändare som skickar MilesTag II
   kommandopaket (respawn / add-health / new-game) — eller lokal respawn-timer.
```

**Två radio-roller i Fas 1, båda ESP-NOW (ingen AP behövs):**
- **Vapen ↔ egen väst/hjälm** — väst rapporterar "jag är träffad/KIA", vapen speglar till HUD + bolt-lock. Hälsan/livet *bor i västen*.
- **Peer ↔ peer (valfritt)** — vapen kan broadcasta skott-/träffhändelser för enkel matchpoäng utan server. (Hook: samma frames vidarebefordras till en gateway i Fas 2.)

---

## 2. Vapenenhet — komponenter & motivering (Fas 1)

| Block | Del (Fas 1) | Motivering / not | Fas 2-väg |
|---|---|---|---|
| MCU | **ESP32-P4 PICO** (P4 + C6 ombord) | Dual-core RISC-V @400 MHz: pinna IR/rekyl/trigger på en kärna, C6 sköter radio (WiFi6/BLE/802.15.4/ESP-NOW). RMT för IR-bärvåg. **Fas 2-gränssnitt (MIPI-CSI-kamera + H.264, MIPI-DSI, ljud) finns ombord — vilande.** Byggs på målplattformen direkt → ingen port senare. | samma kort: aktivera kamera/HUD/WiFi6 |
| IR-emitter | **ams-OSRAM SFH 4715AS** (860 nm) ×1–2 + lins/snoot ~±15° | Trivialt Class 1 (inkoherent), ~30–60 m med lins. **HW-strömgräns via resistor = ögonsäkerhetstak.** | + diffuserad 905 nm-laservariant (verifierad AE) |
| IR-driver | **AO3400** logic-level MOSFET + serie-strömresistor + gate-R 100 Ω | De-facto-standard i DIY-lasertag; robust. R_limit sätter peak-ström (=säkerhetstak). Bärvåg gateas från RMT-pin. | iC-HG om laser |
| IMU | **TDK ICM-45686** (SPI), 6DOF, gyro ≥1–2 kHz | Fångar sub-100 ms mynningsklättring; magnetometer-fri (vapen = stål). | (oförändrad) |
| NFC | **PN532** (I²C) + magwell-switch | Enkelt, mogna libb. Räcker för Fas 1 ammo-logik. | → ST25R3916 + NTAG424 DNA (anti-fusk) |
| HUD | **micro-OLED SSD1306/SH1107** (I²C/SPI) | Ammo · träffar · weapon state · batteri. | + AR-reticle (waveguide) |
| Avtryckare | mikrobrytare → GPIO (debounce) | semi/burst/full, RoF-cap från profil. | — |
| Rack-sensor | mikrobrytare/hall på charging handle → GPIO | "chamber a round" → soft-start rekylskena. | — |
| Mag-release | mikrobrytare/hall → GPIO | släpp skena FÖRST, sen kall extraktion. | — |
| Rekylaktuator | **reciprok. massa** (solenoid Fas 1-prototyp → BLDC+vev+ODrive S1 final) | PWM-skalad felt-recoil per profil. | BLDC/FOC per-profil-kraftkurva |
| Rekyl-load-switch | **TI TPS25983** 20 A eFuse (soft-start) + SS54 flyback + cap-bank 2×2200 µF | Inrush/OC/SC/termiskt skydd i ett chip. På endast mellan rack och mag-release. | — |
| Ljud | **native på P4 PICO** (I²S in+ut) — annars MAX98357A + högtalare | skott/tom/träff-ljud → realism (README roadmap). | + mikrofon-capture för AAR + bolt-lock/muzzle-report |
| Logikbatteri | 2S Li-ion (t.ex. 2×18650) + buck 3V3/5V | ~0.95 A snitt; håller noden vid liv utan magasin. | — |
| Radio | ESP-NOW (inbyggt) | vapen↔väst + peer-poäng. | + WiFi/server-uplink |

---

## 3. Väst + hjälm ("väst") — komponenter (Fas 1)

| Block | Del | Not |
|---|---|---|
| MCU | **ESP32-C6** | RMT avkodar IR-bärvåg i HW; WiFi6/BLE/**802.15.4 (Thread)** för ESP-NOW nu + resilient mesh i Fas 2; billig (~$3). |
| Detektorer | **Vishay TSOP misc. 56 kHz** (matcha emitter!), zonindelade | Avkodar bärvåg i kapsel, solljus-/AGC-immunitet "gratis". |
| — hjälm "halo" | 6–8 st, utåtvinklade | full 360°-täckning av huvudet (MILES-mönster). |
| — torso | 8–16 st i kluster: **bröst / rygg / vä / hö** | varje zon = egen MCU-ingång → identifierar träffzon. |
| Träff-feedback | WS2812 LED-remsor (lagfärg + träffblink) + haptisk motor + I²S-ljud | tydlig "du är träffad/KIA". |
| KIA-indikator | LED på hjälmtopp / ryggtavla | synlig för andra spelare. |
| Batteri | 1S Li-ion + buck 3V3/5V | egen kraft (ingen kabel tvärs kroppen). |
| Länk | ESP-NOW → vapen | rapporterar träff/KIA, tar emot respawn/health. |

**Zon-till-ingång & träfflogik:** varje zon dras till en egen GPIO (eller via RMT-RX/interrupt + I/O-expander MCP23017 om pinnar tryter). Den zon vars TSOP avkodar ett giltigt paket avgör träffplats. Väst applicerar **lokal zon-multiplikator** (huvud > bröst > extremitet) på paketets skadekod, drar hälsa, och vid hälsa = 0 → **KIA-lockout** + notis till eget vapen (bolt-lock + HUD "KIA") tills respawn.

```
   HJÄLM-HALO (6–8 TSOP, 360°)
        ◍   ◍   ◍
      ◍   [huvud]   ◍          ──► zon HEAD
        ◍   ◍   ◍

   TORSO (8–16 TSOP)
   ┌───────────────┐
   │  ◍   BRÖST  ◍ │  ──► zon CHEST
   │ ◍           ◍ │
   │◍   VÄ │ HÖ   ◍│  ──► zon LEFT / RIGHT
   │ ◍           ◍ │
   │  ◍   RYGG   ◍ │  ──► zon BACK   (på baksidan)
   └───────────────┘
```

---

## 4. Magasin (Fas 1)

| Del | Spec | Not |
|---|---|---|
| NFC-tag | **NTAG215** (passiv) | UID · capacity · remaining · profile (se README tag-layout). Skrivs en gång vid extraktion + en gång vid bas-omladdning. |
| Rekylbatteri | hög-C LiPo (≥25C) eller **Molicel P42A/P45B** | matar *endast* rekylskenan. |
| Kraftkontakter | rated **>25 A**, fjäderbelastade | kall-mate; bryts aldrig under last (FSM garanterar). |

**Ammo ≠ laddning:** bas-omladdning = snabb NFC-omskrivning + (separat) långsam batteriladdning. Rotera en pool av magasin. (Anti-fusk HMAC/NTAG424 = Fas 2.)

---

## 5. Engagemangssekvens (Fas 1, helt lokal)

```
 SKYTT                                              MÅL (väst)
 ───────                                            ──────────
 avtryckare (i READY)
   │
   ├─► RMT sänder MilesTag II-paket ──IR-stråle──►  TSOP i en zon avkodar
   │     (header + shooterID + team + damage)        │
   ├─► rekyl fyrar (PWM ur profil)                    ├─ giltig header + bitcount?
   ├─► IMU samplar mynningsklättring (logg)           ├─ zon-multiplikator × damage
   ├─► ammo − 1                                        ├─ hälsa − skada
   └─► HUD uppdateras                                  ├─ LED/haptik/ljud "TRÄFF"
                                                       └─ hälsa ≤ 0 → KIA-lockout
                                                            │ ESP-NOW
                                                            ▼
                                                       skyttens HUD: "KILL"
                                                       målets vapen: bolt-lock + "KIA"
```

Borrlinjerad emitter → vid full-auto klättrar strålen fysiskt och serien vandrar av målet (realistisk rekyl utan serverberäkning). RoF capas av rekylcykeln (~12 Hz) och profilen.

---

## 6. Make-ready-tillståndsmaskin (Fas 1, oförändrad princip)

```
NO MAG ──insert mag──► MAG IN  (rail OFF, kalla kontakter)
                          │
                          └─ rack charging handle
                                 └─ validate (mag present via NFC, ammo>0)
                                       └─ soft-start rekylskena (TPS25983)
                                             └─ chamber ──► READY (rail ON)
READY ──avtryckare──► IR + rekyl, ammo−1 ──► READY
READY ──ammo == 0──► EMPTY (eld blockerad, bolt-lock)
EMPTY ──byt mag + re-rack──► READY
KIA   ──(från väst)──► eld blockerad tills respawn
ANY   ──mag-release──► släpp skena FÖRST → mag ut (kall) → skriv tag → NO MAG
```

Skenan är på **endast mellan rack och mag-release** → kraftkontakterna görs/bryts alltid kalla.

---

## 7. Kraftträd (Fas 1)

```
LOGIKRAIL (vapen)            internt 2S Li-ion ─► buck 3V3 ─► MCU, IMU, NFC, OLED, IR-logik
   ~0.95 A snitt                              └► buck 5V  ─► TSOP-logik, LED, I²S-ljud

REKYLRAIL (vapen)            magasin-LiPo ─► KALL-MATE kontakt >25A
   ~4 A snitt, ~20 A peak                  └► TPS25983 eFuse (soft-start, OC/SC/termiskt)
                                              └► cap-bank 2×2200µF låg-ESR + MLCC
                                                 └► rekylaktuator   [SS54 flyback över spolen]
   ⚠ skena ENABLE endast mellan rack och mag-release (MCU-styrd)

VÄST                         1S Li-ion ─► buck 3V3/5V ─► MCU, TSOP-array, WS2812, haptik, ljud
```

---

## 8. Representativ pinkarta

> Pinnar är representativa. P4:s GPIO-matris kan routa RMT/LEDC/SPI/I²C/TWAI till de flesta pinnar — **verifiera mot ESP32-P4 PICO:s exponerade headers** och undvik strapping-/USB-pinnar. (Numren nedan är platshållare att mappa om till P4/C6.)

**Vapen — ESP32-P4 PICO** (P4 + C6)
| Funktion | Pin | Not |
|---|---|---|
| IR-TX (RMT → MOSFET-gate) | GPIO17 | 56 kHz bärvåg, gateas av RMT |
| Rekyl-PWM (LEDC) | GPIO18 | → eFuse EN / gate-driver |
| Rekyl eFuse FAULT (in) | GPIO8 | TPS25983 fault-flagga |
| Avtryckare | GPIO4 | intern pull-up, debounce |
| Rack-sensor | GPIO5 | pull-up |
| Mag-release | GPIO6 | pull-up |
| IMU SPI (SCLK/MOSI/MISO/CS) | GPIO12/11/13/10 | ICM-45686 |
| IMU INT | GPIO9 | data-ready |
| NFC PN532 I²C (SDA/SCL) | GPIO1/2 | + magwell-switch GPIO7 |
| OLED I²C | delad m. NFC (SDA/SCL) | eller egen SPI |
| I²S ljud (BCLK/LRCLK/DOUT) | GPIO40/41/42 | MAX98357A (valfritt) |
| Batteri-ADC | GPIO16 | spänningsdelare |

**Väst — ESP32-C6**
| Funktion | Pin | Not |
|---|---|---|
| Zon HEAD (TSOP-array OR) | GPIO2 | interrupt + avkod |
| Zon CHEST | GPIO3 | |
| Zon BACK | GPIO4 | |
| Zon LEFT | GPIO5 | |
| Zon RIGHT | GPIO6 | |
| WS2812 data | GPIO7 | lagfärg + träffblink |
| Haptisk motor | GPIO8 | via MOSFET |
| I²S ljud | GPIO18/19/10 | valfritt |
| Batteri-ADC | GPIO0 | |

> Räcker inte pinnarna för separata zoner: använd **MCP23017 I²C I/O-expander** eller P4/C6:s RMT-RX-kanaler.

---

## 9. Firmware-arkitektur (Fas 1)

```
firmware/
├─ shared/
│  └─ milestag2/        # gemensam codec: encode/decode header+1200/600µs PWM, CRC+nonce
├─ weapon-node/         # ESP32-P4 PICO (P4 + C6, ESP-IDF)
│  ├─ fsm_makeready     # NO_MAG→MAG_IN→READY→EMPTY→KIA (Del 6)
│  ├─ ir_tx             # RMT 56 kHz, paketbygge ur weapon-profil
│  ├─ recoil            # LEDC PWM, soft-start via eFuse EN, RoF-cap
│  ├─ imu               # ICM-45686 ≥1kHz, muzzle-climb capture + logg
│  ├─ nfc               # PN532: läs vid insert, skriv vid extraktion
│  ├─ hud               # OLED: ammo/hits/state/batteri
│  ├─ link_espnow       # ↔ väst (+ peer-broadcast)
│  └─ audio             # I²S in/ut (native P4 PICO)
└─ vest-node/           # ESP32-C6
   ├─ ir_rx             # per-zon avkodning (interrupt/RMT-RX)
   ├─ fsm_health        # hälsa, zon-multiplikator, KIA-lockout, respawn
   ├─ feedback          # WS2812 + haptik + ljud
   └─ link_espnow       # ↔ vapen
```

**Tidskritiskt** (IR-bärvåg, paket-timing, rekyl-PWM) ligger på **RMT/LEDC-hårdvara** — inte i mjukvaruloopar. Övrigt körs som FreeRTOS-tasks. **Varje händelse tidsstämplas** med lokal monotonisk klocka (Fas 2 PTP-synkar den).

**Vapenprofil (oförändrad från README, lokalt tolkad i Fas 1):**
```yaml
# profiles/m4_556.yaml
name: "M4 / 5.56 sim"
rof_rpm: 720          # capad av rekylcykel (~12 Hz)
recoil_pwm: 0.65      # 0..1 felt-recoil-skala
mag_capacity: 30
damage_code: 0x12     # tolkas lokalt av väst i Fas 1; av server i Fas 2
# (muzzle_velocity/drag/drop läses men adjudikeras först i Fas 2)
```

---

## 10. Bygg- & kalibreringschecklista (Fas 1)

- [ ] IR-emitter verifierad inom **Class 1** (HW-strömgräns bekräftad med mätning vid aperturen).
- [ ] Emitter borrlinjerad mot optiken; hit-cone/divergens satt (~±15°), räckvidd uppmätt.
- [ ] Emitter- och TSOP-bärvåg **matchade** (en frekvens systemvitt, t.ex. 56 kHz).
- [ ] Västtäckning verifierad: inga döda zoner i 360° (gå runt en skytt, alla vinklar registrerar).
- [ ] Rekyl soft-start verifierad; inget kontaktbågslag vid rack/mag-release.
- [ ] Make-ready-FSM: skena ALDRIG på under mag-insert/extract (mät kall).
- [ ] NFC: insert läser ammo, extraktion skriver, EMPTY blockerar eld + bolt-lock.
- [ ] ESP-NOW vapen↔väst: träff → HUD "KILL" + bolt-lock på mål inom < ~50 ms.
- [ ] KIA-lockout + respawn fungerar (lokal timer eller admin-IR-kommando).
- [ ] Logik- och rekylrail separerade; LiPo balanserad/laddad; ögonskydd utdelat.

---

## 11. Hooks för Fas 2 (så inget behöver byggas om)

Designa in dessa redan nu — kostar nästan inget i Fas 1:

1. **Tidsstämpla allt** med lokal monotonisk klocka → Fas 2 disciplinerar den med **PTP** + HW-tidsstämplad IR-ankomst.
2. **IR-paketet bär redan** shooterID + team + weapon-profil/damage → servern kan **re-adjudikera** samma skott positionellt utan nytt protokoll. Lägg in **CRC + rullande nonce** nu (anti-replay) — det behövs ändå i Fas 2.
3. **ESP-NOW-frames struktureras** så de kan vidarebefordras till en **gateway** (Fas 2 WiFi/server-uplink) utan formatändring.
4. **Kamera (MIPI-CSI), AR-HUD (MIPI-DSI), WiFi 6 och ljud finns redan på P4 PICO** — lämna kontakterna obestyckade i Fas 1. Reservera GPIO + en intern kontakt för **UWB-modul (DW3000/Makerfabs)**.
5. **Logga IMU-mynningsklättring** redan i Fas 1 → blir indata till Fas 2:s trajektorie-adjudikation och AAR.
6. **Ingen MCU-migration behövs** — vi bygger redan på ESP32-P4 PICO. Strukturera koden så P4:s andra kärna + C6-radion kan ta WiFi6/server-uplink och kamera-pipeline i Fas 2 utan refaktorering.

---

## 12. BOM Fas 1 (per spelare)

| Enhet | Del | ~Pris |
|---|---|---|
| **Vapen** | ESP32-P4 PICO (P4 + C6; kamera/DSI/ljud ombord, vilande) | ~$24 |
| | ICM-45686 IMU-breakout | $10–25 |
| | SFH 4715AS ×2 + lins + AO3400 + R | ~$8 |
| | PN532 NFC-läsare + magwell-switch | $10–15 |
| | micro-OLED (SSD1306/SH1107) | $5–8 |
| | TPS25983 eFuse + cap-bank + SS54 | ~$8 |
| | Rekylaktuator (solenoid proto → BLDC+ODrive S1 final) | $20 → $150 |
| | Mikrobrytare ×3 (trigger/rack/mag-rel) | ~$3 |
| | Ljud native på P4 PICO (ev. extern högtalare) | ~$2 |
| | 2S Li-ion + buck | ~$15 |
| **Väst+hjälm** | ESP32-C6 | ~$3–6 |
| | TSOP 56 kHz ×~16–24 (torso+hjälm) | ~$20–25 |
| | WS2812-remsa + haptisk motor + ljud | ~$12 |
| | 1S Li-ion + buck | ~$8 |
| **Magasin** (×flera) | NTAG215 + hög-C LiPo + kontakter >25A | ~$12/st |
| **Summa kärnsats** (1 vapen + väst, exkl. final-rekyl & extra mag) | | **~$175–235** |

---

## 13. Föreslagen byggordning (delfaser inom Fas 1)

1. **Engagemang-kärna:** ESP32-P4 PICO + IR-TX (RMT) + en TSOP → bekräfta att ett kodat skott avkodas. *(milestone: "det skjuter och registrerar")*
2. **Väst:** zon-array + feedback + ESP-NOW-länk → träff lyser/låter, HUD säger "KILL".
3. **Ammo-logik:** PN532 + make-ready-FSM + HUD → insert/rack/fire/empty/reload.
4. **Rekyl:** solenoid-prototyp + eFuse + cold-mate → felt-recoil, kall kontakt verifierad.
5. **Profiler + spel-loop:** vapenprofiler, KIA/respawn, peer-poäng. → **komplett, spelbart vapen.**
6. **Finputs:** BLDC/ODrive-rekyl, ljud, IMU-loggning, anti-replay-CRC.

---

*Fas 1 ger ett fullt spelbart, fristående vapen + väst. Fas 2 (UWB-positionering, server-adjudikation av simulerad ballistik, live-cam och AAR) bygger ovanpå via hooks i Del 11 — utan att något i Fas 1 behöver göras om.*
