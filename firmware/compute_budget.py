"""STRILAS firmware — COMPUTE- & EFFEKT-COSIM (Fas 2): "orkar vi driva allt?"

Modellerar P4-pipelinen per frame (kamera→tröskling→blob-kluster→PnP→fire-control +
IMU-fusion + radio) mot ESP32-P4:s faktiska envelope, samt bandbredd och effekt/drifttid.
Cykel-kostnaderna är ENGINEERING-ESTIMAT kalibrerade mot de FAKTISKA operationerna i
cv_pose.py — de ska bekräftas på kisel (se HIL-checklistan sist). Modellen flaggar var
marginalen är tunn och ger konkreta rekommendationer.

Kör:  python3 -m firmware.compute_budget
"""
from __future__ import annotations
from dataclasses import dataclass
from . import config as C


# ───────────────────────── ESP32-P4 (Waveshare-modul) ─────────────────────────
@dataclass
class P4:
    f_hz: float = 400e6          # HP-kärnor RISC-V
    cores: int = 2               # 2× HP400 (+ 1 LP40, räknas ej)
    simd_lanes: int = 4          # PIE 128-bit, realistiskt ~4× på 8/16-bit pixlar
    usb_hs_mbs: float = 40.0     # USB2 HS UVC, användbart (480 Mbps gross)
    mipi_csi_mbs: float = 200.0  # MIPI-CSI 2-lane, gott om marginal
    ppa: bool = True             # 2D pixel-accelerator (tröskling/kopiering ~minnesbandbredd)

P4D = P4()


# ───────────────────────── pipeline-modell ─────────────────────────
# cykler/operation (scalar). SIMD/PPA delar pixel-stegen. Kalibrerat mot cv_pose.py.
C_THRESH = 2.0     # gray>thresh : load+cmp+store-mask per px
C_SCAN   = 1.0     # nonzero-extrakt per px
C_CLUST  = 2.0     # greedy-kluster NUVARANDE: hypot+jämför per (bright-px)²  (cv_pose rad 26-27)
C_CCL    = 20.0    # FÖRESLAGEN connected-components: union-find + 8-grannar per bright-px → O(n)
FIX_POSE = 8_000   # centroid + match_to_model + estimate_pose (fix)
C_IMU    = 2_000   # ICM-42688-P sample + komplementär/EKF-uppdatering


@dataclass
class Scene:
    name: str
    bright_px: int        # antal pixlar över tröskel (5 LED nominellt; sol = mer)


def frame_cycles(px, bright_px, p: P4, clust="greedy", use_ppa_thresh=True):
    """Cykler för EN frame (1 kärna gör pixeljobbet). clust: 'greedy' (O(n²), nuvarande)
    eller 'ccl' (O(n) connected-components, föreslagen)."""
    thr = px * C_THRESH / p.simd_lanes
    if use_ppa_thresh and p.ppa:
        thr = px * 0.1 / p.simd_lanes        # PPA gör tröskling nära minnesbandbredd
    scan = px * C_SCAN / p.simd_lanes
    if clust == "ccl":
        clu = bright_px * C_CCL              # O(n) — växer linjärt, robust i dagsljus
    else:
        clu = bright_px * bright_px * C_CLUST  # O(n²) greedy (cv_pose) — skenar med ljusa px!
    return thr + scan + clu + FIX_POSE


def report_compute(px, fps, scenes, p: P4 = P4D, roi_frac=None, clust="greedy", label=""):
    budget_cyc = p.f_hz / fps                # cykler/ram per kärna @ fps
    print(f"\n  {label}  ({px:,} px @ {fps:.0f} fps → budget {1e3/fps:.2f} ms/frame, "
          f"{budget_cyc/1e6:.2f} Mcyc/kärna)")
    eff_px = int(px * roi_frac) if roi_frac else px
    for s in scenes:
        bp = int(s.bright_px * (roi_frac or 1.0)) if roi_frac else s.bright_px
        cyc = frame_cycles(eff_px, bp, p, clust=clust)
        ms = cyc / p.f_hz * 1e3
        util = cyc / budget_cyc * 100
        flag = "✅" if util < 60 else ("⚠️" if util < 100 else "❌ ÖVER BUDGET")
        print(f"    {s.name:22s} bright≈{bp:6d}px → {ms:6.2f} ms/frame · "
              f"{util:5.1f}% av en kärna {flag}")


def report_bandwidth(px, fps, p: P4 = P4D):
    raw_mbs = px * 1 * fps / 1e6          # mono8
    print(f"\n  BANDBREDD: {px:,}px · mono8 · {fps:.0f}fps = {raw_mbs:.0f} MB/s")
    print(f"    USB2-HS UVC (~{p.usb_hs_mbs:.0f} MB/s användbart): "
          f"{'✅ ryms' if raw_mbs <= p.usb_hs_mbs else f'❌ ÖVER ({raw_mbs/p.usb_hs_mbs:.1f}×)'}")
    print(f"    MIPI-CSI 2-lane (~{p.mipi_csi_mbs:.0f} MB/s): "
          f"{'✅ ryms' if raw_mbs <= p.mipi_csi_mbs else '❌ över'}")
    # ROI efter lock
    win = 256 * 256
    roi_mbs = win * fps / 1e6
    print(f"    ROI-spårning {int(win**0.5)}×{int(win**0.5)} efter lock = {roi_mbs:.1f} MB/s "
          f"({'✅ ryms på USB' if roi_mbs <= p.usb_hs_mbs else 'över'})  ← rekommenderat fönsterläge")


