"""STRILAS firmware-skelett — automatiska tester (utan hårdvara).
Kör:  python -m firmware.test_chain   (eller pytest)
Verifierar att logikkedjan ger rätt verdikt för kända scenarier.
"""
import numpy as np
from . import world_sim as W, cv_pose, config as C
from .weapon_node import WeaponNode
from .target_node import TargetNode
from .adjudicator import adjudicate

R = 150.0


def _engage(az, el, los_blocked=False, use_image=False):
    w, t = WeaponNode(), TargetNode()
    blobs = (cv_pose.detect_blobs(W.render_frame(W.project_constellation(az, el, R)))
             if use_image else W.noisy_detections(az, el, R))
    w.process_detections(blobs)
    fe, code = w.fire(1.0)
    seen = W.ir_link(az, el, R, los_blocked)
    return adjudicate(fe, t.on_ir(code, 7, 1.0005) if seen else None), len(blobs)


def run():
    fails = []
    def check(name, cond):
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
        if not cond: fails.append(name)

    # 1. bild→detektion hittar alla 5 LED
    _, n = _engage(0, 0, use_image=True)
    check("detect_blobs hittar 5 konstellations-LED", n == 5)

    # 2. centrerat → HIT Bröst
    v, _ = _engage(0, 0.0)
    check("centrerat → HIT Bröst", v.result == "HIT" and v.zone == "Bröst")

    # 3. sikte mot huvud → HIT Huvud
    v, _ = _engage(0, -np.degrees(np.arctan(0.38/R)))
    check("sikte huvud → HIT Huvud", v.result == "HIT" and v.zone == "Huvud")

    # 4. 0.6 m sidled → MISS
    v, _ = _engage(np.degrees(np.arctan(0.6/R)), 0)
    check("0.6 m sidled → MISS", v.result == "MISS")

    # 5. centrerat men cover → NEAR_MISS_NO_LOS (geometri ja, IR nej)
    v, _ = _engage(0, 0, los_blocked=True)
    check("cover (ingen IR-LOS) → NEAR_MISS_NO_LOS", v.result == "NEAR_MISS_NO_LOS")

    # 6. range-estimat inom 3 % @150 m
    w = WeaponNode(); w.process_detections(W.noisy_detections(0, 0, R))
    fe, _ = w.fire(1.0)
    check(f"PnP-range {fe.range_m:.1f} m inom 3 %", abs(fe.range_m - R)/R < 0.03)

    print(f"\n{'ALLA TESTER PASS' if not fails else f'{len(fails)} FAIL: '+', '.join(fails)}")
    return not fails


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
