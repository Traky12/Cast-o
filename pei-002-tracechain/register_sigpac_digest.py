#!/usr/bin/env python3
"""
PEI-002: digest SHA-256 del informe PEI-001 y:
  - payload Castuo (tokenId, action, status, details, compliance) -> POST /api/audit/register-event
  - envelope TraceChain (event_type, digest sha256:, metadata sin geometrias) -> archivo o stub HTTP
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict


def _digest_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _cumple_via_counts(results: list) -> Dict[str, int]:
    out: Dict[str, int] = defaultdict(int)
    for r in results:
        if r.get("cumple"):
            via = str(r.get("cumple_via") or "literal")
            out[via] += 1
        else:
            out["no"] += 1
    return dict(out)


def build_sigpac_envelope(report_path: Path) -> Dict[str, Any]:
    """
    Envelope para integradores / stub PEI-002: sin geometrias (RGPD / minimizacion).
    Coherente con summary del informe PEI-001 (cumple / no_cumple / usos_problematicos).
    """
    raw = json.loads(report_path.read_text(encoding="utf-8"))
    summary = raw.get("summary") or {}
    results = raw.get("results") or []
    dg = _digest_file(report_path)
    mapping_path = raw.get("mapping_path")
    ts = raw.get("generated_utc")
    try:
        from datetime import datetime

        if ts:
            t_unix = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
        else:
            t_unix = int(time.time())
    except (ValueError, TypeError):
        t_unix = int(time.time())

    total = int(summary.get("total_parcelas") or len(results))
    cumplen = int(summary.get("cumple") or sum(1 for r in results if r.get("cumple")))

    return {
        "event_type": "sigpac_validation",
        "digest": f"sha256:{dg}",
        "timestamp": t_unix,
        "parcelas": total,
        "cumplen": cumplen,
        "metadata": {
            "mapping_path": mapping_path,
            "usos_problematicos": summary.get("usos_problematicos") or {},
            "summary": {
                "total_parcelas": total,
                "cumple": summary.get("cumple"),
                "no_cumple": summary.get("no_cumple"),
                "porcentaje_cumplimiento": summary.get("porcentaje_cumplimiento"),
            },
            "cumple_via_counts": _cumple_via_counts(results),
            "report_generated_utc": ts,
            "report_generated_utc_unix": t_unix,
        },
    }


def build_event_payload(report_path: Path, token_id: int) -> Dict[str, Any]:
    raw = json.loads(report_path.read_text(encoding="utf-8"))
    summary = raw.get("summary") or {}
    dg = _digest_file(report_path)
    return {
        "tokenId": token_id,
        "action": "sigpac_pei001_report_sealed",
        "status": "completed" if summary.get("no_cumple", 1) == 0 else "completed_with_findings",
        "details": {
            "report_path": str(report_path.resolve()),
            "report_sha256": dg,
            "generated_utc": raw.get("generated_utc"),
            "mapping_path": raw.get("mapping_path"),
            "total_parcelas": summary.get("total_parcelas"),
            "cumple": summary.get("cumple"),
            "no_cumple": summary.get("no_cumple"),
            "porcentaje_cumplimiento": summary.get("porcentaje_cumplimiento"),
            "cumple_via_counts": _cumple_via_counts(raw.get("results") or []),
        },
        "compliance": {
            "source": "pei-002-tracechain",
            "protocol_note": "Evidencia primaria = fichero JSON en disco; cadena = ancla digest.",
        },
    }


def post_audit_api(payload: Dict[str, Any]) -> Dict[str, Any]:
    base = (os.environ.get("CASTUO_AUDIT_API_URL") or "").strip()
    token = (os.environ.get("CASTUO_AUDIT_API_TOKEN") or "").strip()
    if not base or not token:
        return {"skipped": True, "reason": "CASTUO_AUDIT_API_URL y CASTUO_AUDIT_API_TOKEN requeridos"}

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    return _urlopen_json(req)


def post_envelope_stub(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST opcional al stub PEI-002 (PEI002_ENVELOPE_POST_URL). Prefiere requests si existe."""
    base = (os.environ.get("PEI002_ENVELOPE_POST_URL") or "").strip()
    token = (os.environ.get("PEI002_STUB_BEARER_TOKEN") or "").strip()
    if not base or not token:
        return {"skipped": True, "reason": "PEI002_ENVELOPE_POST_URL y PEI002_STUB_BEARER_TOKEN requeridos"}
    try:
        import requests

        r = requests.post(
            base,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=45,
        )
        try:
            parsed = r.json() if r.text else {}
        except json.JSONDecodeError:
            parsed = {"raw": r.text}
        if r.ok:
            return {"skipped": False, "ok": True, "http_status": r.status_code, "response": parsed}
        return {
            "skipped": False,
            "ok": False,
            "http_status": r.status_code,
            "error": parsed if isinstance(parsed, dict) else str(parsed),
        }
    except ImportError:
        pass
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    return _urlopen_json(req)


def _urlopen_json(req: urllib.request.Request) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return {"skipped": False, "ok": True, "response": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return {
            "skipped": False,
            "ok": False,
            "http_status": exc.code,
            "error": err_body or str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        return {"skipped": False, "ok": False, "error": str(exc)}


def main() -> int:
    p = argparse.ArgumentParser(description="PEI-002 digest + payloads audit / envelope")
    p.add_argument(
        "--report",
        "--report-path",
        type=Path,
        dest="report",
        required=True,
        help="JSON generado por validate_sigpac.py",
    )
    p.add_argument(
        "--out-payload",
        type=Path,
        default=None,
        help="Escribir envelope TraceChain (JSON) sin geometrias",
    )
    p.add_argument("--post", action="store_true", help="POST payload Castuo a CASTUO_AUDIT_API_URL")
    p.add_argument(
        "--post-envelope",
        action="store_true",
        help="POST envelope a PEI002_ENVELOPE_POST_URL (stub laboratorio)",
    )
    p.add_argument(
        "--no-stdout-payload",
        action="store_true",
        help="No imprimir payload Castuo en stdout (CI: pasos POST posteriores)",
    )
    args = p.parse_args()
    rp = args.report.resolve()
    if not rp.is_file():
        print(f"No existe informe: {rp}", file=sys.stderr)
        return 2
    try:
        tid = int(os.environ.get("CASTUO_AUDIT_TOKEN_ID") or "1")
    except ValueError:
        tid = 1

    castuo_payload = build_event_payload(rp, tid)
    envelope = build_sigpac_envelope(rp)

    if not args.no_stdout_payload:
        print(json.dumps(castuo_payload, indent=2, ensure_ascii=False))

    if args.out_payload:
        args.out_payload.parent.mkdir(parents=True, exist_ok=True)
        args.out_payload.write_text(
            json.dumps(envelope, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Envelope escrito: {args.out_payload.resolve()}", file=sys.stderr)

    if args.post:
        res = post_audit_api(castuo_payload)
        print(json.dumps(res, indent=2, ensure_ascii=False), file=sys.stderr)
        if res.get("ok") is False:
            return 3

    if args.post_envelope:
        res = post_envelope_stub(envelope)
        print(json.dumps(res, indent=2, ensure_ascii=False), file=sys.stderr)
        if res.get("ok") is False:
            return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
