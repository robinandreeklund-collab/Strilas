"""STRILAS firmware-skelett — VAPEN-NOD (ESP32-P4-logik, HW-abstraherad).
Samma kod sim↔HW: process_detections() tar detektor-utdata (sim nu / ESP-kamera sen)."""
from . import cv_pose, config as C
from .protocol import FireEvent


class WeaponNode:
    def __init__(self, shooter_id=7, profile="M4 / 5.56"):
        self.id = shooter_id
        self.profile = profile
        self.pose = None
        self.seq = 0
        self._ir_code = 0x1A2B

    def process_detections(self, detections):
        """Kamera/blob-detektor → relativ pose (az,el,range). Anropas per bildruta."""
        self.pose = cv_pose.estimate_pose(detections)
        return self.pose

    def next_ir_code(self):
        self._ir_code = (self._ir_code * 1103515245 + 12345) & 0xFFFF   # rullande
        return self._ir_code

    def fire(self, t):
        """Trigger → FireEvent från senaste pose. None om inget lås."""
        if self.pose is None:
            return None, None
        self.seq += 1
        code = self.next_ir_code()
        fe = FireEvent(
            shooter_id=self.id, t_fire=t, seq=self.seq,
            aim_az_deg=self.pose["az_deg"], aim_el_deg=self.pose["el_deg"],
            range_m=self.pose["range_m"], weapon_profile=self.profile,
            ir_code=code, n_blobs=self.pose["n_blobs"])
        return fe, code
