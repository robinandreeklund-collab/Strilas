"""STRILAS firmware-skelett — delad konfiguration (HW-spec).
Samma värden som hårdvaru-/verifieringsdokumenten. Allt i SI där inget annat sägs.
"""
import numpy as np

# ---- Sikteskamera (LÅST 2026-06): VEYE RAW-MIPI-AR0234M MONO, GS, MIPI-CSI på CM5 ----
# AR0234 2,3 MP 1920×1200, 3 µm-pixlar, 1/2.6". Global shutter → ingen pan-smet. Mono = full NIR-QE
# utan Bayer (ser 860 nm). RAW Mono8/10, 22-pin MIPI-CSI (passar CM5), 120 fps @4-lane / 60 @2-lane.
# DRIVER: VEYE V4L2 på Raspberry Pi (ej libcamera) → firmware läser rå mono via cv2.VideoCapture.
# LINS: ~24 mm M12 → 2·atan(2.88/24) = 13,7° H FOV (1/2.6″). + 850/860 nm bandpass (dagsljus-rejekt).
# Mount: M12-hållare; board 29×29 mm (DXF/STP från VEYE → exakta hål). VAL: tillgänglighet (Mira220
# svår att få) + VEYE RPi-driver + 120 fps. (Mira220 hade bättre NIR-SNR → bänkmät AR0234 dagsljus-SNR.)
NX, NY = 1920, 1200
FOV_DEG = 13.7
F_PX = (NX/2)/np.tan(np.radians(FOV_DEG/2))      # brännvidd i pixlar (~7995)
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
