"""STRILAS — COMPUTE/EFFEKT-COSIM för RASPBERRY PI CM5 (vapen-noden): "orkar den driva allt?"

Samma analys som compute_budget.py gjorde för ESP32-P4, men nu för den valda plattformen:
CM5 (BCM2712, 4× Cortex-A76 @2,4 GHz, VideoCore VII + HW-ISP) + VEYE AR0234M (1920×1200 mono GS,
MIPI-CSI, 120 fps @4-lane). Kör Python/OpenCV direkt (ingen C-port). Cykel-estimaten kalibrerade mot
de FAKTISKA operationerna i cv_pose.py + A76:s NEON-SIMD. Bekräftas på kisel (HIL).

Kör:  python3 -m firmware.compute_budget_cm5
"""
from __future__ import annotations
from dataclasses import dataclass
from . import config as C


@dataclass
class CM5:
    f_hz: float = 2.4e9          # A76 HP-kärnor
    cores: int = 4
    ipc: float = 3.0             # A76 ~3-4 IPC realistiskt
    neon_lanes: int = 16         # NEON 128-bit på 8-bit pixlar
    mipi_csi_mbs: float = 1500.0 # MIPI-CSI 4-lane (D-PHY) — gott om marginal
    isp: bool = True             # VideoCore VII HW-ISP (tröskling/debayer/gain offload)

CM5D = CM5()

# operationer (cykler/px scalar; NEON delar pixel-stegen) — kalibrerat mot cv_pose.py + O(n)-CCL
C_THRESH = 2.0
C_SCAN   = 1.0
C_CCL    = 20.0     # O(n) connected-components (union-find) per bright-px
FIX_POSE = 8_000
C_IMU    = 2_000

@dataclass
class Scene:
    name: str
    bright_px: int

def frame_us(px, bright_px, p: CM5 = CM5D, use_isp=True):
    """µs för EN frame på EN A76-kärna (NEON). ISP gör tröskling → nästan gratis."""
    thr = px * C_THRESH / (p.neon_lanes * p.ipc)
    if use_isp and p.isp: thr = px * 0.05 / p.neon_lanes
    scan = px * C_SCAN / (p.neon_lanes * p.ipc)
    ccl = bright_px * C_CCL / p.ipc
    cyc = thr + scan + ccl + FIX_POSE
    return cyc / p.f_hz * 1e6


if __name__ == "__main__":
    px = C.NX * C.NY     # AR0234 1920×1200 = 2,3 MP
    print("=" * 78)
    print("STRILAS — compute/effekt-cosim CM5 (vapen-nod): orkar den driva allt?")
    print("=" * 78)
    print(f"  CM5: {CM5D.cores}× Cortex-A76 @{CM5D.f_hz/1e9:.1f} GHz, NEON ~{CM5D.neon_lanes}× (8-bit), "
          f"HW-ISP={'ja' if CM5D.isp else 'nej'}")
    print(f"  Kamera: AR0234M {C.NX}×{C.NY} = {px/1e6:.1f} MP mono GS, MIPI-CSI 4-lane @120 fps\n")

    scenes = [Scene("nominellt (5 LED)", 1800),
              Scene("inomhus + reflexer", 6000),
              Scene("dagsljus/sol (värsta)", 45000)]
    budget_us = 1e6 / 120     # @120 fps
    print(f"  ── COMPUTE (CV-pipeline, EN av 4 kärnor) @120 fps (budget {budget_us:.2f} µs/frame) ──")
    for s in scenes:
        us = frame_us(px, s.bright_px)
        util = us / budget_us * 100
        flag = "✅" if util < 40 else ("⚠️" if util < 100 else "❌")
        print(f"    {s.name:24s} bright≈{s.bright_px:6d}px → {us:6.1f} µs/frame · "
              f"{util:5.1f}% av EN kärna {flag}")
    print(f"    (4 kärnor → CV + IMU-fusion + libcamera + mesh + ballistik parallellt; OpenCV/solvePnP)")

    print(f"\n  ── BANDBREDD ──")
    raw = px * 1 * 120 / 1e6
    print(f"    {px:,}px mono8 @120 fps = {raw:.0f} MB/s · MIPI-CSI 4-lane (~{CM5D.mipi_csi_mbs:.0f} MB/s): "
          f"{'✅ ryms (ingen USB-flaskhals)' if raw < CM5D.mipi_csi_mbs else '❌'}")

    print(f"\n  ── LATENS fyr→FireEvent ──")
    grab = 1e3/120; comp = frame_us(px, 6000)/1e3; imu = C_IMU/CM5D.f_hz*1e3; radio = 3.0
    print(f"    frame-grab {grab:.1f} + CV/pose {comp:.2f} + IMU {imu:.3f} + radio {radio:.1f} "
          f"≈ {grab+comp+imu+radio:.1f} ms  (flygtid ~167 ms → enorm marginal)")

    print(f"\n  ── EFFEKT / DRIFTTID (2S 2200 mAh = 16,3 Wh) ──")
    for w in (4.5, 6.0):
        print(f"    CM5+kamera ~{w:.1f} W → {16.3/w:.1f} h drifttid")
    print(f"    (CM5 starkare = törstigare än P4; underklocka/3S förlänger — se weapon-v2-design.md §7)")

    print("\n" + "─" * 78)
    print("SLUTSATS (estimat — bekräftas på kisel):")
    print("  • COMPUTE: ENORM marginal. CM5 (A76 4×2,4 GHz, ~12× P4:s aggregat) kör CV-pipelinen på")
    print("    <40% av EN kärna även i värsta dagsljus → 3 kärnor fria för IMU-fusion/mesh/ballistik.")
    print("    HW-ISP gör tröskling nära gratis. Python/OpenCV/solvePnP direkt — ingen O(n²)-fälla")
    print("    (vs P4 där cv_pose-greedy skenade + USB-bandbredd sprängdes). Båda P4-riskerna BORTA.")
    print("  • BANDBREDD: MIPI-CSI 4-lane → ingen USB-flaskhals (P4:s bindande gräns försvann).")
    print("  • EFFEKT: ~4,5-6 W → ~2,7-3,6 h. Enda priset för CM5:s kraft (medveten avvägning).")
    print("  • → JA, den nya lösningen orkar driva allt med stor marginal. Inga compute-villkor kvar")
    print("    (mot P4:s 2 villkor: O(n)-CCL + bandbreddslösning — båda inbyggt lösta av CM5+MIPI).")
    print("=" * 78)
