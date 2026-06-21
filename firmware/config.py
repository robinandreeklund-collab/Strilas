"""STRILAS firmware-skelett — delad konfiguration (HW-spec).
Samma värden som hårdvaru-/verifieringsdokumenten. Allt i SI där inget annat sägs.
"""
import numpy as np

# ---- Sikteskamera (LÅST 2026-06): ams Mira220 MONO, GS NIR-enhanced, MIPI-CSI på CM5 ----
# 2,2 MP 1600×1400, 2,79 µm BSI-pixlar, 1/2.7". Global shutter → ingen pan-smet. NIR-enhanced
# (~38% QE@940, högre @860) → bäst dagsljus-SNR; mono = full NIR-QE utan Bayer. Samma leverantör
# (ams OSRAM) som OSLON-emittrarna. Turnkey libcamera-driver på RPi CM5 (ams_rpi_kernel).
# LINS: ~18 mm M12 → 2·atan(2.23/18) = 13,7° H FOV (1/2.7″). + 850/860 nm bandpass (dagsljus-rejekt).
# (Fysik: 13,7° ger ~14 px LED-sep + 24 px baslinje @150 m → robust PnP. Se hardware/camera-selection.md
#  + weapon-v2-design.md. Tidigare Arducam B0332/USB UTGICK — fast lins, nådde ej 150 m.)
NX, NY = 1600, 1400
FOV_DEG = 13.7
F_PX = (NX/2)/np.tan(np.radians(FOV_DEG/2))      # brännvidd i pixlar (~6660)
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
