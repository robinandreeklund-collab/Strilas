# STRILAS — Systembeskrivning

> Komplett referens: **vad varje PCB gör** och **hur systemet är tänkt att fungera**.
> STRILAS är ett IR-baserat laser-tag-/stridssimuleringssystem där varje skott löses
> **optiskt** (kameran är siktet) i stället för med en rak IR-stråle — vilket ger riktig
> ballistik, förhållning på rörliga mål och anatomiska träffzoner på långt håll.

Detta dokument beskriver systemet som det är tänkt idag. Korten definieras i kod
(SKiDL-netlistor + pcbnew-placering/routning); tillverkningsunderlaget per kort ligger i
[`leverans/`](leverans/). Designfilosofi och djupare motivering finns i
[`STRILAS-SYSTEM-GUIDE.md`](STRILAS-SYSTEM-GUIDE.md).

---

## 1. Grundidé

Vanlig laser-tag = rak IR-stråle, träff = "strålen råkade pricka en sensor". STRILAS gör
i stället så här:

- **Vapnet skjuter ett brett, ögonsäkert 940 nm IR-ljus** som bär ett datapaket (skytte-ID,
  vapenprofil, skada). Det är bara en **LOS-grind** ("nådde ljuset fram, utan vägg emellan?")
  — inte själva träffdomen.
- **Kameran på vapnet är siktet.** Varje mål bär en **850 nm-konstellation** (kända LED-mönster).
  Kameran ser konstellationen, löser målets **pose** (avstånd, bäring, orientering) via PnP, och
  räknar **ballistik** (kulfall + flygtid) → en **deferred hit**: träff om den världsfasta,
  fall-korrigerade skottlinjen skär målets **verkliga** läge när "kulan" når fram.
- Detta ger zon-träffar (huvud/torso/lem) på avstånd, förhållning på rörliga mål och anti-fusk
  (väggar blockerar både IR och kamera).

Två våglängder, åtskilda med optiska filter (måste matcha — se §4):

| Funktion | Våglängd | Källa | Mottagare |
|---|---|---|---|
| **Skott / LOS-grind** | **940 nm** | OSLON Black SFH 4725AS (vapnets emitter) | TSOP4856 på patcharna |
| **Konstellation / pose** | **850 nm** | Lumileds L1I0-0850090200000 (LUXEON IR Domed, LED på mål) | Vapnets kamera m. 850 nm-bandpass |

Kameran ser 850 nm och **avvisar** vapnets egna 940 nm → ingen självbländning.

---

## 2. Systemöversikt — 3 noder

| Nod | Roll | Kort |
|---|---|---|
| **Vapen** | "Sikte + domare" — fyrar IR, ser konstellationer, löser pose, **adjudikerar** | CM5-stack: carrier + **vapen-HAT** + **optik-huvud** + extern **ESP32-C6**-brygga (+ kamera på carriern) |
| **Väst** | Träff-mottagare torso 360° + haptik | **väst-moderkort** + 10× **patch** (rund) |
| **Hjälm** | Huvud-mottagare + **RTK-position** + headset | **hjälm-moderkort** (rund) + 4× **patch** + 6× **LED-tab** |

Alla tre noder pratar **ESP-NOW** (samma mesh). Vapnet löser posen och dömer; väst/hjälm
rapporterar DATA-träffar + RTK-position och driver haptik/ljud lokalt. Allt tidsstämplas och
loggas för live-spårning och efteranalys (AAR).

> **Två radio-generationer i meshen:** väst och hjälm kör **ESP32-P4-WIFI6** (P4 + onboard C6).
> Vapnet uppgraderades till **CM5** (kraftfullare CV/PnP), men CM5:ans Broadcom-radio kan **inte**
> tala ESP-NOW → vapnet bär en separat **ESP32-C6** som UART-brygga in i meshen (se §6).

---

## 3. Hur ett skott går till (end-to-end)

