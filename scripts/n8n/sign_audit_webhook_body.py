#!/usr/bin/env python3
"""
Firma HMAC-SHA256 para POST /webhook/audit-trigger.
Debe coincidir con el nodo Code: firma del **objeto body JSON completo** (stableStringify).

Uso:
  set CASTUO_AUDIT_WEBHOOK_SECRET=...
  python scripts/n8n/sign_audit_webhook_body.py '{"kind":"ia","agente_id":"x","decision":"riego","confianza":82}'

Salida: hex (cabecera X-Castuo-Signature).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys


def stable_stringify(v: object) -> str:
    """Canonicalización alineada con el nodo n8n (JSON.stringify por primitivos)."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=True)
    if isinstance(v, list):
        return "[" + ",".join(stable_stringify(x) for x in v) + "]"
    if isinstance(v, dict):
        keys = sorted(v.keys())
        parts = [json.dumps(k, ensure_ascii=True) + ":" + stable_stringify(v[k]) for k in keys]
        return "{" + ",".join(parts) + "}"
    return json.dumps(str(v), ensure_ascii=True)


def main() -> int:
    secret = os.environ.get("CASTUO_AUDIT_WEBHOOK_SECRET", "").strip()
    if not secret:
        print("Definir CASTUO_AUDIT_WEBHOOK_SECRET", file=sys.stderr)
        return 1
    raw = sys.argv[1] if len(sys.argv) > 1 else "{}"
    body = json.loads(raw)
    payload = stable_stringify(body)
    sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    print(sig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
