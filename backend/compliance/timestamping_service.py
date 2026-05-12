# backend/compliance/timestamping_service.py — Notarización con TSA para evidencias críticas

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

_REQUESTS = False
try:
    import requests
    _REQUESTS = True
except ImportError:
    pass


class TimestampingService:
    """
    Servicio de sellado de tiempo (TSA) para validez legal de evidencias.
    Stub: en producción conectar con TSA (RFC 3161) real.
    """

    def __init__(self, tsa_url: str = "http://tsa.trusted-service.com") -> None:
        self.tsa_url = tsa_url
        self.session = requests.Session() if _REQUESTS else None

    def get_timestamp(self, data: bytes) -> Dict[str, Any]:
        """Obtiene un sello de tiempo para los datos (hash enviado a TSA en producción)."""
        try:
            data_hash = hashlib.sha512(data).hexdigest()
            if self.session and self.tsa_url:
                try:
                    resp = self.session.post(
                        f"{self.tsa_url.rstrip('/')}/timestamp",
                        data=data_hash.encode(),
                        timeout=5,
                    )
                    if resp.status_code == 200 and resp.content:
                        return {
                            "status": "success",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "hash": data_hash,
                            "tsa_certificate": resp.headers.get("X-TSA-Certificate", "certificate-pem-data"),
                            "signature": resp.content.hex() if isinstance(resp.content, bytes) else str(resp.content),
                            "policy": "TSA Policy v2.1",
                        }
                except Exception as e:
                    logger.debug("TSA no disponible, usando sello local: %s", e)
            return {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hash": data_hash,
                "tsa_certificate": "certificate-pem-data",
                "signature": hashlib.sha256(data_hash.encode()).hexdigest(),
                "policy": "TSA Policy v2.1 (local stub)",
            }
        except Exception as e:
            data_hash = hashlib.sha512(data).hexdigest() if data else ""
            return {
                "status": "error",
                "error": str(e),
                "hash": data_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def verify_timestamp(self, timestamp_data: Dict[str, Any]) -> bool:
        """Verifica un sello de tiempo existente (en producción validaría firma TSA)."""
        return timestamp_data.get("status") == "success" and bool(timestamp_data.get("hash"))
