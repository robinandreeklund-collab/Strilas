"""STRILAS firmware-skelett — SERVER- motor (tick-loop, pairing, lag-komp).
Buffrar FireEvents, parar mot inkommande IRHit per ir_code, hämtar målets sanna fart
ur PlayerState (lag-komp), kör adjudicator. Timeout utan IR → cover/no-LOS-väg.
"""
from . import config as C
from .adjudicator import adjudicate
from .anticheat import ReplayGuard
from .protocol import PlayerState


class Server:
    def __init__(self, key=b"strilas-demo-key"):
        self.key = key
        self.replay = ReplayGuard()
        self.pending = {}            # ir_code -> (FireEvent, t_fire)
        self.players = {}            # id -> PlayerState
        self.verdicts = []

    def on_player_state(self, ps: PlayerState):
        self.players[ps.player_id] = ps

    def on_fire(self, fe):
        self.pending[fe.ir_code] = (fe, fe.t_fire)

    def _vtrue(self, target_id):
        ps = self.players.get(target_id)
        return ps.vx if ps else 0.0

    def on_ir(self, ih):
        item = self.pending.pop(ih.ir_code, None)
        if item is None:
            return None
        fe, _ = item
        vd = adjudicate(fe, ih, self._vtrue(ih.target_id), self.key, self.replay)
        self.verdicts.append(vd)
        return vd

    def tick(self, now, default_target_id=1):
        """Avgör skott som inte fått IR inom fönstret (cover/no-LOS)."""
        out, done = [], []
        for code, (fe, t) in self.pending.items():
            if now - t > C.IR_WINDOW_S:
                vd = adjudicate(fe, None, self._vtrue(default_target_id), self.key, self.replay)
                self.verdicts.append(vd); out.append(vd); done.append(code)
        for c in done:
            self.pending.pop(c)
        return out
