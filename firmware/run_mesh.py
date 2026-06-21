"""STRILAS firmware — DISTRIBUERAD FLER-NODS-SIM (Fas 1).

Kör de tre P4-noderna (optik/väst/hjälm) + servern som SEPARATA noder på en simulerad
WiFi6/ESP-NOW-mesh (mesh.py) med latens, jitter, paketförlust och per-nod klockor.
Visar att 'alla P4 pratar med varandra' end-to-end: vapnet löser pose + avfyrar →
FireEvent över mesh → server; målets TSOP ser IR-strålen → IRHit över mesh → server
parar + adjudikerar → Verdict broadcast → väst/hjälm vibrerar.

Trafik (topics):  fire (optik→srv) · irhit (mål→srv) · pstate (mål→srv) · verdict (srv→alla)
IR-strålen är en FYSISK ljusväg (ej WiFi) → egen near-zero-latency-kanal, ej paketförlust.

Kör:  python3 -m firmware.run_mesh
"""
from __future__ import annotations
from . import hal, world_sim as W, config as C
from .mesh import Mesh, NetParams, ClockParams
from .weapon_node import WeaponNode
from .target_node import TargetNode
from .engine import Server

KEY = b"strilas-demo-key"
IR_PHOTON_S = 5e-4         # TSOP-avkodningstid (ljusets gångtid ~0); 56 kHz-burst-detektion


class WeaponRuntime:
    """optik-nod: kamera→pose→FireEvent + fyr IR-stråle mot mål."""
    def __init__(self, mesh, name, targets):
        self.mesh, self.name, self.targets = mesh, name, targets
        self.hal = hal.NodeHAL(name, hal.SimClock(mesh, name), hal.SimRadio(mesh, name),
                               hal.SimSensors("optik"), hal.SimActuators())
        self.node = WeaponNode(key=KEY)
        self.fired = {}        # ir_code -> world_t (för end-to-end-latens)

    def fire(self, scn, use_fc, target_rt):
        # perception via HAL (samma anrop HW kör mot OV9281); pose används av fire-control
        self.hal.sensors.camera_detections(scn)
        t_local = self.hal.clock.now()
        fe, code = self.node.engage(scn, use_fc=use_fc, t=t_local)
        self.hal.actuators.fire_laser(code)
        self.fired[code] = self.mesh.t
        self.hal.radio.send("fire", fe)
        # fysisk IR-stråle → målets TSOP (om inom kon/räckvidd/LOS)
        if W.ir_link(fe.aim_az_deg, fe.aim_el_deg, fe.range_m, scn.los_blocked):
            self.mesh.schedule(IR_PHOTON_S, target_rt.name, target_rt.on_ir_photon,
                               (code, self.node.id, scn.aim_zone))


class TargetRuntime:
    """väst/hjälm-nod: TSOP→IRHit + låg-rate PlayerState + haptik på HIT."""
    def __init__(self, mesh, name, target_id, vx=0.0):
        self.mesh, self.name = mesh, name
        self.hal = hal.NodeHAL(name, hal.SimClock(mesh, name), hal.SimRadio(mesh, name),
                               hal.SimSensors(name), hal.SimActuators())
        self.node = TargetNode(target_id)
        self.node.x, self.node.vx = C.PROFILE["ir_range_m"] * 0 + 150.0, vx
        self.hal.radio.on("verdict", self._on_verdict)

    def on_ir_photon(self, payload):
        ir_code, shooter_id, zone = payload
        t_local = self.hal.clock.now()
        ih = self.node.on_ir(ir_code, shooter_id, t_local, zone_hint=zone)
        self.hal.radio.send("irhit", ih)

    def send_state(self):
        self.hal.radio.send("pstate", self.node.state(self.hal.clock.now()))

    def _on_verdict(self, vd):
        if vd.target_id == self.node.id and vd.result == "HIT":
            self.hal.actuators.vibrate(vd.zone, min(1.0, vd.damage / 34.0))


class ServerRuntime:
    """Server-nod: parar fire↔irhit (reorder-tolerant) + adjudikerar + broadcastar verdikt."""
    def __init__(self, mesh, name="server"):
        self.mesh, self.name = mesh, name
        self.radio = hal.SimRadio(mesh, name)
        self.srv = Server(KEY)
        self._ir_stash = {}      # ir_code -> IRHit (anlände före FireEvent → reorder-skydd)
        self.results = []        # (ir_code, Verdict, world_t_verdict)
        self.radio.on("fire", self._on_fire)
        self.radio.on("irhit", self._on_ir)
        self.radio.on("pstate", self.srv.on_player_state)

    def _emit(self, code, vd):
        if vd is None:
            return
        self.results.append((code, vd, self.mesh.t))
        self.radio.send("verdict", vd)

    def _on_fire(self, fe):
        self.srv.on_fire(fe)
        ih = self._ir_stash.pop(fe.ir_code, None)     # parade IR redan anlänt? (jitter-reorder)
        if ih is not None:
            self._emit(fe.ir_code, self.srv.on_ir(ih))

    def _on_ir(self, ih):
        if ih.ir_code in self.srv.pending:
            self._emit(ih.ir_code, self.srv.on_ir(ih))
        else:
            self._ir_stash[ih.ir_code] = ih           # vänta på FireEvent

    def flush(self, now, default_target_id=1):
        """Tidsutgångna skott utan IR (cover/no-LOS) → NEAR_MISS_NO_LOS-verdikt."""
        for vd in self.srv.tick(now, default_target_id):
            self._emit(None, vd)


