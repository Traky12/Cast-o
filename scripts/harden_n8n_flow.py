#!/usr/bin/env python3
"""
Harden / validate workflows de n8n contra el estándar TRL9 + Cripto-Fortaleza.

Enfoque:
- Auditar cumplimiento documental (nombres/huellas) y flujo lógico (grafo) para que:
  1) no haya salidas externas sin pasar por un paso Crypto PQC
  2) exista ruta Modo Isla (“tierra_firme_alert”)

Nota: este script NO reescribe conexiones complejas si el workflow no está ya
estructurado; se limita a validar y a anotar el JSON con un reporte.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlparse


ALLOWED_URL_HOSTS = {
    "localhost",
    "127.0.0.1",
    "api",
    "api:8000",
    "sabionda.local",
    "sabionda-kernel.local",
}


TRIGGER_NODE_TYPES = {
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.mqttTrigger",
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.cron",
}

# Canales internos donde el Sabionda Feedback Loop espera recibir telemetría de eficiencia.
FEEDBACK_TELEMETRY_TOPICS = {
    "sabionda/telemetry_anon",
    "sabionda/feedback",
}


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    code: str
    message: str
    evidence: Optional[dict] = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_node_name(node: Dict[str, Any]) -> str:
    return str(node.get("name") or "")


def get_node_type(node: Dict[str, Any]) -> str:
    return str(node.get("type") or "")


def node_code_text(node: Dict[str, Any]) -> str:
    params = node.get("parameters") or {}
    return str(params.get("jsCode") or params.get("js_code") or "")


def node_http_url(node: Dict[str, Any]) -> str:
    params = node.get("parameters") or {}
    url = params.get("url") or ""
    if not isinstance(url, str):
        return ""
    return url


def is_http_request(node: Dict[str, Any]) -> bool:
    return get_node_type(node) == "n8n-nodes-base.httpRequest"


def build_edges(connections: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Build directed edges from n8n connections graph.
    """
    edges: Dict[str, List[str]] = {}
    if not isinstance(connections, dict):
        return edges

    for src, payload in connections.items():
        if not isinstance(payload, dict):
            continue
        main = payload.get("main")
        if not isinstance(main, list):
            continue
        out: List[str] = []
        # main is typically: [ [ {node: "X", index:0, type:"main"} ], [ ... ] ]
        for branch in main:
            if not isinstance(branch, list):
                continue
            for edge in branch:
                if isinstance(edge, dict):
                    tgt = edge.get("node")
                    if isinstance(tgt, str) and tgt:
                        out.append(tgt)
        if out:
            edges[src] = out
    return edges


def reachable_from_sources(
    edges: Dict[str, List[str]],
    sources: Iterable[str],
    blocked: Set[str],
) -> Set[str]:
    visited: Set[str] = set()
    stack: List[str] = []
    for s in sources:
        if s in blocked:
            continue
        if s:
            stack.append(s)

    while stack:
        cur = stack.pop()
        if cur in visited or cur in blocked:
            continue
        visited.add(cur)
        for nxt in edges.get(cur, []):
            if nxt and nxt not in visited and nxt not in blocked:
                stack.append(nxt)
    return visited


def find_trigger_nodes(workflow: Dict[str, Any], nodes: List[Dict[str, Any]]) -> List[str]:
    triggers: List[str] = []
    for n in nodes:
        if get_node_type(n) in TRIGGER_NODE_TYPES:
            triggers.append(get_node_name(n))
    return [t for t in triggers if t]


def is_pqc_encryption_node(node: Dict[str, Any]) -> bool:
    name = get_node_name(node).lower()
    if "crypto" in name and ("pqc" in name or "encrypt" in name or "lacre" in name):
        return True

    if is_http_request(node):
        url = node_http_url(node).lower()
        if "/encrypt" in url or "encrypt" in url and ("pqc" in url or "kyber" in url or "ml-kem" in url):
            return True

    if get_node_type(node) == "n8n-nodes-base.code":
        code = node_code_text(node)
        if "crypto_pqc.encrypt" in code or "pqc" in code.lower() and "encrypt" in code.lower():
            return True

    return False


def _safe_urlparse(url: str) -> Optional[Any]:
    try:
        # n8n expressions may include `={{ ... }}`; treat as unknown host -> external by default
        if "{{" in url or "}}" in url:
            return None
        parsed = urlparse(url)
        return parsed
    except Exception:
        return None


def is_external_destination(node: Dict[str, Any], allowed_hosts: Set[str]) -> bool:
    if not is_http_request(node):
        return False
    url = node_http_url(node).strip()
    if not url:
        return False

    # Heurística: si el URL es expresión n8n, no podemos validar con exactitud -> considerarlo externo.
    if "{{" in url or "}}" in url:
        return True

    parsed = _safe_urlparse(url)
    if parsed is None:
        return True

    host = parsed.hostname or ""
    host = host.strip().lower()
    return host != "" and host not in allowed_hosts


def code_contains_isla(node: Dict[str, Any]) -> bool:
    code = node_code_text(node).lower()
    if "tierra_firme_alert" in code:
        return True
    return False


