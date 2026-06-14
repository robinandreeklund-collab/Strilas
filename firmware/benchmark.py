"""STRILAS firmware-skelett — prestanda-benchmark (server-adjudikation).
Mäter adjudikationer/sekund + latens. Mål: klara full-auto för 16–32 spelare
(~500 skott/s aggregerat) med stor marginal på en laptop.
Kör:  python -m firmware.benchmark
"""
import time
from .weapon_node import WeaponNode
from .target_node import TargetNode
from .adjudicator import adjudicate
from .anticheat import ReplayGuard
from .world_sim import Scenario

KEY = b"strilas-demo-key"


def run(n=20000):
    w, t = WeaponNode(key=KEY), TargetNode()
    scn = Scenario(range_m=150, v_lat_mps=4.0)
    # förbered N signerade FireEvents (realistiska)
    fires = []
    for i in range(n):
        fe, code = w.engage(scn, use_fc=True, t=1.0 + i*1e-3)
        fires.append((fe, t.on_ir(code, w.id, fe.t_fire + 5e-4)))

    rg = ReplayGuard()
    t0 = time.perf_counter()
    for fe, ih in fires:
        adjudicate(fe, ih, target_v_true=4.0, key=KEY, replay=rg)
    dt = time.perf_counter() - t0

    rate = n/dt
    print(f"Adjudikationer: {n} på {dt*1e3:.0f} ms")
    print(f"  → {rate:,.0f} adj/s   ({dt/n*1e6:.1f} µs/skott)")
    load = 32*15      # 32 spelare × 15 skott/s full-auto
    print(f"  full-auto-last 32 spelare ≈ {load} skott/s → marginal ×{rate/load:,.0f}  "
          f"{'✅' if rate > load*10 else '⚠️'}")
    return rate


if __name__ == "__main__":
    run()
