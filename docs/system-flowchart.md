# STRILAS — Systemflödesschema (hur allt hänger ihop)

> Visuell karta över nivå-3-systemet: vilka komponenter som sitter var, hur data
> flödar mellan dem, och vad som händer från trigger till "du är träffad".
> Kompletterar [`level3-ballistic-architecture.md`](level3-ballistic-architecture.md)
> (texten) och [`hardware-analysis.md`](hardware-analysis.md) (delarna/BOM).

---

## 1. Komponentkarta — vem pratar med vem

Tre domäner: **vapennod** och **väst/hjälm-nod** på spelaren, **infrastruktur** i
arenan, och en **server** som ensam avgör träff. Allt sensordata flödar till servern;
bara feedback flödar tillbaka.

```mermaid
flowchart LR
  subgraph WPN["🔫 VAPENNOD (ESP32-P4 PICO + RP2350 IO)"]
    direction TB
    TRG[Trigger / sear] --> FSM[Ballistik-FSM]
    IMU["IMU-array<br/>ICM-45686 ×2–4<br/>(tilt, hög-rate)"] --> FSM
    GNSSH["GNSS-heading<br/>ZED-X20D ~0,1°<br/>(absolut yaw)"] --> FSM
    CAM["Sikteskamera + AI<br/>MIPI-CSI / thermal<br/>(bäring+zon+ID, uppgr.)"] --> FSM
    UWBT1["UWB-tagg<br/>DWM3001"] --> FSM
    NFC["NFC-läsare<br/>ST25R3916"] --> FSM
    FSM --> IRR["IR-emitter-RING<br/>4× SFH4715AS runt kameran<br/>(kodad stråle, samaxlig)"]
    FSM --> RCL["Rekyl<br/>BLDC + ODrive"]
    FSM --> HUD["AR-HUD<br/>(reticle/ammo)"]
    FSM --> RADW["Radio<br/>ESP32-C5 5GHz"]
  end

  subgraph VST["🦺 VÄST/HJÄLM-NOD (ESP32-C5)"]
    direction TB
    TSOP["IR-detektorer<br/>Vishay TSOP4856 ×16–24<br/>(zonade)"] --> VMCU[Väst-MCU]
    BIMU["Kropps-IMU<br/>ICM-45686<br/>(stå/huk/ligg)"] --> VMCU
    UWBT2["UWB-tagg"] --> VMCU
    FID["Fiducials<br/>ArUco/aktiv konstellation"] -. ses av andras kameror .-> CAM
    VMCU --> FB["Feedback<br/>LED + haptik + ljud"]
    VMCU --> RADV["Radio 5GHz"]
  end

  subgraph INF["🏟️ INFRASTRUKTUR"]
    direction TB
    ANCH["UWB-ankare ×4–8<br/>Qorvo QM35825 (AoA)"]
    GBASE["GNSS-bas<br/>mosaic-X5 (RTK/anti-jam)"]
    PTP["PTP-grandmaster<br/>(IEEE-1588)"]
    AP["WiFi-7 AP<br/>(MLO 5/6 GHz)"]
  end

  subgraph SRV["🧠 SERVER (Jetson Orin NX)"]
    direction TB
    ING["MQTT-ingest"] --> FUSE["Sensorfusion<br/>ESKF/FGO → världspose"]
    FUSE --> BAL["Ballistik-motor<br/>flygtid, fall, vind"]
    BAL --> ADJ["Adjudikation<br/>geometri × IR-zon-grind"]
    ADJ --> DB["TimescaleDB"]
    ADJ --> AAR["Dashboard / AAR-karta"]
  end

  RADW -- "FireEvent (signerad)" --> AP
  RADV -- "IRHit + PlayerState" --> AP
  ANCH -- ranges --> AP
  GBASE -- RTK-korr --> AP
  AP --> ING
  PTP -. tidssynk .-> WPN
  PTP -. tidssynk .-> VST
  PTP -. tidssynk .-> SRV
  IRR -. "kodad 905/860 nm IR (luften)" .-> TSOP
  ADJ -- "hit/miss + zon + skada" --> RADV
  RADV --> FB
```

**Läsregel:** heldragna pilar = data/nätverk. Prickade pilar = optik/IR genom luften
eller tidssynk. **IR-strålen** är den enda fysiska länken mellan skytt och mål — den
är "siktlinje-sanningen" som grindar geometrin.

---

## 2. Skottsekvens — från trigger till "träffad"

Det här är den heta loopen. Notera att **kulans flygtid modelleras** (mäts inte), och
att **servern ensam** avgör — vapnet och västen skickar bara signerade bevis.

```mermaid
sequenceDiagram
    autonumber
    participant W as 🔫 Vapen
    participant A as 🌫️ Luft (IR)
    participant V as 🦺 Mål-väst
    participant S as 🧠 Server

    Note over W: Trigger break
    W->>W: Lås pose (IMU+GNSS-yaw+ev. kamera)
    W->>A: Sänd kodad IR-stråle (ring, samaxlig)
    par Två oberoende bevis
        W->>S: FireEvent {shooter_id, t_fire, muzzle_pos,<br/>aim_vec, ir_code, hmac}
    and
        A->>V: Stråle träffar TSOP (om LOS finns)
        V->>S: IRHit {target_id, t_ir_rx, ir_code,<br/>zone, target_pos, hmac}
    end
    Note over S: Adjudikations-tick (120–250 Hz)
    S->>S: 1. Rewind mål till t_fire (lag-komp)
    S->>S: 2. Integrera ballistik längs aim_vec
    S->>S: 3. Placera hitbox vid kulans ankomsttid
    S->>S: 4. Skär bana × kapslar → geometrisk kandidat + zon
    S->>S: 5. Grinda mot IR-zon (matchande ir_code) /<br/>annars cover-/penetrationsmodell
    S-->>V: hit/miss + zon + skada
    V->>V: Feedback (LED/haptik/ljud)
    S->>S: Logga → TimescaleDB → AAR
```

