"""
Framework de Mejora Continua, Excelencia y Six Sigma para CASTUO-SYSTEM

Implementa:
- PDCA (Plan-Do-Check-Act)
- DMAIC (Define-Measure-Analyze-Improve-Control)
- Análisis crítico de vulnerabilidades
- KPIs y métricas de calidad
- Auditoría de procesos
"""

import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# =========================================================================
# 1. FRAMEWORK PDCA - MEJORA CONTINUA CÍCLICA
# =========================================================================

class PDCAPhase(str, Enum):
    """Fases del ciclo PDCA."""
    PLAN = "plan"  # Planificar mejoras
    DO = "do"      # Implementar cambios
    CHECK = "check"  # Verificar resultados
    ACT = "act"    # Actuar basado en resultados


@dataclass
class PDCARecord:
    """Registro de una iteración PDCA."""
    cycle_id: str
    phase: PDCAPhase
    title: str
    description: str
    metrics_before: dict[str, Any]
    metrics_after: Optional[dict[str, Any]] = None
    timestamp: str = None
    status: str = "in_progress"  # in_progress, completed, failed

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class PDCAManager:
    """Gestor de ciclos PDCA."""

    def __init__(self) -> None:
        self.cycles: dict[str, list[PDCARecord]] = defaultdict(list)
        self.current_cycle_id: Optional[str] = None

    def start_cycle(self, cycle_id: str) -> None:
        """Inicia un nuevo ciclo PDCA."""
        self.current_cycle_id = cycle_id
        logger.info(f"PDCA Cycle started: {cycle_id}")

    def log_phase(
        self,
        phase: PDCAPhase,
        title: str,
        description: str,
        metrics_before: dict[str, Any],
    ) -> None:
        """Registra una fase PDCA."""
        if not self.current_cycle_id:
            raise ValueError("No active PDCA cycle")

        record = PDCARecord(
            cycle_id=self.current_cycle_id,
            phase=phase,
            title=title,
            description=description,
            metrics_before=metrics_before,
        )
        self.cycles[self.current_cycle_id].append(record)
        logger.info(f"PDCA {phase.value}: {title}")

    def complete_phase(
        self,
        phase: PDCAPhase,
        metrics_after: dict[str, Any],
    ) -> None:
        """Completa una fase con métricas finales."""
        if not self.current_cycle_id:
            return

        records = self.cycles[self.current_cycle_id]
        for record in reversed(records):
            if record.phase == phase and record.status == "in_progress":
                record.metrics_after = metrics_after
                record.status = "completed"
                self._log_improvement(record)
                break

    def _log_improvement(self, record: PDCARecord) -> None:
        """Registra mejora observada."""
        if not record.metrics_after:
            return

        improvements = {}
        for key, before_val in record.metrics_before.items():
            after_val = record.metrics_after.get(key)
            if after_val is not None and isinstance(before_val, (int, float)):
                if before_val != 0:
                    percent_change = ((after_val - before_val) / before_val) * 100
                    improvements[key] = f"{percent_change:+.1f}%"

        if improvements:
            logger.info(f"Improvements detected: {improvements}")

    def get_cycle_summary(self, cycle_id: str) -> dict[str, Any]:
        """Obtiene resumen de un ciclo."""
        records = self.cycles.get(cycle_id, [])
        return {
            "cycle_id": cycle_id,
            "total_phases": len(records),
            "completed": sum(1 for r in records if r.status == "completed"),
            "records": [asdict(r) for r in records],
        }


# =========================================================================
# 2. FRAMEWORK DMAIC - SEIS SIGMA
# =========================================================================

class DMIOPhase(str, Enum):
    """Fases del DMAIC."""
    DEFINE = "define"
    MEASURE = "measure"
    ANALYZE = "analyze"
    IMPROVE = "improve"
    CONTROL = "control"


