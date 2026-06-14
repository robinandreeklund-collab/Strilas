"""STRILAS firmware-skelett — meddelandeprotokoll (vapen/mål → server).
Samma fält som level3-arkitektur §6. Dataclasses = lätt att serialisera (JSON/msgpack
på riktig HW); här används de direkt i sim.
"""
from dataclasses import dataclass, field, asdict
import json, time


@dataclass
class FireEvent:
    """Vapen → server vid trigger."""
    shooter_id: int
    t_fire: float                 # sekunder (PTP-synkad på HW)
    seq: int                      # anti-replay
    aim_az_deg: float             # uppmätt bäring till mål rel. boresight (kamera-PnP)
    aim_el_deg: float
    range_m: float                # PnP-avstånd (eller inmätt i v1)
    weapon_profile: str
    ir_code: int                  # rullande kod (matchas mot IRHit)
    n_blobs: int                  # hur många konstellations-LED som syntes (konfidens)
    hmac: str = ""

    def to_json(self): return json.dumps(asdict(self))


@dataclass
class IRHit:
    """Mål → server om TSOP avkodade strålen."""
    target_id: int
    t_rx: float
    ir_code: int                  # ska matcha en live FireEvent
    shooter_id_decoded: int
    rssi: float
    seq: int
    hmac: str = ""

    def to_json(self): return json.dumps(asdict(self))


@dataclass
class Verdict:
    shooter_id: int
    target_id: int
    result: str                   # HIT / MISS / NEAR_MISS_NO_LOS / REJECTED
    zone: str = ""
    damage: float = 0.0
    miss_lateral_cm: float = 0.0
    miss_vertical_cm: float = 0.0
    reason: str = ""

    def to_json(self): return json.dumps(asdict(self))
