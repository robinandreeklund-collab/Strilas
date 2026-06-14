# STRILAS — 3D hårdvarusimulator (webb-frontend)

En **komplett interaktiv simulering** av hela STRILAS-vapnet med den valda hårdvaran, i en 3D-vy. Inget behöver köpas — du ser exakt hur allt fungerar och hänger ihop, och kan trimma alla parametrar förrän du spikar designen.

## Kör den

Den är **självständig (offline)** — Three.js ligger lokalt i `vendor/`. ES-moduler kräver en HTTP-server (inte `file://`):

```bash
cd sim
python3 -m http.server 8099
# öppna http://localhost:8099 i Chrome/Edge/Firefox
```

## Vad som simuleras (all "riktig" hårdvara)

| Hårdvara | Modelleras som |
|---|---|
| **ESP32-P4 + C6** | fire-control-FSM (NO_MAG→MAG_IN→READY→EMPTY→KIA), ammo, timing |
| **SFH 4715AS-emitter** | IR-länkbudget på riktigt: räckvidd = √(Ie/Emin), beror på **pulsström, strålvinkel, antal LED, 860 nm-filter och miljö (sol!)**. IR-räckviddsringen på marken blir röd när målet är utom räckhåll. |
| **TSOP4856-detektorer** | kroppszoner (huvud/bröst/mage/ben) som tänds vid träff; träff kräver att strålen når inom IR-räckvidd |
| **ICM-45686-IMU** | rekyl-klättring per skott (ackumuleras i auto → serien vandrar av), IMU-pitch-rate i telemetrin |
| **Magasin / NFC** | ammo-räkning, omladdning |
| **MilesTag II** | paketet (typ+ID+team+skada) byggs och visas live + airtime |
| **Ballistik (M4-profil)** | flygtid/drop, skalas per vapenprofil |
| **Fas 2 server-adjudikation** | togglas: flygtid + lead mot rörligt mål + exakt zon (headshot på alla avstånd). Av = Fas 1 (stråle+zon, headshot bara nära). |

## Kontroller

- **Auto-eld** (på som default) visar systemet live direkt.
- **Skytt-vy (FPS):** klicka knappen → sikta med musen, vänsterklick = eld, `Esc` = tillbaka till orbit.
- **Orbit:** dra för att rotera, scrolla för zoom.
- Reglage: vapenprofil, miljö (sol), pulsström, strålvinkel, antal LED, 860 nm-filter, Fas 2 på/av, skytt-skicklighet (siktfel σ), målets fart.
- FSM-knappar: sätt i magasin · rack · avfyra · ladda om.

## Saker att testa (bevisa designen själv)

1. Ställ miljö = **"Direkt sol mot sensor"**, pulsström **1 A**, 1 LED → se IR-räckvidden krympa (ringen röd, missar). Höj till **3 A, 2 LED, smal stråle, +filter** → räckvidden återvänder. (Bevisar IR-länkbudgeten från `docs/phase1-feasibility-sim.md`.)
2. Sätt **strålvinkel ±0.4°** och hög skicklighet → precisa headshots. Höj **σ** → missar. (Sikt-momentet.)
3. **Fas 2 av** + snabbt mål → se hur headshot-precisionen tappas på avstånd. **Fas 2 på** → återställs.
4. Håll auto-eld i gång → se **rekyl-klättringen** vandra serien uppåt (IMU).

Modellerna ligger i `hardware.js` (porterade från Python-simuleringen i `docs/`).

## Nivå 3 — geometrisk ballistik-adjudikation (uppdaterad)

Simulatorn kör nu den **riktiga nivå-3-pipelinen** (se `docs/level3-ballistic-architecture.md`), inte laser-tag:

1. **① Sikte** — auto-aim/FPS-siktvektor med siktfel σ, rekyl-klättring och **IMU heading-drift** (växer över tid, **nollställs av varje IR-träff** → visar varför IR-ankaret behövs).
2. **② Ballistik-bana** — kulan integreras i 3D (`integrate3D`): gravitation + drag + **sidvind**. Banan ritas som en **böjd gul kurva**; kulan flyger längs den med drop.
3. **③ Geometri** — **CCD-skärning** av banan mot målets **kapsel-kropp** (huvud/bröst/mage/ben), utvärderad vid varje tidssteg → leadet mot rörligt mål sköts automatiskt.
4. **④ IR LOS + zon** — strålen mot målplanet: inom strålkon + IR-räckvidd → LOS ✓ + zon.
5. **FUSION** — `HIT` = geometri-anlände **OCH** IR-LOS; zon från IR, skada skalad av anslagsfart. Annars NEAR-MISS / FÖRKASTAD / MISS.

Adjudikationspanelen (nere till höger) visar alla fyra steg + fusionsverdikt live. Testa: sätt **sidvind** och se banan kröka i sidled; öka **avstånd/målfart** och se geometrin räkna lead; dra ut målet bortom IR-räckvidden och se att fusionen kräver både geometri och IR.
