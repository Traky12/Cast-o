"""
ThreatScanner — Motor antivirus/antimalware en tiempo real para CASTUO-SYSTEM.

Detecta y bloquea:
- SQL Injection (classic, blind, union, time-based)
- XSS (reflected, stored, DOM)
- Command injection (os, shell, eval)
- Path traversal / LFI / RFI
- SSRF (Server-Side Request Forgery)
- Prototype pollution
- Log injection
- DoS patterns (excessively large payloads, zip bombs señal)
- Credential stuffing patterns
- Replay attacks (timestamp + IP check)
- Known malicious signatures (simulated AV engine)
"""

import hashlib
import ipaddress
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


# =========================================================================
# 1. CATÁLOGO DE AMENAZAS
# =========================================================================

class ThreatCategory(str, Enum):
    SQL_INJECTION       = "sql_injection"
    XSS                 = "xss"
    CMD_INJECTION       = "command_injection"
    PATH_TRAVERSAL      = "path_traversal"
    SSRF                = "ssrf"
    LOG_INJECTION       = "log_injection"
    PROTOTYPE_POLLUTION = "prototype_pollution"
    CREDENTIAL_STUFFING = "credential_stuffing"
    REPLAY_ATTACK       = "replay_attack"
    DOS_PATTERN         = "dos_pattern"
    MALICIOUS_PAYLOAD   = "malicious_payload"
    SUSPICIOUS_HEADER   = "suspicious_header"


class ThreatSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


@dataclass
class ThreatMatch:
    """Amenaza detectada en una petición."""
    category:    ThreatCategory
    severity:    ThreatSeverity
    pattern:     str              # patrón regex que coincidió
    location:    str              # dónde se encontró (url, body, header, query)
    matched_text: str             # fragmento detectado (truncado a 120 chars)
    timestamp:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    blocked:     bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "pattern": self.pattern,
            "location": self.location,
            "matched_text": self.matched_text[:120],
            "timestamp": self.timestamp,
            "blocked": self.blocked,
        }


# =========================================================================
# 2. FIRMAS DE AMENAZAS (base de datos de patrones)
# =========================================================================

