"""STRILAS firmware-skelett — datorseende: blob-detektion + pose-estimering.

HW-abstraktion: på riktig HW kommer `detect_blobs(frame)` från ESP-P4:s kamera/ISP
(ev. ESP-DL); här matas en syntetisk frame eller färdiga centroider. `estimate_pose`
är identisk sim↔HW. Production-uppgradering: byt centroid+baslinje mot cv2.solvePnP.
"""
import numpy as np
from . import config as C


# ----------------------------------------------------------- blob-detektion
def detect_blobs(gray, thresh=0.35, min_pix=2):
    """Tröskla en gråskalebild → klustrade centroider (subpixel). Ren numpy.
    Returnerar lista av (u, v, intensitet). Klustrar ljusa pixlar girigt på avstånd."""
    mask = gray > (thresh * gray.max() if gray.max() > 0 else 1)
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return []
    pts = np.stack([xs, ys], 1).astype(float)
    w = gray[ys, xs].astype(float)
    used = np.zeros(len(xs), bool)
    blobs = []
    for i in range(len(xs)):
        if used[i]:
            continue
        d = np.hypot(pts[:, 0] - pts[i, 0], pts[:, 1] - pts[i, 1])
        grp = (d < 6) & (~used)          # 6 px klusterradie
        used |= grp
        if grp.sum() < min_pix:
            continue
        ww = w[grp]
        cu = (pts[grp, 0] * ww).sum() / ww.sum()    # intensitets-viktad centroid
        cv = (pts[grp, 1] * ww).sum() / ww.sum()
        blobs.append((cu, cv, ww.sum()))
    return blobs


# ----------------------------------------------------------- matchning till modell
def match_to_model(blobs):
    """Sortera blobbar → identifiera helmet(topp) & midja(botten) för baslinjen.
    På HW: använd modulerad blink-ID per LED. Här: geometrisk topp/botten."""
    if len(blobs) < 2:
        return None
    arr = np.array([[b[0], b[1]] for b in blobs])
    top = arr[np.argmin(arr[:, 1])]      # minsta v = högst upp (helmet)
    bot = arr[np.argmax(arr[:, 1])]      # största v = lägst (midja)
    centroid = arr.mean(0)
    return dict(centroid=centroid, top=top, bottom=bot, n=len(blobs))


# ----------------------------------------------------------- pose-estimering
def estimate_pose(blobs):
    """Konstellations-blobbar → (az, el, range). az/el = bäring till mål rel. boresight.
    range ur känd vertikal baslinje (BASELINE_V) / uppmätt vinkel. Returnerar None om <2."""
    m = match_to_model(blobs)
    if m is None:
        return None
    cu, cv = m["centroid"]
    az = np.degrees(np.arctan((cu - C.CX) / C.F_PX))
    el = -np.degrees(np.arctan((cv - C.CY) / C.F_PX))   # el upp positiv
    dv_px = abs(m["top"][1] - m["bottom"][1])
    ang = dv_px / C.F_PX                                  # radianer
    rng = C.BASELINE_V / np.tan(ang) if ang > 1e-9 else float("inf")
    return dict(az_deg=az, el_deg=el, range_m=rng, n_blobs=m["n"])
