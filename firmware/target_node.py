"""STRILAS firmware-skelett — MÅL-NOD (väst/hjälm, ESP32-C5-logik).
TSOP avkodar strålen → IRHit. HW-abstraherad: on_ir() matas av TSOP-capture (sim/HW)."""
from .protocol import IRHit


class TargetNode:
    def __init__(self, target_id=1):
        self.id = target_id
        self.seq = 0

    def on_ir(self, ir_code, shooter_id, t, rssi=-40.0):
        """TSOP avkodade en kodad stråle → bygg IRHit."""
        self.seq += 1
        return IRHit(target_id=self.id, t_rx=t, ir_code=ir_code,
                     shooter_id_decoded=shooter_id, rssi=rssi, seq=self.seq)
