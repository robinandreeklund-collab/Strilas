"""STRILAS firmware — HAL (hardware abstraction layer), Fas 0.

Formaliserar gränsen mellan NOD-LOGIK (identisk sim↔HW) och I/O. All logik ovanför
HAL:en (cv_pose, fire_control, weapon_node, adjudicator, engine) är oförändrad
sim↔hårdvara; bara HAL-implementationen byts. Tre roller (optik/väst/hjälm) får var
sin `NodeHAL` injicerad: en `SimHAL` (wrappar world_sim + mesh) körs nu, en
`HardwareHAL` (stub) pekar på var ESP-IDF-drivrutinerna kopplas in i Fas 3.

Gränssnitt:
  Clock      now() → nodens lokala tid (sim-tid / PTP-synkad monoton på HW)
  Sensors    camera_detections(), imu(), ir_decode()   (rollberoende; saknas → None)
  Radio      send(topic, msg), on(topic, fn)            (mesh nu → ESP-NOW/MQTT på HW)
  Actuators  fire_laser(), recoil(), vibrate(), set_constellation()
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from . import world_sim as W, cv_pose, config as C


# ───────────────────────── abstrakta gränssnitt ─────────────────────────
class Clock(ABC):
    @abstractmethod
    def now(self) -> float: ...


class Sensors(ABC):
    """Rollberoende. Metod som noden saknar HW för returnerar None."""
    def camera_detections(self, scn=None): return None    # optik: blob-lista (px)
    def imu(self): return None                             # dict(attityd/rate)
    def ir_decode(self): return None                       # (ir_code, shooter_id, zone) el. None


class Radio(ABC):
    @abstractmethod
    def send(self, topic: str, msg): ...
    @abstractmethod
    def on(self, topic: str, fn): ...


class Actuators(ABC):
    def fire_laser(self, ir_code: int): ...
    def recoil(self, profile: str): ...
    def vibrate(self, zone: str, intensity: float): ...
    def set_constellation(self, current_a: float): ...


class NodeHAL:
    """Buntar ihop I/O som injiceras i en nod."""
    def __init__(self, name, clock: Clock, radio: Radio,
                 sensors: Sensors = None, actuators: Actuators = None):
        self.name = name
        self.clock = clock
        self.radio = radio
        self.sensors = sensors or Sensors()
        self.actuators = actuators or _NullActuators()


# ───────────────────────── SIM-implementation ─────────────────────────
class SimClock(Clock):
    """Nodens lokala klocka i mesh-sim: världstid via mesh + nodens offset/drift."""
    def __init__(self, mesh, node_name):
        self._mesh, self._n = mesh, node_name
    def now(self) -> float:
        return self._mesh.local_time(self._n)


class SimSensors(Sensors):
    """Fejk-sensorer från world_sim. Scenariot bestämmer vad noden 'ser'."""
    def __init__(self, role, scn=None):
        self.role = role            # "optik" | "vast" | "hjalm"
        self.scn = scn
        self._ir_inbox = []         # (ir_code, shooter_id, zone) som TSOP avkodat

    def camera_detections(self, scn=None):
        if self.role != "optik":
            return None
        s = scn or self.scn
        cents = W.project_constellation(0.0, 0.0, s.range_m)
        return cv_pose.detect_blobs(W.render_frame(cents))

    def imu(self):
        # platshållare: world_sim modellerar IMU-residualen i CV_RESIDUAL_DEG.
        return dict(roll=0.0, pitch=0.0, yaw=0.0, gyro_dps=(0.0, 0.0, 0.0))

    def push_ir(self, ir_code, shooter_id, zone):
        self._ir_inbox.append((ir_code, shooter_id, zone))

    def ir_decode(self):
        return self._ir_inbox.pop(0) if self._ir_inbox else None


class SimRadio(Radio):
    """Radio bunden till mesh:en — send() lämnar till nät-modellen (latens/loss)."""
    def __init__(self, mesh, node_name):
        self._mesh, self._n = mesh, node_name
    def send(self, topic, msg):
        self._mesh.send(self._n, topic, msg)
    def on(self, topic, fn):
        self._mesh.subscribe(topic, self._n, fn)


class SimActuators(Actuators):
    """Loggar ställdons-anrop (för verifiering/visualisering i sim)."""
    def __init__(self):
        self.log = []
    def fire_laser(self, ir_code):           self.log.append(("laser", ir_code))
    def recoil(self, profile):               self.log.append(("recoil", profile))
    def vibrate(self, zone, intensity):      self.log.append(("vibrate", zone, intensity))
    def set_constellation(self, current_a):  self.log.append(("led", current_a))


class _NullActuators(Actuators):
    pass


# ───────────────────────── HÅRDVARU-stub (Fas 3) ─────────────────────────
_HW = "HardwareHAL: kopplas in i Fas 3 (ESP-IDF). "

class HardwareSensors(Sensors):
    def camera_detections(self, scn=None):
        raise NotImplementedError(_HW + "OV9281 MIPI-CSI/USB-UVC grab → tröskling/CCL på PPA.")
    def imu(self):
        raise NotImplementedError(_HW + "ICM-42688-P över SPI/I²C (SCL=GPIO8/SDA=GPIO7).")
    def ir_decode(self):
        raise NotImplementedError(_HW + "TSOP4856 DATA-linje → 56 kHz-avkodning (RMT).")

class HardwareActuators(Actuators):
    def fire_laser(self, ir_code):
        raise NotImplementedError(_HW + "SFH4725S CC-driver, 56 kHz-burst (eye-safe HW-tak 1 A).")
    def recoil(self, profile):
        raise NotImplementedError(_HW + "recoil-solenoid PWM + FAULT-feedback.")
    def vibrate(self, zone, intensity):
        raise NotImplementedError(_HW + "TPIC6B595 open-drain PWM → ERM-vibrator.")
    def set_constellation(self, current_a):
        raise NotImplementedError(_HW + "LED_EN filtrerad PWM → CC-sänkans setpunkt (C6/C23).")
