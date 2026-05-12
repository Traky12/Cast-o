#!/usr/bin/env python3
"""
Control serial opcional para laboratorio; sin hardware usar mock (entorno CASTUO_ROBOT_SERIAL_MOCK=1).
Integración profunda: backend/integrations/robotics/.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_SERIAL = None
try:
    import serial  # type: ignore

    _SERIAL = serial
except ImportError:
    pass


class RobotController:
    def __init__(self, port: str = "COM3", baudrate: int = 9600) -> None:
        self.port = port
        self.baudrate = baudrate
        self.logs: List[str] = []
        self.connection: Any = None
        self._mock = os.environ.get("CASTUO_ROBOT_SERIAL_MOCK", "").lower() in ("1", "true", "yes")

    def connect(self) -> bool:
        if self._mock or _SERIAL is None:
            self.connection = object()
            self.logs.append(f"[mock] conectado {self.port} @ {self.baudrate}")
            return True
        try:
            self.connection = _SERIAL.Serial(self.port, self.baudrate, timeout=1)
            self.logs.append(f"conectado {self.port} @ {self.baudrate}")
            return True
        except Exception as e:
            self.logs.append(f"error conexión: {e}")
            return False

    def send_command(self, command: str) -> Dict[str, Any]:
        if not self.connection:
            return {"error": "sin conexión"}
        if self._mock or _SERIAL is None:
            self.logs.append(f"cmd {command} -> OK")
            return {"status": "ok", "response": f"MOCK {command}"}
        try:
            self.connection.write((command + "\n").encode())
            time.sleep(0.05)
            raw = self.connection.readline()
            resp = raw.decode(errors="replace").strip()
            self.logs.append(f"cmd {command} -> {resp}")
            return {"status": "ok", "response": resp}
        except Exception as e:
            self.logs.append(f"error cmd: {e}")
            return {"error": str(e)}

    def disconnect(self) -> None:
        if self.connection and _SERIAL is not None and not self._mock:
            try:
                self.connection.close()
            except Exception:
                pass
        self.connection = None
        self.logs.append("desconectado")

    def save_logs(self, log_path: str = "logs/robotics_controller.json") -> None:
        lp = Path(log_path)
        lp.parent.mkdir(parents=True, exist_ok=True)
        lp.write_text(json.dumps(self.logs, indent=2), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--port", default=os.environ.get("CASTUO_ROBOT_PORT", "COM3"))
    p.add_argument("--baud", type=int, default=int(os.environ.get("CASTUO_ROBOT_BAUD", "9600")))
    p.add_argument("--command", default="")
    p.add_argument("--log", default="logs/robotics_controller.json")
    args = p.parse_args()

    c = RobotController(port=args.port, baudrate=args.baud)
    if not c.connect():
        print(json.dumps({"error": "connect failed", "logs": c.logs}))
        return
    if args.command:
        print(json.dumps(c.send_command(args.command)))
    c.disconnect()
    c.save_logs(args.log)


if __name__ == "__main__":
    main()
