#!/usr/bin/env python3
"""
Genera informes de auditoría:
- Verificación de cifrado y cadena
- Cobertura normativa
- Eventos críticos y recomendaciones
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from backend.compliance.immutable_traceability import ImmutableTraceability
    from backend.security.end_to_end_encryption import EndToEndEncryption
except ImportError as e:
    print("Error importando módulos:", e, file=sys.stderr)
    sys.exit(1)


def _analyze_normative_coverage(chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    coverage: Dict[str, int] = {}
    for block in chain:
        event = block.get("event", block)
        for norm in event.get("normative_references", []):
            coverage[norm] = coverage.get(norm, 0) + 1
    return {
        "total_normatives": len(coverage),
        "coverage_details": coverage,
        "most_frequent": max(coverage.items(), key=lambda x: x[1]) if coverage else None,
    }


def _find_critical_events(chain: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for block in chain:
        event = block.get("event", block)
        if event.get("severity") in ("critical", "high"):
            out.append(block)
        elif event.get("type") in ("fl_round_error", "action_error", "compliance_violation"):
            out.append(block)
    return out


def _analyze_encryption(chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    encrypted = 0
    algorithms = set()
    for block in chain:
        event = block.get("event", block)
        if any(k.endswith("_encrypted") for k in event.keys()):
            encrypted += 1
        algo = event.get("encryption_metadata", {}).get("algorithm") or event.get("integrity", {}).get("algorithm")
        if algo:
            algorithms.add(str(algo))
    return {
        "total_encrypted_events": encrypted,
        "encryption_percentage": (encrypted / len(chain) * 100) if chain else 0,
        "algorithms_used": list(algorithms),
    }


def _generate_recommendations(chain: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    critical = _find_critical_events(chain)
    if critical:
        recs.append({
            "priority": "high",
            "title": "Investigar eventos críticos",
            "details": f"{len(critical)} eventos críticos detectados",
            "action": "Revisar logs y tomar acciones correctivas",
        })
    enc = _analyze_encryption(chain)
    if chain and enc["encryption_percentage"] < 90:
        recs.append({
            "priority": "medium",
            "title": "Aumentar uso de cifrado",
            "details": f"Solo {enc['encryption_percentage']:.1f}% de eventos cifrados",
            "action": "Revisar configuración de campos sensibles",
        })
    cov = _analyze_normative_coverage(chain)
    if cov["total_normatives"] < 5 and chain:
        recs.append({
            "priority": "low",
            "title": "Ampliar cobertura normativa",
            "details": f"Solo {cov['total_normatives']} normativas diferentes cubiertas",
            "action": "Revisar mapeo de normativas en eventos",
        })
    return recs


def generate_audit_report(period_days: int = 30) -> Dict[str, Any]:
    encryption = EndToEndEncryption()
    traceability = ImmutableTraceability(encryption)
    since = datetime.now(timezone.utc) - timedelta(days=period_days)
    chain = traceability.get_audit_trail(since=since)
    return {
        "metadata": {
            "period": f"last_{period_days}_days",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_events": len(chain),
            "chain_integrity": traceability.verify_chain(),
        },
        "normative_coverage": _analyze_normative_coverage(chain),
        "critical_events": _find_critical_events(chain),
        "encryption_stats": _analyze_encryption(chain),
        "recommendations": _generate_recommendations(chain),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generador de informes de auditoría")
    parser.add_argument("--period", type=int, default=30, help="Días a auditar")
    parser.add_argument("--output", default="audit_report.json", help="Archivo de salida")
    args = parser.parse_args()
    report = generate_audit_report(args.period)
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = _root / out_path
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("Informe generado en", out_path)
    print("Resumen:", report["metadata"]["total_events"], "eventos analizados")
    print("  Críticos:", len(report["critical_events"]))
    print("  Normativas cubiertas:", report["normative_coverage"]["total_normatives"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
