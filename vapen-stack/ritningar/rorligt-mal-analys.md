# STRILAS — hur bra är systemet? + rörliga mål (lead)

> Figur: [`lead-rorligt-mal.png`](lead-rorligt-mal.png) · bygger på [`precision-iim42653.md`](precision-iim42653.md)

## Kort svar
- **Stillastående mål:** sensorbruset (~5 mm 1σ @150 m) är ~27× mindre än hållpunkten (kulfall
  140 mm). Du **måste** hålla över rätt, annars missar du. Inte point-and-shoot.
- **Rörligt mål:** ja — om du **leder rätt** (siktar framför) träffar du; gör du inte det missar du.
  Systemet avgör det **geometriskt korrekt**, inte med en "nära-nog"-tröskel. Också inte point-and-shoot.
- **Begränsningen är spelarens sikte + några obyggda/omätta saker (dagsljus-SNR, recoil-aktuator),
  inte elektronikens precision.**

## Hur rörligt mål avgörs RÄTT (mekaniken)
Realismen kommer ur **flygtiden**. På 150 m tar "kulan" ~167 ms (v0≈900 m/s) = **20 frames @120 fps**.
Vi använder **uppskjuten (deferred) träff-bedömning** — ingen gissad framtid:

1. Vid **avtryck** låses skottlinjen i **världsram** (riktningen pipan pekar, + ballistiskt fall).
2. Kameran **fortsätter spåra** målets konstellation varje frame under hela flygtiden.
3. **IMU:n (IIM-42653)** håller skottlinjen världsfast medan vapnet rör sig (recoil/svaj) — så att
   linjen inte "följer med" pipan efter skottet.
4. När kulan når målets avstånd: **träff om den världsfasta, fall-korrigerade linjen skär målets
   VERKLIGA läge då** — inte där det var vid avtryck.

Konsekvens: sikta på där målet ÄR (ingen lead) → kulan anländer dit målet VAR → **miss** på ett
korsande mål. Sikta **framför** (rätt lead) → målet hinner in i skottlinjen → **träff**. Exakt det du vill.
Och eftersom linjen låses vid avtryck: ett mål som **tvärbromsar/jukar efter** att du skjutit hinner
undan — realistiskt, inte ett systemfel.

## Lead-vinkeln är liten och hamnar alltid i bild
Matematiskt: **lead-vinkel = v_mål / v0** (oberoende av avstånd).
| Målfart | lead-vinkel | lead @150 m | i FOV (±6,85°)? |
|---|---|---|---|
| 3 m/s | 0,19° | 0,50 m | ja |
| 5 m/s | 0,32° | 0,83 m | ja |
| 10 m/s | 0,64° | 1,67 m | ja |
| 15 m/s | 0,95° | 2,50 m | ja |

Leadet kastar alltså aldrig målet ur synfältet — det är litet jämfört med kamerans ±6,85°.

## Precision för rörligt mål (ärligt)
Så länge målet **spåras kontinuerligt** under flygtiden (det gör det — du följer ju målet) är
felet i princip detsamma som stilla: bäring ~mm-klass, avstånd sub-meter, plus
- **IMU-världsram över 167 ms:** om kameralåset hålls → ~0 (re-ankras); om låset TAPPAS (recoil,
  ockludering) → IMU-dödräkning ≈ 0,002° = **5,3 mm** över flygtiden (litet, tack vare ±0,5 % SF + låg drift).
- **Latens** (sensor→beslut, ~8–16 ms): måste kompenseras, annars biaserar den leadet. Hanterbart vid 120 fps men ett verkligt mjukvaru-jobb.

→ Rörligt-mål-precisionen är **cm-klass** när målet hålls i bild. Spelaren måste fortfarande leda rätt.

## Ärligt: vad som kan förstöra det (måste byggas/mätas)
1. **Spårnings-kontinuitet i 167 ms** (~20 frames). Tappas målet (skymd, extrem korsning, recoil ur FOV)
   degraderar bedömningen till IMU-dödräkning. 120 fps + IMU bryggar korta glapp; långa glapp inte.
2. **Latens-budget** end-to-end måste vara känd och kompenserad (annars systematiskt lead-fel).
3. **Dagsljus-SNR @150 m** — fortfarande risk #1, omätt; utan robust blob-detektion varje frame faller
   spårningen (och därmed lead-bedömningen).
4. **Manöverförmåga inom flygtiden** — om målet ändrar fart/riktning under de 167 ms blir ett "rätt
   lett" skott ändå miss. Det är realistiskt, men värt att veta för speldesign.
5. **Recoil-aktuatorn** (obyggd) avgör hur ofta låset faktiskt tappas mitt i en serie.

## Speldesign-regel (för att ALDRIG bli point-and-shoot)
- **Auto-kompensera varken hållover eller lead åt spelaren.** Visa gärna avstånd/målfart som info,
  men låt spelaren själv hålla över OCH leda. Systemet räknar bara träffen ärligt mot var pipan pekade.
- Med både **fall** (drop) och **lead** krävda blir det skicklighet, inte tur.

## Sammanfattande betyg (ärligt)
| Aspekt | Bedömning |
|---|---|
| Vinkel/bäringsprecision | Utmärkt (~mm @150 m) — vida bättre än vad en spelare kan hålla |
| Avstånd (för fall + flygtid) | Sub-meter — gott och väl nog |
| Rörligt mål / lead | Geometriskt korrekt **om** kontinuerlig spårning + latenskompensation byggs |
| "Aldrig point-and-shoot" | Uppfyllt: kräver både hållover och lead |
| Största osäkerheter | Dagsljus-SNR @150 m (omätt), recoil-ur-FOV, latens/spårnings-mjukvara |

**TL;DR:** Hårdvaran är mer än precis nog för riktigt fall- OCH förhållningsskytte på 150 m — det
blir skicklighetsstyrt, aldrig pek-och-skjut. Det som avgör om det blir *perfekt* är inte sensorerna
utan tre byggsten/mätpunkter: **dagsljus-detektion @150 m**, **kontinuerlig spårning + latenskompensation**,
och **recoil-hanteringen**. Inga av dem är lösta i hårdvaran än — men inga av dem är heller blockerade av den.