**Varför två bevis?** Geometrin (FireEvent + poser) avgör *om kulan anländer, varifrån,
hur hårt*. IR-zonen (IRHit) avgör *var på kroppen* och bevisar **siktlinje** — geometri
ensam kan inte se en vägg emellan. Servern kombinerar dem (steg 5).

---

## 3. Pose-fusion — de fyra lagren som bygger siktriktningen

Vapnets siktriktning är systemets nyckelgräns. Den byggs i lager (beslut: **fuserad**):

```mermaid
flowchart TB
    A["IR-stråle<br/>LOS-grind + heading-ankare<br/>+ zon + ID"] --> FUSE
    B["ICM-45686-array<br/>hög-rate tilt/attityd<br/>(√N-brus)"] --> FUSE
    C["GNSS dubbelantenn<br/>ZED-X20D ~0,1°<br/>(absolut yaw)"] --> FUSE
    D["Kamera + AI + fiducials<br/>optisk bäring ~2 mrad<br/>(UPPGRADERING)"] -. compute/ljus tillåter .-> FUSE
    FUSE["Fuserad pose<br/>(ESKF/FGO på server)"] --> OUT["aim_vec + aim_quat<br/>+ kovarians"]
```

| Lager | Ger | Svaghet som täcks av andra | Status |
|---|---|---|---|
| IR-stråle | LOS-sanning, grov bäring, ID | grov vinkel → IMU/kamera förfinar | **nu** |
| IMU-array | hög-rate, låg latens | driver → GNSS/kamera binder | **nu** |
| GNSS-heading | absolut yaw (ingen drift, ingen magnetometer) | bara ute, ~Hz-rate → IMU broar | **nu (ute)** |
| Kamera + AI | skarp bäring + zon + ID | mörker (→ thermal), compute | **uppgradering** |

---

## emitter-ring — 4 IR-emittrar i kvadrat runt kameran

Din fråga: **ja**, och det är ett elegant val. Layouten löser tre saker samtidigt:

```mermaid
flowchart TB
    subgraph RING["Optikmodul (sett framifrån)"]
        direction TB
        E1["◤ IR-emitter 1"] -.- E2["IR-emitter 2 ◥"]
        CAMC(["📷 Kamera<br/>(centrerad)"])
        E3["◣ IR-emitter 3"] -.- E4["IR-emitter 4 ◢"]
    end
    RING --> P1["1. Samaxlig fire-stråle<br/>siktbäring = IR-bäring"]
    RING --> P2["2. Aktiv fiducial-konstellation<br/>känd kvadrat → 6DoF-PnP<br/>(andras kameror, även mörker)"]
    RING --> P3["3. Bättre Class 1-ögonsäkerhet<br/>4 källor = större apparent källa<br/>→ lägre näthinneirradians"]
```

**Varför fungerar det:**

1. **Samaxlighet (boresight).** Med kameran i mitten och strålen runt om sammanfaller
   den optiska axeln med IR-axeln. Det kameran/AI:n pekar på = dit kodad IR går. Det
   gör kamera-bäring och IR-träff till *samma* riktning — ingen parallax att kalibrera bort.
2. **Aktiv fiducial.** Fyra emittrar med *känt* kvadratavstånd (t.ex. 40–60 mm) är ett
   plant PnP-mål. En observerande kamera (annan spelare/arena) kan lösa full 6DoF-pose
   på vapnet — och eftersom det är aktiv IR funkar det **i mörker**, till skillnad från
   passiva ArUco-tryck. Modulera varje hörn individuellt → ID + roll-orientering (bryter
   kvadratens symmetri-tvetydighet).
3. **Ögonsäkerhet.** Att sprida emissionen över 4 källor i en kvadrat **ökar den apparenta
   källstorleken**. Under IEC 60825-1 har en utsträckt källa högre tillåten exponering →
   *lättare* att nå Class 1 än en enda punktkälla med samma totaleffekt. (Total tillgänglig
   energi måste fortfarande bänkmätas; C5-derating gäller pulståget.)

**Praktiska designregler:**

- Håll emittrarna **strax utanför kamerans FOV-kon** med en liten skärm/baffel så IR inte
  blöder in i linsen (bloom/flare i bilden).
- Vinkla dem lätt framåt så strålkonerna överlappar på engagemangsavstånd → jämn irradians,
  tolerans mot delvis skymd emitter (redundans 4→ funkar även om 1 skyms).
- Samma bärvåg (38/40/56 kHz) och våglängd som resten av systemet; individuellt adresserbara
  hörn för rikare ID/roll-kodning.

---

## Relaterade dokument

- [`level3-ballistic-architecture.md`](level3-ballistic-architecture.md) — arkitektur i text (geometri + IR-ankare + fuserad pose)
- [`hardware-analysis.md`](hardware-analysis.md) — komponentval + nivå-3-BOM
- [`phase1-build.md`](phase1-build.md) · [`phase1-engagement-sim.md`](phase1-engagement-sim.md) — Fas 1
- [`../sim/`](../sim/) — interaktiv 3D-simulator