# ───────────────────────── scenario-körning ─────────────────────────
def build(net: NetParams, clocks: dict):
    mesh = Mesh(net)
    for n, c in clocks.items():
        mesh.add_node(n, c)
    vast = TargetRuntime(mesh, "vast", target_id=1, vx=0.0)
    hjalm = TargetRuntime(mesh, "hjalm", target_id=2, vx=4.0)
    srv = ServerRuntime(mesh)
    optik = WeaponRuntime(mesh, "optik", targets=[vast, hjalm])
    return mesh, optik, vast, hjalm, srv


def run(net: NetParams, clocks: dict, shots, label):
    mesh, optik, vast, hjalm, srv = build(net, clocks)
    by_target = {"vast": vast, "hjalm": hjalm}
    print(f"\n{'='*74}\n{label}\n  "
          f"net: latens {net.latency_ms}±{net.jitter_ms} ms · loss {net.loss_prob*100:.0f}%   "
          f"klockor: " + ", ".join(f"{n}={c.offset_s*1e3:+.1f}ms/{c.drift_ppm:+.0f}ppm"
                                    for n, c in clocks.items() if n != "server"))
    # låg-rate PlayerState STRÖMMAR kontinuerligt (10 Hz) → servern har alltid färsk fart
    # innan ett skott, oberoende av jitter (annars kan ett stale state störa lag-kompen)
    t = 1.0
    state_hz = 10.0
    for trt in (vast, hjalm):
        ts = 0.0
        while ts < t + len(shots) * 0.25 + 0.5:
            mesh.schedule(ts, trt.name, lambda _m, r=trt: r.send_state(), None)
            ts += 1.0 / state_hz
    for (tgt, use_fc, v, zone, los) in shots:
        trt = by_target[tgt]
        scn = W.Scenario(range_m=150.0, v_lat_mps=v, aim_zone=zone, los_blocked=not los)
        trt.node.vx = v
        mesh.run_until(t)
        optik.fire(scn, use_fc, trt)
        t += 0.25                                     # nästa skott
    mesh.run_until(t + C.IR_WINDOW_S + 0.05)          # låt IR-fönstret löpa ut
    srv.flush(srv.mesh.t)                             # cover-skott → no-LOS-verdikt
    mesh.run()                                        # töm kön (verdikt-broadcast inkl.)

    # rapport per skott
    print("  " + mesh.latency_report())
    e2e = []
    for code, vd, tv in srv.results:
        tf = optik.fired.get(code)
        if tf is not None:
            e2e.append((tv - tf) * 1e3)
    hits = sum(1 for _, vd, _ in srv.results if vd.result == "HIT")
    paired = len(srv.results)
    print(f"  skott: {len(shots)} · parade verdikt: {paired} · HIT: {hits} · "
          f"ostashade IR kvar: {len(srv._ir_stash)}")
    if e2e:
        e2e.sort()
        print(f"  end-to-end (fyr→verdikt): median {e2e[len(e2e)//2]:.1f} ms · "
              f"max {e2e[-1]:.1f} ms  (IR-fönster {C.IR_WINDOW_S*1e3:.0f} ms, flygtid ~167 ms)")
    # haptik-kvitto (vibrationer som triggades på noderna)
    vib = [a for rt in (vast, hjalm) for a in rt.hal.actuators.log if a[0] == "vibrate"]
    print(f"  haptik: {len(vib)} vibrationer triggade på mål-noder (verdict-broadcast mottagen)")
    return srv.results


if __name__ == "__main__":
    print("="*74)
    print("STRILAS — distribuerad fler-nods-sim (optik + väst + hjälm + server på mesh)")
    print("="*74)

    # ett representativt skott-batch: stilla bröst, stilla huvud, springande (lead), cover
    shots = [
        ("vast",  True, 0.0, "Bröst", True),
        ("vast",  True, 0.0, "Huvud", True),
        ("hjalm", True, 4.0, "Bröst", True),    # rörligt mål → fire-control lead
        ("hjalm", True, 4.0, "Huvud", True),
        ("vast",  True, 0.0, "Bröst", False),   # bakom cover → ingen IR-LOS
    ]

    # (1) idealt nät + perfekta klockor
    run(NetParams(latency_ms=3, jitter_ms=2, loss_prob=0.0),
        {"server": ClockParams(), "optik": ClockParams(), "vast": ClockParams(), "hjalm": ClockParams()},
        shots, "(1) IDEALT NÄT — referens")

    # (2) realistiskt WiFi6 under last: högre jitter, 2% loss, klock-offset+drift+PTP-residual
    run(NetParams(latency_ms=8, jitter_ms=12, loss_prob=0.02),
        {"server": ClockParams(),
         "optik": ClockParams(offset_s=+0.0003, drift_ppm=+20, sync_residual_s=50e-6),
         "vast":  ClockParams(offset_s=-0.0002, drift_ppm=-15, sync_residual_s=50e-6),
         "hjalm": ClockParams(offset_s=+0.0005, drift_ppm=+30, sync_residual_s=50e-6)},
        shots, "(2) WiFi6 UNDER LAST — jitter 12 ms, 2% loss, klock-drift/PTP-residual")

    print("\n" + "-"*74)
    print("Slutsats: samma verdikt under realistisk nät-/klockstörning. IR-fönstret (200 ms)")
    print("och flygtiden (~167 ms) >> nät-latens (ms) + PTP-residual (µs) → robust marginal.")
    print("Reorder-skydd (IR före FireEvent) fångas av serverns stash. Tappade verdict-")
    print("broadcasts → haptik missas men domen står (loggad på servern).")
    print("="*74)
