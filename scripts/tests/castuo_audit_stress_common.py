"""Helpers compartidos: stableStringify (como n8n) + cuerpos tipo audit-trigger."""
from __future__ import annotations

import hashlib
import hmac
import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
_SIGN_PATH = ROOT / "scripts" / "n8n" / "sign_audit_webhook_body.py"


def _load_stable_stringify():
    spec = importlib.util.spec_from_file_location("castuo_sign_audit", _SIGN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {_SIGN_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.stable_stringify


stable_stringify = _load_stable_stringify()


def build_audit_like_body(core_index: int) -> dict[str, Any]:
    sid = f"SECTOR-{core_index:03d}"
    return {
        "kind": "ia",
        "agente_id": f"CORE-{core_index:03d}",
        "actor": f"CORE-{core_index:03d}",
        "confianza": 72 + (core_index % 28),
        "contexto": f"STRESS_POC core={core_index} tipo=OT_FORCE_SIM",
        "decision": "[CRITICAL] Umbral demo stress-test",
        "details": {"core_index": core_index, "sensor": "EC", "val": round(2.5 + (core_index % 10) * 0.1, 2)},
        "event": "STRESS_DIAGNOSTICO",
        "status": "CRITICAL",
        "tags": ["#ia-decision", f"#sector-{sid}"],
    }


def sign_body_hmac_sha256(secret: bytes, body: dict[str, Any]) -> str:
    payload = stable_stringify(body)
    return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
