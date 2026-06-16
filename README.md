# STRILAS

**Ballistic Laser Tactical-Engagement Simulator** — an open, DIY force-on-force training/gaming system. Players carry replica weapons that fire **coded infrared light** (not projectiles). Hits are registered by body/helmet detectors, ballistics and time-of-flight are simulated centrally, and every shot, movement, reload and hit is logged for live tracking and after-action review.

Think MILES / laser-tag, but with simulated ballistics, physical recoil feedback, NFC-based ammunition logistics, and an open telemetry stack you own.

> 📖 **Komplett systemguide (master-referens):** [`STRILAS-SYSTEM-GUIDE.md`](STRILAS-SYSTEM-GUIDE.md)
> — allt på ett ställe: arkitektur, ballistik/räckvidd, precision, hitbox, algoritm, optik, RTK-position,
> haptik, korten, batteritid, eye-safety, tillverkning, verifiering och repo-karta.
> Tillverkningsberedskap: [`vapen-stack/nextpcb/FORSTA-BATCH.md`](vapen-stack/nextpcb/FORSTA-BATCH.md).

---

## ⚠️ Safety first — read this before building anything

STRILAS is a **simulation and immersion** system. It does **not** fire projectiles and provides **no** uplift toward any real weapon. It does, however, contain three genuine hazards that you are responsible for handling correctly:

1. **Eye safety (IR laser).** The engagement emitter uses near-IR (~905 nm) which is **invisible**. Keep the optical output within **Class 1 (eye-safe)** limits and enforce the current limit **in hardware**, not just firmware. The risk is highest near the muzzle where players point at each other. If you are not confident you can keep it Class 1, use a diverged IR-LED emitter instead of a collimated laser diode.
2. **LiPo charging.** The base dock charges many lithium packs at once. This is the single largest fire risk in the project — larger than the laser. Use per-cell balancing, a real BMS, thermal monitoring, and a fire-safe charging area.
3. **High-current contacts.** The recoil rail carries ~20 A peaks through the magazine interface. Use contacts rated **> 25 A** and only ever make/break them **cold** (rail disabled during insert/extract — see the make-ready state machine).

**Replica / airsoft chassis:** STRILAS is typically built onto an airsoft replica body. Airsoft replicas are age- and region-restricted; check and follow your local laws for ownership, transport (e.g. muzzle covers / cases), and where you may use them. Treat and store the device responsibly and never carry it in public in a way that could be mistaken for a real firearm.

**Play safety:** eye protection (rated goggles) for all participants, defined play boundaries, and a clear "weapons safe" procedure.

---

## What it does

- **Coded IR engagement** — every shot transmits a packet (shooter ID, weapon profile, ammo/damage code). Detectors on harness + 360° helmet register hits and hit zones.
- **Simulated ballistics** — per-weapon/ammo profiles define muzzle velocity, drag model, drop and time-of-flight. Because the laser arrives instantly, the **server** adjudicates whether the simulated round would land, using both players' positions, the weapon's attitude and the computed flight time.
- **Physical recoil** — an electronic reciprocating-mass unit gives a real kick, scaled per weapon profile. The IMU senses the muzzle climb it causes and feeds it into the **next** shot's trajectory (the recoil-to-aim loop), so uncontrolled bursts walk off target.
- **NFC ammunition logistics** — each magazine carries a passive NFC tag (ID, capacity, rounds remaining). Inserting a mag sets the ammo counter; running dry blocks fire; reloading rewrites the tag to full at base.
- **Make-ready drill** — the recoil power rail (sourced from a battery inside the magazine) is enabled only after racking a charging handle, mirroring "chamber a round," and disabled before the magazine is released. This also guarantees the high-current contacts are always made/broken cold.
- **Live positioning & telemetry** — UWB (+ GNSS outdoors) gives sub-30 cm position; body/weapon IMUs give pose. Everything is timestamped to a shared clock.
- **After-action review** — weapon-cam video synced with the full event timeline, plus a live dashboard and map.

