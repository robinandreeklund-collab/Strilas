"""STRILAS firmware — simulerad mesh + klock-modell (Fas 1).

Diskret-händelse-nät som modellerar WiFi6/ESP-NOW mellan P4-noderna + servern:
latens, jitter, paketförlust och per-nod klocka (offset + frekvensdrift + PTP-residual).
Allt seedat → reproducerbart. Radio-API:t (hal.SimRadio) ovanför detta lager är
byte-identiskt mot ESP-NOW/MQTT på riktig hårdvara — bara leverans-mekanismen skiljer.

Tidsmodell: världsklockan T driver händelsekön. Varje nod n har
    lokal_tid(n) = T·(1 + drift_ppm·1e-6) + offset_s
så noder tidsstämplar meddelanden i SIN klocka; servern jämför dem. PTP-synk
modelleras genom att hålla offset/drift små + en sync_residual som visar hur
robust 0,2 s-fönstret och lag-kompen är mot realistiskt klockfel.
"""
from __future__ import annotations
import heapq, random
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class NetParams:
    latency_ms: float = 3.0      # WiFi6/ESP-NOW median en väg (LAN)
    jitter_ms: float = 2.0       # likformig ± kring medianen
    loss_prob: float = 0.0       # paketförlust per hopp [0..1]
    seed: int = 1


@dataclass
class ClockParams:
    offset_s: float = 0.0        # konstant bias mot världsklockan
    drift_ppm: float = 0.0       # frekvensdrift (kristall)
    sync_residual_s: float = 0.0 # PTP-residual (slumpas ± per tidsstämpel)


@dataclass
class _Stats:
    sent: int = 0
    delivered: int = 0
    dropped: int = 0
    latencies_ms: list = field(default_factory=list)


class Mesh:
    """Diskret-händelse-mesh. Registrera noder, prenumerera på topics, send() schemalägger
    leverans med per-länk-fördröjning/förlust. run()/run_until() processar i världstid."""

    def __init__(self, net: NetParams = None):
        self.net = net or NetParams()
        self.t = 0.0                                   # världstid (s)
        self._q = []                                   # heap: (deliver_t, seq, node, fn, msg)
        self._seq = 0
        self._subs = defaultdict(list)                 # topic -> [(node, fn)]
        self._clocks = {}                              # node -> ClockParams
        self._rng = random.Random(self.net.seed)
        self.stats = _Stats()

    # ---- registrering ----
    def add_node(self, name, clock: ClockParams = None):
        self._clocks[name] = clock or ClockParams()

    def subscribe(self, topic, node, fn):
        self._subs[topic].append((node, fn))

    # ---- klock-modell ----
    def local_time(self, node):
        c = self._clocks.get(node, ClockParams())
        return self.t * (1.0 + c.drift_ppm * 1e-6) + c.offset_s

    def stamp(self, node):
        """Tidsstämpel som noden skulle skriva (lokal klocka + PTP-residual)."""
        c = self._clocks.get(node, ClockParams())
        jit = self._rng.uniform(-c.sync_residual_s, c.sync_residual_s) if c.sync_residual_s else 0.0
        return self.local_time(node) + jit

    # ---- händelse-schemaläggning ----
    def schedule(self, dt, node, fn, msg, counted=False):
        """counted=True → räknas som ett WiFi-paket i statistiken (ej fysiska IR-fotoner)."""
        self._seq += 1
        heapq.heappush(self._q, (self.t + dt, self._seq, node, fn, msg, counted))

    def send(self, src, topic, msg):
        """Publicera till alla prenumeranter med per-länk latens/jitter/förlust."""
        for node, fn in self._subs.get(topic, []):
            self.stats.sent += 1
            if self._rng.random() < self.net.loss_prob:
                self.stats.dropped += 1
                continue
            delay = max(0.0, (self.net.latency_ms
                              + self._rng.uniform(-self.net.jitter_ms, self.net.jitter_ms)) / 1e3)
            self.stats.latencies_ms.append(delay * 1e3)
            self.schedule(delay, node, fn, msg, counted=True)

    # ---- körning ----
    def _fire(self, ev):
        self.t, _, node, fn, msg, counted = ev
        if counted:
            self.stats.delivered += 1
        fn(msg)

    def run_until(self, t_world):
        while self._q and self._q[0][0] <= t_world:
            self._fire(heapq.heappop(self._q))
        self.t = max(self.t, t_world)

    def run(self):
        while self._q:
            self._fire(heapq.heappop(self._q))

    # ---- rapport ----
    def latency_report(self):
        L = sorted(self.stats.latencies_ms)
        if not L:
            return "inga paket"
        n = len(L)
        p = lambda q: L[min(n - 1, int(q * n))]
        loss = self.stats.dropped / max(1, self.stats.sent) * 100
        return (f"paket: {self.stats.sent} sänt · {self.stats.delivered} levererat · "
                f"{self.stats.dropped} tappat ({loss:.1f}%)  |  "
                f"latens median {p(0.5):.1f} ms · p95 {p(0.95):.1f} ms · max {L[-1]:.1f} ms")
