"""STRILAS firmware-skelett — delad konfiguration (HW-spec).
Samma värden som hårdvaru-/verifieringsdokumenten. Allt i SI där inget annat sägs.
"""
import numpy as np

# ---- Sikteskamera (LÅST): OV9281 mono GLOBAL SHUTTER NoIR, USB-UVC, M12 NoIR-lins ----
# 1 MP 1280×800, 3 µm-pixlar, 1/4". Global shutter → ingen pan-smet. NoIR krävs för 860 nm.
# LINS: 16 mm M12 → 2·atan(3.84/32) = 13,7° H FOV. (Fysik: 1 MP @ 6mm/35,5° upplöser bara
# ~9 px konstellation @150 m → LED:erna smälter ihop. 16 mm ger ~14 px LED-separation + 24 px
# baslinje → ROBUST PnP @150 m med marginal. Scen @150 m = 36 m bred (gott om plats att hitta mål).
# 12 mm (18°) = vidare FOV men knappare marginal; 6 mm = bara ~80 m. Se camera-selection.md.)
NX, NY = 1280, 800
FOV_DEG = 13.7
F_PX = (NX/2)/np.tan(np.radians(FOV_DEG/2))     # brännvidd i pixlar (~5330)
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
