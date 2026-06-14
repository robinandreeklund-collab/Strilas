# STRILAS — firmware/CV-skelett (körbart utan hårdvara)

Hårdvaru-abstraherad logik för hela kedjan + en sim-harness som matar syntetisk data,
så **allt kan testas i kod innan en enda lödpunkt**. Samma logik portar till ESP-IDF
(vapen/mål) — bara I/O-lagret byts (sim-harness → riktiga sensorer).

## Kör

```bash
cd <repo-rot>
python3 -m firmware.run_demo      # end-to-end-demo @150 m
python3 -m firmware.test_chain    # automatiska tester (PASS/FAIL)
```

## Moduler

| Fil | Roll | HW-motsvarighet |
|---|---|---|
| `config.py` | delade HW-värden (kamera, konstellation, zoner, profil) | — |
| `protocol.py` | `FireEvent` / `IRHit` / `Verdict` (JSON-serialiserbara) | WiFi-meddelanden |
| `cv_pose.py` | **blob-detektion + pose** (az/el/range) | ESP-P4 kamera/ISP (+ ev. ESP-DL) |
| `ballistics.py` | 3-DOF-bana → flygtid/drop/anslagsfart | server |
| `adjudicator.py` | **server**: geometri × IR-grind → verdikt | laptop/server (Python skarpt också) |
| `weapon_node.py` | vapen-logik: detektioner → FireEvent | ESP32-P4 firmware |
| `target_node.py` | mål-logik: TSOP → IRHit | ESP32-C5 firmware |
| `world_sim.py` | **sim-harness**: fejk-kamera, IR-länk, trigger | *ersätts av hårdvaran* |

## Hårdvaru-abstraktionen (nyckeln)

`WeaponNode.process_detections(detections)` tar **detektor-utdata** — i sim från
`world_sim`, på HW från P4-kameran. Allt ovanför (pose → FireEvent → adjudikation) är
**identiskt** sim↔HW. `world_sim` är det enda som kastas när hårdvaran kommer.

## Vad demon bevisar (allt verifierat i kod @150 m)

- **Bild→pose:** `render_frame` → `detect_blobs` hittar alla 5 konstellations-LED → pose.
- **Adjudikation:** centrerat → HIT Bröst · sikte huvud → HIT Huvud · 0,6 m bom → MISS ·
  cover (ingen IR-LOS) → NEAR_MISS_NO_LOS (geometrin är domare, **IR grindar hits**).
- **PnP-range:** ~149 m (sant 150) ur konstellationens baslinje.
- **Monte Carlo:** träff-% begränsas av **mänsklig sikt-σ**, inte av systemet — vilket
  motiverar fire-control-läget (kameran mäter felet exakt → guida/korrigera mot centrum).

## Nästa steg

1. **Fire-control-läge:** låt kameran-felet driva en HUD/auto-korrigering (σ→0).
2. **Port till ESP-IDF:** `cv_pose`/`weapon_node` → C, behåll `adjudicator` i Python på servern.
3. **Riktig CV-uppgradering:** byt centroid+baslinje mot `cv2.solvePnP` (full 6DoF) + blink-ID-matchning.
4. **Nät/tidssynk:** lägg WiFi-transport + PTP-tidsstämplar på protokoll-lagret.
