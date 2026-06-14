"""STRILAS firmware-skelett — SERVER-adjudikator (auktoritativ).
Tar FireEvent (+ ev. IRHit) → ballistik + geometri mot kroppskapslar + IR-grind → Verdict.
Detta körs på laptopen/servern (Python både i sim och skarpt).
"""
import numpy as np
from . import config as C, ballistics
from .protocol import Verdict


def _zone(lat_m, vert_m):
    """Vilken kroppszon träffas av skottpunkten (rel. bröstcentrum)? None = bom."""
    for name, zlo, zhi, r, mult in C.BODY_ZONES:
        if zlo <= vert_m <= zhi and abs(lat_m) <= r:
            return name, mult
    return None


def adjudicate(fire, irhit, target_id=1):
    """fire: FireEvent, irhit: IRHit|None. Returnerar Verdict."""
    az, el, R = np.radians(fire.aim_az_deg), np.radians(fire.aim_el_deg), fire.range_m
    # skottet går längs boresight (0,0); målet är (az,el) bort → skottet landar (-az,-el)
    # rel. målcentrum (drop kompenseras via holdover på measured range).
    lat = -R * np.tan(az)
    vert = -R * np.tan(el)
    geo = _zone(lat, vert)

    # IR-grind: matchande kod inom tidsfönster?
    los = (irhit is not None and irhit.ir_code == fire.ir_code
           and abs(irhit.t_rx - fire.t_fire) < C.IR_WINDOW_S)

    v = Verdict(fire.shooter_id, target_id, "MISS",
                miss_lateral_cm=round(lat * 100, 1), miss_vertical_cm=round(vert * 100, 1))
    # Geometrin är domaren; IR GRINDAR endast hits (bekräftar siktlinje).
    if geo and los:
        zone, mult = geo
        _, _, vimp = ballistics.integrate(R, C.PROFILE["v0"])
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
