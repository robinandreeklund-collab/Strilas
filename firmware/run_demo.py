"""STRILAS firmware-skelett — END-TO-END DEMO (utan hårdvara).
Kör hela kedjan: fejk-kamera → CV → FireEvent → IR → adjudikator → verdikt.
Kör:  python -m firmware.run_demo
"""
import numpy as np
from . import world_sim as W, cv_pose, config as C
from .weapon_node import WeaponNode
from .target_node import TargetNode
from .adjudicator import adjudicate

RANGE = 150.0


def engage(label, az, el, rng=RANGE, los_blocked=False, use_image=False, sigma_px=0.1):
    weapon, target = WeaponNode(shooter_id=7), TargetNode(target_id=1)
    if use_image:                                   # BEVISA bild→pose-vägen
        cents = W.project_constellation(az, el, rng)
        blobs = cv_pose.detect_blobs(W.render_frame(cents))
    else:                                           # snabb centroid-väg
        blobs = W.noisy_detections(az, el, rng, sigma_px)
    weapon.process_detections(blobs)
    t = 1.000
    fe, code = weapon.fire(t)
    seen = W.ir_link(az, el, rng, los_blocked)
    irhit = target.on_ir(code, fe.shooter_id, t + 5e-4) if seen else None
    v = adjudicate(fe, irhit, target_id=1)
    print(f"\n■ {label}")
    print(f"   CV: {len(blobs)} blobbar → az {fe.aim_az_deg:+.4f}° el {fe.aim_el_deg:+.4f}° "
          f"range {fe.range_m:.1f} m (sant {rng:.0f})   ir_code 0x{code:04X}  IR-LOS {seen}")
    print(f"   VERDIKT: {v.result}" + (f' · {v.zone} · skada {v.damage}' if v.zone else '')
          + f"   (miss {v.miss_lateral_cm:+.1f},{v.miss_vertical_cm:+.1f} cm)")
    print(f"   skäl: {v.reason}")
    return v


if __name__ == "__main__":
    print("="*70); print("STRILAS firmware-skelett — end-to-end @150 m (ingen hårdvara)"); print("="*70)
    # vinklar för att LANDA på en zon: skott landar (-R·tanaz, -R·tanel) rel centroid
    el_head = -np.degrees(np.arctan(0.38/RANGE))     # → landar +0.38 vert = huvud
    el_chest = 0.0                                    # → landar ~0 = bröst
    az_miss = np.degrees(np.arctan(0.55/RANGE))       # → landar 0.55 m åt sidan = bom

    engage("BILD-VÄG (render→detect_blobs→pose), centrerat", 0, el_chest, use_image=True)
    engage("Centrerat sikte (brus 0.1px)", 0, el_chest)
    engage("Sikte mot HUVUD", 0, el_head)
    engage("Bom 0.55 m i sidled", az_miss, el_chest)
    engage("Centrerat men COVER (ingen IR-LOS)", 0, el_chest, los_blocked=True)

    # Monte Carlo träff% vid skytte-skicklighet σ=0.3° (människa + system)
    print("\n"+"-"*70); print("Monte Carlo: 2000 skott, skicklighet σ=0.3°, mål 0.5 m bröst-radie")
    rng = np.random.default_rng(3); hit = 0; N = 2000
    w, tg = WeaponNode(), TargetNode()
    for _ in range(N):
        az, el = rng.normal(0, 0.3), rng.normal(0, 0.3)
        w.process_detections(W.noisy_detections(az, el, RANGE))
        fe, code = w.fire(1.0)
        seen = W.ir_link(az, el, RANGE)
        v = adjudicate(fe, tg.on_ir(code, 7, 1.0005) if seen else None)
        if v.result == "HIT":
            hit += 1
    print(f"   träff-% = {hit/N*100:.1f}%  (begränsas av MÄNSKLIG sikt-σ, ej systemet)")
    print("="*70)
