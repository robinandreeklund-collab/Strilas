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
python3 -m firmware.run_mesh      # DISTRIBUERAD fler-nods-sim: optik+väst+hjälm+server på mesh
python3 -m firmware.test_mesh     # 7 tester för distribuerade vägen (reorder, loss, klockfel)
python3 -m firmware.compute_budget # COMPUTE/EFFEKT-cosim: orkar P4:n driva allt? + HIL-plan
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
| `target_node.py` | mål-logik: TSOP → IRHit + PlayerState | ESP32-C5/XIAO-S3 |
| `vest_mb_hw.py` | **väst-moderkortets HW-I/O**: 74HC165-läsning + TPIC6B595-PWM + LED_EN (delat SPI-svep) | XIAO ESP32-S3 (MicroPython→ESP-IDF) |
| `world_sim.py` | **sim-harness**: fejk-kamera, IR-länk, scenario | *ersätts av hårdvaran* |
| `hal.py` | **HAL (Fas 0)**: Clock/Sensors/Radio/Actuators-gräns; `SimHAL` nu, `HardwareHAL`-stub | *byts mot ESP-IDF-drivrutiner* |
| `mesh.py` | **mesh (Fas 1)**: diskret-händelse-nät (latens/jitter/loss) + per-nod klocka (offset/drift/PTP) | WiFi6/ESP-NOW |
| `run_mesh.py` | **distribuerad sim (Fas 1)**: 3 P4-noder + server pratar över mesh:en | *3 fysiska noder* |
| `test_mesh.py` | 7 tester: distribuerade domar = in-process, reorder, loss, klockdrift | — |
| `compute_budget.py` | **compute/effekt-cosim (Fas 2)**: P4-pipeline-budget, bandbredd, W/drifttid, HIL-plan | — |

## Faser (mjukvaru-program)

- **Fas 0 — HAL-gräns ✅** `hal.py`: nod-logiken kör mot `SimHAL` (nu) eller `HardwareHAL` (Fas 3) utan ändring.
- **Fas 1 — distribuerad fler-nods-sim ✅** `mesh.py`+`run_mesh.py`: optik/väst/hjälm/server som separata noder på en
  WiFi6/ESP-NOW-modell (latens, jitter, paketförlust, klock-offset/drift/PTP-residual). Visar att domarna står sig
  under realistisk störning (IR-fönster 200 ms + flygtid ~167 ms ≫ ms-latens + µs-klockfel); reorder-skydd för IR
  som anländer före FireEvent; kontinuerlig PlayerState-ström för lag-komp.
- **Fas 2 — compute/effekt-cosim ✅** `compute_budget.py`: modellerar P4-pipelinen mot ESP32-P4 (2× RISC-V 400 MHz,
  PIE-SIMD, PPA). Svar på "orkar vi driva allt?": **ja, villkorat av två fixar.** (1) `cv_pose`-klustringen är O(n²)
  och skenar i dagsljus (redan 95 % av en kärna nominellt) → byt mot O(n) connected-components → då **26,7 % även i
  värsta solfall**, <2 % med ROI. (2) Full-frame mono8 @120 fps ≈ 123 MB/s **spränger USB2** (~40 MB/s) → MIPI-CSI
  ELLER full-frame-sök @30 fps + ROI-spårning @120 fps (256×256 ≈ 7,9 MB/s, ryms USB). Effekt/latens med marginal.
  Levererar en **HIL-checklista** att mäta på kisel innan full batch.
- **Fas 3 — ESP-IDF/C-port ✅** `../firmware-esp/`: portabel C-kärna (`strilas_core`: blob-CCL O(n), pose,
  fire-control, ballistik, rullande kod) **host-kompilerad + paritetstestad mot denna Python-referens** (17/17 OK);
  per-nod-appar (optik/väst/hjälm via `-DSTRILAS_ROLE`); HAL med HW-drivrutins-stubbar; JSON som matchar
  `protocol.py`. Hela nod-trädet länkar koherent på host. Server (`adjudicator`/`engine`) stannar i Python.
  Kvar: fyll HW-stubbar (`hal_esp.c`) + ESP-IDF-bygge vid bänk-bringup (Fas 2:s HIL-checklista). Se `firmware-esp/README.md`.

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