---

## How it works (engagement model)

```
trigger ──► IR emitter sends coded pulse ──► target detector registers strike
   │                                                  │
   └─► recoil unit fires (PWM scaled)                 │
   └─► IMU captures barrel attitude                   ▼
                                       SERVER adjudicates:
                                       shooter pos + target pos (UWB/GNSS)
                                       + barrel attitude (IMU)
                                       + simulated time-of-flight & drop
                                       ──► hit / miss / hit-zone outcome
```

The key design choice is **central, positional adjudication**: rather than computing the result on each weapon, the server knows where both parties are and how they are moving, and resolves the engagement with the simulated projectile's flight time. This is fairer for moving targets and is the basis for the analytics layer.

---

## Project map (design → validated → runnable)

This repo has grown from the spec above into a **physically-validated design with a runnable
reference implementation**. Where to look:

| Area | What | Where |
|---|---|---|
| **Analysis & BOM** | README review + state-of-the-art level-3 BOM + chosen dev boards | [`docs/hardware-analysis.md`](docs/hardware-analysis.md) |
| **Architecture** | geometric ballistic adjudication + fused pose stack (incl. precision ≠ beam width) | [`docs/level3-ballistic-architecture.md`](docs/level3-ballistic-architecture.md) |
| **System flow** | how it all connects (component map, shot sequence, pose layers) | [`docs/system-flowchart.md`](docs/system-flowchart.md) |
| **v1 build** | exact shopping list for a precise 100–150 m shooting test | [`docs/mvp-shooting-test-bom.md`](docs/mvp-shooting-test-bom.md) |
| **Weapon PCB** | optic module: camera + 2× 940 nm emitters + IMU + buck-CC driver (42×62 mm) | [`hardware/README.md`](hardware/README.md) |
| **Receiver PCBs** | vest detector patch + helmet halo (TSOP + 860 nm constellation + GNSS) | [`hardware/receiver-boards.md`](hardware/receiver-boards.md) |
| **Design resolution** | every open problem → decision (wavelength split, eye safety, etc.) | [`hardware/weapon-module-design-resolution.md`](hardware/weapon-module-design-resolution.md) |
| **Eye safety** | Class 1 current budget (script + report) | [`hardware/eye-safety-budget.md`](hardware/eye-safety-budget.md) |
| **Physics verification** | end-to-end @150 m (radiometry + Monte Carlo + link budget) | [`hardware/system-verification-report.md`](hardware/system-verification-report.md) |
| **Firmware/CV** | runnable, hardware-abstracted chain (CV → fire-control → server) — no HW needed | [`firmware/README.md`](firmware/README.md) |
| **3D simulator** | interactive level-3 pipeline in the browser | [`sim/README.md`](sim/README.md) |

Run it (no hardware): `python3 -m firmware.run_demo` · `python3 -m firmware.test_chain` ·
`python3 hardware/system_physics_verification.py`

The key design choice — **central, positional adjudication** — is fully realized in
[`firmware/adjudicator.py`](firmware/adjudicator.py): the server knows where both parties are and
how they move, and resolves the engagement with the simulated projectile's flight time.

---

## System architecture

```
PLAYER NODE ×N
  ├─ Weapon unit (ESP32 + IMU)   ── ballistics, recoil control, state machine, radio
  ├─ IR emitter (905 nm, coded)
  ├─ Recoil unit (reciprocating mass)   ◄── powered by magazine LiPo via load-switch
  ├─ Harness + 360° helmet detectors
  ├─ Magazine (NFC tag + recoil LiPo + power contacts)
  ├─ Charging-handle & mag-release sensors  (make-ready / cold-mate sequencing)
  ├─ Internal logic cell  ── keeps node alive without a magazine
  └─ Weapon camera
        │  ESP-NOW / WiFi
        ▼
NETWORK (field)
  ├─ UWB anchors ×4–8   (sub-30 cm trilateration)
  ├─ WiFi mesh AP        (telemetry + video backhaul)
  └─ [optional] LoRa gateway + GNSS beacons   (large outdoor fields, coarse/long-range)
        │
        ▼
SERVER / EXERCISE CONTROL
  ├─ Hit adjudicator      (position + attitude + flight time → outcome)
  ├─ Position engine      (UWB + GNSS + IMU fusion → live map)
  ├─ Telemetry DB         (shots · movement · recoil · hits · ammo · make-ready)
  └─ AAR / replay + live dashboard
```

