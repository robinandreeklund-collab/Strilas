# STRILAS — komplett systemstruktur (vapen)

> Ritning: [`system-oversikt.png`](system-oversikt.png) · jfr [`vapen-layout.png`](vapen-layout.png)

Tre fysiska enheter: **vapenlåda** (all elektronik + huvudbatteri), **magasin** (uttagbart:
NFC-tagg + separat rekyl-batteri) och **laddstation** (laddar mag-batteri + virtuell omladdning).

## 1. Vapenlådan — tre kort + batteri i en låda
| Block | Roll | Kopplas |
|---|---|---|
| **Huvudbatteri** 2S LiPo | matar all elektronik | → OPTIK J2 (VBAT) |
| **OPTIK-PCB** | lins+kamera, 2× IR-emitter (940 nm), 1× IMU | J1 → P4 **edge B** (SPI+IR+ström) |
| **ESP32-P4** | beräkning, WiFi6, hit-/ballistik-logik | edge B↔optik · edge A↔FC · USB↔kamera |
| **FC-PCB** | **I/O-hub** för alla brytare/NFC/rekyl + 2× IMU | J1 → P4 **edge A** · J2 = 3V3-tapp |
| **USB-kamera** OV9281 120 fps | siktet (PnP-konstellation) | USB → P4 |

**Nyckel:** FC är samlingspunkten. Alla brytare, NFC och rekyl-styrning kommer in på FC J3–J8,
buntas på **FC J1 = P4 edge A** (12-stifts buss) och går till P4. Optiken pratar med P4 på edge B.

## 2. FC-portarna — exakt destination (ur netlistan)
| Port | Går till | Signaler |
|---|---|---|
| **J1** | P4 **edge A** (buss) | MAGWELL · RECOIL_PWM · RECOIL_FAULT · NFC_SCL · NFC_SDA · IMU2_INT · IMU3_INT · RACK · TRIG · MAG_REL · 2×GND |
| **J2** | P4 **edge B** 3/4/5 | 3V3 + GND (kraft-tapp — FC matas härifrån, ingen egen kabel) |
| **J3** | Avtryckare | TRIG + GND |
| **J4** | Rack/laddhandtag | RACK + GND (ladda patron / bolt) |
| **J5** | Magasinlås | MAG_REL + GND (frigör magasin) |
| **J6** | Magwell-givare | MAGWELL + GND (magasin isatt?) |
| **J7** | Rekyl-kort | RECOIL_PWM (ut) · RECOIL_FAULT (in) · GND |
| **J8** | NFC-läsare PN532 | NFC_SDA · NFC_SCL · 3V3 · GND (I²C, delas med FC:s 2 IMU) |

## 3. Kraftarkitektur — TVÅ batterier (medvetet isärhållna)
- **Huvudbatteri (2S, i lådan)** → OPTIK J2 → P4:ans VSYS-buck → 3V3 → **allt** (P4, optik, FC,
  kamera, 3× IMU, NFC). Liten, jämn last → förutsägbar drifttid.
- **Mag-batteri (2S, i magasinet)** → magwell-kontakter → rekyl-kort → **rekyl-aktuator**. Hög,
  pulsad ström hålls **helt borta** från huvudbatteriet → ingen spänningsdipp i kamera/P4 vid rekyl,
  och tomt magasin = ingen rekyl + inga skott (snyggt sammanlänkat).

### Effektbudget huvudbatteri (ärliga uppskattningar)
| Last | typ | hög | not |
|---|---|---|---|
| ESP32-P4 + WiFi6 | 1,20 W | 2,50 W | **dominanten — mät** |
| USB-kamera OV9281 120 fps | 0,50 W | 0,90 W | sensor + UVC-brygga |
| 2× IR-emitter (pulsad @1 A) | 0,50 W | 0,90 W | ~0 i vila; peak tas av C2 |
| 3× IIM-42653 | 0,05 W | 0,06 W | försumbar |
| NFC PN532 | 0,05 W | 0,33 W | låg duty |
| FC + övrigt | 0,10 W | 0,20 W | |
| **Summa** | **2,4 W** | **4,9 W** | ~324 / 661 mA @7,4 V |

**Batterirekommendation (huvud):**
| 2S-pack | energi | drifttid typ | drifttid hög |
|---|---|---|---|
| 1500 mAh | 11,1 Wh | 4,6 h | 2,3 h |
| **2200 mAh** | **16,3 Wh** | **6,8 h** | **3,3 h** |
| 3000 mAh | 22,2 Wh | 9,3 h | 4,5 h |

→ **2S ~2200 mAh** ger en speldag med marginal (~65×35×15 mm, ~120 g — får lätt plats i lådan).
Vill du säkra full-auto-tunga pass: 3000 mAh. *Dominanten är P4+WiFi — mät den verkliga
modulströmmen vid bringup; resten är små och välkända.*

### Mag-batteriet (rekyl) — separat dimensionering
Storleken sätts av **aktuatorn** (ej byggd än): energi/skott × skott/magasin. Metod:
`mAh ≈ (I_aktuator × t_puls × skott_per_mag) / 3,6` vid 2S. När aktuatorns ström/pulslängd är
bestämd räknar jag exakt. Poäng: rekyl-energin "tankas" när du byter/laddar magasin.

## 4. Magasin + ammo-logik (NFC)
- **NFC-tagg i magasinet** bär *kvarvarande skott* + magasin-ID. **PN532-läsaren** (FC J8) läser
  taggen när magasinet sätts i (magwell-givaren J6 triggar läsningen).
- **Skott räknas ned** i P4 vid varje eld; vid tomt → ingen eld (och rekyl-batteriet är ändå urladdat/uttaget).
- **Virtuell omladdning:** ta ut magasinet (MAG_REL J5) och lägg på **laddstationen** → den
  (a) laddar rekyl-batteriet och (b) **skriver NFC-taggen full** → magasinet är "laddat" igen.
- **Rack/laddhandtag (J4):** kammar en patron / nollställer bolt-stopp efter magasinbyte (realism).

## 5. Hur allt hänger ihop (en mening)
Huvudbatteriet driver hela sikteshjärnan (optik+P4+FC+kamera) via en enda 3V3- from-edge-B-kedja;
FC samlar alla brytare/NFC/rekyl och lämnar dem till P4 på edge A; magasinet är en **uttagbar
energi-+ammo-modul** (eget rekyl-batteri + NFC-skotträkning) som "fylls på" på laddstationen.

## 6. Öppna punkter (ärligt)
- **P4-modulens verkliga ström** — enda stora osäkerheten i batteribudgeten; mät vid bringup.
- **Rekyl-aktuatorn** (typ, ström, pulslängd) — sätter mag-batteriets storlek; ej vald än.
- **Magwell-kontakter** för rekyl-ström + NFC-antennplacering — mekanisk konstruktion kvar.
- **Laddstationens NFC-skrivning** + säker ammo-bokföring (anti-fusk) — firmware/protokoll kvar.
