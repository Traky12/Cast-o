"""
CASTÚO-SYSTEM™ v3.1 — Controlador de Actuadores
Control bidireccional de actuadores del invernadero agrovoltaico hidropónico
mediante MQTT con persistencia de estado en memoria.

Actuadores gestionados:
  - VENTILACION     Control de ventiladores (temperatura/HR)
  - CALEFACCION     Sistema de calefacción
  - RIEGO           Bombas de riego hidropónico
  - ILUMINACION_LED Iluminación LED suplementaria (PWM)
  - SOMBRA          Pantallas de sombra motorizadas (agrovoltaico)
  - NUTRIENTES_A    Bomba peristáltica nutrientes concentrado A
  - NUTRIENTES_B    Bomba peristáltica nutrientes concentrado B
  - ACIDO           Bomba dosificadora de ácido (bajada pH)
  - BASE            Bomba dosificadora de base (subida pH)
  - CO2_INYECCION   Inyección de CO₂

Variables de entorno:
    MQTT_BROKER_HOST     Broker MQTT (default: localhost)
    MQTT_BROKER_PORT     Puerto (default: 1883)
    MQTT_USERNAME        Usuario (opcional)
    MQTT_PASSWORD_FILE / MQTT_PASSWORD  Contraseña
    MQTT_TLS             "1" para TLS
    MQTT_ACTUATOR_PREFIX Prefijo de topics (default: castuo/invernadero/actuadores)
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger("castuo.actuator_controller")


# ── Secrets helper ─────────────────────────────────────────────────────────────

def _read_secret(name: str) -> str:
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            pass
    return os.getenv(name, "")


# ── Configuración ──────────────────────────────────────────────────────────────

MQTT_HOST    = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT    = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USER    = os.getenv("MQTT_USERNAME", "")
MQTT_PASS    = _read_secret("MQTT_PASSWORD")
MQTT_TLS     = os.getenv("MQTT_TLS", "0") == "1"
TOPIC_PREFIX = os.getenv("MQTT_ACTUATOR_PREFIX", "castuo/invernadero/actuadores")

try:
    import paho.mqtt.client as _mqtt  # type: ignore
    _MQTT_AVAILABLE = True
except ImportError:
    _MQTT_AVAILABLE = False
    logger.info("[actuator_controller] paho-mqtt no disponible — modo simulación activo")


# ── Enumerados ─────────────────────────────────────────────────────────────────

class Actuador(str, Enum):
    VENTILACION     = "ventilacion"
    CALEFACCION     = "calefaccion"
    RIEGO           = "riego"
    ILUMINACION_LED = "iluminacion_led"
    SOMBRA          = "sombra"
    NUTRIENTES_A    = "nutrientes_a"
    NUTRIENTES_B    = "nutrientes_b"
    ACIDO           = "acido"
    BASE            = "base"
    CO2_INYECCION   = "co2_inyeccion"


class Accion(str, Enum):
    ENCENDER    = "encender"
    APAGAR      = "apagar"
    PULSO       = "pulso"       # Activar N segundos y apagar (dosificadoras)
    AJUSTAR     = "ajustar"     # Ajustar a valor% (ventiladores PWM, sombra %)
    EMERGENCIA  = "emergencia"  # Parada de emergencia


# Estado por defecto de cada actuador
_DEFAULT_STATES: dict[str, dict] = {
    Actuador.VENTILACION:     {"on": False, "nivel_pct": 0,   "zona": "general"},
    Actuador.CALEFACCION:     {"on": False, "nivel_pct": 0,   "zona": "general"},
    Actuador.RIEGO:           {"on": False, "caudal_l_h": 0,  "zona": "general"},
    Actuador.ILUMINACION_LED: {"on": False, "nivel_pct": 0,   "zona": "general"},
    Actuador.SOMBRA:          {"on": False, "cobertura_pct": 0, "zona": "general"},
    Actuador.NUTRIENTES_A:    {"on": False, "ml_dosificados": 0, "zona": "general"},
    Actuador.NUTRIENTES_B:    {"on": False, "ml_dosificados": 0, "zona": "general"},
    Actuador.ACIDO:           {"on": False, "ml_dosificados": 0, "zona": "general"},
    Actuador.BASE:            {"on": False, "ml_dosificados": 0, "zona": "general"},
    Actuador.CO2_INYECCION:   {"on": False, "ppm_objetivo": 0, "zona": "general"},
}


class ActuatorController:
    """
    Controlador de actuadores con publicación MQTT y fallback simulado.
    Mantiene el estado de cada actuador en memoria para consultas rápidas.
    """

    def __init__(self) -> None:
        self._state: dict[str, dict] = {k.value: dict(v) for k, v in _DEFAULT_STATES.items()}
        self._history: list[dict] = []
        self._mqtt_client: Any = None

        if _MQTT_AVAILABLE:
            self._connect_mqtt()

    # ── Conexión MQTT ──────────────────────────────────────────────────────────

    def _connect_mqtt(self) -> None:
        try:
            import paho.mqtt.client as mqtt  # type: ignore
            client = mqtt.Client(
                client_id="castuo-actuator-ctrl",
                protocol=mqtt.MQTTv5,
            )
            if MQTT_USER:
                client.username_pw_set(MQTT_USER, MQTT_PASS or None)
            if MQTT_TLS:
                import ssl
                client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_start()
            self._mqtt_client = client
            logger.info("[actuator_controller] Conectado a MQTT %s:%d", MQTT_HOST, MQTT_PORT)
        except Exception as exc:
            logger.warning("[actuator_controller] MQTT no disponible: %s — modo simulación", exc)
            self._mqtt_client = None

    # ── Control de actuadores ──────────────────────────────────────────────────

    def control(
        self,
        actuador: str,
        accion: str,
        zona: str = "general",
        valor: float | None = None,
        duracion_seg: int | None = None,
        triggered_by: str = "manual",
    ) -> dict:
        """
        Controla un actuador: publica en MQTT y actualiza el estado interno.

        actuador:     Nombre del actuador (Actuador enum value)
        accion:       Acción a ejecutar (Accion enum value)
        zona:         Zona del invernadero
        valor:        Valor numérico (% para ventilación/sombra, ml para dosificadoras)
        duracion_seg: Duración del pulso en segundos (para PULSO)
        triggered_by: Origen del comando (manual | regla | ia | n8n | nodered)
        """
        now = datetime.now(timezone.utc)

        # Validar actuador
        valid_actuadores = {a.value for a in Actuador}
        if actuador not in valid_actuadores:
            return {"ok": False, "error": f"Actuador '{actuador}' no reconocido"}

        # Construir payload MQTT
        payload: dict = {
            "actuador": actuador,
            "accion": accion,
            "zona": zona,
            "timestamp": now.isoformat(),
            "triggered_by": triggered_by,
        }
        if valor is not None:
            payload["valor"] = valor
        if duracion_seg is not None:
            payload["duracion_seg"] = duracion_seg

        # Actualizar estado interno
        self._update_state(actuador, accion, zona, valor)

        # Publicar en MQTT
        topic = f"{TOPIC_PREFIX}/{zona}/{actuador}"
        published = self._publish(topic, payload)

        # Registrar en historial (últimas 500 acciones)
        event = {**payload, "topic": topic, "mqtt_published": published}
        self._history.append(event)
        if len(self._history) > 500:
            self._history.pop(0)

        logger.info(
            "[actuator_controller] %s %s zona=%s valor=%s mqtt=%s triggered_by=%s",
            accion, actuador, zona, valor, published, triggered_by,
        )

        return {
            "ok": True,
            "actuador": actuador,
            "accion": accion,
            "zona": zona,
            "valor": valor,
            "mqtt_published": published,
            "timestamp": now.isoformat(),
        }

    def emergencia_stop(self, zona: str = "all") -> dict:
        """Para de emergencia: apaga todos los actuadores de una zona o todo."""
        resultados = []
        for actuador in Actuador:
            if zona == "all" or self._state[actuador.value].get("zona") == zona:
                r = self.control(
                    actuador=actuador.value,
                    accion=Accion.APAGAR.value,
                    zona=zona if zona != "all" else self._state[actuador.value].get("zona", "general"),
                    triggered_by="emergencia",
                )
                resultados.append(r)
        logger.warning("[actuator_controller] EMERGENCIA STOP aplicada a zona=%s", zona)
        return {"ok": True, "accion": "emergencia_stop", "zona": zona, "actuadores_apagados": len(resultados)}

    # ── Estado y historial ─────────────────────────────────────────────────────

    def get_status(self, zona: str | None = None) -> dict:
        """Devuelve el estado actual de todos los actuadores."""
        if zona:
            return {k: v for k, v in self._state.items() if v.get("zona") == zona or zona == "all"}
        return dict(self._state)

    def get_history(self, limit: int = 50) -> list[dict]:
        """Devuelve los últimos N eventos de actuación."""
        return self._history[-limit:]

    # ── Helpers internos ───────────────────────────────────────────────────────

    def _update_state(self, actuador: str, accion: str, zona: str, valor: float | None) -> None:
        state = self._state.setdefault(actuador, {"on": False, "zona": zona})
        state["zona"] = zona
        state["ultimo_cambio"] = datetime.now(timezone.utc).isoformat()

        if accion == Accion.ENCENDER.value:
            state["on"] = True
            if valor is not None:
                state["nivel_pct"] = valor
        elif accion in (Accion.APAGAR.value, Accion.EMERGENCIA.value):
            state["on"] = False
            state["nivel_pct"] = 0
        elif accion == Accion.AJUSTAR.value and valor is not None:
            state["on"] = valor > 0
            state["nivel_pct"] = valor
        elif accion == Accion.PULSO.value:
            # El pulso se considera transitorio; el estado no cambia permanentemente
            if actuador in (Actuador.NUTRIENTES_A.value, Actuador.NUTRIENTES_B.value,
                            Actuador.ACIDO.value, Actuador.BASE.value):
                ml = state.get("ml_dosificados", 0)
                state["ml_dosificados"] = round(ml + (valor or 0), 2)

    def _publish(self, topic: str, payload: dict) -> bool:
        if self._mqtt_client:
            try:
                import json
                result = self._mqtt_client.publish(topic, json.dumps(payload), qos=1)
                return result.rc == 0
            except Exception as exc:
                logger.warning("[actuator_controller] Error publicando MQTT: %s", exc)
        return False  # Simulación


# ── Lógica de control automático ───────────────────────────────────────────────

def recomendar_accion_temperatura(
    temp_actual: float,
    temp_min: float = 18.0,
    temp_max: float = 28.0,
) -> dict | None:
    """
    Devuelve la acción recomendada para mantener la temperatura en rango.
    Retorna None si la temperatura está en rango.
    """
    if temp_actual > temp_max:
        intensidad = min(100, int((temp_actual - temp_max) * 20))
        return {
            "actuador": Actuador.VENTILACION.value,
            "accion": Accion.AJUSTAR.value,
            "valor": intensidad,
            "motivo": f"Temperatura {temp_actual}°C > máximo {temp_max}°C",
        }
    elif temp_actual < temp_min:
        return {
            "actuador": Actuador.CALEFACCION.value,
            "accion": Accion.ENCENDER.value,
            "motivo": f"Temperatura {temp_actual}°C < mínimo {temp_min}°C",
        }
    return None


def recomendar_accion_ph(
    ph_actual: float,
    ph_min: float = 5.5,
    ph_max: float = 6.5,
    ml_por_dosis: float = 10.0,
) -> dict | None:
    """Devuelve la acción recomendada para ajustar pH (dosificadora ácido/base)."""
    if ph_actual > ph_max:
        return {
            "actuador": Actuador.ACIDO.value,
            "accion": Accion.PULSO.value,
            "valor": ml_por_dosis,
            "duracion_seg": 5,
            "motivo": f"pH {ph_actual} > máximo {ph_max} — dosificar ácido",
        }
    elif ph_actual < ph_min:
        return {
            "actuador": Actuador.BASE.value,
            "accion": Accion.PULSO.value,
            "valor": ml_por_dosis,
            "duracion_seg": 5,
            "motivo": f"pH {ph_actual} < mínimo {ph_min} — dosificar base",
        }
    return None


def recomendar_accion_ec(
    ec_actual: float,
    ec_min: float = 1.5,
    ec_max: float = 3.0,
    ml_por_dosis: float = 20.0,
) -> dict | None:
    """Devuelve la acción para ajustar EC (bombas de nutrientes)."""
    if ec_actual < ec_min:
        return {
            "actuador": Actuador.NUTRIENTES_A.value,
            "accion": Accion.PULSO.value,
            "valor": ml_por_dosis,
            "duracion_seg": 10,
            "motivo": f"EC {ec_actual} mS/cm < mínimo {ec_min} — añadir nutrientes A+B",
        }
    elif ec_actual > ec_max:
        return {
            "actuador": Actuador.RIEGO.value,
            "accion": Accion.ENCENDER.value,
            "motivo": f"EC {ec_actual} mS/cm > máximo {ec_max} — diluir solución con agua",
        }
    return None


_PAR_OPTIMO_ACTUADOR: dict[str, float] = {
    "tomate":   600.0, "pimiento": 600.0, "pepino":  550.0,
    "lechuga":  350.0, "fresa":    400.0, "albahaca": 350.0,
    "espinaca": 300.0, "cilantro": 300.0,
}


def recomendar_sombra_agrovoltaica(
    luz_actual_umol: float,
    cultivo: str = "tomate",
    cobertura_actual_pct: float = 20.0,
    luz_optima_umol: float | None = None,
) -> dict | None:
    """
    Calcula el ajuste necesario de la pantalla de sombra agrovoltaica.
    luz_actual_umol:    Irradiancia PAR medida (μmol/m²/s)
    cultivo:            Cultivo activo (para obtener el PAR óptimo automáticamente)
    cobertura_actual_pct: % cobertura de sombra actual (0-100)
    luz_optima_umol:    Override manual del PAR óptimo (usa tabla cultivo si None)
    """
    if luz_optima_umol is None:
        luz_optima_umol = _PAR_OPTIMO_ACTUADOR.get(cultivo.lower(), 500.0)
    diferencia = luz_actual_umol - luz_optima_umol
    if diferencia > 100:
        nueva_cobertura = min(80, cobertura_actual_pct + 20)
        return {
            "actuador": Actuador.SOMBRA.value,
            "accion": Accion.AJUSTAR.value,
            "valor": nueva_cobertura,
            "motivo": f"Luz {luz_actual_umol} μmol/m²/s > óptimo {luz_optima_umol} — aumentar sombra a {nueva_cobertura}%",
        }
    elif diferencia < -100:
        nueva_cobertura = max(0, cobertura_actual_pct - 20)
        return {
            "actuador": Actuador.SOMBRA.value,
            "accion": Accion.AJUSTAR.value,
            "valor": nueva_cobertura,
            "motivo": f"Luz {luz_actual_umol} μmol/m²/s < óptimo {luz_optima_umol} — reducir sombra a {nueva_cobertura}%",
        }
    return None


# ── Instancia global ───────────────────────────────────────────────────────────

_controller_instance: ActuatorController | None = None


def get_controller() -> ActuatorController:
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = ActuatorController()
    return _controller_instance