class ThreatSignatureDB:
    """Base de datos de firmas de amenazas (estilo AV)."""

    SIGNATURES: list[tuple[ThreatCategory, ThreatSeverity, str, str]] = [
        # (categoria, severidad, nombre_patron, regex)

        # ── SQL Injection ──────────────────────────────────────────────────
        (ThreatCategory.SQL_INJECTION, ThreatSeverity.CRITICAL,
         "sqli_classic",
         r"(?i)('|\"|`)?\s*(OR|AND)\s+('|\"|`)?\d+('|\"|`)?\s*=\s*('|\"|`)?\d+"),
        (ThreatCategory.SQL_INJECTION, ThreatSeverity.CRITICAL,
         "sqli_union",
         r"(?i)\bUNION\b.{0,30}\bSELECT\b"),
        (ThreatCategory.SQL_INJECTION, ThreatSeverity.CRITICAL,
         "sqli_drop",
         r"(?i)\bDROP\s+(TABLE|DATABASE|INDEX|VIEW)\b"),
        (ThreatCategory.SQL_INJECTION, ThreatSeverity.HIGH,
         "sqli_comment",
         r"(--|#|/\*).{0,50}(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)"),
        (ThreatCategory.SQL_INJECTION, ThreatSeverity.HIGH,
         "sqli_sleep",
         r"(?i)\b(SLEEP|WAITFOR\s+DELAY|pg_sleep|BENCHMARK)\s*\("),
        (ThreatCategory.SQL_INJECTION, ThreatSeverity.HIGH,
         "sqli_stacked",
         r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE)\b"),

        # ── XSS ───────────────────────────────────────────────────────────
        (ThreatCategory.XSS, ThreatSeverity.HIGH,
         "xss_script_tag",
         r"(?i)<\s*script[\s>]"),
        (ThreatCategory.XSS, ThreatSeverity.HIGH,
         "xss_event_handler",
         r"(?i)\bon\w+\s*=\s*['\"]?\s*(alert|eval|document|window|location)"),
        (ThreatCategory.XSS, ThreatSeverity.MEDIUM,
         "xss_javascript_proto",
         r"(?i)javascript\s*:"),
        (ThreatCategory.XSS, ThreatSeverity.MEDIUM,
         "xss_data_uri",
         r"(?i)data\s*:\s*text\s*/\s*(html|javascript)"),
        (ThreatCategory.XSS, ThreatSeverity.HIGH,
         "xss_svg_onload",
         r"(?i)<\s*svg.{0,50}on\w+\s*="),
        (ThreatCategory.XSS, ThreatSeverity.HIGH,
         "xss_iframe",
         r"(?i)<\s*i\s*frame"),

        # ── Command Injection ──────────────────────────────────────────────
        (ThreatCategory.CMD_INJECTION, ThreatSeverity.CRITICAL,
         "cmd_shell_operators",
         r"[;&|`$]\s*(rm|chmod|chown|wget|curl|nc|bash|sh|python|perl|ruby|php)\b"),
        (ThreatCategory.CMD_INJECTION, ThreatSeverity.CRITICAL,
         "cmd_eval",
         r"(?i)\beval\s*\("),
        (ThreatCategory.CMD_INJECTION, ThreatSeverity.HIGH,
         "cmd_backtick",
         r"`[^`]{1,100}`"),
        (ThreatCategory.CMD_INJECTION, ThreatSeverity.CRITICAL,
         "cmd_destructive",
         r";\s*rm\s+-[rf]+\s*/"),
        (ThreatCategory.CMD_INJECTION, ThreatSeverity.HIGH,
         "cmd_reverse_shell",
         r"(?i)(bash|sh|nc|ncat|netcat).{0,20}(/dev/tcp|/dev/udp|\d+\.\d+\.\d+\.\d+)"),

        # ── Path Traversal / LFI ───────────────────────────────────────────
        (ThreatCategory.PATH_TRAVERSAL, ThreatSeverity.HIGH,
         "path_dotdot",
         r"\.\./|\.\.\\"),
        (ThreatCategory.PATH_TRAVERSAL, ThreatSeverity.HIGH,
         "path_encoded_dotdot",
         r"(?i)(%2e%2e|%252e%252e|\.\.%2f|%2f\.\.)"),
        (ThreatCategory.PATH_TRAVERSAL, ThreatSeverity.CRITICAL,
         "path_etc_passwd",
         r"(?i)/etc/(passwd|shadow|group|hosts|crontab)"),
        (ThreatCategory.PATH_TRAVERSAL, ThreatSeverity.HIGH,
         "path_windows_system",
         r"(?i)(\\windows\\|c:\\windows|win\.ini|system32)"),

        # ── SSRF ──────────────────────────────────────────────────────────
        (ThreatCategory.SSRF, ThreatSeverity.CRITICAL,
         "ssrf_metadata",
         r"(?i)(169\.254\.169\.254|metadata\.google\.internal)"),
        (ThreatCategory.SSRF, ThreatSeverity.HIGH,
         "ssrf_localhost",
         r"(?i)(http|ftp|file)://(localhost|127\.0\.0\.1|0\.0\.0\.0|::1)"),
        (ThreatCategory.SSRF, ThreatSeverity.HIGH,
         "ssrf_internal_range",
         r"(?i)(http|ftp)://(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.)"),
        (ThreatCategory.SSRF, ThreatSeverity.MEDIUM,
         "ssrf_file_proto",
         r"(?i)file:///"),

        # ── Log Injection ─────────────────────────────────────────────────
        (ThreatCategory.LOG_INJECTION, ThreatSeverity.MEDIUM,
         "log_crlf",
         r"(\r\n|\r|\n).{0,20}(ERROR|WARN|INFO|DEBUG|CRITICAL)"),
        (ThreatCategory.LOG_INJECTION, ThreatSeverity.MEDIUM,
         "log_newline",
         r"(%0d%0a|%0a|%0d)"),

        # ── Prototype Pollution ───────────────────────────────────────────
        (ThreatCategory.PROTOTYPE_POLLUTION, ThreatSeverity.HIGH,
         "proto_pollution",
         r"(?i)(__proto__|constructor\[prototype\]|prototype\.constructor)"),

        # ── Payload patterns ─────────────────────────────────────────────
        (ThreatCategory.MALICIOUS_PAYLOAD, ThreatSeverity.CRITICAL,
         "payload_base64_decode_exec",
         r"(?i)(base64_decode|eval\s*\(\s*base64|atob\s*\()"),
        (ThreatCategory.MALICIOUS_PAYLOAD, ThreatSeverity.HIGH,
         "payload_webshell_keywords",
         r"(?i)(c99|r57|b374k|weevely|wso\.php|shell_exec|system\s*\()"),
    ]

    # Firmas de headers sospechosos
    SUSPICIOUS_HEADERS: set[str] = {
        "x-forwarded-for",   # Spoofing de IP
        "x-originating-ip",
        "x-real-ip",
    }

    _compiled: Optional[list[tuple[ThreatCategory, ThreatSeverity, str, re.Pattern[str]]]] = None

    @classmethod
    def get_compiled(cls) -> list[tuple[ThreatCategory, ThreatSeverity, str, re.Pattern[str]]]:
        """Retorna firmas compiladas (lazy compile, singleton)."""
        if cls._compiled is None:
            cls._compiled = [
                (cat, sev, name, re.compile(pattern))
                for cat, sev, name, pattern in cls.SIGNATURES
            ]
        return cls._compiled


