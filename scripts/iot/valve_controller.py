#!/usr/bin/env python3
"""Válvula hidropónica: MQTT → GPIO (Raspberry Pi) o modo simulación sin RPi.GPIO."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_IOT = Path(__file__).resolve().parent
if str(_IOT) not in sys.path:
    sys.path.insert(0, str(_IOT))

try:
    import RPi.GPIO as GPIO  # type: ignore[import-not-found]

    _HAS_GPIO = True
except ImportError:
    GPIO = None  # type: ignore[assignment]
    _HAS_GPIO = False

from mqtt_actuator_common import run_actuator_loop


def main() -> None:
    valve_id = os.getenv("CASTUO_VALVE_ID", "valvula_agua")
    pin = int(os.getenv("CASTUO_GPIO_PIN", "17"))

    if _HAS_GPIO:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

        def on_high(state: bool) -> None:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

        def cleanup() -> None:
            GPIO.cleanup()

    else:

        def on_high(state: bool) -> None:
            print(f"[simulación] válvula {valve_id} -> {state}")

        def cleanup() -> None:
            pass

    run_actuator_loop(valve_id, on_high, cleanup)


if __name__ == "__main__":
    main()
