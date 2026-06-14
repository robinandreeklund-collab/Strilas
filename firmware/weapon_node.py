"""STRILAS firmware-skelett — VAPEN-NOD (ESP32-P4-logik, HW-abstraherad).
- process_detections(): perception (kamera/blob → pose) — samma kod sim↔HW.
- engage(): siktar (naivt eller fire-control) → signerad FireEvent.
"""
import numpy as np
from . import cv_pose, fire_control, world_sim as W, config as C, anticheat
from .protocol import FireEvent

_rng = np.random.default_rng(11)


def _payload(fe: FireEvent) -> str:
    return (f"{fe.shooter_id}|{fe.t_fire:.6f}|{fe.seq}|{fe.nonce}|{fe.ir_code}"
            f"|{fe.aim_az_deg:.5f}|{fe.aim_el_deg:.5f}|{fe.range_m:.3f}")


class WeaponNode:
    def __init__(self, shooter_id=7, profile="M4 / 5.56", key=b"strilas-demo-key"):
        self.id = shooter_id
        self.profile = profile
        self.key = key
        self.seq = 0
        self.roll = anticheat.RollingCode(0x1A2B ^ shooter_id)
        self.pose = None

    # --- perception (för HW: ESP-kamera; här sim-detektioner) ---
    def process_detections(self, detections):
        self.pose = cv_pose.estimate_pose(detections)
        return self.pose

    # --- sikta + avfyra ---
    def engage(self, scn, use_fc, t):
        p = W.perceive(scn)
        rng, v_est = p["range_m"], p["v_est"]
        zone_ang = np.degrees(np.arctan(W.zone_vert(scn.aim_zone) / rng))
        if use_fc:
            s = fire_control.firing_solution(rng, v_est, C.PROFILE["v0"])
            az = s["lead_az_deg"] + _rng.normal(0, W.CV_RESIDUAL_DEG)
            el = zone_ang + s["holdover_el_deg"] + _rng.normal(0, W.CV_RESIDUAL_DEG)
        else:
            az = _rng.normal(0, scn.human_sigma_deg)
            el = zone_ang + _rng.normal(0, scn.human_sigma_deg)
        self.seq += 1
        code, nonce = self.roll.next(), self.roll.next()
        fe = FireEvent(shooter_id=self.id, t_fire=t, seq=self.seq, nonce=nonce,
                       aim_az_deg=az, aim_el_deg=el, range_m=rng, target_vx_mps=v_est,
                       weapon_profile=self.profile, fire_control=use_fc,
                       ir_code=code, n_blobs=p["n_blobs"])
        fe.hmac = anticheat.sign(self.key, _payload(fe))
        return fe, code
