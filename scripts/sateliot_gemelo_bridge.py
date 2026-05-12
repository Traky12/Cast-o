#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gateway NTN → GEMelo → CASTÚO: ingestión hacia el SoT del gemelo; CASTÚO consume por pull.
Sin dependencia de `requests` (urllib); rutas y URL solo por entorno. El servicio GEMelo debe implementar el contrato HTTP acordado.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("castuo.sateliot_gemelo_bridge")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def holographic_envelope(sensor_data: Any) -> str:
    """
    Sobre de integridad sobre el territorio de datos: canonical JSON + HMAC-SHA256 si hay secreto;
    si no, solo digest (lab). No sustituye cifrado autenticado de aplicación ni claves gestionadas en HSM.
    """
    raw = _canonical_json(sensor_data)
    secret = os.environ.get("GEMELO_ENVELOPE_SECRET", "").strip().encode()
    if secret:
        mac = hmac.new(secret, raw, hashlib.sha256).hexdigest()
    else:
        mac = hashlib.sha256(raw).hexdigest()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"{b64}.{mac}"


def _http_json(
    method: str,
    url: str,
    body: Optional[Mapping[str, Any]] = None,
    timeout_s: float = 30.0,
) -> Dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = resp.read().decode("utf-8")
            if not payload.strip():
                return {}
            return json.loads(payload)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e


class SateliotGemeloGateway:
    """Sateliot (u origen NTN) publica solo hacia GEMelo; CASTÚO obtiene estado vía pull por gemelo_id."""

    def __init__(self) -> None:
        base = os.environ.get("GEMELO_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
        self.gemelo_base = base
        self.ingest_path = os.environ.get("GEMELO_INGEST_PATH", "/agents/gemelo/ingest").strip()
        self.castuo_path_tpl = os.environ.get(
            "GEMELO_CASTUO_PATH_TEMPLATE",
            "/agents/gemelo/{gemelo_id}/castuo",
        ).strip()
        self.source_tag = os.environ.get("CASTUO_NTN_SOURCE", "sateliot_sband").strip()
        self._timeout = float(os.environ.get("GEMELO_HTTP_TIMEOUT", "30"))

    def holographic_encrypt(self, sensor_data: Any) -> str:
        return holographic_envelope(sensor_data)

    def sateliot_to_gemelo(self, sensor_data: Any) -> str:
        payload: Dict[str, Any] = {
            "source": self.source_tag,
            "encrypted": self.holographic_encrypt(sensor_data),
            "timestamp": _utc_iso(),
        }
        extra = os.environ.get("GEMELO_INGEST_EXTRA_JSON", "").strip()
        if extra:
            payload["extra"] = json.loads(extra)
        url = f"{self.gemelo_base}{self.ingest_path}"
        out = _http_json("POST", url, payload, timeout_s=self._timeout)
        for key in ("gemelo_id", "id", "gemeloId"):
            if key in out and out[key]:
                return str(out[key])
        raise KeyError(f"respuesta sin gemelo_id (claves: {list(out.keys())})")

    def gemelo_to_castuo(self, gemelo_id: str) -> Dict[str, Any]:
        path = self.castuo_path_tpl.format(gemelo_id=gemelo_id)
        url = f"{self.gemelo_base}{path}"
        got = _http_json("GET", url, None, timeout_s=self._timeout)
        if not isinstance(got, dict):
            raise TypeError("respuesta CASTÚO no es objeto JSON")
        return got


def _load_sensor_payload() -> Any:
    raw = os.environ.get("CASTUO_SENSOR_JSON", "").strip()
    if raw:
        return json.loads(raw)
    stdin = sys.stdin.read().strip()
    if not stdin:
        raise ValueError("CASTUO_SENSOR_JSON vacío y stdin vacío")
    return json.loads(stdin)


def main() -> int:
    p = argparse.ArgumentParser(description="Gateway Sateliot/NTN → GEMelo → CASTÚO (pull)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest", help="POST sensor → GEMelo, imprime gemelo_id")
    pull_p = sub.add_parser("pull", help="GET vista CASTÚO para gemelo_id")
    pull_p.add_argument("gemelo_id")
    args = p.parse_args()
    gw = SateliotGemeloGateway()
    try:
        if args.cmd == "ingest":
            data = _load_sensor_payload()
            gid = gw.sateliot_to_gemelo(data)
            print(gid)
            return 0
        if args.cmd == "pull":
            print(json.dumps(gw.gemelo_to_castuo(args.gemelo_id), ensure_ascii=False, indent=2))
            return 0
    except Exception as e:
        logger.error("%s", e)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
