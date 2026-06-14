"""STRILAS firmware-skelett — delad konfiguration (HW-spec).
Samma värden som hårdvaru-/verifieringsdokumenten. Allt i SI där inget annat sägs.
"""
import numpy as np

# ---- Sikteskamera (OV5640 + M12, FOV 18°) ----
NX, NY = 2592, 1944
FOV_DEG = 18.0
F_PX = (NX/2)/np.tan(np.radians(FOV_DEG/2))     # brännvidd i pixlar (~8183)
CX, CY = NX/2, NY/2
DEG_PX = FOV_DEG/NX

# ---- Konstellation (860 nm), offset i KAMERA-AILGNAD kroppsram [m] ----
# (x=höger, y=ned, z=fram); mål vänt mot skytt → z≈0. Origo = KONSTELLATIONSCENTRUM
# (= aim-referensen som kameran mäter bäring till). Byggd så centroiden = (0,0).
CONSTELLATION = {
    "helmet": (0.00, -0.38, 0.00),
    "chestL": (-0.15, -0.03, 0.00),
    "chestR": (0.15,  -0.03, 0.00),
    "beltL":  (-0.12,  0.22, 0.00),
    "beltR":  (0.12,   0.22, 0.00),
}
# känd vertikal baslinje (hjälm→midja) för PnP-range
BASELINE_V = 0.60

# ---- Kroppskapslar (zoner), vert (upp+) relativt konstellationscentrum, radie lateralt [m] ----
BODY_ZONES = [   # namn, vert_lo, vert_hi, radie, skademultiplikator
    ("Huvud",  0.28, 0.50, 0.11, 3.0),
    ("Bröst", -0.12, 0.25, 0.20, 1.0),
    ("Mage",  -0.32,-0.12, 0.18, 0.8),
    ("Ben",   -1.10,-0.32, 0.15, 0.5),
]

# ---- Vapenprofil (5.56) ----
PROFILE = dict(v0=880.0, dmg=34, beam_half_deg=7.5, ir_range_m=153.0)

# ---- IR-kodning ----
IR_CARRIER_HZ = 56_000
IR_WINDOW_S = 0.20      # tidsfönster för att matcha FireEvent↔IRHit