@dataclass
class SixSigmaProject:
    """Proyecto Six Sigma."""
    project_id: str
    title: str
    problem_statement: str
    goal: str
    process: str
    owner: str
    baseline_sigma: float = 3.0  # Defecto actual nivel sigma
    target_sigma: float = 6.0    # Objetivo (99.99966%)
    created_at: str = None
    updated_at: str = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class DMICAnalysis:
    """Análisis DMAIC."""
    project_id: str
    phase: DMIOPhase
    findings: list[str]
    defect_rate: float  # Porcentaje de defectos
    sigma_level: float  # Nivel sigma calculado
    root_causes: Optional[list[str]] = None
    improvement_actions: Optional[list[str]] = None
    timestamp: str = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class SixSigmaManager:
    """Gestor de proyectos Six Sigma."""

    # Conversión defect rate → Sigma level
    SIGMA_CONVERSION = {
        308537: 2.0,  # 30.85% defect rate
        66807: 3.0,   # 6.68% defect rate
        6210: 4.0,    # 0.62% defect rate
        233: 5.0,     # 0.023% defect rate
        3.4: 6.0,     # 0.0034% defect rate (Six Sigma)
    }

    def __init__(self) -> None:
        self.projects: dict[str, SixSigmaProject] = {}
        self.analyses: dict[str, list[DMICAnalysis]] = defaultdict(list)

    def create_project(
        self,
        project_id: str,
        title: str,
        problem_statement: str,
        goal: str,
        process: str,
        owner: str,
    ) -> SixSigmaProject:
        """Crea un proyecto Six Sigma."""
        project = SixSigmaProject(
            project_id=project_id,
            title=title,
            problem_statement=problem_statement,
            goal=goal,
            process=process,
            owner=owner,
        )
        self.projects[project_id] = project
        logger.info(f"Six Sigma project created: {project_id}")
        return project

    def log_analysis(
        self,
        project_id: str,
        phase: DMIOPhase,
        findings: list[str],
        defect_rate: float,
    ) -> DMICAnalysis:
        """Registra análisis de una fase."""
        sigma_level = self.calculate_sigma_level(defect_rate)
        
        analysis = DMICAnalysis(
            project_id=project_id,
            phase=phase,
            findings=findings,
            defect_rate=defect_rate,
            sigma_level=sigma_level,
        )
        self.analyses[project_id].append(analysis)
        logger.info(f"DMAIC {phase.value}: Sigma level {sigma_level:.2f}")
        return analysis

    def calculate_sigma_level(self, defect_rate: float) -> float:
        """Calcula nivel sigma basado en defect rate (porcentaje, ej: 0.61 = 0.61%)."""
        # Convertir porcentaje a fracción para comparar contra DPMO/1_000_000
        defect_fraction = defect_rate / 100.0
        for defects, sigma in sorted(self.SIGMA_CONVERSION.items(), reverse=True):
            if defect_fraction >= (defects / 1_000_000):
                return sigma
        return 6.0  # Por debajo del umbral Six Sigma → excelencia máxima

    def get_project_summary(self, project_id: str) -> dict[str, Any]:
        """Obtiene resumen de proyecto."""
        project = self.projects.get(project_id)
        analyses = self.analyses.get(project_id, [])

        if not project:
            return {}

        return {
            "project_id": project_id,
            "title": project.title,
            "owner": project.owner,
            "baseline_sigma": project.baseline_sigma,
            "target_sigma": project.target_sigma,
            "current_sigma": analyses[-1].sigma_level if analyses else project.baseline_sigma,
            "analyses": [
                {
                    "phase": a.phase.value,
                    "sigma_level": a.sigma_level,
                    "defect_rate": f"{a.defect_rate:.4f}%",
                }
                for a in analyses
            ],
        }


# =========================================================================
# 3. ANÁLISIS CRÍTICO DE VULNERABILIDADES
# =========================================================================

