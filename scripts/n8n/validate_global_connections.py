"""
Valida conectividad HTTP básica hacia endpoints declarados en config/global_vars.json.

Uso (desde la raíz del repo):
  python scripts/n8n/validate_global_connections.py
  CASTUO_GLOBAL_VARS_PATH=config/global_vars.override.json python scripts/n8n/validate_global_connections.py

No envía secretos a stdout. Si un endpoint está vacío, se omite.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = ROOT / "config" / "global_vars.json"
TIMEOUT = 12


def _load_config() -> dict[str, Any]:
    p = os.environ.get("CASTUO_GLOBAL_VARS_PATH", "").strip()
    path = Path(p) if p else DEFAULT_PATH
    if not path.is_file():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        sys.exit(2)
    return json.loads(path.read_text(encoding="utf-8"))


def _check_url(label: str, url: str | None, method: str = "HEAD") -> list[str]:
    errs: list[str] = []
    if not url or not str(url).strip():
        return errs
    u = str(url).strip()
    if u.startswith("REPLACE_") or "example.com" in u:
        return errs
    ctx = ssl.create_default_context()
    req = urllib.request.Request(u, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            if resp.status >= 400:
                errs.append(f"{label}: HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code >= 400:
            errs.append(f"{label}: HTTP {e.code}")
    except Exception as e:
        errs.append(f"{label}: {e}")
    return errs


def main() -> int:
    cfg = _load_config()
    errors: list[str] = []

    ext = cfg.get("external_services") or {}
    pb = ext.get("power_bi") or {}
    errors += _check_url("power_bi.streaming", pb.get("streaming_endpoint"))
    errors += _check_url("power_bi.certificados", pb.get("certificados_endpoint"))

    g = ext.get("gaiachain") or {}
    gaia = g.get("api_endpoint")
    if gaia and str(gaia).strip():
        headers = {}
        key = (g.get("api_key") or "").strip()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        u = str(gaia).strip()
        req = urllib.request.Request(u, method="GET", headers=headers)
        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
                if resp.status >= 500:
                    errors.append(f"gaiachain.api: HTTP {resp.status}")
        except urllib.error.HTTPError as e:
            if e.code >= 500:
                errors.append(f"gaiachain.api: HTTP {e.code}")
        except Exception as e:
            errors.append(f"gaiachain.api: {e}")

    pdf = ext.get("pdf_generation") or {}
    errors += _check_url("pdf_generation", pdf.get("pdf_generation_service_url"))
    errors += _check_url("latex", pdf.get("latex_compilation_service"))

    if errors:
        print("Fallos:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK: sin errores en endpoints configurados (vacíos omitidos).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
