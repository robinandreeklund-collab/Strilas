# STRILAS — ärlig precisionsanalys (verkliga komponenter)

> Figur: [`precision-felbudget.png`](precision-felbudget.png) · jfr [`ballistik-analys.md`](ballistik-analys.md)
> **OBS: IMU bytt till IIM-42653** (drop-in) — denna baslinjeanalys skrevs för ICM-42670-P;
> låsta IIM-42653-tal + uppdaterad budget finns i [`precision-iim42653.md`](precision-iim42653.md).
>
> **Ingen hype.** Alla tal är 1σ-uppskattningar med angivna antaganden; det som inte är
> uppmätt flaggas som **OVERIFIERAT**.

## 0. Slutsats först (BLUF)
- I **steady-state** (målet i bild, kameran låst) är sensorbruset litet: **~7 mm 1σ @150 m**.
  Det är ~20× mindre än den hållpunkt (kulfall ~14 cm) som krävs på 150 m. **Alltså: det är
  ditt sikte/hållover som avgör träff — inte sensorbruset.** Det ger exakt den "måste-sikta"-
  känsla du vill ha; det blir INTE point-and-shoot.
- **Svagheten är recoil + den smala synfältet (13,7° FOV)**: kastas målet ur bild, eller blir
  bilden suddig under rekylpulsen, måste IMU:n död-räkna och felet växer till **decimeter–meter**
  tills kameran återlåser. Det är här designen kan falla, och det är delvis obyggt/omätt.
- **Största enskilda risken är overifierad:** att konstellationen överhuvudtaget syns @150 m i
  **dagsljus**. Faller det, faller allt annat. Det är en mätpunkt vid bringup, inte bevisat.

## 1. Exakta delar och relevanta specar
| Del | Spec som styr precisionen |
|---|---|
| Kamera **Arducam B0332 / OV9281** | 1280×800, **3 µm** pixel, **global shutter** (ingen rolling-smet), mono NIR |
| Lins **16 mm M12** | ~13,7° HFOV → **0,0107 °/px** ; ~24 px konstellationsbaslinje @150 m |
| IMU **ICM-42670-P** (DS-000451) | gyro **RNSD 0,007 °/s/√Hz**, RMS 0,07 °/s ; ZRO ±1 °/s, **±0,015 °/s/°C** ; accel 100 µg/√Hz, 1 mg-rms ; ODR ≤1600 Hz |
| IR-konstellation (mål) | modulerade 860 nm-LED, känt 3D-mönster → **PnP** |
| Skott-emitter | 940 nm (rakt; bär skott-ID, ej geometrin) |

**Antagande om arkitektur:** kameran ÄR siktet (digital retikel ur kamerabilden), och
träffen adjungeras i kamerakoordinater. Då finns ingen separat fysisk boresight↔kamera-
parallax att kalibrera bort → extrinsik-felet ≈ 0. *(Har man ett SEPARAT fysiskt sikte
tillkommer ett boresightnings-fel på ~0,01–0,05° = 26–130 mm @150 m, som då dominerar.)*

## 2. Steady-state felbudget @150 m (mål i bild)  — 1σ
Skala: **1° = 2 618 mm @150 m**.

| Felkälla | vinkel (1σ) | @150 m | kommentar |
|---|---|---|---|
| Centroid-brus, modulerad blob (~0,1 px) | 0,0011° | **2,8 mm** | frame-differencing ger ren blob; SNR-beroende |
| Intrinsisk kamerakalibrering (rest) | ~0,002° | **5,2 mm** | linsdistorsion/brännvidd efter schackrute-kalibrering; *ofta den verkliga begränsningen* |
| IMU mellan-frame-brygga (60 fps, ARW) | 0,0009° | **2,4 mm** | 0,007·√(1/60); kameran re-ankrar varje frame |
| Avstånd→hållpunkt (PnP ±0,9 m) | 0,0006° | **1,6 mm** | d(fall)/dR ≈ 1,8 mm/m → range-fel nästan irrelevant |
| **RSS totalt** | **0,0025°** | **≈ 6,6 mm** | |

Referens: hållpunkt @150 m = 140 mm; halv torsobredd ≈ 200 mm. Sensorbruset (~7 mm) ligger
alltså långt under båda. **Slutsats: precisionen begränsas av spelaren, inte av elektroniken.**

## 3. IMU:ns roll — och en ärlig nedgradering
- IMU:n ger INTE absolut sikte. **Kameran ger absolut bäring varje frame**; IMU:n bryggar
  bara *mellan* frames och *under* rekyltransienten.
- Med ICM-42670-P (RNSD 0,007) är mellan-frame-driften **~0,001° (2,4 mm) @60 fps** —
  försumbar. *(Den dyrare ICM-45686 hade gett ~0,0005°; vi bytte till 42670-P för lager-
  tillgång, vilket är ~2× sämre här men fortfarande litet. Ärlig nedgradering, inget problem
  i steady-state.)*
- ZRO-bias ±1 °/s och drift ±0,015 °/s/°C skulle ensamt ge 0,017° per frame — MEN den
  skattas och tas bort kontinuerligt av kamera-fusionen, så det som återstår är slumpvandringen
  ovan. Funkar bara så länge kameran ser konstellationen (se §4).

## 4. Recoil — den verkliga svagheten (ärligt)
Du vill att recoil ska påverka siktet realistiskt. Fysiskt gör den det: aktuatorn kastar
mynningen, boresight pekar någon annanstans — det är *äkta*, inte ett fel. Problemet är om
systemet **tappar reda på var det pekar** under pulsen:

