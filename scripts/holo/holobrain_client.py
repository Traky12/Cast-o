"""
Cliente Holobrain → webhook n8n (stub: castuo-holobrain-webhook-stub.json).

La cadena firmada coincide con el nodo Code: JSON.stringify({ metrics, plant_status })
con plant_status normalizado en minúsculas (misma regla que en n8n).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

import requests


def normalized_plant_status(metrics: dict[str, Any]) -> str:
    return str(metrics.get("plant_status") or metrics.get("status") or "unknown").lower()


def holobrain_signing_string(metrics: dict[str, Any]) -> str:
    status = normalized_plant_status(metrics)
    return json.dumps({"metrics": metrics, "plant_status": status}, separators=(",", ":"))


def sign_holobrain_metrics(metrics: dict[str, Any], secret: str) -> str:
    msg = holobrain_signing_string(metrics).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


class HolobrainClient:
    def __init__(
        self,
        *,
        n8n_base_url: str | None = None,
        webhook_path: str = "holobrain-display",
        hmac_secret: str | None = None,
        basic_user: str | None = None,
        basic_pass: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (
            n8n_base_url or os.environ.get("N8N_WEBHOOK_BASE", "http://localhost:5678")
        ).rstrip("/")
        self.webhook_path = webhook_path.strip().strip("/")
        raw_secret = hmac_secret if hmac_secret is not None else os.environ.get(
            "HOLOBRAIN_HMAC_SECRET", ""
        )
        self.hmac_secret = raw_secret.strip() or None
        self.basic_user = (basic_user if basic_user is not None else os.environ.get("N8N_BASIC_AUTH_USER", "")).strip() or None
        self.basic_pass = (basic_pass if basic_pass is not None else os.environ.get("N8N_BASIC_AUTH_PASSWORD", "")).strip() or None
        self.timeout = timeout

    def webhook_url(self) -> str:
        return f"{self.base_url}/webhook/{self.webhook_path}"

    def send(self, metrics: dict[str, Any]) -> requests.Response:
        headers = {"Content-Type": "application/json"}
        if self.hmac_secret:
            headers["X-Holobrain-HMAC"] = sign_holobrain_metrics(metrics, self.hmac_secret)
        auth = (
            (self.basic_user, self.basic_pass)
            if self.basic_user and self.basic_pass
            else None
        )
        return requests.post(
            self.webhook_url(),
            json={"metrics": metrics},
            headers=headers,
            timeout=self.timeout,
            auth=auth,
        )