---

## Hardware (reference BOM, per player)

| Subsystem | Part (reference) | Notes |
|---|---|---|
| Weapon MCU | ESP32 (WiFi/BLE/ESP-NOW) | the brain; timing-critical IO |
| IMU | BNO085 (or BNO055) | barrel attitude + muzzle climb |
| IR emitter | 905 nm pulsed module + constant-current driver | **Class 1**, hardware current limit |
| Detectors | IR receiver array (harness) + 360° helmet sensor | hit + hit-zone |
| NFC reader | PN532 (I²C/SPI) + magwell switch | wakes on mag insert |
| Magazine tag | NTAG215 (passive) | ID / capacity / remaining |
| Recoil unit | reciprocating-mass actuator | ~0.12 kg moving mass, ~30 mm stroke |
| Recoil switching | logic-level MOSFET load-switch (>30 A) + flyback diode + 2×2200 µF low-ESR | soft-start |
| Magazine battery | high-discharge LiPo (≥25C) | powers recoil rail only |
| Logic battery | small internal 1S/2S cell + buck | keeps node alive without mag |
| Tracking | UWB tag (e.g. DW3000) + GNSS + body IMU | sub-30 cm + pose |
| Camera | ESP32-CAM / RunCam (5.8 GHz FPV or WiFi) | AAR + live |
| HUD | micro-OLED (SPI) | ammo · hits · weapon state |
| Sensors | charging-handle + mag-release micro-switches/hall | make-ready sequencing |

**Infrastructure:** UWB anchors ×4–8, WiFi mesh AP, server host, multi-bay LiPo charging dock (with BMS), optional Heltec CubeCell (HTCC-AB02S) boards as GNSS beacons / LoRa gateway for large outdoor fields.

> The CubeCell boards are **not** suitable as the weapon MCU (no WiFi/BLE, low-power M0+ core, LoRa is low-rate/duty-cycle-limited). Use them only for coarse outdoor GNSS beaconing or as a long-range LoRa gateway.

---

## Power architecture

Two physical sources, deliberately separated:

- **Logic rail** — internal cell → buck (3V3/5V) → MCU, IMU, IR driver, NFC, camera, OLED, radio. ~0.95 A average.
- **Recoil rail** — magazine LiPo → cold-mate power contacts → MOSFET load-switch (soft-start) → cap bank → recoil motor. ~4 A average, ~20 A peaks during full-auto.

The recoil rail is enabled by the MCU **only between "rack" and "mag release"**, so the magazine contacts are never made or broken under load.

---

## Make-ready state machine

```
NO MAG ──insert mag──► MAG IN (rail OFF, cold contacts)
                          │
                          └─ rack charging handle ─► validate (mag present, ammo>0)
                                                     ─► soft-start recoil rail
                                                     ─► chamber ─► READY (rail ON)
READY ──trigger──► IR + recoil, ammo−1 ──► READY
READY ──ammo == 0──► EMPTY (fire blocked, bolt-lock)
EMPTY ──swap mag + re-rack──► READY
ANY  ──mag-release──► drop rail FIRST ─► mag out (cold) ─► NO MAG
```

---

## Magazine NFC tag layout

| Field | Size | Contents |
|---|---|---|
| UID | 7 B | fixed magazine ID (read-only) |
| Capacity | 2 B | max rounds |
| Remaining | 2 B | current rounds |
| Profile | 1 B | weapon/ammo type |
| HMAC (optional) | 4–8 B | signature to prevent tampering |

