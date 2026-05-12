# -*- coding: utf-8 -*-
"""FHSS (Frequency Hopping Spread Spectrum) para resistencia a jamming en LoRaWAN."""
from __future__ import annotations

import random
import time
from typing import List

# EU868 bandas típicas (MHz)
EU868_CHANNELS = [868.1, 868.3, 868.5, 867.1, 867.3, 867.5, 867.7, 867.9]


class FHSSManager:
    """Gestiona saltos de frecuencia para dispositivos LoRa (stub; en prod: gateway real)."""

    def __init__(self, frequencies: List[float] = None):
        self.frequencies = list(frequencies or EU868_CHANNELS)
        random.shuffle(self.frequencies)
        self._index = 0

    def get_next_frequency(self) -> float:
        """Devuelve la siguiente frecuencia en la secuencia."""
        freq = self.frequencies[self._index]
        self._index = (self._index + 1) % len(self.frequencies)
        return freq

    def current_frequency(self) -> float:
        return self.frequencies[self._index]

    def sync_devices(self, mqtt_publish_fn=None) -> float:
        """Sincroniza dispositivos a la nueva frecuencia (en prod: publicar por MQTT)."""
        current = self.get_next_frequency()
        if mqtt_publish_fn:
            mqtt_publish_fn("castuo/fhss/sync", str(current))
        return current
