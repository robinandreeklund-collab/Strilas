"""STRILAS firmware-skelett — anti-fusk (tvärgående).
Rullande IR-kod + nonce + HMAC + replay/seq-koll. På HW: HMAC med per-spelare-nyckel
i säkert element; här en enkel men strukturellt korrekt implementation.
"""
import hmac as _hmac
import hashlib


class RollingCode:
    """Deterministisk rullande 16-bit IR-kod + nonce (LCG). Delas vapen↔server."""
    def __init__(self, seed=0x1A2B):
        self.state = seed & 0xFFFFFFFF

    def next(self):
        self.state = (self.state * 1103515245 + 12345) & 0xFFFFFFFF
        return (self.state >> 8) & 0xFFFF        # 16-bit kod


def sign(key: bytes, payload: str) -> str:
    return _hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()[:16]


def verify(key: bytes, payload: str, mac: str) -> bool:
    return _hmac.compare_digest(sign(key, payload), mac)


class ReplayGuard:
    """Avvisar omspelade/för-gamla sekvensnummer per skytt."""
    def __init__(self):
        self._last = {}

    def ok(self, shooter_id, seq):
        last = self._last.get(shooter_id, -1)
        if seq <= last:
            return False
        self._last[shooter_id] = seq
        return True
