"""
Hardening avanzado contra ataques específicos.

Implementa:
- WAF (Web Application Firewall) básico
- OWASP Top 10 mitigations
- Advanced logging y alerting
- Threat detection
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


# =========================================================================
# WAF - Web Application Firewall Básico
# =========================================================================

@dataclass
class ThreatPattern:
    """Patrón de amenaza detectado."""
    pattern_type: str  # sql_injection, xss, command_injection, etc
    pattern_regex: str
    severity: str  # critical, high, medium
    action: str  # block, log, alert


class WAFEngine:
    """Motor WAF para detección de ataques."""

    # Patrones de ataques comunes
    THREAT_PATTERNS = [
        # SQL Injection
        ThreatPattern(
            pattern_type="sql_injection",
            pattern_regex=r"(\bUNION\b|\bSELECT\b|\bDROP\b|\bINSERT\b|\bEXEC\b)",
            severity="critical",
            action="block",
        ),
        ThreatPattern(
            pattern_type="sql_injection",
            pattern_regex=r"(--|;|/\*|\*/)",
            severity="high",
            action="block",
        ),
        # XSS
        ThreatPattern(
            pattern_type="xss",
            pattern_regex=r"(<script|javascript:|onerror=|onclick=|onload=)",
            severity="high",
            action="block",
        ),
        # Command Injection
        ThreatPattern(
            pattern_type="command_injection",
            pattern_regex=r"(;|\||&|\$\(|`)",
            severity="critical",
            action="block",
        ),
        # Path Traversal
        ThreatPattern(
            pattern_type="path_traversal",
            pattern_regex=r"(\.\./|\.\.\\|%2e%2e)",
            severity="high",
            action="block",
        ),
        # XXE
        ThreatPattern(
            pattern_type="xxe",
            pattern_regex=r"(<!ENTITY|SYSTEM|PUBLIC)",
            severity="critical",
            action="block",
        ),
    ]

    def __init__(self) -> None:
        self.blocked_count = 0
        self.threat_log = []

    def analyze_request(
        self,
        request: Request,
        body: Optional[str] = None,
    ) -> bool:
        """
        Analiza request en busca de patrones de ataque.
        
        Returns:
            True si es seguro, False si detectó amenaza
        """
        # Analizar URL
        url = str(request.url)
        query_string = request.query_params

        threat_found = False

        # Escanear parámetros
        for key, value in query_string.items():
            if self._is_threat(str(value)):
                threat_found = True
                self._log_threat(
                    ip=request.client.host if request.client else "unknown",
                    endpoint=request.url.path,
                    param=key,
                    value=value,
                )
                self.blocked_count += 1
                break

        # Escanear body si está disponible
        if not threat_found and body:
            if self._is_threat(body):
                threat_found = True
                self._log_threat(
                    ip=request.client.host if request.client else "unknown",
                    endpoint=request.url.path,
                    param="body",
                    value=body[:100],  # Primeros 100 chars
                )
                self.blocked_count += 1

        return not threat_found

    def _is_threat(self, value: str) -> bool:
        """Detecta si un valor contiene patrón de amenaza."""
        for pattern in self.THREAT_PATTERNS:
            if re.search(pattern.pattern_regex, value, re.IGNORECASE):
                return True
        return False

    def _log_threat(
        self,
        ip: str,
        endpoint: str,
        param: str,
        value: str,
    ) -> None:
        """Registra amenaza detectada."""
        threat_record = {
            "timestamp": json.dumps({"_timestamp": ""}, default=str),
            "ip": ip,
            "endpoint": endpoint,
            "parameter": param,
            "value_hash": hashlib.sha256(value.encode()).hexdigest(),
        }
        self.threat_log.append(threat_record)

        logger.warning(
            f"WAF: Threat detected from {ip} on {endpoint} "
            f"parameter={param}"
        )

    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas del WAF."""
        return {
            "total_blocked": self.blocked_count,
            "threats_logged": len(self.threat_log),
            "top_ips": self._get_top_ips(),
        }

    def _get_top_ips(self) -> list[tuple[str, int]]:
        """Obtiene IPs con más amenazas detectadas."""
        from collections import Counter

        ips = [t["ip"] for t in self.threat_log]
        counts = Counter(ips)
        return counts.most_common(5)


# =========================================================================
# OWASP TOP 10 MITIGATIONS
# =========================================================================

