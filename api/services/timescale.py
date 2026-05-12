from __future__ import annotations

from typing import Any, Optional

try:
    from database.timescale import timescale_db as _core_timescale_db
except ModuleNotFoundError:  # pragma: no cover
    from api.database.timescale import timescale_db as _core_timescale_db


class TimescaleService:
    """Adaptador de servicio para compatibilidad con api.services.timescale."""

    @property
    def conn(self):
        return _core_timescale_db.conn

    @property
    def available(self) -> bool:
        return _core_timescale_db.available

    def insert_telemetry(
        self,
        device_id: str,
        metric: str,
        value: float,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        return _core_timescale_db.insert_telemetry(device_id, metric, value, metadata)

    def get_device_latest(self, device_id: str, metric: str = "readings") -> Optional[dict[str, Any]]:
        return _core_timescale_db.get_device_latest(device_id, metric)

    def insert_sensor_event(self, event: dict[str, Any]) -> bool:
        return _core_timescale_db.insert_sensor_event(event)


timescale_db = TimescaleService()
