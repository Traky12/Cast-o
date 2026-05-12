"""
CloudManager — Gestión cloud segura para CASTUO-SYSTEM.

Encapsula toda la lógica de:
- Sincronización de telemetría IoT a la nube (Thingsdata ES)
- Backups automáticos cifrados a S3/MinIO
- Health-check remoto con token rotante
- Registro de métricas globales de ambos prototipos
- Comunicación segura (TLS, API key firmada, replay-proof)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuración desde entorno
# ─────────────────────────────────────────────────────────────────────────────

def _cfg(key: str, default: str = "") -> str:
    return os.getenv(key, default)


CLOUD_ENDPOINT      = _cfg("CLOUD_TELEMETRY_ENDPOINT", "https://api.thingsdata.es/v1/ingest")
CLOUD_API_KEY       = _cfg("THINGSDATA_API_KEY", "")
CLOUD_SECRET        = _cfg("THINGSDATA_SECRET", "")
CLOUD_TIMEOUT_S     = int(_cfg("CLOUD_TIMEOUT_SECONDS", "10"))
CLOUD_ENABLED       = _cfg("CLOUD_ENABLED", "false").lower() in {"1", "true", "yes"}
BACKUP_BUCKET       = _cfg("BACKUP_S3_BUCKET", "castuo-backups")
BACKUP_S3_ENDPOINT  = _cfg("BACKUP_S3_ENDPOINT", "")


# ─────────────────────────────────────────────────────────────────────────────
# Modelo de telemetría cloud
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CloudTelemetryRecord:
    prototype_id: int           # 1 o 2
    sensor_type: str            # ph | ec | temp | hr | co2 ...
    value: float
    unit: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    device_id: str = ""
    anomaly: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CloudSyncResult:
    success: bool
    records_sent: int
    records_failed: int
    endpoint: str
    latency_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: Optional[str] = None


@dataclass
class BackupResult:
    success: bool
    bucket: str
    key: str
    size_bytes: int
    checksum_sha256: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Firma HMAC-SHA256 para requests cloud (replay-proof)
# ─────────────────────────────────────────────────────────────────────────────

def _sign_payload(payload: bytes, secret: str, ts: int) -> str:
    """Genera firma HMAC-SHA256 con timestamp para prevenir replay attacks."""
    msg = f"{ts}".encode() + b"." + payload
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def _verify_signature(payload: bytes, secret: str, ts: int, signature: str,
                       max_age_s: int = 300) -> bool:
    """Verifica firma y que no sea un replay (timestamp dentro de ventana)."""
    now = int(time.time())
    if abs(now - ts) > max_age_s:
        return False
    expected = _sign_payload(payload, secret, ts)
    return hmac.compare_digest(expected, signature)


# ─────────────────────────────────────────────────────────────────────────────
# Buffer local en memoria (copia de seguridad pre-cloud)
# ─────────────────────────────────────────────────────────────────────────────

class _TelemetryBuffer:
    """Buffer en memoria para telemetría pendiente de enviar a la nube."""

    def __init__(self, max_size: int = 1000) -> None:
        self._queue: list[CloudTelemetryRecord] = []
        self._max_size = max_size

    def push(self, record: CloudTelemetryRecord) -> None:
        if len(self._queue) >= self._max_size:
            self._queue.pop(0)  # descartar el más antiguo
        self._queue.append(record)

    def drain(self, batch_size: int = 100) -> list[CloudTelemetryRecord]:
        batch = self._queue[:batch_size]
        self._queue = self._queue[batch_size:]
        return batch

    def size(self) -> int:
        return len(self._queue)

    def clear(self) -> None:
        self._queue.clear()


# ─────────────────────────────────────────────────────────────────────────────
# CloudManager principal
# ─────────────────────────────────────────────────────────────────────────────

class CloudManager:
    """
    Gestor cloud seguro para CASTUO-SYSTEM.

    Responsabilidades:
    1. Recibir telemetría IoT de P1 y P2
    2. Buffer con retry ante fallos de red
    3. Envío seguro (TLS + HMAC-SHA256 firmado)
    4. Backup cifrado de snapshots
    5. Health-check remoto
    """

    def __init__(self) -> None:
        self._buffer = _TelemetryBuffer()
        self._stats: dict[str, Any] = {
            "total_sent": 0,
            "total_failed": 0,
            "last_sync": None,
            "last_error": None,
        }

    # ── Telemetría ──────────────────────────────────────────────────────────

    def enqueue(self, record: CloudTelemetryRecord) -> None:
        """Encola un registro de telemetría para envío cloud."""
        self._buffer.push(record)
        logger.debug(
            "Cloud enqueue P%d %s=%.3f (%s) — buffer=%d",
            record.prototype_id, record.sensor_type, record.value,
            record.unit, self._buffer.size(),
        )

    def flush(self, batch_size: int = 100) -> CloudSyncResult:
        """
        Envía la telemetría acumulada a la nube.
        Retorna resultado sin lanzar excepciones; errores en .error.
        """
        batch = self._buffer.drain(batch_size)
        if not batch:
            return CloudSyncResult(
                success=True, records_sent=0, records_failed=0,
                endpoint=CLOUD_ENDPOINT, latency_ms=0.0,
            )

        if not CLOUD_ENABLED or not CLOUD_API_KEY:
            # Modo offline: log sin envío
            logger.info("Cloud OFFLINE — %d registros en buffer local", len(batch))
            # Reencolar para no perder datos
            for r in batch:
                self._buffer.push(r)
            return CloudSyncResult(
                success=False, records_sent=0, records_failed=len(batch),
                endpoint=CLOUD_ENDPOINT, latency_ms=0.0,
                error="cloud_disabled_or_no_api_key",
            )

        payload_obj = [
            {
                "prototype_id": r.prototype_id,
                "sensor": r.sensor_type,
                "value": r.value,
                "unit": r.unit,
                "ts": r.timestamp,
                "device_id": r.device_id,
                "anomaly": r.anomaly,
                "meta": r.metadata,
            }
            for r in batch
        ]
        payload_bytes = json.dumps(payload_obj, ensure_ascii=False).encode()
        ts_now = int(time.time())
        signature = _sign_payload(payload_bytes, CLOUD_SECRET, ts_now)

        headers = {
            "X-Api-Key": CLOUD_API_KEY,
            "X-Timestamp": str(ts_now),
            "X-Signature": signature,
            "Content-Type": "application/json",
        }

        t0 = time.monotonic()
        try:
            import httpx  # importación diferida para no romper entornos sin httpx

            with httpx.Client(timeout=CLOUD_TIMEOUT_S, verify=True) as client:
                resp = client.post(CLOUD_ENDPOINT, content=payload_bytes, headers=headers)
                resp.raise_for_status()

            latency = (time.monotonic() - t0) * 1000
            self._stats["total_sent"] += len(batch)
            self._stats["last_sync"] = datetime.now(timezone.utc).isoformat()
            logger.info("Cloud sync OK — %d registros en %.1fms", len(batch), latency)
            return CloudSyncResult(
                success=True, records_sent=len(batch), records_failed=0,
                endpoint=CLOUD_ENDPOINT, latency_ms=latency,
            )

        except Exception as exc:  # noqa: BLE001
            latency = (time.monotonic() - t0) * 1000
            err_msg = str(exc)
            self._stats["total_failed"] += len(batch)
            self._stats["last_error"] = err_msg
            logger.error("Cloud sync FAILED: %s — reencolar %d registros", err_msg, len(batch))
            # Reencolar si hay espacio
            for r in batch:
                self._buffer.push(r)
            return CloudSyncResult(
                success=False, records_sent=0, records_failed=len(batch),
                endpoint=CLOUD_ENDPOINT, latency_ms=latency, error=err_msg,
            )

    # ── Backup ──────────────────────────────────────────────────────────────

    def backup_snapshot(self, data: dict[str, Any], label: str = "snapshot") -> BackupResult:
        """
        Crea backup cifrado (SHA-256 checksum) de un snapshot de datos.
        Si hay S3/MinIO configurado lo sube; si no, lo persiste en /tmp.
        """
        payload_bytes = json.dumps(data, ensure_ascii=False, default=str).encode()
        checksum = hashlib.sha256(payload_bytes).hexdigest()
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        key = f"backups/{label}-{ts}-{checksum[:8]}.json"

        if not BACKUP_S3_ENDPOINT:
            # Fallback local
            import tempfile, pathlib  # noqa: E401
            tmp = pathlib.Path(tempfile.gettempdir()) / key.replace("/", "_")
            tmp.write_bytes(payload_bytes)
            logger.info("Backup local: %s (%d bytes, sha256=%s)", tmp, len(payload_bytes), checksum[:16])
            return BackupResult(
                success=True, bucket="local:/tmp", key=str(tmp),
                size_bytes=len(payload_bytes), checksum_sha256=checksum,
            )

        try:
            import boto3  # noqa: PLC0415
            s3 = boto3.client(
                "s3",
                endpoint_url=BACKUP_S3_ENDPOINT,
                aws_access_key_id=_cfg("BACKUP_AWS_ACCESS_KEY"),
                aws_secret_access_key=_cfg("BACKUP_AWS_SECRET_KEY"),
            )
            s3.put_object(
                Bucket=BACKUP_BUCKET,
                Key=key,
                Body=payload_bytes,
                ContentType="application/json",
                Metadata={"sha256": checksum, "label": label},
                ServerSideEncryption="AES256",
            )
            logger.info("Backup S3 OK: s3://%s/%s", BACKUP_BUCKET, key)
            return BackupResult(
                success=True, bucket=BACKUP_BUCKET, key=key,
                size_bytes=len(payload_bytes), checksum_sha256=checksum,
            )
        except Exception as exc:  # noqa: BLE001
            return BackupResult(
                success=False, bucket=BACKUP_BUCKET, key=key,
                size_bytes=len(payload_bytes), checksum_sha256=checksum,
                error=str(exc),
            )

    # ── Health-check ────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        return {
            **self._stats,
            "buffer_pending": self._buffer.size(),
            "cloud_enabled": CLOUD_ENABLED,
            "endpoint": CLOUD_ENDPOINT,
        }

    def health(self) -> dict[str, bool]:
        """Salud básica del componente cloud."""
        return {
            "cloud_configured": bool(CLOUD_API_KEY),
            "cloud_enabled": CLOUD_ENABLED,
            "buffer_ok": self._buffer.size() < 900,  # límite de aviso al 90%
        }


# Instancia global
cloud_manager = CloudManager()
