"""STRILAS firmware-skelett — END-TO-END DEMO (utan hårdvara).
Hela kedjan: fejk-kamera → CV → fire-control → FireEvent → IR → server → verdikt.
Kör:  python -m firmware.run_demo
"""
import numpy as np
from . import world_sim as W, cv_pose, config as C
from .weapon_node import WeaponNode
from .target_node import TargetNode
from .engine import Server
from .protocol import PlayerState

KEY = b"strilas-demo-key"
R = 150.0


def engage(label, use_fc, v=0.0, zone="Bröst", sigma=0.3, los=True):
    srv = Server(KEY)
    srv.on_player_state(PlayerState(1, 0, R, 0, 0, vx=v))
    w, tg = WeaponNode(key=KEY), TargetNode(1)
    scn = W.Scenario(range_m=R, v_lat_mps=v, aim_zone=zone,
                     human_sigma_deg=sigma, los_blocked=not los)
    fe, code = w.engage(scn, use_fc=use_fc, t=1.0)
    srv.on_fire(fe)
    seen = W.ir_link(fe.aim_az_deg, fe.aim_el_deg, fe.range_m, scn.los_blocked)
    vd = srv.on_ir(tg.on_ir(code, w.id, 1.0005, zone)) if seen else (srv.tick(2.0) or [None])[0]
    mode = "FIRE-CONTROL" if use_fc else "naivt"
    print(f"\n■ {label}  [{mode}]")
    print(f"   FireEvent: aim az{fe.aim_az_deg:+.3f}° el{fe.aim_el_deg:+.3f}° range {fe.range_m:.0f} m "
          f"v_mål {fe.target_vx_mps:.1f} m/s  IR-LOS {seen}")
    print(f"   VERDIKT: {vd.result}" + (f' · {vd.zone} · skada {vd.damage}' if vd.zone else '')
          + f"   miss ({vd.miss_lateral_cm:+.0f},{vd.miss_vertical_cm:+.0f}) cm")


def mc(use_fc, v, sigma=0.3, n=3000):
    from .adjudicator import adjudicate
    from .anticheat import ReplayGuard
    w, tg = WeaponNode(key=KEY), TargetNode(); hit = 0
    for i in range(n):
        scn = W.Scenario(range_m=R, v_lat_mps=v, human_sigma_deg=sigma)
        fe, code = w.engage(scn, use_fc=use_fc, t=1.0+i)
        seen = W.ir_link(fe.aim_az_deg, fe.aim_el_deg, fe.range_m, False)
        ih = tg.on_ir(code, w.id, fe.t_fire+5e-4) if seen else None
        if adjudicate(fe, ih, v, KEY, ReplayGuard()).result == "HIT": hit += 1
    return hit/n


if __name__ == "__main__":
    print("="*70); print("STRILAS firmware-skelett — end-to-end @150 m (ingen hårdvara)"); print("="*70)

    blobs = cv_pose.detect_blobs(W.render_frame(W.project_constellation(0, 0, R)))
    pose = cv_pose.estimate_pose(blobs)
    print(f"\n● PERCEPTION (bild→detect_blobs→pose): {len(blobs)} LED, "
          f"range {pose['range_m']:.1f} m (sant 150)")

    engage("Stationärt mål, sikte bröst", use_fc=False, v=0, sigma=0.0)   # drop → lågt
    engage("Stationärt mål, sikte bröst", use_fc=True,  v=0)
    engage("Stationärt mål, sikte HUVUD", use_fc=True,  v=0, zone="Huvud")
    engage("Mål springer 6 m/s",          use_fc=False, v=6.0, sigma=0.0) # ingen lead → MISS
    engage("Mål springer 6 m/s",          use_fc=True,  v=6.0)
    engage("Stationärt bakom COVER",      use_fc=True,  v=0, los=False)

    print("\n"+"-"*70); print("Monte Carlo träff-% (skytt-σ=0.3°)")
    for v in (0.0, 4.0):
        print(f"  mål {v:.0f} m/s:   naivt {mc(False,v)*100:5.1f}%   |   FIRE-CONTROL {mc(True,v)*100:5.1f}%")
    print("\n  → fire-control tar träff-% från människo-begränsad → ~100 % (kameran")
    print("    mäter felet exakt + räknar lead/holdover). Kör 'python -m firmware.benchmark'")
    print("    för server-prestanda (~57k adj/s, ×120 marginal mot full-auto 32 spelare).")
    print("="*70)