def code_contains_try_catch(node: Dict[str, Any]) -> bool:
    code = node_code_text(node).lower()
    return "try" in code and "catch" in code


def harden_validate(
    workflow: Dict[str, Any],
    allowed_hosts: Set[str],
) -> Tuple[List[Finding], Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = workflow.get("nodes") or []
    connections: Dict[str, Any] = workflow.get("connections") or {}
    edges = build_edges(connections)

    node_names = {get_node_name(n) for n in nodes if get_node_name(n)}
    encryption_nodes = {get_node_name(n) for n in nodes if is_pqc_encryption_node(n)}
    trigger_nodes = set(find_trigger_nodes(workflow, nodes))

    external_nodes: Set[str] = set()
    for n in nodes:
        nm = get_node_name(n)
        if not nm:
            continue
        if is_external_destination(n, allowed_hosts=allowed_hosts):
            external_nodes.add(nm)

    findings: List[Finding] = []

    if external_nodes and not encryption_nodes:
        findings.append(
            Finding(
                severity="error",
                code="NO_CRYPTO_PQC_NODE",
                message="Existen nodos HTTP externos pero no hay nodo de cifrado PQC identificable.",
                evidence={"external_nodes": sorted(external_nodes), "encryption_nodes": sorted(encryption_nodes)},
            )
        )

    # Modo Isla: buscamos patrón “tierra_firme_alert” o settings.errorWorkflow con pista.
    settings = workflow.get("settings") or {}
    error_workflow = settings.get("errorWorkflow") if isinstance(settings, dict) else None
    has_isla_code = any(code_contains_isla(n) for n in nodes if get_node_type(n) == "n8n-nodes-base.code")
    has_isla_errorwf = isinstance(error_workflow, str) and ("tierra" in error_workflow.lower() or "isla" in error_workflow.lower())

    if not has_isla_code and not has_isla_errorwf:
        findings.append(
            Finding(
                severity="error",
                code="NO_MODO_ISLA",
                message="No se detecta ruta de contingencia Modo Isla (tierra_firme_alert / errorWorkflow con pista).",
                evidence={"errorWorkflow": error_workflow},
            )
        )

    # Si hay encryption_nodes, verificamos que no existe camino desde triggers hacia nodos externos sin pasar por encryption_nodes.
    if external_nodes and encryption_nodes:
        blocked = set(encryption_nodes)
        reachable_without_crypto = reachable_from_sources(edges, trigger_nodes, blocked=blocked)
        # Si un externo es alcanzable en el grafo sin tocar crypto -> incumplimiento.
        reachable_externals = external_nodes.intersection(reachable_without_crypto)
        if reachable_externals:
            findings.append(
                Finding(
                    severity="error",
                    code="CRYPTO_NOT_ON_ALL_PATHS",
                    message="Hay nodos externos alcanzables desde triggers sin pasar por el nodo de cifrado PQC (seguridad por invisibilidad rota).",
                    evidence={
                        "reachable_externals_without_crypto": sorted(reachable_externals),
                        "encryption_nodes": sorted(encryption_nodes),
                    },
                )
            )

    # Try-catch como señal de cumplimiento mínimo
    has_try_catch_isla = any(
        code_contains_try_catch(n) and code_contains_isla(n)
        for n in nodes
        if get_node_type(n) == "n8n-nodes-base.code"
    )
    if not has_try_catch_isla:
        findings.append(
            Finding(
                severity="warning",
                code="TRY_CATCH_NOT_DETECTED",
                message="No se detectó un try-catch que invoque tierra_firme_alert en nodos code (heurística).",
            )
        )

    # Feedback Loop: telemetría de eficiencia hacia Sabionda (no debe detener el despliegue).
    has_feedback_telemetry = False
    for n in nodes:
        if get_node_type(n) == "n8n-nodes-base.mqtt":
            params = n.get("parameters") or {}
            topic = params.get("topic") or ""
            if isinstance(topic, str) and topic.strip().lower() in FEEDBACK_TELEMETRY_TOPICS:
                has_feedback_telemetry = True
                break
    if not has_feedback_telemetry:
        findings.append(
            Finding(
                severity="warning",
                code="MISSING_FEEDBACK_LOOP_TELEMETRY",
                message="No se detectó un nodo MQTT de Telemetría de Eficiencia hacia sabionda/telemetry_anon.",
            )
        )

    # Parametrización Zero-Leak v2 (env vars obligatorias): si el workflow contiene nodos esperados,
    # verificamos que usan CASTUO_*_URL y ZERO_LEAK_OUT_URL para evitar URLs hardcodeadas.
    zero_leak_nodes = {
        "Crypto_PQC_Encrypt_Lacre_CifradoReal": ("url", "CASTUO_ENCRYPT_URL"),
        "Crypto_PQC_Sign_Ciphertext": ("url", "CASTUO_PQC_SIGN_URL"),
        "ZeroLeak_Register_Audit_Event": ("url", "CASTUO_AUDIT_REGISTER_URL"),
        "ZeroLeak_Compliance_Audit_Latest": ("url", "CASTUO_COMPLIANCE_LATEST_URL"),
        "ZeroLeak_External_Send_CiphertextOnly": ("url", "ZERO_LEAK_OUT_URL"),
    }

    node_by_name = {get_node_name(n): n for n in nodes if get_node_name(n)}
    for node_name, (param_key, env_var) in zero_leak_nodes.items():
        n = node_by_name.get(node_name)
        if not n:
            continue  # no aplica si no es zero-leak v2
        params = n.get("parameters") or {}
        value = params.get(param_key)
        if not isinstance(value, str):
            findings.append(
                Finding(
                    severity="error",
                    code="ZERO_LEAK_ENV_NOT_FOUND",
                    message=f"Nodo '{node_name}' no tiene parámetro '{param_key}' string con $env.{env_var}.",
                )
            )
            continue
        if f"$env.{env_var}" not in value:
            findings.append(
                Finding(
                    severity="error",
                    code="ZERO_LEAK_URL_HARDCODED",
                    message=f"Nodo '{node_name}' no usa $env.{env_var} (posible URL hardcodeada).",
                    evidence={"current_value": value, "expected_env": env_var},
                )
            )

    # Auth Kyber + auditoría deben usar N8N_ADMIN_JWT
    if "Crypto_PQC_Sign_Ciphertext" in node_by_name:
        params = node_by_name["Crypto_PQC_Sign_Ciphertext"].get("parameters") or {}
        hdrs = (params.get("headerParameters") or {}).get("parameters") or []
        hdr_text = json.dumps(hdrs, ensure_ascii=False)
        if "$env.N8N_ADMIN_JWT" not in hdr_text:
            findings.append(
                Finding(
                    severity="error",
                    code="ZERO_LEAK_MISSING_ADMIN_JWT",
                    message="Firma PQC no referencia $env.N8N_ADMIN_JWT en headerParameters.",
                )
            )

    # Interoperabilidad educativa: no permitir hardcode de bootstrap public key ML-DSA.
    # (Base44 debe poder apuntar a un endpoint parametrizado/descubrible.)
    for n in nodes:
        ntype = get_node_type(n)
        params = n.get("parameters") or {}
        if ntype == "n8n-nodes-base.httpRequest":
            url = params.get("url")
            if isinstance(url, str) and "/public_key/ml_dsa" in url:
                if "$env." not in url:
                    findings.append(
                        Finding(
                            severity="error",
                            code="PUBLIC_KEY_ENDPOINT_HARDCODED",
                            message="Se detectó uso de /public_key/ml_dsa hardcodeado (requiere $env.*).",
                            evidence={"node": get_node_name(n) or "<unnamed>", "url": url},
                        )
                    )


    report: Dict[str, Any] = {
        "generated_at": _now_iso(),
        "trigger_nodes": sorted(trigger_nodes),
        "encryption_nodes": sorted(encryption_nodes),
        "external_nodes": sorted(external_nodes),
        "violations": [
            {"severity": f.severity, "code": f.code, "message": f.message, "evidence": f.evidence}
            for f in findings
            if f.severity == "error"
        ],
        "warnings": [
            {"code": f.code, "message": f.message} for f in findings if f.severity == "warning"
        ],
    }

    # Anotación para el workflow
    meta = workflow.get("meta") if isinstance(workflow.get("meta"), dict) else {}
    meta = dict(meta)
    meta["castuo_trl9_hardening"] = {
        "status": "ok" if not any(f.severity == "error" for f in findings) else "needs_fixes",
        "report": report,
    }
    workflow_out = dict(workflow)
    workflow_out["meta"] = meta
    return findings, workflow_out


def main() -> int:
    parser = argparse.ArgumentParser(description="Harden/validate n8n workflows vs TRL9 + Cripto-Fortaleza")
    parser.add_argument("--input", required=True, help="Ruta al JSON exportado del workflow de n8n")
    parser.add_argument("--output", default="", help="Ruta salida JSON (si vacío, usa *.hardened.json)")
    parser.add_argument("--fail-on-violation", action="store_true", default=True, help="Salir con código 1 si hay errores")
    parser.add_argument("--allowed-host", action="append", default=[], help="Hosts permitidos adicionales (puede repetirse)")

    args = parser.parse_args()

    input_path = args.input
    if not args.output:
        if input_path.lower().endswith(".json"):
            args.output = input_path[:-5] + ".hardened.json"
        else:
            args.output = input_path + ".hardened.json"

    allowed = set(ALLOWED_URL_HOSTS)
    for h in args.allowed_host:
        if h:
            allowed.add(h.strip().lower())

    try:
        wf = load_json(input_path)
        findings, wf_out = harden_validate(wf, allowed_hosts=allowed)
        dump_json(args.output, wf_out)

        errors = [f for f in findings if f.severity == "error"]
        warnings = [f for f in findings if f.severity == "warning"]

        print(f"[hardener] output: {args.output}")
        print(f"[hardener] errors: {len(errors)} warnings: {len(warnings)}")
        for f in findings:
            print(f"- {f.severity.upper()} {f.code}: {f.message}")

        if errors and args.fail_on_violation:
            return 1
        return 0
    except Exception as exc:
        print("[hardener] ERROR: Exception during validation", file=sys.stderr)
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