# ───────────────────────── effekt / drifttid ─────────────────────────
@dataclass
class Node:
    name: str
    w_active: float       # medeleffekt aktiv (P4+kamera+last), från system-guiden
    wh: float = 16.3      # 2S 2200 mAh

def report_power(nodes):
    print(f"\n  EFFEKT / DRIFTTID (2S 2200 mAh = 16,3 Wh):")
    for n in nodes:
        h = n.wh / n.w_active
        print(f"    {n.name:14s} ~{n.w_active:.1f} W → {h:.1f} h drifttid")


# ───────────────────────── latensbudget (fyr→FireEvent) ─────────────────────────
def report_latency(px, p: P4 = P4D):
    grab = 1e3 / 120                          # 1 frame-tid (global shutter grab) ~8.3 ms
    comp = frame_cycles(256*256, 256, p, clust="ccl") / p.f_hz * 1e3  # rekommenderad O(n)+ROI
    imu = C_IMU / p.f_hz * 1e3
    radio = 3.0                               # mesh-median (Fas 1)
    tot = grab + comp + imu + radio
    print(f"\n  LATENS fyr→FireEvent→server (rekommenderad O(n)+ROI-pipeline):")
    print(f"    frame-grab {grab:.1f} + CV/pose {comp:.2f} + IMU {imu:.2f} + radio {radio:.1f}"
          f" ≈ {tot:.1f} ms   (flygtid ~167 ms + IR-fönster 200 ms → stor marginal)")


if __name__ == "__main__":
    px = C.NX * C.NY
    print("=" * 78)
    print("STRILAS — compute/effekt-cosim (Fas 2): orkar P4:n driva allt?")
    print("=" * 78)
    print(f"  P4: {P4D.cores}× RISC-V @ {P4D.f_hz/1e6:.0f} MHz, PIE-SIMD ~{P4D.simd_lanes}×, "
          f"PPA={'ja' if P4D.ppa else 'nej'}")

    scenes = [Scene("nominellt (5 LED)", 1200),
              Scene("inomhus + reflexer", 4000),
              Scene("dagsljus/sol (värsta)", 30000)]

    print("\n── COMPUTE (vapen/optik = tyngst) ──")
    report_compute(px, 120, scenes, clust="greedy",
                   label="NUVARANDE cv_pose (O(n²)-greedy) @120 fps — exponerar problemet")
    report_compute(px, 120, scenes, clust="ccl",
                   label="FÖRESLAGEN connected-components (O(n)) full-frame @120 fps")
    report_compute(px, 120, scenes, roi_frac=(256*256)/px, clust="ccl",
                   label="FÖRESLAGEN O(n) + ROI-spårning 256×256 @120 fps")

    report_bandwidth(px, 120)

    report_latency(px)

    report_power([Node("optik/vapen", 2.5), Node("väst-mb", 1.5), Node("hjälm-mb", 1.8)])

    print("\n" + "─" * 78)
    print("SLUTSATSER (estimat — bekräftas på kisel):")
    print("  • COMPUTE: nominellt ryms med god marginal. Den O(n²)-greedy-klustringen i")
    print("    cv_pose.py SKENAR vid många ljusa pixlar (sol/reflex) → byt mot connected-")
    print("    components (radvis union-find) + robust adaptiv tröskel. Då stabilt <60%.")
    print("  • BANDBREDD är den BINDANDE gränsen: full-frame mono8 @120 fps ≈ 123 MB/s")
    print("    SPRÄNGER USB2-HS (~40 MB/s). Lösning: (a) MIPI-CSI för full-frame @120 fps,")
    print("    ELLER (b) full-frame-sök @30 fps (≈31 MB/s, ryms USB) + ROI-spårning @120 fps")
    print("    (256×256 ≈ 7,9 MB/s). ROI-strategin är billigast och ryms på befintlig USB.")
    print("  • EFFEKT: konsistent med system-guidens budget (~2,5/1,5/1,8 W → ~6,5/10,9/9,1 h).")
    print("  • LATENS: fyr→FireEvent ~ms ≪ flygtid 167 ms → riklig marginal.")
    print("\nHIL-CHECKLISTA (mät på riktig P4 innan beställning av en full batch):")
    print("  1. Kamera-grab-latens + verklig fps vid 1280×800 (USB-UVC vs MIPI-CSI).")
    print("  2. Tröskling+CCL µs/frame på PPA vs CPU (nominellt + dagsljus-SNR).")
    print("  3. PnP-solve µs (5 punkter) + end-to-end fyr→FireEvent.")
    print("  4. Faktisk strömförbrukning per läge (idle/sök/spårning/fyr) → drifttid.")
    print("  5. Dagsljus-SNR @150 m: hur många ljusa px ger sol → dimensionerar klustringen.")
    print("=" * 78)
