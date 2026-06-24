"""STRILAS firmware-skelett — SIM-HARNESS (ersätter hårdvaran).
(a) Perception: fejk-kamera projicerar konstellationen + brus → blob-detektion (bevisar CV).
(b) Engagemang: scenario (avstånd, målfart, skytt-σ, cover) → sensordata för hela kedjan.
Låter allt köras utan hårdvara. Samma gränssnitt som riktiga sensorer matar.
"""
from dataclasses import dataclass
import numpy as np
from . import config as C

_rng = np.random.default_rng(7)

# brus-modeller (från fysik-verifieringen)
CV_RESIDUAL_DEG = 0.002      # kamera-bäring + IMU-residual (verifierat ~0.0004°, konservativt)
RANGE_SIGMA_M = 0.5          # PnP-avstånd
VEL_SIGMA_MPS = 0.3          # målfarts-skattning


# ---------------- (a) PERCEPTION: bild → blobbar (bevisar detect_blobs) ----------------
def project_constellation(az_deg, el_deg, range_m):
    az, el = np.radians(az_deg), np.radians(el_deg)
    Tx, Ty, Tz = range_m*np.tan(az), -range_m*np.tan(el), range_m
    out = {}
    for name, (ox, oy, oz) in C.CONSTELLATION.items():
        X, Y, Z = Tx+ox, Ty+oy, Tz+oz
        out[name] = (C.CX + C.F_PX*X/Z, C.CY + C.F_PX*Y/Z)
    return out


def render_frame(centroids, sigma_px=1.2, peak=1.0):
    img = np.zeros((C.NY, C.NX), np.float32)
    r = int(4*sigma_px)
    for (u, v) in centroids.values():
        ui, vi = int(round(u)), int(round(v))
        if not (r <= ui < C.NX-r and r <= vi < C.NY-r):
            continue
        ys, xs = np.mgrid[vi-r:vi+r+1, ui-r:ui+r+1]
        img[vi-r:vi+r+1, ui-r:ui+r+1] += peak*np.exp(-((xs-u)**2+(ys-v)**2)/(2*sigma_px**2))
    return np.clip(img, 0, 1)


# ---------------- (b) ENGAGEMANG-scenario ----------------
@dataclass
class Scenario:
    range_m: float = 150.0
    v_lat_mps: float = 0.0       # målets laterala fart
    aim_zone: str = "Bröst"     # vart skytten SIKTAR (zonens vert-mitt)
    human_sigma_deg: float = 0.3 # mänskligt siktfel (naivt läge)
    los_blocked: bool = False    # cover bryter IR
    seed: int = 0


def perceive(scn):
    """Vad sensorerna rapporterar (med brus): range, målfart, n_blobs."""
    r = np.random.default_rng(scn.seed) if scn.seed else _rng
    return dict(range_m=scn.range_m + r.normal(0, RANGE_SIGMA_M),
                v_est=scn.v_lat_mps + r.normal(0, VEL_SIGMA_MPS),
                n_blobs=len(C.CONSTELLATION))


def ir_link(aim_az_deg, aim_el_deg, range_m, los_blocked):
    """Ser målets TSOP skottet? Bred kon (beam_half) + räckvidd + LOS."""
    off = np.hypot(aim_az_deg, aim_el_deg)
    return (off < C.PROFILE["beam_half_deg"]
            and range_m <= C.PROFILE["ir_range_m"]
            and not los_blocked)


def zone_vert(zone):
    for name, lo, hi, r, m in C.BODY_ZONES:
        if name == zone:
            return (lo+hi)/2
    return 0.0
