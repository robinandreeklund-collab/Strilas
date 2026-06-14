"""STRILAS firmware-skelett — automatiska tester (utan hårdvara).
Kör:  python -m firmware.test_chain
Täcker: perception, fire-control, drop, lead/rörligt mål, IR-grind, anti-fusk, Monte Carlo.
"""
import numpy as np
from . import world_sim as W, cv_pose, config as C
from .weapon_node import WeaponNode
from .target_node import TargetNode
from .adjudicator import adjudicate
from .anticheat import ReplayGuard
from .engine import Server
from .protocol import PlayerState

KEY = b"strilas-demo-key"
R = 150.0


def _shot(use_fc, v=0.0, zone="Bröst", sigma=0.0, los=True):
    w, t = WeaponNode(key=KEY), TargetNode()
    scn = W.Scenario(range_m=R, v_lat_mps=v, aim_zone=zone, human_sigma_deg=sigma,
                     los_blocked=not los)
    fe, code = w.engage(scn, use_fc=use_fc, t=1.0)
    seen = W.ir_link(fe.aim_az_deg, fe.aim_el_deg, fe.range_m, scn.los_blocked)
    ih = t.on_ir(code, w.id, 1.0005, zone) if seen else None
    return adjudicate(fe, ih, target_v_true=v, key=KEY, replay=ReplayGuard())


def run():
    fails = []
    def chk(name, cond):
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
        if not cond: fails.append(name)

    # 1. perception: bild → detektion hittar 5 LED
    blobs = cv_pose.detect_blobs(W.render_frame(W.project_constellation(0, 0, R)))
    chk("perception: detect_blobs hittar 5 konstellations-LED", len(blobs) == 5)
    pose = cv_pose.estimate_pose(blobs)
    chk(f"perception: PnP-range {pose['range_m']:.1f} m inom 3 %", abs(pose['range_m']-R)/R < 0.03)

    # 2. fire-control: stationärt → HIT rätt zon
    chk("FC stationärt Bröst → HIT Bröst", (v := _shot(True, 0, "Bröst")).result == "HIT" and v.zone == "Bröst")
    chk("FC stationärt Huvud → HIT Huvud", (v := _shot(True, 0, "Huvud")).result == "HIT" and v.zone == "Huvud")

    # 3. drop: naivt utan holdover landar LÅGT (men ändå på kroppen vid σ=0)
    vn = _shot(False, 0, "Bröst", sigma=0.0)
    chk(f"naivt drop: landar {vn.miss_vertical_cm:.0f} cm (lägre än FC)", vn.miss_vertical_cm < -8)

    # 4. lead/rörligt mål 6 m/s: naivt MISS, FC HIT
    chk("rörligt 6 m/s naivt → MISS (ingen lead)", _shot(False, 6.0, "Bröst", 0.0).result == "MISS")
    chk("rörligt 6 m/s FC → HIT (lead+holdover)", _shot(True, 6.0, "Bröst", 0.0).result == "HIT")

    # 5. IR-grind: cover → NEAR_MISS_NO_LOS
    chk("cover (ingen IR-LOS) → NEAR_MISS_NO_LOS", _shot(True, 0, "Bröst", los=False).result == "NEAR_MISS_NO_LOS")

    # 6. anti-fusk: manipulerad HMAC + replay
    w, t = WeaponNode(key=KEY), TargetNode()
    fe, code = w.engage(W.Scenario(), use_fc=True, t=1.0)
    fe.aim_az_deg += 5.0        # manipulera efter signering
    chk("anti-fusk: manipulerad HMAC → REJECTED",
        adjudicate(fe, t.on_ir(code, w.id, 1.0005), 0.0, KEY, ReplayGuard()).result == "REJECTED_REPLAY")
    rg = ReplayGuard()
    fe2, code2 = w.engage(W.Scenario(), use_fc=True, t=2.0)
    ih2 = t.on_ir(code2, w.id, 2.0005)
    adjudicate(fe2, ih2, 0.0, KEY, rg)            # första OK
    chk("anti-fusk: replay samma seq → REJECTED",
        adjudicate(fe2, ih2, 0.0, KEY, rg).result == "REJECTED_REPLAY")

    # 7. server-motor: pairing + tick
    srv = Server(KEY)
    srv.on_player_state(PlayerState(1, 0, 150, 0, 0, vx=0))
    w3 = WeaponNode(key=KEY)
    fe3, code3 = w3.engage(W.Scenario(aim_zone="Bröst"), use_fc=True, t=10.0)
    srv.on_fire(fe3); v3 = srv.on_ir(t.on_ir(code3, w3.id, 10.0005, "Bröst"))
    chk("server pairing FireEvent↔IRHit → HIT", v3 and v3.result == "HIT")
    srv.on_fire(w3.engage(W.Scenario(), use_fc=True, t=20.0)[0])
    chk("server tick timeout (ingen IR) → NEAR_MISS_NO_LOS",
        srv.tick(21.0) and srv.verdicts[-1].result == "NEAR_MISS_NO_LOS")

    # 8. Monte Carlo: FC ≫ naivt på rörligt mål
    def mc(use_fc, n=1500, v=4.0, sigma=0.3):
        w, t = WeaponNode(key=KEY), TargetNode(); hit = 0
        for i in range(n):
            scn = W.Scenario(range_m=R, v_lat_mps=v, human_sigma_deg=sigma)
            fe, code = w.engage(scn, use_fc=use_fc, t=1.0+i)
            seen = W.ir_link(fe.aim_az_deg, fe.aim_el_deg, fe.range_m, False)
            ih = t.on_ir(code, w.id, fe.t_fire+5e-4) if seen else None
            if adjudicate(fe, ih, v, KEY, ReplayGuard()).result == "HIT": hit += 1
        return hit/n
    fc, na = mc(True), mc(False)
    print(f"     MC rörligt mål 4 m/s: FC {fc*100:.0f}%  vs naivt {na*100:.0f}%")
    chk("MC: fire-control ≥ 95 %", fc >= 0.95)
    chk("MC: fire-control ≫ naivt", fc > na + 0.3)

    print(f"\n{'ALLA TESTER PASS' if not fails else f'{len(fails)} FAIL: '+', '.join(fails)}")
    return not fails


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
