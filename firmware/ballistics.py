"""STRILAS firmware-skelett — ballistik (server-sidan), OPTIMERAD.
Banan integreras EN gång per mynningshastighet (cache) → därefter O(1)-interpolation
per skott. Ger flygtid/drop/anslagsfart. Samma fysik som verifieringen.
"""
from functools import lru_cache
import numpy as np

_G, _KD, _DT = 9.81, 0.001277, 5e-4


@lru_cache(maxsize=8)
def _table(v0):
    """Integrera banan en gång (Euler, 0.5 ms) → arrays (x, t, drop, v)."""
    x = y = t = 0.0
    vx, vy = v0, 0.0
    X, T, Y, V = [0.0], [0.0], [0.0], [v0]
    while x < 320 and y > -5:
        sp = (vx*vx + vy*vy) ** 0.5
        vx += -_KD*sp*vx*_DT
        vy += (-_G - _KD*sp*vy)*_DT
        x += vx*_DT; y += vy*_DT; t += _DT
        X.append(x); T.append(t); Y.append(-y); V.append((vx*vx + vy*vy) ** 0.5)
    return np.array(X), np.array(T), np.array(Y), np.array(V)


def integrate(range_m, v0=880.0):
    """Returnerar (tof_s, drop_m, v_impact) vid horisontellt avstånd range_m. O(1)."""
    X, T, Y, V = _table(round(float(v0), 1))
    return (float(np.interp(range_m, X, T)),
            float(np.interp(range_m, X, Y)),
            float(np.interp(range_m, X, V)))


def drop_cm(range_m, v0=880.0):
    return integrate(range_m, v0)[1] * 100.0


def lead_cm(range_m, target_speed_mps, v0=880.0):
    return integrate(range_m, v0)[0] * target_speed_mps * 100.0