Notes:
- The live count is held in **weapon RAM** while seated; the tag is written **once on extraction** (and once on base reload), staying well within EEPROM endurance.
- **Ammo count and battery charge are separate quantities.** Base reload is two decoupled cycles: a fast NFC ammo rewrite, and a slow BMS-managed battery charge. Keep a pool of magazines in rotation.
- For competitive integrity, sign `remaining` with an HMAC shared by weapon and base; mirror counts server-side per mag ID as backup.

---

## Weapon profile (example)

```yaml
# profiles/m4_556.yaml
name: "M4 / 5.56 sim"
muzzle_velocity_mps: 880
drag_model: G7
ballistic_coefficient: 0.151
rof_rpm: 720           # capped by recoil cycle time (~12 Hz)
recoil_pwm: 0.65       # 0..1 felt-recoil scale
mag_capacity: 30
damage_code: 0x12
```

---

## Repository structure

```
strilas/
├─ firmware/
│  ├─ weapon-node/        # ESP32: ballistics, recoil FSM, IR, NFC, IMU, radio
│  ├─ tracking-tag/       # UWB + GNSS + IMU beacon
│  ├─ base-dock/          # NFC rewrite + charge sequencing + logging
│  └─ detectors/          # harness / helmet receiver
├─ server/
│  ├─ adjudicator/        # positional hit resolution + flight-time model
│  ├─ position-engine/    # UWB/GNSS/IMU fusion
│  ├─ telemetry-db/       # time-series store
│  └─ dashboard/          # live map + AAR replay
├─ hardware/
│  ├─ weapon-unit/        # schematics, PCB, enclosures
│  ├─ magazine/           # tag + LiPo + contacts
│  └─ base-dock/          # multi-bay charger + BMS
├─ profiles/              # weapon/ammo YAML
├─ docs/
│  └─ strilas-systemritning.html   # full schematic set
└─ README.md
```

---

## Build & flash (outline)

> Detailed per-module instructions live in each subfolder's README.

```bash
# Weapon node (ESP32, PlatformIO)
cd firmware/weapon-node
pio run -t upload

# Server (dev)
cd server
docker compose up        # adjudicator + position-engine + telemetry-db + dashboard
```

Configuration (network keys, UWB anchor coordinates, weapon profiles) is set in `config/` — see `config/example.env`.

---

## Calibration & pre-game checklist

- [ ] IR emitter verified within Class 1 limits (hardware current limit confirmed).
- [ ] IR/detector boresight and range check; hit-cone divergence set per play style.
- [ ] UWB anchors surveyed; position fix < 30 cm in the play area.
- [ ] Recoil rail soft-start verified; no contact arcing on rack/mag-release.
- [ ] Magazine tags initialised (ID, capacity, profile); base reload writes full.
- [ ] All LiPos balanced/charged on the BMS dock; no swollen cells.
- [ ] Clocks synced across nodes (NTP/PTP); telemetry logging confirmed.
- [ ] Eye protection issued; boundaries and "weapons safe" briefed.

---

## Roadmap

- [ ] Environmental ballistics (wind, temperature) in the flight model.
- [ ] AR reticle/HUD overlay in the optic.
- [ ] Auto-generated engagement clips in AAR (tag video by event).
- [ ] Optional LoRa layer for large outdoor fields.
- [ ] Bolt-lock-back + muzzle-report audio for empty/feedback realism.

---

## Contributing

Issues and PRs welcome. Please keep the safety constraints (IR class, cold-mate contacts, BMS charging) non-negotiable in any hardware change, and document power/timing implications for changes that touch the recoil or engagement path.

---

## License

- Code: MIT
- Hardware: CERN-OHL-S
- Docs: CC BY 4.0

*(Adjust to taste before publishing.)*

---

*STRILAS is a training/gaming simulator. It is not a weapon and provides no real-world weapon capability. Build and operate it responsibly and within your local laws.*
