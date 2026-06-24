"""STRILAS firmware-skelett — FIRE-CONTROL (sikteslösning).
Kameran mäter målets bäring + avstånd; IMU/frame-historik ger målets fart.
Fire-control räknar ut LEAD (mål rör sig under flygtiden) + HOLDOVER (kuldrop)
så att skottet träffar — det som tar träff-% från människo-begränsad → ~100 %.
"""
import numpy as np
from . import ballistics


def firing_solution(range_m, v_lat_mps, v0=880.0):
    """Returnerar siktkorrektion: lead (sidled) + holdover (höjd för drop), i GRADER,
    plus flygtid/drop/anslagsfart. v_lat_mps = målets laterala fart (uppskattad)."""
    tof, drop, vimp = ballistics.integrate(range_m, v0)
    lead_az_deg = np.degrees(np.arctan((v_lat_mps * tof) / range_m))
    holdover_el_deg = np.degrees(np.arctan(drop / range_m))
    return dict(lead_az_deg=lead_az_deg, holdover_el_deg=holdover_el_deg,
                tof=tof, drop=drop, vimp=vimp)


def reticle_offset_cm(range_m, v_lat_mps, v0=880.0):
    """HUD-läge: var ska skytten lägga pricken (cm vid målet) = lead + holdover."""
    s = firing_solution(range_m, v_lat_mps, v0)
    return dict(lead_cm=range_m*np.tan(np.radians(s["lead_az_deg"]))*100,
                holdover_cm=s["drop"]*100)
