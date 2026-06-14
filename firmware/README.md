# STRILAS — firmware/CV-skelett (komplett, körbart utan hårdvara)

Hårdvaru-abstraherad referensimplementation av **hela** STRILAS-kedjan + sim-harness,
så allt kan köras och testas i kod innan en enda lödpunkt. Samma logik portar till ESP-IDF
(vapen/mål); bara I/O-lagret (`world_sim`) byts mot riktiga sensorer.

## Kör

```bash
cd <repo-rot>
python3 -m firmware.run_demo      # end-to-end-demo @150 m (perception → FC → server → verdikt)
python3 -m firmware.test_chain    # 15 automatiska tester (alla PASS)
python3 -m firmware.benchmark     # server-prestanda (~57k adj/s)
```

## Moduler

| Fil | Roll | HW-motsvarighet |
|---|---|---|
| `config.py` | delade HW-värden (kamera, konstellation, zoner, profil) | — |
| `protocol.py` | `FireEvent`/`IRHit`/`PlayerState`/`Verdict` (+ nonce/hmac) | WiFi/MQTT-meddelanden |
| `cv_pose.py` | **blob-detektion + pose** (az/el/range) | ESP-P4 kamera/ISP |
| `fire_control.py` | **sikteslösning**: lead (rörligt mål) + holdover (drop) | vapen-firmware/HUD |
| `ballistics.py` | bana → flygtid/drop/anslagsfart (**cachad tabell, O(1)**) | server |
| `imu`-modell | *(IMU-residual i `world_sim`)* | ICM-45686 |
| `anticheat.py` | rullande IR-kod + nonce + HMAC + replay-skydd | säkert element + server |
| `transport.py` | meddelandebuss (pub/sub) | WiFi6/MQTT |
| `engine.py` | **server**: pairing FireEvent↔IRHit, lag-komp, tick-loop | laptop/server |
| `adjudicator.py` | **dom**: ballistik + lead + geometri × IR-grind + anti-fusk | server |
| `weapon_node.py` | vapen-logik: perception + engage → signerad FireEvent | ESP32-P4 |
| `target_node.py` | mål-logik: TSOP → IRHit + PlayerState | ESP32-C5 |
| `world_sim.py` | **sim-harness**: fejk-kamera, IR-länk, scenario | *ersätts av hårdvaran* |

## Vad som är verifierat i kod (@150 m, allt PASS)

- **Perception:** `render_frame`→`detect_blobs` hittar alla 5 konstellations-LED → pose, range ~150 m.
- **Fire-control:** stationärt + rörligt → HIT rätt zon (bröst/huvud); lead + holdover räknas.
- **Realism:** naivt skott utan holdover landar **lågt** (drop 16 cm @150 m); utan lead **missar** rörligt mål.
- **IR-grind:** cover (ingen IR-LOS) → `NEAR_MISS_NO_LOS` (geometrin dömer, IR grindar hits).
- **Anti-fusk:** manipulerad HMAC + omspelad sekvens → `REJECTED_REPLAY`.
- **Server-motor:** pairing FireEvent↔IRHit, tick-timeout, lag-komp via PlayerState.
- **Prestanda:** **~57 000 adjudikationer/s** (17 µs/skott) → ×120 marginal mot full-auto 32 spelare.

## Nyckelresultat: fire-control

| Mål | Naivt (människa) | Fire-control |
|---|---|---|
| Stationärt | ~10 % | **~100 %** |
| 4 m/s | ~7 % | **~100 %** |

Människans sikt-σ är begränsningen — **inte systemet** (kamerans σ ≈ 0,0004°). Kameran mäter
felet exakt och räknar lead/holdover → träff-% mot 100 %.

## Hårdvaru-abstraktionen (nyckeln)

`WeaponNode.process_detections()` tar **detektor-utdata** (sim nu / P4-kamera sen). Allt ovanför
(pose → fire-control → FireEvent → server-adjudikation) är **identiskt** sim↔HW. `world_sim` är
det enda som kastas när hårdvaran kommer.

## Nästa steg mot skarp drift

1. **Port:** `cv_pose`/`fire_control`/`weapon_node` → C (ESP-IDF); `adjudicator`/`engine` stannar i Python.
2. **Riktig CV:** byt centroid+baslinje mot `cv2.solvePnP` (full 6DoF) + modulerad blink-ID-matchning.
3. **Nät/tid:** WiFi6/MQTT på `transport` + PTP-tidsstämplar på protokoll-lagret.
4. **Bänk:** koppla mot riktiga kort + mät (Class 1, dagsljus-SNR, räckvidd).
