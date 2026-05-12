"""
CASTÚO-SYSTEM™ v3.1 — InfluxDB Time-Series Writer
Almacena lecturas de sensores, energía y eventos de actuadores en InfluxDB 2.x.

Variables de entorno:
    INFLUXDB_URL          URL del servidor InfluxDB (default: http://localhost:8086)
    INFLUXDB_TOKEN_FILE   Fichero con el token de autenticación (Opción A)
    INFLUXDB_TOKEN        Token plano (Opción B)
    INFLUXDB_ORG          Organización InfluxDB (default: castuo)
    INFLUXDB_BUCKET_SENSORS   Bucket para sensores (default: invernadero_sensores)
    INFLUXDB_BUCKET_ENERGY    Bucket para energía (default: invernadero_energia)
    INFLUXDB_BUCKET_ACTUATORS Bucket para actuadores (default: invernadero_actuadores)

Dependencias opcionales:
    pip install influxdb-client>=3.0.0
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("castuo.influx_writer")


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

INFLUXDB_URL    = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN  = _read_secret("INFLUXDB_TOKEN")
INFLUXDB_ORG    = os.getenv("INFLUXDB_ORG", "castuo")
BUCKET_SENSORS  = os.getenv("INFLUXDB_BUCKET_SENSORS",   "invernadero_sensores")
BUCKET_ENERGY   = os.getenv("INFLUXDB_BUCKET_ENERGY",    "invernadero_energia")
BUCKET_ACTUATORS = os.getenv("INFLUXDB_BUCKET_ACTUATORS", "invernadero_actuadores")

# Detectar si influxdb-client está disponible
try:
    from influxdb_client import InfluxDBClient, WriteOptions  # type: ignore
    from influxdb_client.client.write_api import SYNCHRONOUS  # type: ignore
    _INFLUX_AVAILABLE = bool(INFLUXDB_TOKEN)
except ImportError:
    _INFLUX_AVAILABLE = False
    logger.info("[influx_writer] influxdb-client no instalado — modo simulación activo")


class InfluxWriter:
    """
    Cliente InfluxDB con fallback a registro en memoria cuando las credenciales
    no están configuradas o la librería no está instalada.
    """

    def __init__(self) -> None:
        self._client = None
        self._write_api = None
        self._sim_buffer: list[dict] = []

        if _INFLUX_AVAILABLE:
            try:
                self._client = InfluxDBClient(
                    url=INFLUXDB_URL,
                    token=INFLUXDB_TOKEN,
                    org=INFLUXDB_ORG,
                )
                self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
                logger.info("[influx_writer] Conectado a InfluxDB en %s", INFLUXDB_URL)
            except Exception as exc:
                logger.warning("[influx_writer] No se pudo conectar a InfluxDB: %s — simulación activa", exc)
                self._client = None

    @property
    def is_connected(self) -> bool:
        return self._write_api is not None

    # ── Escritura de lecturas de sensores ──────────────────────────────────────

    def write_sensor_reading(
        self,
        lote_id: str,
        zona: str,
        cultivo: str,
        measurement: str,
        fields: dict[str, float],
        tags: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> bool:
        """
        Escribe una lectura de sensor en el bucket de sensores.
        measurement: 'solucion_nutritiva' | 'clima' | 'hidroponia'
        fields: dict con los valores medidos (ph, ec, co2, etc.)
        """
        ts = timestamp or datetime.now(timezone.utc)
        base_tags = {"lote_id": lote_id, "zona": zona, "cultivo": cultivo}
        if tags:
            base_tags.update(tags)

        return self._write(
            bucket=BUCKET_SENSORS,
            measurement=measurement,
            tags=base_tags,
            fields=fields,
            timestamp=ts,
        )

    def write_energy_reading(
        self,
        lote_id: str,
        panel_id: str,
        fields: dict[str, float],
        timestamp: datetime | None = None,
    ) -> bool:
        """Escribe una lectura del sistema agrovoltaico en el bucket de energía."""
        ts = timestamp or datetime.now(timezone.utc)
        return self._write(
            bucket=BUCKET_ENERGY,
            measurement="agrovoltaico",
            tags={"lote_id": lote_id, "panel_id": panel_id},
            fields=fields,
            timestamp=ts,
        )

    def write_actuator_event(
        self,
        actuador: str,
        accion: str,
        zona: str,
        triggered_by: str = "auto",
        valor: float | None = None,
        timestamp: datetime | None = None,
    ) -> bool:
        """Registra un evento de actuación (encendido, apagado, ajuste) en InfluxDB."""
        ts = timestamp or datetime.now(timezone.utc)
        fields: dict[str, Any] = {"evento": 1}
        if valor is not None:
            fields["valor"] = valor
        return self._write(
            bucket=BUCKET_ACTUATORS,
            measurement="actuador_evento",
            tags={"actuador": actuador, "accion": accion, "zona": zona, "triggered_by": triggered_by},
            fields=fields,
            timestamp=ts,
        )

    # ── Escritura interna ──────────────────────────────────────────────────────

    def _write(
        self,
        bucket: str,
        measurement: str,
        tags: dict[str, str],
        fields: dict[str, Any],
        timestamp: datetime,
    ) -> bool:
        if self._write_api:
            try:
                from influxdb_client.client.write_api import Point  # type: ignore
                p = Point(measurement)
                for k, v in tags.items():
                    p = p.tag(k, v)
                for k, v in fields.items():
                    p = p.field(k, float(v) if isinstance(v, (int, float)) else v)
                p = p.time(timestamp)
                self._write_api.write(bucket=bucket, record=p)
                return True
            except Exception as exc:
                logger.warning("[influx_writer] Error escribiendo en InfluxDB: %s — simulando", exc)

        # Fallback: buffer en memoria (útil para tests y desarrollo)
        self._sim_buffer.append({
            "bucket": bucket,
            "measurement": measurement,
            "tags": tags,
            "fields": fields,
            "timestamp": timestamp.isoformat(),
        })
        if len(self._sim_buffer) > 1000:
            self._sim_buffer.pop(0)
        return False

    def get_sim_buffer(self) -> list[dict]:
        """Devuelve los registros en el buffer de simulación (para tests)."""
        return list(self._sim_buffer)

    def flush_sim_buffer(self) -> None:
        self._sim_buffer.clear()

    def close(self) -> None:
        if self._client:
            self._client.close()


# ── Instancia global compartida ────────────────────────────────────────────────

_writer_instance: InfluxWriter | None = None


def get_writer() -> InfluxWriter:
    """Retorna la instancia global del escritor (singleton lazy)."""
    global _writer_instance
    if _writer_instance is None:
        _writer_instance = InfluxWriter()
    return _writer_instance