```
1. AVTRYCK → vapen-HAT signalerar CM5. Villkor: NFC-ammo > 0 + laddhandtag "racked" (make-ready).
2. EMITTER fyrar (optik-huvudet): 2× 940 nm OSLON i serie via aktiv konstantströms-sänka
   (OPA171 + DPAK pass-FET + sense-R). Firmware-styrd ström 0–3 A (HW-tak 3 A, boot 0 A).
   56 kHz-gatad burst bär skott-paketet (skytte-ID, vapenprofil, skada).
3. SKOTTLINJEN LÅSES i världsram vid avtryck (pipans riktning + ballistiskt fall). IMU håller
   linjen världsfast medan vapnet rör sig (recoil/svaj).
4. KAMERAN (850 nm-pass, global shutter) ser målets 850 nm-KONSTELLATION → frame-differencing →
   rena blobbar → PnP (≥4 LED i känt 3D-mönster) → mål-pose: avstånd R + bäring + orientering.
5. BALLISTIK: R → kulfall → hållpunkts-offset. Flygtid → kameran spårar målet under hela tiden.
6. DEFERRED HIT: när "kulan" når R → träff OM den världsfasta, fall-korrigerade linjen skär
   målets VERKLIGA läge då. Träffpunkten mappas på målets 3D-modell → anatomisk zon.
7. MÅLET: TSOP-patch (940 nm) ger en LOS-grind/anti-fusk DATA-puls → väst/hjälm-nod → mesh.
   Vid ADJUDIKERAD träff fyras zon-VIBRATORN (haptik) + ljud/score. (Rå TSOP ≠ poäng; kameran avgör.)
```

IR-skottet (940 nm → TSOP) är en **separat länk**, oberoende av radion. Radion bär spel-state,
poäng och position.

---

## 4. Optik & våglängder

- **940 nm = skott.** Osynligt, brett (divergerad LED, **ej** kollimerad laser → ögonsäkerhets-marginal).
  Emittern sitter under en **Carclo TIR-kollimatorlins** (10003/10195-serien) för räckvidd; lins +
  hållare (Carclo 10734) köps separat och monteras manuellt över emittern.
- **850 nm = konstellation.** Riktade **Lumileds LUXEON IR-LED (L1I0-0850090200000, 90° dome)** på målen;
  kameran har **850 nm-bandpassfilter** så att den ser konstellationen men inte vapnets egen 940 nm-stråle.
  *(Bytt från OSLON SFH 4715AS @860 nm → Lumileds @850 nm: starkare Ie (~750 mW/sr@1A ≈ 2× VSMY) → räckvidd
  vid lägre ström + lager-verifierad.)*
- Filter/emitter/LED **måste matcha** kamerans pass-band — annars ser kameran fel sak eller bländas.

---

## 5. Korten

### 5.1 Vapen (v2 — CM5-stack)

Vapnet är en stack: **CM5 → CM5-carrier (t.ex. CM5-NANO-B) → vapen-HAT → optik-huvud**, plus en
extern ESP32-C6 och kameran på carriern.

```
            kamera (VEYE AR0234, MIPI-CSI) ──┐
                                             ▼
   CM5  ──DF40──►  CM5-carrier  ──40-pin──►  VAPEN-HAT  ──JST(VBAT·IR_MOD·EMIT_SET·GND)──►  OPTIK-HUVUD
                       ▲                        │                                              │
                       │ 5V back-feed           ├─ JST 4-pol ──► extern ESP32-C6 (ESP-NOW)     ├─ 2× 940 nm emitter
                       └────────────────────────┘                                              └─ CC-sänka + linser
                          2S-batteri → HAT-buck
```

**Vapen-HAT** — `hardware/weapon_hat_netlist.py` → `leverans/weapon-hat/`
*56 × 41 mm, 4-lager.* Pluggar på carrierns 40-pin GPIO-header (hona-sockel på baksidan, centrum;
all övrig montering på framsidan). Carriern sköter CM5↔DF40 + kamerans MIPI-CSI; HAT:en bär resten:
- **Kraft:** 2S (6–8,4 V) → skydd (P-FET + PTC + TVS) → **AP63203 buck → 5 V/3 A** som
  **back-powerar carriern/CM5:an** via headerns 5V-stift. Separat **VBAT-rail** matar emittern.
- **Emitter-styrning:** CC-sänkan sitter på optik-huvudet (kortare pulsloop) — HAT:en skickar bara
  **VBAT + IR_MOD (56 kHz) + EMIT_SET (ström-set-PWM) + GND** via emitter-JST:en. EMIT_SET =
  CM5 GPIO13/PWM1 → firmware sätter emitter-strömmen 0–3 A kontinuerligt.