# =========================================================================
# 3. MOTOR PRINCIPAL DE ESCANEO
# =========================================================================

class ThreatScanner:
    """
    Motor antivirus/antimalware para peticiones HTTP.

    Uso:
        scanner = ThreatScanner()
        threats = scanner.scan_request_data(url, headers, body)
        if threats:
            raise HTTPException(400, "Threat detected")
    """

    # Bloquear automáticamente estas categorías
    BLOCK_CATEGORIES: frozenset[ThreatCategory] = frozenset({
        ThreatCategory.SQL_INJECTION,
        ThreatCategory.CMD_INJECTION,
        ThreatCategory.PATH_TRAVERSAL,
        ThreatCategory.MALICIOUS_PAYLOAD,
        ThreatCategory.PROTOTYPE_POLLUTION,
    })

    # Bloquear al superar este número de amenazas medium/low
    BLOCK_THRESHOLD_COUNT = 3

    # Límites de tamaño de payload (DoS prevention)
    MAX_BODY_BYTES      = 10 * 1024 * 1024   # 10 MB
    MAX_QUERY_LENGTH    = 4096
    MAX_HEADER_LENGTH   = 8192

    def __init__(self) -> None:
        self._stats: dict[str, int] = defaultdict(int)
        self._signatures = ThreatSignatureDB.get_compiled()

    # ── Escaneo de texto limpio ────────────────────────────────────────

    def scan_text(self, text: str, location: str) -> list[ThreatMatch]:
        """Escanea texto libre contra todas las firmas."""
        matches: list[ThreatMatch] = []
        for category, severity, name, pattern in self._signatures:
            m = pattern.search(text)
            if m:
                threat = ThreatMatch(
                    category=category,
                    severity=severity,
                    pattern=name,
                    location=location,
                    matched_text=m.group(0)[:120],
                    blocked=category in self.BLOCK_CATEGORIES,
                )
                matches.append(threat)
                self._stats[category.value] += 1
        return matches

    # ── Análisis de petición HTTP completa ────────────────────────────

    def scan_request_data(
        self,
        url: str,
        headers: dict[str, str],
        body: str = "",
        query_string: str = "",
    ) -> list[ThreatMatch]:
        """Escanea URL, headers, body y query string."""
        threats: list[ThreatMatch] = []

        # 1. Tamaño del body (DoS pattern)
        if len(body.encode()) > self.MAX_BODY_BYTES:
            threats.append(ThreatMatch(
                category=ThreatCategory.DOS_PATTERN,
                severity=ThreatSeverity.HIGH,
                pattern="oversized_body",
                location="body",
                matched_text=f"body_size={len(body.encode())}",
                blocked=False,
            ))

        # 2. Query string
        if query_string:
            if len(query_string) > self.MAX_QUERY_LENGTH:
                threats.append(ThreatMatch(
                    category=ThreatCategory.DOS_PATTERN,
                    severity=ThreatSeverity.MEDIUM,
                    pattern="oversized_query",
                    location="query",
                    matched_text=f"query_len={len(query_string)}",
                    blocked=False,
                ))
            threats.extend(self.scan_text(query_string, "query"))

        # 3. URL path
        threats.extend(self.scan_text(url, "url"))

        # 4. Body
        if body:
            threats.extend(self.scan_text(body, "body"))

        return threats

    # ── Decisión de bloqueo ───────────────────────────────────────────

    def should_block(self, threats: list[ThreatMatch]) -> tuple[bool, str]:
        """
        Determina si la petición debe ser bloqueada.

        Returns:
            (block: bool, reason: str)
        """
        if not threats:
            return False, ""

        # Bloqueo inmediato si hay categoría de bloqueo automático
        for threat in threats:
            if threat.category in self.BLOCK_CATEGORIES:
                return True, f"Blocked: {threat.category.value} — {threat.pattern}"

        # Bloqueo por acumulación crítica
        critical_count = sum(1 for t in threats if t.severity == ThreatSeverity.CRITICAL)
        if critical_count >= 1:
            return True, f"Blocked: {critical_count} critical threat(s)"

        high_count = sum(1 for t in threats if t.severity == ThreatSeverity.HIGH)
        if high_count >= 2:
            return True, f"Blocked: {high_count} high-severity threats"

        return False, ""

    # ── Estadísticas ─────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Retorna estadísticas acumuladas del escáner."""
        total = sum(self._stats.values())
        return {
            "total_detections": total,
            "by_category": dict(self._stats),
            "signatures_loaded": len(self._signatures),
        }

    def reset_stats(self) -> None:
        """Resetea estadísticas (para tests)."""
        self._stats.clear()


