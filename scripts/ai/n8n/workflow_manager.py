#!/usr/bin/env python3
"""
Utilidades CLI sobre workflows JSON del repo (carpeta `n8n/workflows`).
Validación estructural mínima; ejecución vía webhook solo si defines URL (n8n en marcha).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def workflows_dir() -> Path:
    override = os.environ.get("CASTUO_N8N_WORKFLOWS_DIR", "").strip()
    if override:
        return Path(override)
    return _repo_root() / "n8n" / "workflows"


def list_workflow_stems() -> List[str]:
    d = workflows_dir()
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def validate_workflow(stem: str) -> Dict[str, Any]:
    path = workflows_dir() / f"{stem}.json"
    if not path.is_file():
        return {"error": f"No existe {path}"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"error": f"JSON inválido: {e}"}
    if not isinstance(data.get("nodes"), list) or len(data["nodes"]) == 0:
        return {"error": "Falta lista nodes no vacía (formato n8n export)"}
    return {"status": "ok", "nodes": len(data["nodes"]), "path": str(path)}


def trigger_webhook(base_url: str, stem: str, payload: Dict[str, Any], timeout: float = 15.0) -> Dict[str, Any]:
    """POST a {base}/{stem} — ajustar base al path real del webhook en n8n."""
    url = base_url.rstrip("/") + "/" + stem.lstrip("/")
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        out: Dict[str, Any] = {"http_status": r.status_code, "url": url}
        try:
            out["body"] = r.json()
        except Exception:
            out["body_text"] = r.text[:2000]
        return out
    except requests.RequestException as e:
        return {"error": str(e), "url": url}


def main() -> None:
    p = argparse.ArgumentParser(description="Listar / validar workflows n8n del repo; webhook opcional.")
    p.add_argument("--list", action="store_true", help="Listar stems .json")
    p.add_argument("--validate", metavar="STEM", help="Validar workflow por nombre sin .json")
    p.add_argument("--webhook-base", metavar="URL", help="Base URL de webhooks (ej. https://n8n.ejemplo/webhook)")
    p.add_argument("--trigger", metavar="STEM", help="POST JSON a webhook STEM")
    p.add_argument("--payload", default="{}", help='JSON para --trigger (default "{}")')
    args = p.parse_args()

    if args.list:
        for s in list_workflow_stems():
            print(s)
        return
    if args.validate:
        print(json.dumps(validate_workflow(args.validate), indent=2))
        return
    if args.trigger:
        base = args.webhook_base or os.environ.get("CASTUO_N8N_WEBHOOK_BASE", "").strip()
        if not base:
            p.error("--webhook-base o variable CASTUO_N8N_WEBHOOK_BASE requeridos con --trigger")
        payload = json.loads(args.payload)
        print(json.dumps(trigger_webhook(base, args.trigger, payload), indent=2))
        return
    p.print_help()


if __name__ == "__main__":
    main()
