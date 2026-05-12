# -*- coding: utf-8 -*-
"""
Agente IoT para Raspberry Pi: sensores (DHT22, MH-Z19, EC/pH), actuadores (bomba, LED),
envío a CASTUO-SYSTEM y generación de QR para trazabilidad de bandejas hidropónicas.
En entorno sin hardware (Windows/dev) usa sensores simulados.
"""
from __future__ import annotations

import json
import random
import time
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    import qrcode
except ImportError:
    qrcode = None

# Hardware opcional (Raspberry Pi)
try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO = None
    _GPIO_AVAILABLE = False

try:
    import board
    import adafruit_dht
    _DHT_AVAILABLE = True
except ImportError:
    board = None
    adafruit_dht = None
    _DHT_AVAILABLE = False

try:
    import busio
    import adafruit_mhz19
    _MHZ19_AVAILABLE = True
except ImportError:
    busio = None
    adafruit_mhz19 = None
    _MHZ19_AVAILABLE = False

try:
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    _ADS_AVAILABLE = True
except ImportError:
    ADS = None
    AnalogIn = None
    _ADS_AVAILABLE = False


class SimulatedSensors:
    """Sensores simulados para desarrollo sin hardware."""

    def __init__(self) -> None:
        self._t = 22.0
        self._h = 65.0
        self._co2 = 450.0
        self._ec = 1.4
        self._ph = 5.9

    def read(self) -> Dict[str, Any]:
        self._t += random.uniform(-0.5, 0.5)
        self._t = max(18, min(28, self._t))
        self._h += random.uniform(-2, 2)
        self._h = max(50, min(80, self._h))
        self._co2 += random.uniform(-20, 20)
        self._co2 = max(400, min(800, self._co2))
        self._ec += random.uniform(-0.05, 0.05)
        self._ec = max(1.0, min(2.0, self._ec))
        self._ph += random.uniform(-0.05, 0.05)
        self._ph = max(5.5, min(6.5, self._ph))
        return {
            "temperature": round(self._t, 1),
            "humidity": round(self._h, 1),
            "co2": int(self._co2),
            "ec": round(self._ec, 2),
            "ph": round(self._ph, 2),
            "ec_raw": int(self._ec * 10000),
            "ph_raw": int(self._ph * 10000),
            "camera_status": "active",
            "timestamp": datetime.now().isoformat(),
        }


