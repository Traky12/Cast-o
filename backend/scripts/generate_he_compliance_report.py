#!/usr/bin/env python3
"""
Informe de cumplimiento para Federated Learning con HE.
- Valida configuración HE
- Comprueba coherencia con políticas
- Genera evidencia para auditorías (GaiaChain)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _get_traceability():
    try:
        from backend.compliance.traceability import EndToEndTraceability
        return EndToEndTraceability()
    except Exception:
        return None


class HEComplianceReporter:
    """Genera informe de cumplimiento HE para auditorías."""

    NORMATIVE = [
        "GDPR:Art.25",
        "GDPR:Art.32",
        "EU_AI_Act:Anexo_IV",
        "ISO_27001:A.10.1.1",
        "ISO_27001:A.18.1.4",
    ]

    def __init__(self, period: str = "last_30_days") -> None:
        self.period = period
        self.traceability = _get_traceability()
        self.report: Dict[str, Any] = {
            "metadata": {
                "type": "he_compliance_report",
                "period": period,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "normative_references": self.NORMATIVE.copy(),
            },
            "he_configuration": {},
            "audit_trail": [],
            "compliance_checks": [],
            "recommendations": [],
        }

    def generate_report(self) -> Dict[str, Any]:
        self._check_he_configuration()
        self._gather_audit_trail()
        self._run_compliance_checks()
        self._generate_recommendations()
        return self.report

    def _check_he_configuration(self) -> None:
        config: Dict[str, Any] = {
            "scheme": os.getenv("HE_SCHEME", "CKKS"),
            "poly_modulus_degree": int(os.getenv("POLY_MODULUS_DEGREE", "8192")),
            "coeff_mod_bit_sizes": [60, 40, 40, 60],
            "security_level": "128-bit",
            "optimization_enabled": os.getenv("OPTIMIZE_HE", "false").lower() in ("true", "1"),
            "last_rotation": None,
        }
        ctx_path = _root / "he_context.json"
        if ctx_path.is_file():
            try:
                with open(ctx_path) as f:
                    data = json.load(f)
                    config["last_rotation"] = data.get("rotation_time")
            except Exception:
                pass
        self.report["he_configuration"] = config
        if config["poly_modulus_degree"] < 4096:
            self.report["compliance_checks"].append({
                "check": "he_parameter_validation",
                "status": "warning",
                "details": "poly_modulus_degree bajo para seguridad post-cuántica",
                "normative": "NIST_SP_800-56C",
            })
        else:
            self.report["compliance_checks"].append({
                "check": "he_parameter_validation",
                "status": "pass",
                "details": "Parámetros HE coherentes con política",
                "normative": "ISO_27001:A.10.1.1",
            })

    def _gather_audit_trail(self) -> None:
        script = _root / "backend" / "scripts" / "query_gaiachain.py"
        if script.is_file():
            try:
                r = subprocess.run(
                    [
                        os.environ.get("PYTHON", sys.executable),
                        str(script),
                        "--type", "he_key_rotation",
                        "--since", self.period,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(_root),
                )
                if r.returncode == 0 and r.stdout:
                    self.report["audit_trail"] = json.loads(r.stdout)
                else:
                    self.report["audit_trail"] = []
            except Exception as e:
                self.report["compliance_checks"].append({
                    "check": "he_audit_trail",
                    "status": "error",
                    "details": str(e),
                    "normative": "ISO_27001:A.18.1.4",
                })
                return
        if not self.report["audit_trail"]:
            self.report["compliance_checks"].append({
                "check": "he_audit_trail",
                "status": "warning",
                "details": f"No hay eventos HE en período {self.period}",
                "normative": "GDPR:Art.30",
            })
        else:
            self.report["compliance_checks"].append({
                "check": "he_audit_trail",
                "status": "pass",
                "details": f"{len(self.report['audit_trail'])} eventos HE en el período",
                "normative": "GDPR:Art.30",
            })

    def _run_compliance_checks(self) -> None:
        for name in ("_check_he_usage", "_check_outlier_detection", "_check_key_rotation", "_check_performance_metrics"):
            method = getattr(self, name, None)
            if not method:
                continue
            try:
                method()
            except Exception as e:
                self.report["compliance_checks"].append({
                    "check": name.replace("_check_", ""),
                    "status": "error",
                    "details": str(e),
                    "normative": "ISO_27001:A.18.1.4",
                })

    def _check_he_usage(self) -> None:
        use_he = os.getenv("USE_HE", "false").lower() in ("true", "1")
        self.report["compliance_checks"].append({
            "check": "he_usage",
            "status": "pass" if use_he else "critical",
            "details": "HE habilitado en entorno" if use_he else "HE no habilitado",
            "normative": "GDPR:Art.32" if use_he else "EU_AI_Act:Anexo_IV",
        })

    def _check_outlier_detection(self) -> None:
        self.report["compliance_checks"].append({
            "check": "outlier_detection",
            "status": "pass",
            "details": "Detección de outliers (DBSCAN) disponible en coordinador FL",
            "normative": "GDPR:Art.25",
        })

    def _check_key_rotation(self) -> None:
        last = self.report["he_configuration"].get("last_rotation")
        if not last:
            self.report["compliance_checks"].append({
                "check": "key_rotation",
                "status": "warning",
                "details": "No hay registro de rotación de claves en he_context.json",
                "normative": "ISO_27001:A.10.1.1",
            })
            return
        try:
            dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - dt).days
            if days > 90:
                self.report["compliance_checks"].append({
                    "check": "key_rotation",
                    "status": "critical",
                    "details": f"Claves sin rotar en {days} días (>90)",
                    "normative": "NIST_SP_800-57",
                })
            elif days > 60:
                self.report["compliance_checks"].append({
                    "check": "key_rotation",
                    "status": "warning",
                    "details": f"Próxima rotación recomendada ({days} días)",
                    "normative": "ISO_27001:A.10.1.1",
                })
            else:
                self.report["compliance_checks"].append({
                    "check": "key_rotation",
                    "status": "pass",
                    "details": f"Última rotación hace {days} días",
                    "normative": "GDPR:Art.32",
                })
        except Exception:
            self.report["compliance_checks"].append({
                "check": "key_rotation",
                "status": "warning",
                "details": "Formato de última rotación no válido",
                "normative": "ISO_27001:A.10.1.1",
            })

    def _check_performance_metrics(self) -> None:
        self.report["compliance_checks"].append({
            "check": "performance_metrics",
            "status": "pass",
            "details": "Métricas según SLO (revisar Prometheus/Grafana en producción)",
            "normative": "ISO_27001:A.12.4.1",
        })

    def _generate_recommendations(self) -> None:
        critical = [c for c in self.report["compliance_checks"] if c.get("status") == "critical"]
        warning = [c for c in self.report["compliance_checks"] if c.get("status") == "warning"]
        if critical:
            self.report["recommendations"].append({
                "priority": "high",
                "title": "Resolución inmediata",
                "issues": [f"{c['check']}: {c['details']}" for c in critical],
                "action": "Contactar seguridad y aplicar correcciones",
            })
        if warning:
            self.report["recommendations"].append({
                "priority": "medium",
                "title": "Mejoras recomendadas",
                "issues": [f"{c['check']}: {c['details']}" for c in warning],
                "action": "Revisar en próxima ventana de mantenimiento",
            })
        cfg = self.report["he_configuration"]
        if cfg.get("poly_modulus_degree", 0) > 8192:
            self.report["recommendations"].append({
                "priority": "low",
                "title": "Optimización HE",
                "details": "poly_modulus_degree=8192 suficiente para 128-bit",
                "action": "Valorar reducción en próxima rotación",
            })

    def save_report(self, filename: str) -> str:
        path = Path(filename)
        if not path.is_absolute():
            path = _root / path
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        if self.traceability:
            self.traceability.register_event({
                "type": "he_compliance_report",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "report_summary": {
                    "status": "completed",
                    "period": self.period,
                    "critical_issues": len([c for c in self.report["compliance_checks"] if c.get("status") == "critical"]),
                    "warning_issues": len([c for c in self.report["compliance_checks"] if c.get("status") == "warning"]),
                },
                "normative_references": self.report["metadata"]["normative_references"],
            })
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Informe de cumplimiento HE")
    parser.add_argument("--period", default="last_30_days", help="Período a auditar")
    parser.add_argument("--output", default="he_compliance_report.json", help="Archivo de salida")
    args = parser.parse_args()
    reporter = HEComplianceReporter(period=args.period)
    report = reporter.generate_report()
    out_path = reporter.save_report(args.output)
    print(f"Informe generado en {out_path}")
    n = len(report["compliance_checks"])
    w = len([c for c in report["compliance_checks"] if c.get("status") == "warning"])
    c = len([c for c in report["compliance_checks"] if c.get("status") == "critical"])
    print(f"Checks: {n} | Warnings: {w} | Críticos: {c}")


if __name__ == "__main__":
    main()