class OWASPMitigation:
    """Mitigaciones para OWASP Top 10."""

    MITIGATIONS = {
        "A01_Broken_Access_Control": {
            "description": "Validar autorización en cada endpoint",
            "implementation": "require_roles() en todos los endpoints",
            "status": "implemented",
        },
        "A02_Cryptographic_Failures": {
            "description": "Usar criptografía fuerte (SHA-256, TLS 1.3+)",
            "implementation": "HSTS headers + JWT con HS256",
            "status": "implemented",
        },
        "A03_Injection": {
            "description": "Validación y sanitización de input",
            "implementation": "InputValidator.sanitize_string() + WAF",
            "status": "implemented",
        },
        "A04_Insecure_Design": {
            "description": "Diseño seguro desde inicio (secure by default)",
            "implementation": "SecretValidator en startup + PDCA",
            "status": "implemented",
        },
        "A05_Security_Misconfiguration": {
            "description": "Configuración segura por defecto",
            "implementation": "Security headers + CORS config by env",
            "status": "implemented",
        },
        "A06_Vulnerable_Components": {
            "description": "Mantener librerías actualizadas",
            "implementation": "pip audit + dependabot en CI",
            "status": "monitoring",
        },
        "A07_Authentication_Failures": {
            "description": "Autenticación robusta",
            "implementation": "JWT validation + MFA support",
            "status": "implemented",
        },
        "A08_Software_Data_Integrity_Failures": {
            "description": "Integridad de código y datos",
            "implementation": "Code signing + blockchain evidence",
            "status": "implemented",
        },
        "A09_Logging_Monitoring_Failures": {
            "description": "Logging y monitoreo completo",
            "implementation": "SecurityAudit logging + metrics",
            "status": "implemented",
        },
        "A10_SSRF": {
            "description": "Validar URLs antes de request",
            "implementation": "URL validation in outbound requests",
            "status": "implemented",
        },
    }

    @classmethod
    def get_summary(cls) -> dict[str, Any]:
        """Obtiene resumen de mitigaciones OWASP."""
        implemented = sum(
            1
            for m in cls.MITIGATIONS.values()
            if m["status"] == "implemented"
        )
        monitoring = sum(
            1
            for m in cls.MITIGATIONS.values()
            if m["status"] == "monitoring"
        )

        return {
            "total_vulnerabilities": len(cls.MITIGATIONS),
            "implemented": implemented,
            "monitoring": monitoring,
            "coverage": f"{(implemented / len(cls.MITIGATIONS)) * 100:.1f}%",
            "details": cls.MITIGATIONS,
        }


# =========================================================================
# THREAT DETECTION & ALERTING
# =========================================================================

class ThreatDetector:
    """Detector de amenazas en tiempo real."""

    def __init__(self) -> None:
        self.waf = WAFEngine()
        self.alerts: list[dict[str, Any]] = []
        self.suspicious_count_by_ip: dict[str, int] = {}

    async def analyze_request(self, request: Request) -> None:
        """Analiza request en busca de amenazas."""
        ip = request.client.host if request.client else "unknown"

        # Detectar patrones de ataque
        body = ""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                body = body.decode("utf-8", errors="ignore")
        except Exception:
            pass

        is_safe = self.waf.analyze_request(request, body)

        if not is_safe:
            # Incrementar contador de requests sospechosos
            self.suspicious_count_by_ip[ip] = (
                self.suspicious_count_by_ip.get(ip, 0) + 1
            )

            # Alerta si excede threshold
            if self.suspicious_count_by_ip[ip] > 5:
                self._trigger_alert(
                    severity="HIGH",
                    ip=ip,
                    message=f"IP {ip} ha generado {self.suspicious_count_by_ip[ip]} requests sospechosos",
                )

    def _trigger_alert(
        self,
        severity: str,
        ip: str,
        message: str,
    ) -> None:
        """Dispara alerta de seguridad."""
        alert = {
            "severity": severity,
            "ip": ip,
            "message": message,
            "timestamp": json.dumps({"_timestamp": ""}, default=str),
        }
        self.alerts.append(alert)
        logger.critical(f"SECURITY ALERT [{severity}]: {message}")

    def get_threat_summary(self) -> dict[str, Any]:
        """Obtiene resumen de amenazas."""
        return {
            "total_alerts": len(self.alerts),
            "critical_alerts": sum(
                1 for a in self.alerts if a["severity"] == "CRITICAL"
            ),
            "suspicious_ips": dict(
                sorted(self.suspicious_count_by_ip.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "waf_stats": self.waf.get_stats(),
        }


# =========================================================================
# SINGLETON INSTANCES
# =========================================================================

_waf_engine = WAFEngine()
_threat_detector = ThreatDetector()


def get_waf_engine() -> WAFEngine:
    """Obtiene motor WAF global."""
    return _waf_engine


def get_threat_detector() -> ThreatDetector:
    """Obtiene detector de amenazas global."""
    return _threat_detector
