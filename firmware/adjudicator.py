"""STRILAS firmware-skelett — SERVER-adjudikator (auktoritativ).
Full fysik: ballistik (drop) + lead (rörligt mål) + geometri mot kroppskapslar + IR-grind
+ anti-fusk (HMAC + replay). Körs på laptop/server (Python både i sim och skarpt).
"""
import numpy as np
from . import config as C, ballistics, anticheat
from .protocol import Verdict


def _payload(fe):
    return (f"{fe.shooter_id}|{fe.t_fire:.6f}|{fe.seq}|{fe.nonce}|{fe.ir_code}"
            f"|{fe.aim_az_deg:.5f}|{fe.aim_el_deg:.5f}|{fe.range_m:.3f}")


def _zone(lat_m, vert_m):
    for name, zlo, zhi, r, mult in C.BODY_ZONES:
        if zlo <= vert_m <= zhi and abs(lat_m) <= r:
            return name, mult
    return None


def adjudicate(fire, irhit, target_v_true=0.0, key=b"strilas-demo-key", replay=None):
    """fire: FireEvent, irhit: IRHit|None, target_v_true: serverns kända målfart (PlayerState)."""
    v = Verdict(fire.shooter_id, getattr(irhit, "target_id", 1), "MISS")

    # --- anti-fusk ---
    if not anticheat.verify(key, _payload(fire), fire.hmac):
        v.result, v.reason = "REJECTED_REPLAY", "ogiltig HMAC (manipulerad/förfalskad)"
        return v
    if replay is not None and not replay.ok(fire.shooter_id, fire.seq):
        v.result, v.reason = "REJECTED_REPLAY", "omspelad/gammal sekvens"
        return v

    # --- ballistik + lead-geometri ---
    R = fire.range_m
    tof, drop, vimp = ballistics.integrate(R, C.PROFILE["v0"])
    az, el = np.radians(fire.aim_az_deg), np.radians(fire.aim_el_deg)
    # skottet landar (rel. målets t_fire-position): boresight-punkt minus drop
    bx, bz = R*np.tan(az), R*np.tan(el) - drop
    # målet rör sig under flygtiden (server vet sann fart via PlayerState)
    tx, tz = target_v_true*tof, 0.0
    miss_x, miss_z = bx - tx, bz - tz
    v.miss_lateral_cm = round(miss_x*100, 1)
    v.miss_vertical_cm = round(miss_z*100, 1)
    geo = _zone(miss_x, miss_z)

    # --- IR-grind (siktlinje) ---
    los = (irhit is not None and irhit.ir_code == fire.ir_code
           and abs(irhit.t_rx - fire.t_fire) < C.IR_WINDOW_S)

    if geo and los:
        zone, mult = geo
        falloff = max(0.5, vimp / C.PROFILE["v0"])
        v.result, v.zone = "HIT", zone
        v.damage = round(C.PROFILE["dmg"] * mult * falloff, 1)
        v.reason = f"geometri träffar + IR-LOS bekräftad (vimp {vimp:.0f} m/s)"
    elif geo and not los:
        v.result, v.zone = "NEAR_MISS_NO_LOS", geo[0]
        v.reason = "geometri träffar men ingen IR-LOS (cover/blockerad) → ingen hit"
    else:
        v.result = "MISS"
        v.reason = "banan missar kroppen" + (" (IR-konen nuddade ändå)" if los else "")
    return v
