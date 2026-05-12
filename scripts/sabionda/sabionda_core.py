"""
Puente Sabionda ↔ n8n alineado al repo: orquestador CASTÚO + Holobrain opcional.

- Orquestador: POST {N8N_WEBHOOK_BASE}/webhook/castuo-orchestrate con cuerpo tipo
  {"request_type": "...", "data": { ... }} y cabecera X-API-KEY si CASTUO_ORCHESTRATOR_API_KEY está definida en n8n.
- Holobrain: scripts/holo/holobrain_client.py (misma firma HMAC que el stub n8n).

No incluye TTS ni SDK holográfico ficticio: cablear voz/render vía HTTP cuando existan URLs reales.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

_HOLO_DIR = Path(__file__).resolve().parent.parent / "holo"
if str(_HOLO_DIR) not in sys.path:
    sys.path.insert(0, str(_HOLO_DIR))

from holobrain_client import HolobrainClient  # noqa: E402


def _analyze_stub(data: dict[str, Any]) -> dict[str, Any]:
    metrics = data.get("metrics") if isinstance(data.get("metrics"), dict) else {}
    return {
        "status": "operational",
        "metrics": metrics,
        "recommendations": ["Revisar caudal", "Ajustar pH si EC sube"],
        "confidence": 0.92,
        "processed_at": int(time.time()),
    }


class SabiondaBridge:
    def __init__(
        self,
        *,
        n8n_base_url: str | None = None,
        orchestrator_api_key: str | None = None,
        holobrain: HolobrainClient | None = None,
    ) -> None:
        self.n8n_base = (
            n8n_base_url or os.environ.get("N8N_WEBHOOK_BASE", "http://localhost:5678")
        ).rstrip("/")
        raw_key = orchestrator_api_key if orchestrator_api_key is not None else os.environ.get(
            "CASTUO_ORCHESTRATOR_API_KEY", ""
        )
        self.orchestrator_api_key = raw_key.strip() or None
        self._holobrain = holobrain

    def orchestrator_url(self) -> str:
        return f"{self.n8n_base}/webhook/castuo-orchestrate"

    def post_orchestrate(
        self,
        request_type: str,
        data: dict[str, Any],
        *,
        timeout: float = 120.0,
    ) -> requests.Response:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.orchestrator_api_key:
            headers["X-API-KEY"] = self.orchestrator_api_key
        body = {"request_type": request_type, "data": data}
        return requests.post(
            self.orchestrator_url(),
            json=body,
            headers=headers,
            timeout=timeout,
        )

    def process_pipeline(
        self,
        data: dict[str, Any],
        *,
        request_type: str = "sensor-data",
        timeout: float = 120.0,
        push_holobrain: bool = False,
    ) -> dict[str, Any]:
        analysis = _analyze_stub(data)
        orch = self.post_orchestrate(request_type, data, timeout=timeout)
        out: dict[str, Any] = {
            "ai_analysis": analysis,
            "n8n_status_code": orch.status_code,
            "n8n_ok": orch.ok,
        }
        try:
            out["n8n_body"] = orch.json()
        except json.JSONDecodeError:
            out["n8n_body"] = orch.text[:4000]

        if push_holobrain and self._holobrain is not None:
            m = data.get("metrics")
            if isinstance(m, dict):
                hr = self._holobrain.send(m)
                out["holobrain_status_code"] = hr.status_code
                try:
                    out["holobrain_body"] = hr.json()
                except json.JSONDecodeError:
                    out["holobrain_body"] = hr.text[:2000]

        return out


# Alias explícito para quien busque el nombre del borrador de producto
SabiondaAI = SabiondaBridge


def default_bridge() -> SabiondaBridge:
    hb = HolobrainClient()
    return SabiondaBridge(holobrain=hb)


if __name__ == "__main__":
    demo = {"metrics": {"plant_status": "optimal", "ph": 6.5, "ec": 1.8, "temperature": 24.5}}
    br = default_bridge()
    r = br.process_pipeline(demo, request_type="sensor-data", push_holobrain=False)
    print(json.dumps(r, indent=2, ensure_ascii=False))
