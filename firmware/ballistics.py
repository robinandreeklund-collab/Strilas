"""STRILAS firmware-skelett — ballistik (server-sidan).
3-DOF-integration (gravitation + drag), kalibrerad så 5.56 stämmer. Ger flygtid,
drop och anslagsfart. Samma modell som sim/hardware-verifieringen.
"""
import numpy as np

_G, _KD, _DT = 9.81, 0.001277, 5e-4


def integrate(range_m, v0=880.0):
    """Returnerar (tof_s, drop_m, v_impact) vid horisontellt avstånd range_m."""
    x = y = t = 0.0
    vx, vy = v0, 0.0
    last = (0.0, 0.0, v0)
    while x < range_m + 1 and y > -3:
        sp = np.hypot(vx, vy)
        vx += -_KD * sp * vx * _DT
        vy += (-_G - _KD * sp * vy) * _DT
        x += vx * _DT; y += vy * _DT; t += _DT
        if x >= range_m:
            return t, -y, np.hypot(vx, vy)
        last = (t, -y, np.hypot(vx, vy))
    return last


def drop_cm(range_m, v0=880.0):
    return integrate(range_m, v0)[1] * 100.0


def lead_cm(range_m, target_speed_mps, v0=880.0):
    return integrate(range_m, v0)[0] * target_speed_mps * 100.0
