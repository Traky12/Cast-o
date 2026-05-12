"""
Orquestador de confianza — Arranque medido (Measured Boot).
Git + ZIP industrial: sin integridad verificada, no hay minado BioCoin ni actuación crítica.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any, Callable

MeasuredBootRegionFn = Callable[[], bool]


class SecurityError(Exception):
    """Entorno comprometido o integridad no verificada."""

    pass


class TrustOrchestrator:
    """Garantiza coherencia entre código Git y binarios del ZIP inyectados."""

    def __init__(self, secret_key: bytes | None = None) -> None:
        raw = secret_key or os.getenv("CASTUO_TRUST_SECRET", "").encode("utf-8")
        self._secret = raw if raw else b"castuo-trust-unset"
        self.verified_modules: dict[str, bool] = {}
        self.trusted_environment = False
        self._irrigation_sector_locked = False
        self._lock_reason: str = ""

    def verify_binary_integrity(self, file_path: str, expected_hash_hex: str) -> bool:
        """SHA-256 del fichero vs hash esperado (manifiesto industrial)."""
        path = os.path.abspath(file_path)
        if not os.path.isfile(path):
            self.verified_modules[path] = False
            return False
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                h.update(block)
        got = h.hexdigest().lower()
        exp = expected_hash_hex.strip().lower().removeprefix("0x")
        ok = len(exp) == 64 and got == exp
        self.verified_modules[path] = ok
        self._recompute_trust()
        return ok

    def verify_from_manifest_entry(self, local_path: str, expected_sha256: str) -> bool:
        return self.verify_binary_integrity(local_path, expected_sha256)

    def _recompute_trust(self) -> None:
        self.trusted_environment = bool(self.verified_modules) and all(self.verified_modules.values())

    def require_trusted_for_mint(self) -> None:
        if os.getenv("CASTUO_MEASURED_BOOT", "").lower() in ("1", "true", "yes"):
            if not self.trusted_environment:
                raise SecurityError(
                    "Entorno no TRUSTED: ejecutar scripts/rebuild_system.py o verificar manifiesto ZIP."
                )

    def secure_token_minting(self, evidence_bundle: dict[str, Any]) -> dict[str, Any]:
        """Solo permite lógica de minado si el entorno es de confianza."""
        self.require_trusted_for_mint()
        if not self.verified_modules:
            raise SecurityError("Ningun modulo industrial verificado; abortando minado BioCoin.")
        if not all(self.verified_modules.values()):
            raise SecurityError("Entorno comprometido: hash distinto al manifiesto. Abortando minado BioCoin.")
        sig = hmac.new(self._secret, str(evidence_bundle.get("evidence_hash", "")).encode(), hashlib.sha256)
        return {"status": "mint_allowed", "hmac_gate": sig.hexdigest()[:32], "bundle_ref": evidence_bundle.get("serial_id")}

    def validar_soberania_despliegue(self, is_in_eu_jurisdiction: MeasuredBootRegionFn | None = None) -> bool:
        """Bloquea minado si HSM/despliegue fuera de jurisdicción soberana (Extremadura/UE)."""
        if is_in_eu_jurisdiction is None:
            return True
        if not is_in_eu_jurisdiction():
            self._irrigation_sector_locked = True
            self._lock_reason = "Intento de despliegue fuera de jurisdiccion soberana UE"
            return False
        return True

    def circuit_breaker_chemical(
        self,
        ozone_confidence: float,
        client_ip: str,
        allowed_ip_prefixes: tuple[str, ...] | None = None,
    ) -> bool:
        """
        Ozono confianza baja + IP no permitida → cierre lógico permanente del sector riego.
        Retorna True si se activó el cierre (circuit breaker).
        """
        if allowed_ip_prefixes is None:
            allowed_ip_prefixes = ("127.", "10.", "192.168.", "172.16.")
        ip_ok = any(client_ip.startswith(p) for p in allowed_ip_prefixes)
        if ozone_confidence < 0.35 and not ip_ok:
            self._irrigation_sector_locked = True
            self._lock_reason = f"Circuit breaker: O3 baja confianza + IP no allowlist ({client_ip})"
            return True
        return False

    def is_irrigation_sector_locked(self) -> tuple[bool, str]:
        return self._irrigation_sector_locked, self._lock_reason


_global_trust: TrustOrchestrator | None = None


def get_trust_orchestrator() -> TrustOrchestrator:
    global _global_trust
    if _global_trust is None:
        _global_trust = TrustOrchestrator()
    return _global_trust
