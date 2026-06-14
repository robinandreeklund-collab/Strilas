# STRILAS — MVP skjut-test: exakt inköpslista

> Minsta möjliga bygge för att **trycka på avtryckaren och se målet reagera på träff**.
> Allt annat (pose-fusion, rekyl, AR-HUD, server) klistras på senare — firmwaren
> (IR-kodning, trigger, träfflogik) portar rakt över. **P4-familjen hela vägen.**

## Kort — köp 2× samma kit (minimal variation)

| Antal | Del | Roll | ~Pris |
|---|---|---|---|
| **2** | **ESP32-P4-WIFI6-KIT-A** (P4 + C6 **WiFi 6** + **kamera** + **högtalare** + mic) | 1 = **vapen**, 1 = **mål** | ~$32/st |

Identisk hårdvara i båda → en toolchain (ESP-IDF), en sak att lära sig. Kamera +
högtalare ingår i kitet och stannar i scope (pose-väg + ljud senare).

> *Har du redan ETH-kitet (PoE) kan det bli målet istället — men 2× samma WIFI6-kit
> är enklast.*

## Vapnet — komponenter att koppla till kit #1

| # | Del | Antal | ~Pris | Not |
|---|---|---|---|---|
| 1 | **IR-LED ams-OSRAM SFH 4715AS** (860 nm) | 2 | ~$2 | skott-emitter (1 + reserv) |
| 2 | **Logic-level N-MOSFET** AO3400 / 2N7000 | 2 | ~$1 | LED-driver |
| 3 | **Motstånd** 33 Ω + 220 Ω + ¼W-sortiment | 1 sats | ~$5 | 33 Ω ⇒ ~100 mA = ögonsäkert + några meter |
| 4 | **Mikrobrytare** (snap-action med arm) | 1 | ~$1 | trigger |
| 5 | Breadboard + Dupont-kablar | 1 | ~$6 | montering utan lödning |

**Valfritt (billigt, blir centralt sen):** **ICM-45686 breakout** ×1, ~$12 — pose/rekyl.
Hoppa över i första "skjuter den?"-testet.

## Målet — komponenter att koppla till kit #2

| # | Del | Antal | ~Pris | Not |
|---|---|---|---|---|
| 1 | **Vishay TSOP4856** (56 kHz) | 4 | ~$4 | IR-mottagare, 4 st = täckning/zoner |
| 2 | Status-LED + kablar | 1 | ~$2 | **högtalaren finns i kitet** = träffljud |
| 3 | Fysiskt mål: kartong/foamboard | 1 | – | montera TSOP-arna på |

## ⚠️ Den enda regeln som måste stämma

**Bärvåg = mottagarfrekvens: 56 kHz.** Emittern moduleras på 56 kHz, TSOP**4856**
lyssnar på 56 kHz. Blanda inte 38/56 kHz — då ser målet ingenting.

## Ögonsäkerhet

Med 33 Ω-motståndet (~100 mA) är en 860 nm-LED trivialt Class 1. Driv den **aldrig**
på ampere utan strömgräns och tryck den inte mot ögat. Resistorn = hårdvaruvakten.

## Verktyg

Lödkolv + tenn (om du vill löda emitter/TSOP fast), multimeter. Allt kan dock
breadboardas utan lödning för första testet.

**Total ~$95** — varav $64 är de två korten du ändå vill ha för projektet.

---

*När korten + komponenterna är hemma: ESP-IDF-firmware till båda (vapen: trigger →
kodat 56 kHz-paket; mål: TSOP → träff → ljud i högtalaren).*