class VulnerabilitySeverity(str, Enum):
    """Severidad de vulnerabilidades."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Vulnerability:
    """Vulnerabilidad encontrada."""
    vuln_id: str
    category: str  # e.g., "authentication", "injection", "crypto"
    title: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: float  # 0-10
    affected_component: str
    remediation: str
    status: str = "open"  # open, in_progress, resolved
    created_at: str = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()


class VulnerabilityScanner:
    """Scanner de vulnerabilidades críticas."""

    CRITICAL_CHECKS = {
        "hardcoded_secrets": {
            "description": "Secretos hardcodeados en código",
            "check": lambda code: any(
                secret in code
                for secret in ["password=", "secret=", "api_key="]
            ),
        },
        "sql_injection": {
            "description": "Queries SQL sin parameterizar",
            "check": lambda code: "f\"SELECT" in code or "f'SELECT" in code,
        },
        "missing_auth": {
            "description": "Endpoints sin autenticación",
            "check": lambda code: "@router.post" in code
            and "authorize_token" not in code,
        },
        "no_input_validation": {
            "description": "Input sin validación",
            "check": lambda code: "query: str" in code and "sanitize" not in code,
        },
        "weak_crypto": {
            "description": "Criptografía débil (MD5, SHA1)",
            "check": lambda code: "md5" in code.lower()
            or "sha1" in code.lower(),
        },
        "insecure_deserialization": {
            "description": "Deserialización insegura (pickle)",
            "check": lambda code: "pickle.loads" in code,
        },
    }

    def __init__(self) -> None:
        self.vulnerabilities: list[Vulnerability] = []

    def scan_code(self, code: str, component: str) -> list[Vulnerability]:
        """Escanea código en busca de vulnerabilidades."""
        found = []

        for check_id, check_config in self.CRITICAL_CHECKS.items():
            try:
                if check_config["check"](code):
                    vuln = Vulnerability(
                        vuln_id=f"{component}_{check_id}",
                        category=check_id,
                        title=check_id.replace("_", " ").title(),
                        description=check_config["description"],
                        severity=VulnerabilitySeverity.HIGH,
                        cvss_score=7.5,
                        affected_component=component,
                        remediation=self._get_remediation(check_id),
                    )
                    found.append(vuln)
                    self.vulnerabilities.append(vuln)
            except Exception:
                pass

        return found

    @staticmethod
    def _get_remediation(check_id: str) -> str:
        """Obtiene remediación para cada tipo de vulnerabilidad."""
        remediations = {
            "hardcoded_secrets": "Mover secretos a variables de entorno o Vault",
            "sql_injection": "Usar parameterized queries / SQLAlchemy ORM",
            "missing_auth": "Agregar authorize_token() en endpoint",
            "no_input_validation": "Usar InputValidator.sanitize_string()",
            "weak_crypto": "Usar SHA-256 o mejor (bcrypt, Argon2)",
            "insecure_deserialization": "Usar JSON en lugar de pickle",
        }
        return remediations.get(check_id, "Ver documentación de seguridad")

    def get_summary(self) -> dict[str, Any]:
        """Obtiene resumen de vulnerabilidades."""
        by_severity = defaultdict(list)
        for vuln in self.vulnerabilities:
            by_severity[vuln.severity.value].append(vuln.title)

        return {
            "total": len(self.vulnerabilities),
            "by_severity": dict(by_severity),
            "critical": len(by_severity[VulnerabilitySeverity.CRITICAL.value]),
            "high": len(by_severity[VulnerabilitySeverity.HIGH.value]),
            "medium": len(by_severity[VulnerabilitySeverity.MEDIUM.value]),
        }


# =========================================================================
# 4. KPIs Y MÉTRICAS DE EXCELENCIA
# =========================================================================

@dataclass
class ExcellenceMetrics:
    """Métricas de excelencia operativa."""
    availability: float  # % uptime
    response_time_p95: float  # ms
    error_rate: float  # %
    security_score: float  # 0-100
    test_coverage: float  # %
    code_quality: float  # 0-100 (basado en cyclomatic complexity)
    deployment_frequency: int  # days
    mean_time_to_recovery: float  # hours
    customer_satisfaction: float  # 1-5
    timestamp: str = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def overall_score(self) -> float:
        """Calcula score general de excelencia (0-100)."""
        weights = {
            "availability": 0.20,
            "security_score": 0.25,
            "test_coverage": 0.20,
            "code_quality": 0.15,
            "error_rate": 0.10,  # Invertido (100 - error_rate)
            "customer_satisfaction": 0.10,  # Escala 1-5 → 0-100
        }

        score = (
            self.availability * weights["availability"]
            + self.security_score * weights["security_score"]
            + self.test_coverage * weights["test_coverage"]
            + self.code_quality * weights["code_quality"]
            + (100 - self.error_rate) * weights["error_rate"]
            + (self.customer_satisfaction * 20) * weights["customer_satisfaction"]
        )

        return min(100, max(0, score))

    def level_of_excellence(self) -> str:
        """Clasifica nivel de excelencia."""
        score = self.overall_score()
        if score >= 95:
            return "🏆 WORLD CLASS (95-100)"
        elif score >= 90:
            return "⭐️ EXCELLENT (90-94)"
        elif score >= 80:
            return "✅ GOOD (80-89)"
        elif score >= 70:
            return "⚠️ ACCEPTABLE (70-79)"
        else:
            return "🔴 NEEDS IMPROVEMENT (<70)"


class MetricsCollector:
    """Recolector de métricas de excelencia."""

    def __init__(self) -> None:
        self.metrics_history: list[ExcellenceMetrics] = []

    def record_metrics(self, metrics: ExcellenceMetrics) -> None:
        """Registra métricas de excelencia."""
        self.metrics_history.append(metrics)
        logger.info(f"Excellence level: {metrics.level_of_excellence()}")
        logger.info(f"Overall score: {metrics.overall_score():.1f}/100")

    def get_trend(self, metric_name: str, last_n: int = 10) -> list[float]:
        """Obtiene tendencia de métrica."""
        recent = self.metrics_history[-last_n:]
        return [getattr(m, metric_name) for m in recent]

    def get_latest_report(self) -> dict[str, Any]:
        """Obtiene reporte más reciente."""
        if not self.metrics_history:
            return {}

        latest = self.metrics_history[-1]
        return {
            "timestamp": latest.timestamp,
            "availability": f"{latest.availability:.2f}%",
            "response_time_p95": f"{latest.response_time_p95:.1f}ms",
            "error_rate": f"{latest.error_rate:.3f}%",
            "security_score": f"{latest.security_score:.1f}/100",
            "test_coverage": f"{latest.test_coverage:.1f}%",
            "code_quality": f"{latest.code_quality:.1f}/100",
            "overall_score": f"{latest.overall_score():.1f}/100",
            "level": latest.level_of_excellence(),
        }


# =========================================================================
# 5. SINGLETON MANAGERS
# =========================================================================

_pdca_manager = PDCAManager()
_dmaic_manager = SixSigmaManager()
_vulnerability_scanner = VulnerabilityScanner()
_metrics_collector = MetricsCollector()


def get_pdca_manager() -> PDCAManager:
    """Obtiene gestor PDCA global."""
    return _pdca_manager


def get_dmaic_manager() -> SixSigmaManager:
    """Obtiene gestor Six Sigma global."""
    return _dmaic_manager


def get_vulnerability_scanner() -> VulnerabilityScanner:
    """Obtiene scanner de vulnerabilidades."""
    return _vulnerability_scanner


def get_metrics_collector() -> MetricsCollector:
    """Obtiene recolector de métricas."""
    return _metrics_collector