- **Sensorer:** 3 IMU:er (1× ICM-42688-P på SPI + 2× I²C) för stabil världsfast skottlinje;
  **I²C-ADC** för batteri-sense (CM5 saknar ADC).
- **Fire-control-IO** (JST/switchar): avtryck, laddhandtag (rack), mag-release, magwell-sense,
  **recoil**, NFC-ammoläsare (I²C), MODE-byglar, PTT.
- **HAT-ID-EEPROM** (RPi HAT-spec) + **ESP-brygga-JST** (4-pol: 5V·TX·RX·GND) till extern ESP32-C6.

**Optik-huvud** — `hardware/optik_head.py` → `leverans/optik-head/`
*41 × 56 mm, 2-lager, allt SMT på framsidan.* Sitter framför HAT:en på standoffs; kameran sitter
bakom på MIPI-CSI till carriern (rör inte detta kort).
- **2× 940 nm OSLON SFH 4725AS** i serie, sida-vid-sida, under **Carclo 10734-hållare** (linser köps
  separat, monteras manuellt över emittrarna; fästben finns på kortet).
- **Aktiv konstantströms-sänka (CC):** OPA171 + AOD4184 DPAK pass-FET + **0R068 sense (2512, 1 W)**.
  **Kontinuerlig firmware-styrd ström 0–3 A:** EMIT_SET-PWM → RC-filter → DC-referens → R3/R4-delare →
  IDRV_REF (= V_SET/16). **56 kHz-grind** (AO3400, styrd av IR_MOD) modulerar bursten. **Boot = 0 A**
  (GPIO13 låg = av).
- **Kamera-cutout** (Ø18 M12-linshållare) i toppen + 4 hörnhål för VEYE AR0234-modulen.
- **JST 4-pol bak** (THT): VBAT·IR_MOD·GND·EMIT_SET → HAT:en.

**Kamera** — VEYE **AR0234M** (global shutter, mono) med 850 nm-bandpass. Sitter på carrierns
**22-pin MIPI-CSI** och **matas via CSI-bandets 3,3 V** (~657 mW = ~199 mA). Rör inte HAT/optik
elektriskt — bara mekaniskt (standoffs).

**Extern ESP32-C6** — radiobrygga. En liten modul (t.ex. Seeed XIAO ESP32-C6, egen LDO + USB för
flash) ansluts via HAT:ens 4-pol JST (5V·TX·RX·GND) och pratar med CM5 över UART. C6:an talar samma
ESP-NOW som väst/hjälm; antennen dras ut ur vapenhuset. Lager-koll: `leverans/esp-c6-sampler/`.

**(Planerat) Magasin-haptik-driver — recoil/återkoppling med 4× Titan Carlton.**
Recoil-funktionen är tänkt att byggas med en array av **4× Titan Haptics Carlton** (röstspole-LMR,
2–10 V, bidirektionell ±V-drivning). Dessa kräver en **egen "smart" 4-kanals drivare** (H-brygga/BTL
per don + liten MCU/haptik-IC som genererar vågformerna) som **matas av ett separat magasin-batteri**.
HAT:en styr den via **recoil-JST:en** (1 kommandolinje RPWM/GPIO12 + FAULT/GPIO16 + gemensam GND);
kraften hålls som en separat ö i magasinet. *Ej ritat ännu — gränssnittet finns på HAT:en.*

### 5.2 Väst

**Väst-moderkort** — `hardware/vest_mb_netlist.py` → `leverans/vest-mb/`
*100 × 60 mm, 4-lager.* Väst-nod; alla 10 patchar + 10 zon-vibratorer pluggas in.
- **ESP32-P4-WIFI6** (stackad Waveshare-modul, 2× kant-sockel edge A/B). Självförsörjer via VSYS=VBAT.
- **2S → AP63203 → 3,3 V/2 A** (logik + motorer + patchars 3V3-rail).
- **10× patch-DATA** (aktiv-låg) läses direkt på GPIO. **10× zon-vibrator** via 2× **TPIC6B595**
  power-shift (open-drain, 3 GPIO: SER/SRCK/RCK). **LED_EN broadcast** → alla patchars konstellation.
- Zon-kontakt 1×6 per patch: VBAT·GND·DATA·LED_EN·3V3·VIB.

### 5.3 Hjälm

