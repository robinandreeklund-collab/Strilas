# STRILAS — väst: vibrator per zon (haptisk träff-feedback)

> Figur: [`vest-haptik.png`](vest-haptik.png)

## Ja — en vibrator bakom varje zon
Varje patch får en **ERM coin-motor** monterad på **baksidan, mot kroppen** → blir du träffad i
t.ex. vä-bröst känner du buzzet **just där**. Patchen blir då: fram = 3× TSOP + 2× 860 nm (mot
skytten), bak = vibrator (mot kroppen).

## Drivning — power shift-register (rent, få stift)
- **TPIC6B595** (power shift-register): 8 open-drain-utgångar à **150 mA**, inbyggd flyback,
  styrs med **3 GPIO** (SER/SRCK/RCK). **2 chip = 16 motorer** → täcker 10 zoner med marginal.
- Sitter på **väst-noden (ESP32-C5)**; motorn matas VBAT→motor→TPIC-kanal (switchad GND). PWM på
  kanalen ger intensitet/mönster.
- Patch-kontakt växer **4→5 pol**: `VBAT · GND · DATA · LED_EN · VIB` (eller motor löst kablad).

## När fyras den? — på ADJUDIKERAD träff (inte rå TSOP)
Den breda 940 nm-konen kan nudda flera patchars TSOP även på en ballistisk **miss**. Därför fyras
vibratorn på **den avgjorda träffen** (kamera/spellogik bekräftar att lösningen landade på zonen) —
**inte** på rå TSOP. Då buzzar du bara när du *faktiskt* är träffad (samma som poängen). Latensen
kamera→P4→väst-nod→motor är **~tiotal ms = känns direkt**.

> Valfri extra-nivå: en **svag** buzz på rå-TSOP ("du beskjuts/undertrycks") + **stark** buzz på
> adjudikerad träff. Två känslor, en motor.

## Effekt (ärligt)
- ERM ~80 mA @3 V, ~200–400 ms/träff. 1–2 zoner samtidigt = 80–160 mA **kort puls** → försumbart medel.
- Alla 10 samtidigt (osannolikt) = ~0,8 A kort; väst-batteriet klarar lätt. Lägg ~50 µF bulk nära TPIC.

## Patch-BOM-tillägg (per patch)
+1 ERM coin-motor (~10 mm). Drivare centraliserad på väst-noden (TPIC6B595 ×2) → patchen förblir nästan
lika enkel, bara +1 motor + VIB-stift.

## Att verifiera
- Motoreffekt/placering så buzzet känns genom väst-tyget (ev. styv platta bakom motorn).
- LRA (kräver DRV2605/AC-drive) om du vill ha krispigare/snabbare känsla än ERM — dyrare/mer komplext.

## TL;DR
Vibrator (ERM) bak på varje patch, mot kroppen → lokal träff-känsla. Drivs av väst-nodens
**TPIC6B595 ×2** (3 GPIO → 16 motorer, direkt motorström). Fyras på **adjudikerad** träff (~tiotal ms
= direkt), inte rå TSOP, så feedbacken matchar poängen. Effekt försumbar i medel.