class RaspberryPiIoTAgent:
    """
    Agente IoT para Raspberry Pi: recopila datos de sensores y los envía a CASTUO-SYSTEM.
    Integra DHT22 (temp/humedad), MH-Z19 (CO₂), EC/pH (ADS1115), bomba de riego y LED.
    Sin hardware usa sensores simulados.
    """

    def __init__(
        self,
        api_endpoint: str,
        tray_id: str,
        auth_token: str = "",
    ) -> None:
        self.api_endpoint = api_endpoint.rstrip("/")
        self.tray_id = tray_id
        self.auth_token = auth_token or "dev-token"
        self.sensors = self._initialize_sensors()
        self.actuators = self._initialize_actuators()
        self.last_readings: Dict[str, Any] = {}
        self.session_id: Optional[str] = None

    def _initialize_sensors(self) -> Any:
        if _DHT_AVAILABLE and board is not None and adafruit_dht is not None:
            try:
                return {"dht22": adafruit_dht.DHT22(board.D4), "mhz19": None, "ec": None, "ph": None, "simulated": False}
            except Exception:
                pass
        if _MHZ19_AVAILABLE and busio is not None and adafruit_mhz19 is not None:
            try:
                uart = busio.UART(board.TX, board.RX, baudrate=9600)
                return {"dht22": None, "mhz19": adafruit_mhz19.MHZ19(uart), "ec": None, "ph": None, "simulated": False}
            except Exception:
                pass
        if _ADS_AVAILABLE and board is not None and ADS is not None:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                ads = ADS.ADS1115(i2c)
                return {
                    "dht22": None,
                    "mhz19": None,
                    "ec": AnalogIn(ads, ADS.P0),
                    "ph": AnalogIn(ads, ADS.P1),
                    "simulated": False,
                }
            except Exception:
                pass
        return {"simulated": True, "sim": SimulatedSensors()}

    def _initialize_actuators(self) -> Dict[str, Any]:
        if _GPIO_AVAILABLE and GPIO is not None:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(17, GPIO.OUT)
                GPIO.output(17, GPIO.LOW)
                GPIO.setup(27, GPIO.OUT)
                try:
                    pwm = GPIO.PWM(27, 100)
                    pwm.start(0)
                except Exception:
                    pwm = None
                return {"water_pump": 17, "grow_light": 27, "led_pwm": pwm, "gpio": True}
            except Exception:
                pass
        return {"water_pump": None, "grow_light": None, "led_pwm": None, "gpio": False}

    def _read_sensors(self) -> Dict[str, Any]:
        if self.sensors.get("simulated"):
            return self.sensors["sim"].read()
        readings: Dict[str, Any] = {"timestamp": datetime.now().isoformat()}
        if self.sensors.get("dht22"):
            try:
                readings["temperature"] = self.sensors["dht22"].temperature
                readings["humidity"] = self.sensors["dht22"].humidity
            except Exception:
                readings["temperature"] = 22.0
                readings["humidity"] = 65.0
        if self.sensors.get("mhz19"):
            try:
                readings["co2"] = self.sensors["mhz19"].co2
            except Exception:
                readings["co2"] = 500
        if self.sensors.get("ec") is not None:
            try:
                readings["ec_raw"] = self.sensors["ec"].value
                readings["ph_raw"] = self.sensors["ph"].value
                readings["ec"] = readings["ec_raw"] * 0.0001
                readings["ph"] = 7.0 + (readings["ph_raw"] - 20000) / 10000
            except Exception:
                readings["ec"] = 1.4
                readings["ph"] = 5.9
        readings["camera_status"] = "active"
        return readings

    def _control_actuators(self, commands: Dict[str, Any]) -> Dict[str, bool]:
        if not self.actuators.get("gpio"):
            return {k: True for k in commands}
        if GPIO is None:
            return {}
        if "water_pump" in commands:
            GPIO.output(self.actuators["water_pump"], GPIO.HIGH if commands["water_pump"] else GPIO.LOW)
        if "grow_light" in commands and self.actuators.get("led_pwm"):
            self.actuators["led_pwm"].ChangeDutyCycle(commands["grow_light"])
        return {k: True for k in commands}

    def _generate_tray_qr(self, tray_data: Dict[str, Any]) -> str:
        qr_data = json.dumps({
            "tray_id": tray_data["tray_id"],
            "batch_id": tray_data.get("batch_id", "N/A"),
            "start_date": tray_data.get("start_date", datetime.now().isoformat()),
            "location": tray_data.get("location", "Cáceres, Extremadura"),
            "gaiachain_tx": tray_data.get("gaiachain_tx", ""),
        })
        filename = f"qr_{self.tray_id}.png"
        if qrcode is not None:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(filename)
        return filename

    def _send_to_castuo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if requests is None:
            return {"status": "success", "gaiachain_tx": "stub-tx", "commands": {}}
        headers = {"Authorization": f"Bearer {self.auth_token}", "Content-Type": "application/json"}
        try:
            r = requests.post(
                f"{self.api_endpoint}/data",
                headers=headers,
                json=data,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"Error al enviar a CASTUO: {e}")
            return {"status": "error", "message": str(e), "commands": {}}

    def _authenticate(self) -> bool:
        if requests is None:
            self.session_id = "dev-session-" + self.tray_id[-3:]
            return True
        try:
            r = requests.post(
                f"{self.api_endpoint}/auth/iot",
                json={
                    "tray_id": self.tray_id,
                    "device_type": "raspberry_pi",
                    "location": "Cáceres, Extremadura",
                },
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            self.session_id = data.get("session_id")
            return bool(self.session_id)
        except Exception as e:
            print(f"Error autenticación: {e}")
            self.session_id = "dev-session"
            return True

    def run(self, interval: int = 300) -> None:
        """Ejecuta el agente en bucle: leer sensores, enviar a CASTUO, aplicar comandos."""
        print(f"Iniciando agente IoT para bandeja {self.tray_id}...")
        if not self._authenticate():
            print("No se pudo autenticar. Usando modo simulación.")
        qr_file = self._generate_tray_qr({
            "tray_id": self.tray_id,
            "batch_id": f"CASTUO-BATCH-{datetime.now().strftime('%Y%m%d')}-001",
            "start_date": datetime.now().isoformat(),
            "location": "Invernadero Piloto, Cáceres",
            "gaiachain_tx": "",
        })
        print(f"QR generado: {qr_file}")
        try:
            while True:
                print(f"\nLectura: {datetime.now().strftime('%H:%M:%S')}")
                readings = self._read_sensors()
                print(f"  Temp: {readings.get('temperature', 'N/A')} C, Humedad: {readings.get('humidity', 'N/A')}%, CO2: {readings.get('co2', 'N/A')} ppm")
                payload = {
                    "session_id": self.session_id,
                    "tray_id": self.tray_id,
                    "timestamp": readings.get("timestamp", datetime.now().isoformat()),
                    "sensors": readings,
                    "actuators": self.last_readings.get("actuators", {}),
                    "metadata": {
                        "qr_code": qr_file,
                        "location": "Cáceres, Extremadura",
                        "crop_type": "Cannabis medicinal (Futura 75)",
                        "growth_stage": "Vegetativo",
                    },
                }
                response = self._send_to_castuo(payload)
                print(f"  CASTUO: {response.get('status', 'unknown')}")
                if response.get("status") == "success" and response.get("gaiachain_tx"):
                    qr_file = self._generate_tray_qr({
                        "tray_id": self.tray_id,
                        "batch_id": payload["metadata"].get("batch_id", "N/A"),
                        "start_date": payload["timestamp"],
                        "location": payload["metadata"]["location"],
                        "gaiachain_tx": response["gaiachain_tx"],
                    })
                commands = response.get("commands", {})
                if commands:
                    self._control_actuators(commands)
                self.last_readings = {"sensors": readings, "actuators": commands, "timestamp": payload["timestamp"]}
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Agente detenido.")
        finally:
            self._control_actuators({"water_pump": 0, "grow_light": 0})
            if _GPIO_AVAILABLE and GPIO is not None:
                try:
                    GPIO.cleanup()
                except Exception:
                    pass


if __name__ == "__main__":
    agent = RaspberryPiIoTAgent(
        api_endpoint="http://localhost:8000/api/iot",
        tray_id="CASTUO-TRAY-001",
        auth_token="dev-token",
    )
    # Ejecutar 2 ciclos de ejemplo (intervalo 5 s)
    for _ in range(2):
        r = agent._read_sensors()
        print("Lectura simulada:", r)
        time.sleep(5)
    print("OK")
