"""STRILAS firmware-skelett — meddelandeprotokoll (vapen/mål → server).
Samma fält som level3-arkitektur §6 + anti-fusk (nonce/seq/hmac). Dataclasses =
lätt att serialisera (JSON/msgpack på riktig HW); här används de direkt i sim.
"""
from dataclasses import dataclass, asdict
import json


@dataclass
class FireEvent:
    """Vapen → server vid trigger."""
    shooter_id: int
    t_fire: float                 # sekunder (PTP-synkad på HW)
    seq: int                      # anti-replay-sekvens
    nonce: int                    # rullande nonce (anti-replay)
    aim_az_deg: float             # boresight-offset rel. MÅLET (inkl. ev. lead)
    aim_el_deg: float             # (inkl. ev. holdover)
    range_m: float                # CV-PnP-avstånd
    target_vx_mps: float          # uppskattad lateral målfart (för server-koll)
    weapon_profile: str
    fire_control: bool            # var fire-control aktiv?
    ir_code: int                  # rullande kod (matchas mot IRHit)
    n_blobs: int                  # konstellations-LED som syntes (konfidens)
    hmac: str = ""

    def to_json(self): return json.dumps(asdict(self))


@dataclass
class IRHit:
    """Mål → server om TSOP avkodade strålen."""
    target_id: int
    t_rx: float
    ir_code: int
    shooter_id_decoded: int
    zone_hint: str                # grov zon från vilken TSOP-patch (geometri dömer slutligt)
    rssi: float
    seq: int
    hmac: str = ""

    def to_json(self): return json.dumps(asdict(self))


@dataclass
class PlayerState:
    """Låg-rate position/pose (UWB/GNSS + kropps-IMU) → server, för lag-komp-rewind."""
    player_id: int
    t: float
    x: float; y: float; z: float          # världsposition [m]
    vx: float = 0.0; vy: float = 0.0      # hastighet [m/s]
    posture: str = "stand"


@dataclass
class Verdict:
    shooter_id: int
    target_id: int
    result: str                   # HIT / MISS / NEAR_MISS_NO_LOS / REJECTED_REPLAY
    zone: str = ""
    damage: float = 0.0
    miss_lateral_cm: float = 0.0
    miss_vertical_cm: float = 0.0
    reason: str = ""

    def to_json(self): return json.dumps(asdict(self))
