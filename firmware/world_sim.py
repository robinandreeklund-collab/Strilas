"""STRILAS firmware-skelett — SIM-HARNESS (ersätter hårdvaran).
Syntetiserar: fejk-kamera (projicerar konstellationen + brus), IR-länk, trigger.
Låter hela kedjan köras utan hårdvara. Samma gränssnitt som riktiga sensorer matar.
"""
import numpy as np
from . import config as C

_rng = np.random.default_rng(7)


def project_constellation(az_deg, el_deg, range_m):
    """Sann bildprojektion av konstellationen givet bäring (az,el) till centroid + range.
    Returnerar dict id->(u,v) i pixlar."""
    az, el = np.radians(az_deg), np.radians(el_deg)
    Tx, Ty, Tz = range_m*np.tan(az), -range_m*np.tan(el), range_m   # centroid i kamera-frame
    out = {}
    for name, (ox, oy, oz) in C.CONSTELLATION.items():
        X, Y, Z = Tx+ox, Ty+oy, Tz+oz
        out[name] = (C.CX + C.F_PX*X/Z, C.CY + C.F_PX*Y/Z)
    return out


def render_frame(centroids, sigma_px=1.2, peak=1.0):
    """Rita konstellationen som Gaussiska blobbar i en full-res gråskalebild (för att
    BEVISA blob-detektionen end-to-end). Bara lokala patchar ritas → snabbt."""
    img = np.zeros((C.NY, C.NX), np.float32)
    r = int(4*sigma_px)
    for (u, v) in centroids.values():
        ui, vi = int(round(u)), int(round(v))
        if not (r <= ui < C.NX-r and r <= vi < C.NY-r):
            continue
        ys, xs = np.mgrid[vi-r:vi+r+1, ui-r:ui+r+1]
        img[vi-r:vi+r+1, ui-r:ui+r+1] += peak*np.exp(-((xs-u)**2+(ys-v)**2)/(2*sigma_px**2))
    return np.clip(img, 0, 1)


def noisy_detections(az_deg, el_deg, range_m, sigma_centroid_px=0.1):
    """Snabbväg: konstellations-centroider + centroidbrus (= 'detektor-utdata').
    Returnerar lista (u,v,intensitet) som cv_pose.estimate_pose tar."""
    pts = project_constellation(az_deg, el_deg, range_m)
    det = []
    for (u, v) in pts.values():
        det.append((u + _rng.normal(0, sigma_centroid_px),
                    v + _rng.normal(0, sigma_centroid_px), 1.0))
    return det


def ir_link(true_az_deg, true_el_deg, range_m, los_blocked=False):
    """Ser målets TSOP skottet? Bred kon (beam_half) + räckvidd + LOS."""
    off = np.hypot(true_az_deg, true_el_deg)
    return (off < C.PROFILE["beam_half_deg"]
            and range_m <= C.PROFILE["ir_range_m"]
            and not los_blocked)