**Hjälm-moderkort ("holo"-kort)** — `hardware/helmet_mb_netlist.py` → `leverans/helmet-mb/`
*Ø100 mm rund, 4-lager.* Centralt hjälm-nav + headset + RTK.
- **ESP32-P4-WIFI6** (samma modul som väst → en source).
- **2S → AP63203 → 3,3 V/2 A.**
- **ZED-F9P RTK-puck** (8-pol JST GH: UART + I²C + IST8310-kompass) + **IIM-42653 IMU** (I²C) →
  GNSS/INS-fusion → cm-position och huvud-attityd.
- **4 egna TSOP4856** (diod-OR → 1 DATA) + 4 patch-DATA, alla lästa direkt (ingen 74HC165).
  6 konstellations-LED-uttag (3 serie-par) + driver (LED_EN).
- **Headset:** ES8388-codec (I²S DAC/ADC + analog bom-mik) → **PAM8302A** klass-D → öronhögtalare;
  PTT-knapp.

**LED-tab (micro-PCB)** — `hardware/led_tab.py` → `leverans/led-tab/`
*~6 × 11 mm, 2-lager. 6 st/hjälm.* En **Lumileds L1I0-0850090200000 (LUXEON IR Domed, 850 nm, 90°)** på en liten tab med 2-håls fot.
Kund löder en **right-angle stiftlist** så tab:en står lodrätt mot hjälm-discen → LED:en strålar
vågrätt radiellt ut mot horisonten (konstellations-täckning runt huvudet). Stiften går i hjälm-MB:ns
tab-socklar.

### 5.4 Patch (väst + hjälm)

**Patch** — (väst-patch) → `leverans/vest-patch/`
*Rund Ø45 mm, 2-lager.* Täcknings-nod som sitter ×10 på västen och ×4 på hjälmen.
- 4× **TSOP4856** (940 nm-mottagare, ledade — ben böjs/sprids diagonalt) för LOS-grind/anti-fusk.
- Konstellations-LED (850 nm, Lumileds LUXEON IR) för pose.
- **6-pol JST** (VBAT·GND·DATA·LED_EN·3V3·VIB) + **2-pol motor-JST**: en **ERM coin-motor** pluggas
  in + 3M-fästs i keepout-ring på baksidan (DNP/kundmonterad) → zon-haptik.

---

## 6. Comms / mesh

- **Väst + hjälm = ESP32-P4-WIFI6** (P4 + onboard ESP32-C6) → ESP-NOW-mesh, gemensam tidsstämpling.
- **Vapnet = CM5** + **extern ESP32-C6** som UART-brygga. CM5:ans egen radio kan inte tala ESP-NOW;
  C6:an gör det åt den. CM5 adjudikerar och skickar spel-state via C6-bryggan in i samma mesh.
- **IR-länken (940 nm → TSOP)** är separat och oberoende av radion: den bär bara LOS-grinden;
  radion bär dom, poäng och RTK-position.

---

## 7. Kraft (per nod)

| Nod | Batteri | Kraft-kedja |
|---|---|---|
| **Vapen** | 2S LiPo | HAT-buck AP63203 **5 V/3 A** → back-powerar CM5/carrier; separat VBAT → emitter (CC-sänka 0–3 A). Kamera ~0,2 A @3,3 V via carrierns CSI. |
| **Väst** | 2S LiPo | P4 självförsörjer (VSYS=VBAT); carrier-buck AP63203 → 3,3 V/2 A för logik/motorer/patchar. |
| **Hjälm** | 2S LiPo | P4 självförsörjer; carrier-buck → 3,3 V/2 A för F9P/IMU/codec/LED. |
| **Magasin** (planerat) | eget batteri | separat ö för 4× Carlton-haptik (matas EJ från HAT:en). |

> **Varför 2S?** 5 V-bucken (AP63203) är en steg-ned-omvandlare → behöver >5 V in. 2× 940 nm-emittrar
> i serie kräver >4 V. 1S (3,7 V) räcker inte till någondera. 2S (6–8,4 V) ger marginal.

---

## 8. Eye-safety (säkerhet före allt)

- 940 nm är **osynligt** → farligast nära mynningen. Emittern är en **divergerad LED** (ej laser),
  och strömmen har ett **hårdvarutak (3 A via 0R068 sense)** plus firmware-styrning 0–3 A; **boot = 0 A**.
