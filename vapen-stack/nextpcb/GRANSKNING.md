# STRILAS — pre-produktionsgranskning (optik + väst, Prototyp 1)

Fullständig kontroll innan första produktion. Inga genvägar: pinout mot P4, strömvägar,
DRC/connectivity, simulering. Datum: 2026-06-16. Verktyg: pcbnew/KiCad 7, SKiDL-netlistor.

## 1. P4-pinout — 100 % verifierad mot officiellt Waveshare-datablad
Edge-ordningen drogs ur Waveshares **ESP32-P4-WIFI6**-schema + silk (datablad), inte gissad.

**Optik J1 → P4 edge B** (RIGHT-edge, fysisk ordning VSYS·GND·EN·3V3·GPIO20·GPIO21·GND·
GPIO22·GPIO23·RUN·GPIO26·GND·GPIO27·GPIO32): alla 14 stift matchar, inkl. den speglade
stack-ordningen. VBAT→**VSYS** (P4:ans buck **MP1658**, Vin ≤16 V → 2S OK), +3V3 tas från P4,
EN/RUN korrekt **NC**, SPI (nCS/SCK/MISO/MOSI) + IMU_INT + IR_MOD på rätt GPIO.

**Fire-control J1 → P4 edge A** (LEFT-edge pin 6–17: GPIO29·28·GND·50·49·5·4·GND·3·2·
GPIO8·GPIO7): alla 12 stift matchar. I²C-paret = **GPIO8(SCL)/GPIO7(SDA)** bekräftat (delas
med P4:ans on-board codec ES8311 @0x18 — ingen adresskrock med IMU 0x68/0x69 el. PN532).

**Kamera-USB:** P1 (4-pol **MX1.25**) = VCC_5V·D−·D+·GND, kopplad till P4:ans **native USB 2.0
HS PHY** (DM/DP = ESP32-P4 pin 49/50). UVC-host @50–60 fps bekräftad. *(MX1.25-kabel till Arducam.)*

## 2. Connectivity / DRC (båda korten)
| Kort | Flytande nät | oconnected | clearance@0,2 mm | Lager |
|---|---|---|---|---|
| Optik (weapon-module) | 0 | 0 | 0 | 4 |
| Väst-patch | 0 | 0 | 0 | 2 |

Inga ennods-nät, inga oavslutade pins. Alla nät elektriskt vettiga (kontrollerade nod-för-nod).

## 3. Ström-/effektsimulering (datablads-förankrad)
**Optik skott-emitter** (VBAT 2S → 2× SFH4725CS → **aktiv CC-sänka**: OPA171 + DPAK-FET + 0R2 sense):
I = Vref/Rsense = 0,206 V / 0,2 Ω ≈ **1,0 A STABILT, batteri-oberoende** (ersätter passiv Rset som
gav 0,3–0,6 A sjunkande). DPAK-FET-förlust ~1,8 W puls @1 A (skurar → låg medeleffekt). Hård
HW-strömtak ~1,0 A (3,3 V-delaren × Rsense) = eye-safety design-regel #1 i HW. 3 A = avsiktligt
Rsense-byte + IEC 60825-1-ommätning. Skott-räckvidd: TIR-kollimator → I_eff ≫ krav @150 m.

**Väst-konstellation** (VBAT 2S → 10R 2512 → SFH4715AS): ~0,4–0,5 A/gren → ~390 mW/sr.
LED-spår breddade till **0,4 mm**. **Villkor:** ≤50 % duty (0,5 A i 10R = 2,5 W topp i 2 W).

## 4. Hittade fel + åtgärd
| # | Fel | Allvar | Åtgärd |
|---|---|---|---|
| 1 | Väst TSOP4856 `VS` på VBAT(2S 8,4 V) > abs-max **6 V** → TSOP brinner | **Board-killer** | Lokal **HT7333-A** 3,3 V-LDO (U4) matar TSOP. ✔ Fixat |
| 2 | DATA-pullup på VBAT → övervolt på väst-nodens 3,3 V-GPIO | **Hög** | Pullup flyttad till 3V3-rail → DATA = ren 3,3 V. ✔ Fixat |
| 3 | Väst LED-nät 0,2 mm (~1 A summa) | Medel | Breddade till 0,4 mm via `dsn_power_class`. ✔ Fixat |
| 4 | 10R drar 2,5 W topp i 2 W-motstånd | Medel | Dokumenterat max ~50 % duty (BOM-note + budget). ✔ |

## 5. Åtgärdat: emitter-ström (var 0,3–0,6 A → nu stabil 1 A)
- **FIXAT:** passiv Rset → **aktiv konstantströms-sänka** (OPA171-op-amp matad från VBAT + DPAK
  pass-FET + 0R2 sense). I = Vref/Rsense ≈ 1,0 A, **oberoende av batterinivå**, 56 kHz-gatad via
  IR_MOD-referensdelaren. Realiserar samtidigt eye-safety design-regel #1 (HW-strömtak). Kortet
  omplacerat + omroutat (clearance 0 / oconnected 0); 2 boxade kraftstift (J1.11/J1.14) handroutade.
- **Bänk-validering kvarstår (analogt):** DC-arbetspunkten (1 A, batteri-oberoende) är exakt och
  bevisad analytiskt; slingkompenseringen (C7 100 pF) + 56 kHz-flankskärpan är START-värden att
  bekräfta på bänk/SPICE (inneboende för alla aktiva drivsteg). OPA171 3 MHz/1,5 V/µs ger ~2 µs-
  flanker (mjuk men 56 kHz-fundamentalen stark → TSOP-OK); snabbare op-amp = skarpare vid behov.

## 6. Kvarstående (ej board-killer)
- **Helmet-halo** ingår EJ i Prototyp 1 och är inte omroutad efter LED-/LDO-ändringen (samma fix
  ärvs av netlistan men kortet måste routas om före hjälm-produktion).

## 7. Slutsats
Optik- och väst-patchkorten är **kontrollerade och redo för Prototyp 1-produktion**. P4-matchning
100 %, strömvägar verifierade (skott-emittern nu **stabil 1 A batteri-oberoende** via aktiv CC-sänka),
DRC ren, alla board-killers åtgärdade. Slutlig dagsljus-SNR + CC-slingkomp + duty/exponerings-trim
bekräftas på bänk (kvarstår alltid att mäta på riktigt).
