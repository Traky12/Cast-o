"""
TimescaleDB client para persistencia duradera de telemetría IoT.
Aligns con el servicio timescaledb-primary de docker-compose.ha.yml.
"""

import os
from datetime import datetime, timezone
from typing import Any

psycopg2 = None
sql = None
extras = None
isolation_level_autocommit = 0

try:
    import psycopg2
    from psycopg2 import sql, extras
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT as isolation_level_autocommit

    _psycopg2_available = True
except ImportError:  # pragma: no cover
    _psycopg2_available = False


class TimescaleDB:
    """Cliente para TimescaleDB con hipertablas para datos IoT.

    Si TimescaleDB no está disponible, opera en modo degradado
    (los datos se pierden al reiniciar, igual que el dict en memoria).
    """

    def __init__(self) -> None:
        self.conn: Any | None = None
        if _psycopg2_available:
            self._connect()

    def _connect(self) -> None:
        """Conecta a TimescaleDB con reconexión automática."""
        host = os.getenv("TIMESCALE_DB_HOST", "")
        password = os.getenv("TIMESCALE_DB_PASSWORD", "")

        # No intentar conexión si no hay host configurado (entorno dev/test)
        if not host:
            return

        try:
            self.conn = psycopg2.connect(  # type: ignore[union-attr]
                dbname=os.getenv("TIMESCALE_DB_NAME", "castuo_telemetry"),
                user=os.getenv("TIMESCALE_DB_USER", "castuo_iot"),
                password=password,
                host=host,
                port=int(os.getenv("TIMESCALE_DB_PORT", "5432")),
                connect_timeout=5,
            )
            self.conn.set_isolation_level(isolation_level_autocommit)
            self._ensure_schema()
        except Exception as exc:  # pragma: no cover
            print(f"⚠️ TimescaleDB no disponible ({exc}). Usando fallback en memoria.")
            self.conn = None

    def _ensure_schema(self) -> None:
        """Crea las tablas e hipertablas si no existen."""
        if not self.conn:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    device_id  VARCHAR(128) PRIMARY KEY,
                    device_type VARCHAR(64),
                    location   VARCHAR(256),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                    time      TIMESTAMPTZ NOT NULL,
                    device_id VARCHAR(128) NOT NULL,
                    metric    VARCHAR(64) NOT NULL,
                    value     DOUBLE PRECISION,
                    metadata  JSONB
                );
                """
            )
            # Crear la hipertabla (no falla si ya existe)
            cur.execute(
                "SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);"
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_telemetry_device
                ON telemetry (device_id, time DESC);
                """
            )

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    def insert_telemetry(
        self,
        device_id: str,
        metric: str,
        value: float,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Inserta un punto de telemetría. Devuelve True si fue persistido."""
        if not self.conn:
            return False
        try:
            import json as _json

            with self.conn.cursor() as cur:
                cur.execute(
                    sql.SQL(  # type: ignore[union-attr]
                        """
                        INSERT INTO telemetry (time, device_id, metric, value, metadata)
                        VALUES (%s, %s, %s, %s, %s);
                        """
                    ),
                    (
                        datetime.now(timezone.utc),
                        device_id,
                        metric,
                        value,
                        _json.dumps(metadata or {}),
                    ),
                )
            return True
        except Exception as exc:  # pragma: no cover
            print(f"❌ Error insertando telemetría: {exc}")
            return False

    def insert_sensor_event(self, event: dict[str, Any]) -> bool:
        """Persiste un evento completo de sensor (readings como JSONB)."""
        if not self.conn:
            return False
        try:
            import json as _json

            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO telemetry (time, device_id, metric, value, metadata)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (
                        datetime.now(timezone.utc),
                        event.get("sensor_id", "unknown"),
                        "readings",
                        0.0,
                        _json.dumps(event.get("readings", {})),
                    ),
                )
            return True
        except Exception as exc:  # pragma: no cover
            print(f"❌ Error insertando evento: {exc}")
            return False

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def get_device_latest(
        self, device_id: str, metric: str = "readings"
    ) -> dict[str, Any] | None:
        """Retorna el último registro de un dispositivo para una métrica."""
        if not self.conn:
            return None
        try:
            with self.conn.cursor(cursor_factory=extras.RealDictCursor) as cur:  # type: ignore[union-attr]
                cur.execute(
                    """
                    SELECT time, value, metadata
                    FROM telemetry
                    WHERE device_id = %s AND metric = %s
                    ORDER BY time DESC
                    LIMIT 1;
                    """,
                    (device_id, metric),
                )
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as exc:  # pragma: no cover
            print(f"❌ Error consultando telemetría: {exc}")
            return None

    @property
    def available(self) -> bool:
        """True si la conexión a TimescaleDB está activa."""
        return self.conn is not None

    def close(self) -> None:
        """Cierra la conexión."""
        if self.conn:
            self.conn.close()
            self.conn = None


# Singleton — reutiliza la conexión en todo el proceso
timescale_db = TimescaleDB()