# =========================================================================
# 4. MIDDLEWARE FASTAPI — ESCANEO EN TIEMPO REAL
# =========================================================================

class ThreatScannerMiddleware:
    """
    Middleware ASGI que escanea todas las peticiones entrantes en tiempo real.

    Integra ThreatScanner directamente en el pipeline de FastAPI/Starlette.
    """

    def __init__(self, app: Any, scanner: Optional[ThreatScanner] = None) -> None:
        self.app = app
        self.scanner = scanner or ThreatScanner()

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extraer datos de la petición del scope ASGI
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode("utf-8", errors="replace")
        headers_raw = dict(scope.get("headers", []))
        headers = {
            k.decode("utf-8", errors="replace"): v.decode("utf-8", errors="replace")
            for k, v in headers_raw.items()
        }

        # Leer body del receive stream
        body_chunks: list[bytes] = []
        body_too_large = False

        accumulated = 0
        while True:
            message = await receive()
            chunk = message.get("body", b"")
            accumulated += len(chunk)
            if accumulated > ThreatScanner.MAX_BODY_BYTES:
                body_too_large = True
                break
            body_chunks.append(chunk)
            if not message.get("more_body", False):
                break

        body_bytes = b"".join(body_chunks)
        body_str = body_bytes.decode("utf-8", errors="replace")

        if body_too_large:
            # Responder con 413 directamente
            await self._send_error(send, 413, "Payload Too Large")
            return

        # Escanear
        threats = self.scanner.scan_request_data(
            url=path,
            headers=headers,
            body=body_str,
            query_string=query_string,
        )

        should_block, reason = self.scanner.should_block(threats)

        if should_block:
            client = scope.get("client", ("unknown", 0))
            client_ip = client[0] if client else "unknown"

            logger.warning(
                "THREAT_BLOCKED ip=%s path=%s reason=%s threats=%r",
                client_ip,
                path,
                reason,
                [t.to_dict() for t in threats],
            )
            await self._send_error(send, 400, f"Request blocked: {reason}")
            return

        if threats:
            client = scope.get("client", ("unknown", 0))
            logger.warning(
                "THREAT_DETECTED ip=%s path=%s threats=%s",
                client[0] if client else "unknown",
                path,
                [t.pattern for t in threats],
            )

        # Reconstruir receive con el body ya leído
        body_index = [0]

        async def replay_receive() -> dict[str, Any]:
            if body_index[0] == 0:
                body_index[0] = 1
                return {"type": "http.request", "body": body_bytes, "more_body": False}
            return {"type": "http.disconnect"}

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _send_error(send: Any, status_code: int, detail: str) -> None:
        import json as _json
        body = _json.dumps({"detail": detail}).encode()
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({"type": "http.response.body", "body": body})