1. **Smal FOV (13,7° = ±6,85°).** En rekyl-mynningsresning på 10–20° kastar målet **ur bild**.
   Då finns ingen kamera-ankring → IMU:n måste död-räkna hela transienten.
2. **Död-räkning × skalfaktorfel.** Integreras 10–20° med ~1–3 % gyro-skalfel blir det
   **0,1–0,6° = 0,26–1,6 m @150 m** transient — tills målet är tillbaka i bild och kameran
   återlåser (då nollställs felet).
3. **Rörelseoskärpa.** Vid 300 °/s och 1 ms exponering smetas bloben **28 px** → centroidering
   kollapsar. Kräver **≤100 µs exponering** (=2,8 px), vilket i sin tur kräver starka modulerade
   LED + bra SNR (kopplar till dagsljus-frågan §6).

**Konsekvens/designval:**
- Skott avlossat *i* transienten (full-auto, snabb uppföljning) har sämre precision tills återlås.
- Motåtgärder: kort exponering (≤100 µs), högre fps (90–120 → kortare brygga + mindre smet),
  något **bredare FOV** (avvägning mot räckvidd/SNR), begränsa recoil-amplituden, och/eller
  **adjungera träffen först när kameran återlåst** (skottet "landar" när låset är tillbaka).
- Detta är delvis **obyggt** (recoil-aktuatorn finns inte än) → måste mätas på riktig hårdvara.

## 5. Ballistik — vad "realistisk kulbana" konkret betyder här
- Kulan finns inte fysiskt → banan **beräknas**: `fall(R) = ½·g·(R/v)²` (+ ev. luftmotstånd/BC
  per vapentyp). Vid 150 m, v≈900 m/s → ~14 cm fall = 0,9 mrad hållpunkt.
- **Träffmodell:** enklast och renast = *hitscan-med-fall*: vid avtryck tas kameraframe →
  boresight-riktning + fall(R) → träffpunkt; träff om den skär målets siluett. Ingen
  flygtid/lead behövs.
- **Vill du ha full realism med rörliga mål** (lead) tillkommer flygtid (~0,17 s @150 m) och
  målhastighet skattad ur kamera-frames → extra fel (mål 3 m/s → 0,5 m på 0,17 s om man inte
  leder). Det är ett medvetet spel-designval, inte ett sensorfel.
- **Viktigt för "måste sikta":** låt INTE systemet auto-kompensera hållovern åt spelaren (då
  blir det point-and-shoot igen). Visa ev. avståndssiffra, men låt spelaren själv hålla över.
  Systemet räknar bara träffen ärligt mot var spelaren faktiskt pekade.

## 6. OVERIFIERAT — de verkliga riskerna (måste mätas)
1. **Dagsljus-SNR @150 m (störst):** syns de modulerade 860 nm-LED:erna mot solbelyst bakgrund
   på 150 m med vald LED-effekt + exponering? Design-resolution §1.3 säger uttryckligen att detta
   är en **mätpunkt**, inte bevisat. Faller detta → ingen detektion → ingen precision alls.
2. **Intrinsisk + extrinsisk kalibrering:** 5,2 mm-termen antar en bra schackrute-kalibrering;
   dålig kalibrering eller mekanisk flex/termik i kort↔lins kan dominera. Mät kalibrerings-residualen.
3. **Recoil-aktuatorn (§4):** dynamik, amplitud, hur ofta målet lämnar FOV — obyggt.
4. **Exponering vs smet** under recoil — beror på faktisk LED-styrka (kopplat till §1).
5. **Atmosfär/värmedaller** på 150 m i solsken — adderar jitter (oftast litet, men mätbart varma dagar).
6. **ICM-42670-P** är en konsument-IMU; OK här *bara för att* kameran re-ankrar. Tappas kameran
   länge (§4) är IMU:n inte bra nog för absolut sikte på egen hand.

## 7. Rekommendationer (prioriterat)
1. **Mät dagsljus-detektion @150 m först** — allt annat hänger på den.
2. Lås **exponering ≤100 µs** + utvärdera **90–120 fps** (USB2.0-bandbredd kan kräva beskärning).
3. Kör en **kamera-IMU-fusion** (EKF) som skattar gyro-bias varje frame och hanterar
   kort-tids-bryggor; definiera tydligt "skott landar vid återlås" för recoil.
4. Bestäm **konstellationsgeometri** (≥4 icke-koplanära LED + blink-ID) för robust, entydig PnP.
5. Bestäm spel-regel: **ingen auto-hållover** (realism) vs assist (lättare). Det avgör hela känslan.
6. Överväg FOV-avvägningen medvetet: 16 mm ger räckvidd/SNR men gör recoil-spårning känsligare;
   en aning bredare lins köper recoil-marginal mot räckvidd.

## TL;DR
Stillastående är systemet **mycket** mer än precist nog (~7 mm 1σ @150 m ≪ 140 mm hållpunkt) —
det blir på riktigt "sikta rätt eller missa", inte laser-tag-pek. De ärliga frågetecknen är
**(a)** om konstellationen syns i dagsljus på 150 m (omätt, störst), och **(b)** recoil/smal-FOV
som kan kasta målet ur bild och tvinga IMU-dödräkning med decimeter–meter-fel tills återlås.
Inget av det är löst i hårdvaran än — det är mät- och avstämningspunkter, inte färdiga sanningar.
