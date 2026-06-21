"""STRILAS firmware — tester för distribuerad mesh-sim (Fas 1).
Verifierar att den distribuerade vägen (optik/väst/hjälm/server på mesh) ger samma
domar som in-process-kedjan, samt robusthet mot reorder, paketförlust och klockfel.
Kör:  python3 -m firmware.test_mesh
"""
from . import world_sim as W, config as C
from .mesh import Mesh, NetParams, ClockParams
from .run_mesh import WeaponRuntime, TargetRuntime, ServerRuntime, build

PASS = 0; FAIL = 0
def ok(name, cond):
    global PASS, FAIL
    print(f"  {'✅' if cond else '❌'} {name}")
    PASS += cond; FAIL += (not cond)


def _verdicts(net, clocks, shots):
    mesh, optik, vast, hjalm, srv = build(net, clocks)
    by = {"vast": vast, "hjalm": hjalm}
    t = 1.0
    for trt in (vast, hjalm):
        ts = 0.0
        while ts < t + len(shots) * 0.25 + 0.5:
            mesh.schedule(ts, trt.name, lambda _m, r=trt: r.send_state(), None); ts += 0.1
    for (tgt, use_fc, v, zone, los) in shots:
        trt = by[tgt]; trt.node.vx = v
        scn = W.Scenario(range_m=150.0, v_lat_mps=v, aim_zone=zone, los_blocked=not los)
        mesh.run_until(t); optik.fire(scn, use_fc, trt); t += 0.25
    mesh.run_until(t + C.IR_WINDOW_S + 0.05); srv.flush(mesh.t); mesh.run()
    return srv, mesh


CLEAN = {"server": ClockParams(), "optik": ClockParams(),
         "vast": ClockParams(), "hjalm": ClockParams()}


def run():
    print("STRILAS — distribuerad mesh-sim, tester")

    shots = [("vast", True, 0.0, "Bröst", True),
             ("hjalm", True, 4.0, "Huvud", True),
             ("vast", True, 0.0, "Bröst", False)]   # sista = cover

    # 1) basväg: stillastående bröst-skott → HIT över mesh
    srv, _ = _verdicts(NetParams(loss_prob=0.0), CLEAN, shots)
    res = [vd.result for _, vd, _ in srv.results]
    ok("stilla bröst-skott → HIT levereras via mesh", "HIT" in res)

    # 2) cover-skott → NEAR_MISS_NO_LOS via server-tick (timeout)
    ok("cover/no-LOS → NEAR_MISS_NO_LOS efter fönster", "NEAR_MISS_NO_LOS" in res)

    # 3) alla skott paras (inget IR-tapp i idealt nät)
    ok("alla 3 skott får ett verdikt", len(srv.results) == 3)

    # 4) reorder-tolerans: IRHit anländer FÖRE FireEvent → stashas + paras ändå
    mesh = Mesh(); [mesh.add_node(n) for n in ("server", "optik", "vast")]
    s = ServerRuntime(mesh); tgt = TargetRuntime(mesh, "vast", 1)
    w = WeaponRuntime(mesh, "optik", [tgt])
    scn = W.Scenario(range_m=150.0, aim_zone="Bröst")
    fe, code = w.node.engage(scn, use_fc=True, t=1.0)
    ih = tgt.node.on_ir(code, w.node.id, 1.0005, "Bröst")
    s._on_ir(ih)                                   # IR först (fel ordning)
    stashed = code in s._ir_stash
    s._on_fire(fe)                                 # FireEvent sen → ska para ihop
    ok("IRHit före FireEvent stashas", stashed)
    ok("reorder paras när FireEvent anländer", len(s.results) == 1 and s.results[0][1].result == "HIT")

    # 5) determinism: samma seed → identiska domar
    a, _ = _verdicts(NetParams(latency_ms=8, jitter_ms=12, loss_prob=0.05, seed=3), CLEAN, shots)
    b, _ = _verdicts(NetParams(latency_ms=8, jitter_ms=12, loss_prob=0.05, seed=3), CLEAN, shots)
    ok("seedat nät är deterministiskt",
       [v.result for _, v, _ in a.results] == [v.result for _, v, _ in b.results])

    # 6) robusthet: domarna är samma under jitter+loss+klockdrift som i idealt nät
    base = [v.result for _, v, _ in _verdicts(NetParams(loss_prob=0.0), CLEAN, shots)[0].results]
    degr = [v.result for _, v, _ in _verdicts(
        NetParams(latency_ms=8, jitter_ms=12, loss_prob=0.02, seed=1),
        {"server": ClockParams(),
         "optik": ClockParams(offset_s=3e-4, drift_ppm=20, sync_residual_s=50e-6),
         "vast": ClockParams(offset_s=-2e-4, drift_ppm=-15, sync_residual_s=50e-6),
         "hjalm": ClockParams(offset_s=5e-4, drift_ppm=30, sync_residual_s=50e-6)},
        shots)[0].results]
    ok("samma domar under WiFi6-störning som idealt nät", sorted(base) == sorted(degr))

    print(f"\n  {PASS} PASS, {FAIL} FAIL")
    return FAIL == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