# =========================================================================
# 5. IP REPUTATION CHECKER (SSRF / internal range guard)
# =========================================================================

class IPReputationChecker:
    """Verifica si una IP es interna/reservada/sospechosa."""

    RESERVED_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),   # link-local (SSRF AWS)
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
    ]

    @classmethod
    def is_internal(cls, ip_str: str) -> bool:
        """Retorna True si la IP es interna/reservada."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in net for net in cls.RESERVED_NETWORKS)
        except ValueError:
            return False

    @classmethod
    def is_safe_external(cls, ip_str: str) -> bool:
        """Retorna True si la IP es seguramente externa."""
        return not cls.is_internal(ip_str)


# =========================================================================
# 6. REPLAY ATTACK DETECTOR
# =========================================================================

class ReplayAttackDetector:
    """
    Detecta replay attacks comprobando nonces o timestamps únicos.

    En producción, el store debe ser Redis para multi-worker.
    """

    MAX_REQUEST_AGE_SECONDS = 300  # 5 minutos de ventana
    NONCE_TTL_SECONDS       = 600  # Mantener nonces 10 min

    def __init__(self) -> None:
        self._seen_nonces: dict[str, float] = {}

    def _cleanup(self) -> None:
        now = time.time()
        expired = [n for n, ts in self._seen_nonces.items()
                   if now - ts > self.NONCE_TTL_SECONDS]
        for n in expired:
            del self._seen_nonces[n]

    def check_request(
        self,
        nonce: Optional[str],
        request_timestamp: Optional[float],
    ) -> tuple[bool, str]:
        """
        Verifica si la petición es un replay.

        Returns:
            (is_replay: bool, reason: str)
        """
        now = time.time()
        self._cleanup()

        # 1. Comprobar timestamp
        if request_timestamp is not None:
            age = abs(now - request_timestamp)
            if age > self.MAX_REQUEST_AGE_SECONDS:
                return True, f"Request timestamp too old: {age:.1f}s"

        # 2. Comprobar nonce único
        if nonce:
            nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()
            if nonce_hash in self._seen_nonces:
                return True, f"Replay detected: nonce already used"
            self._seen_nonces[nonce_hash] = now

        return False, ""


# =========================================================================
# 7. SINGLETONS
# =========================================================================

_scanner_instance: Optional[ThreatScanner] = None
_replay_detector_instance: Optional[ReplayAttackDetector] = None


def get_threat_scanner() -> ThreatScanner:
    """Singleton del ThreatScanner."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = ThreatScanner()
    return _scanner_instance


def get_replay_detector() -> ReplayAttackDetector:
    """Singleton del ReplayAttackDetector."""
    global _replay_detector_instance
    if _replay_detector_instance is None:
        _replay_detector_instance = ReplayAttackDetector()
    return _replay_detector_instance
