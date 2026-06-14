"""STRILAS firmware-skelett — transport (meddelandebuss).
In-process pub/sub nu; samma API portar till WiFi6/MQTT på HW (topics → MQTT-topics).
"""
from collections import defaultdict


class Bus:
    def __init__(self):
        self._subs = defaultdict(list)

    def subscribe(self, topic, fn):
        self._subs[topic].append(fn)

    def publish(self, topic, msg):
        for fn in self._subs[topic]:
            fn(msg)