- **All användning mot människor kräver IEC 60825-1-ommätning** vid den valda strömmen — högre ström =
  mer effekt. Mål: Klass 1. Se `hardware/eye-safety-budget.md`.
- **LiPo-laddning** (dock) = projektets största brandrisk: per-cell-balansering, riktig BMS, termik,
  brandsäker plats.
- **Recoil/haptik-skena** kan dra mycket ström: gör/bryt kallt (skena av vid mag-byte, make-ready-statemaskin),
  rätt dimensionerade kontakter.
- Skyddsglasögon för alla; definierade spelgränser; "weapons safe"-procedur.

---

## 9. Tillverkning & leverans

Per kort i [`leverans/<kort>/`](leverans/): **gerbers.zip + bom.xls + centroid.csv/.xls + .step (3D)**.
FR-4 1,6 mm, HASL/ENIG. Översikt: [`leverans/LÄS-MIG.md`](leverans/LÄS-MIG.md).

| Mapp | Kort | Storlek | Lager |
|---|---|---|---|
| `weapon-hat/` | Vapen-HAT (CM5) | 56×41 mm | 4 |
| `optik-head/` | Optik-huvud (emitter + CC) | 41×56 mm | 2 |
| `vest-mb/` | Väst-moderkort | 100×60 mm | 4 |
| `helmet-mb/` | Hjälm-moderkort (rund) | Ø100 mm | 4 |
| `vest-patch/` | Patch (väst ×10 / hjälm ×4) | Ø45 mm | 2 |
| `led-tab/` | Konstellations-LED-tab (×6/hjälm) | 6×11 mm | 2 |

- **NextPCB monterar bara SMT.** Alla JST-PH-kontakter, batteri-kontakter och stackade moduler
  (P4-socklar, ESP-modul, F9P-puck-kabel) **kund-löds** → markerade **DNP** i BOM (kvar som
  beställningsrader, ute ur centroid).
- **Köps separat:** CM5 + carrier + kamera (VEYE AR0234), 2–3× ESP32-P4-WIFI6, extern ESP32-C6,
  RTK-puck (ZED-F9P GH), headset, ERM-vibratorer + (planerat) Carlton-haptik, 2S-batterier,
  Carclo-linser + hållare, IR-kupa.
- **OSLON-emittrar/LED placeras av NextPCB** (precision under linsen); ledade **TSOP4856 böjs/monteras
  av kund** (ej i centroid).

> ⚠️ **Regel (se [`CLAUDE.md`](CLAUDE.md)):** ändras ett `hardware/*.kicad_pcb` MÅSTE motsvarande
> `leverans/<kort>/`-artefakter regenereras — annars speglar underlaget ett gammalt kort.

---

## 10. Kod-flöde (hur korten byggs)

Korten är **definierade i kod**, inte handritade:

```
*_netlist.py  ──SKiDL──►  *.net  ──pcbnew-placering──►  *.kicad_pcb  ──freerouting+GND-fyll──►  routat kort
                                                                            │
                                                                            ▼
                                          kicad-cli + gen_nextpcb.py  ──►  leverans/<kort>/ (gerbers/BOM/centroid/STEP)
```

- **Netlistor:** `hardware/<kort>_netlist.py` (SKiDL) → `<kort>.net` (konnektivitet).
- **Placering + routning:** `hardware/<kort>_place.py` / `route_<kort>.py` (pcbnew + freerouting).
  Placerarna är **courtyard-medvetna** → 0 komponent-överlapp; routning verifieras till
  **0 oanslutna + 0 clearance**.
- **BOM + centroid:** `vapen-stack/gen_nextpcb.py` (gemensam MPN-databas → matchar NextPCB-lager).
- **Egna footprints:** `hardware/strilas.pretty/`.
- **Test-coupons** (`*-sampler`): små provkort för att lagerkolla komponenter hos NextPCB innan
  produktion (t.ex. `esp-c6-sampler`) — ingår inte i själva systemet.

> **Legacy (ESP32-P4-vapen):** repo:t innehåller även den tidigare P4-baserade vapen-implementationen
> (`weapon-module` → `leverans/optik/`, `firecontrol`, `p4-board`). Den är ersatt av CM5-stacken ovan
> men finns kvar som referens.
