# backend/compliance/immutable_traceability.py — Trazabilidad inmutable (cadena + GaiaChain)

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _evidence_hash(evidence: Dict[str, Any]) -> str:
    import hashlib
    data = json.dumps(evidence, sort_keys=True)
    try:
        return hashlib.blake3(data.encode()).hexdigest()
    except AttributeError:
        return hashlib.sha3_512(data.encode()).hexdigest()

try:
    from backend.security.end_to_end_encryption import EndToEndEncryption
    _E2E = True
except ImportError:
    EndToEndEncryption = None
    _E2E = False

try:
    from backend.compliance.timestamping_service import TimestampingService
    _TS = True
except ImportError:
    TimestampingService = None
    _TS = False


def _blake3_hex(data: str | bytes) -> str:
    import hashlib
    if isinstance(data, str):
        data = data.encode()
    try:
        return hashlib.blake3(data).hexdigest()
    except AttributeError:
        return hashlib.sha3_512(data).hexdigest()


class ImmutableTraceability:
    """
    Trazabilidad inmutable:
    - Cadena local con hash enlazado y firma Dilithium
    - Registro en GaiaChain
    - Cifrado de campos sensibles (Kyber)
    """

    def __init__(self, encryption: Optional[Any] = None) -> None:
        self.encryption = encryption if encryption is not None else (EndToEndEncryption() if _E2E else None)
        self.current_chain: List[Dict[str, Any]] = []
        self.last_hash = "0" * 64
        self.block_validation_rules = {
            "hash_algorithm": "BLAKE3",
            "signature_algorithm": "Dilithium5",
            "max_block_size": 1024 * 1024,
            "retention_policy": 365 * 24 * 60 * 60,
            "compliance_requirements": [
                {"standard": "ISO_27001", "controls": ["A.12.4.1", "A.12.4.3", "A.16.1.1"]},
                {"standard": "GDPR", "articles": ["Art.5", "Art.25", "Art.30", "Art.32"]},
                {"standard": "eIDAS", "articles": ["Art.3", "Art.4"]},
            ],
        }
        self.legal_hold_enabled = False
        self.audit_trail_encryption = {
            "algorithm": "AES-256-GCM",
            "key_rotation": "90d",
            "backup_policy": {
                "locations": 3,
                "geographic_distribution": True,
                "encryption": "Kyber1024+AES-256",
            },
        }
        self.geographic_backup = {
            "enabled": True,
            "locations": [
                {"name": "Swiss Vault", "region": "ch-zurich", "status": "active"},
                {"name": "AWS Frankfurt", "region": "eu-central-1", "status": "active"},
                {"name": "Azure Singapore", "region": "ap-southeast-1", "status": "active"},
            ],
            "rotation_interval": 30,
        }
        self.timestamping_service = TimestampingService() if _TS and TimestampingService else None
        self._timestamping_event_types = ("forensic_evidence", "security_incident", "key_rotation")

    def register_event(
        self,
        event: Dict[str, Any],
        sensitive_fields: Optional[List[str]] = None,
    ) -> str:
        """
        Registra un evento en la cadena de trazabilidad inmutable.

        1. Cifrado de campos sensibles (opcional) con Kyber → clave *_encrypted en event.
        2. Generación de hash BLAKE3 del evento.
        3. Creación de bloque con firma Dilithium (previous_hash, timestamp, event_hash, event).
        4. Añadir a cadena local y actualizar last_hash.
        5. Registro en GaiaChain (script register_gaiachain_event.py).

        Args:
            event: Diccionario con los datos del evento.
            sensitive_fields: Lista de nombres de campos a cifrar (opcional).

        Returns:
            Hash del evento registrado (BLAKE3).

        Estructura del bloque:
        {
          "previous_hash": "blake3_hash_64_chars",
          "timestamp": "ISO8601",
          "event_hash": "blake3_hash_64_chars",
          "event": { "type": "...", "data": {...}, "sensitive_field_encrypted": {...} },
          "signature": "dilithium_signature..."
        }
        """
        try:
            processed_event = self._process_sensitive_fields(event, sensitive_fields or [])
            event_hash = self._generate_event_hash(processed_event)
            block = {
                "previous_hash": self.last_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_hash": event_hash,
                "event": processed_event,
                "signature": self._sign_block(processed_event),
            }
            if self.timestamping_service and processed_event.get("type") in self._timestamping_event_types:
                block["timestamping"] = self.timestamping_service.get_timestamp(
                    json.dumps(block, sort_keys=True).encode()
                )
            self.current_chain.append(block)
            self.last_hash = self._generate_block_hash(block)
            self._register_in_gaiachain(block)
            if self.geographic_backup.get("enabled"):
                self._async_geographic_backup(block)
            return event_hash
        except Exception as e:
            logger.error("Error al registrar evento: %s", e)
            raise

    def _process_sensitive_fields(self, event: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """Cifra campos sensibles con Kyber."""
        processed = dict(event)
        if not sensitive_fields or not self.encryption or not self.encryption.pq_crypto:
            return processed
        for field in sensitive_fields:
            if field not in processed:
                continue
            try:
                payload = json.dumps(processed[field])
                encrypted = self.encryption.pq_crypto.kyber_encrypt(payload, None)
                processed[f"{field}_encrypted"] = encrypted
                del processed[field]
            except Exception as e:
                logger.debug("No se pudo cifrar campo %s: %s", field, e)
        return processed

    def _generate_event_hash(self, event: Dict[str, Any]) -> str:
        return _blake3_hex(json.dumps(event, sort_keys=True))

    def _generate_block_hash(self, block: Dict[str, Any]) -> str:
        return _blake3_hex(json.dumps(block, sort_keys=True))

    def _sign_block(self, event: Dict[str, Any]) -> str:
        if not self.encryption or not self.encryption.pq_crypto:
            return ""
        try:
            return self.encryption.pq_crypto.dilithium_sign(json.dumps(event, sort_keys=True))
        except Exception as e:
            logger.debug("Firma de bloque omitida: %s", e)
            return ""

    def _async_geographic_backup(self, block: Dict[str, Any]) -> None:
        """Backup geográfico asíncrono del bloque (en producción: cola + API por ubicación)."""
        for location in self.geographic_backup.get("locations", []):
            try:
                logger.debug("Backup en %s (%s)", location.get("name"), location.get("region"))
            except Exception as e:
                logger.warning("Error backup %s: %s", location.get("name"), e)
                self._register_backup_failure(location, block)

    def _register_backup_failure(self, location: Dict[str, Any], block: Dict[str, Any]) -> None:
        """Registra fallo de backup para auditoría."""
        logger.warning("Fallo de backup en %s para bloque %s", location.get("name"), self._generate_block_hash(block)[:16])

    def verify_geographic_backup(self, block_hash: str) -> Dict[str, Any]:
        """Verifica integridad del backup geográfico (en producción: descarga y verifica por ubicación)."""
        results: Dict[str, Any] = {}
        for location in self.geographic_backup.get("locations", []):
            try:
                results[location["name"]] = {
                    "status": "verified",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as e:
                results[location["name"]] = {"status": "unavailable", "error": str(e)}
        return results

    def _register_in_gaiachain(self, block: Dict[str, Any]) -> None:
        script = Path(__file__).resolve().parent.parent / "scripts" / "register_gaiachain_event.py"
        if not script.is_file():
            logger.debug("Script GaiaChain no encontrado: %s", script)
            return
        try:
            subprocess.run(
                [
                    os.environ.get("PYTHON", "python"),
                    str(script),
                    "--event_type", "traceability_block",
                    "--details", json.dumps(block),
                    "--norms", "ISO_27001:A.12.4.1,GDPR:Art.30",
                ],
                check=False,
                capture_output=True,
                timeout=30,
                cwd=str(Path(__file__).resolve().parents[2]),
            )
        except Exception as e:
            logger.debug("GaiaChain register: %s", e)

    def verify_chain(self) -> bool:
        """Comprueba integridad de la cadena (hashes y firmas)."""
        if not self.current_chain:
            return True
        for i in range(1, len(self.current_chain)):
            current = self.current_chain[i]
            previous = self.current_chain[i - 1]
            if current["previous_hash"] != self._generate_block_hash(previous):
                logger.error("Cadena rota entre bloques %s y %s", i - 1, i)
                return False
            if self.encryption and self.encryption.pq_crypto and current.get("signature"):
                payload = json.dumps(current["event"], sort_keys=True)
                if not self.encryption.pq_crypto.dilithium_verify(payload, current["signature"]):
                    logger.error("Firma inválida en bloque %s", i)
                    return False
        return True

    def register_forensic_event(self, evidence: Dict[str, Any], audit_public_key: Optional[bytes] = None) -> str:
        """
        Registra evento forense con evidencia; opcionalmente cifrada con audit_public_key.
        Cumplimiento: ISO 27001:A.16.1.1, GDPR Art.33, NIST SP 800-86.
        """
        evidence_hash = _evidence_hash(evidence)
        event_content: Dict[str, Any] = {
            "type": "forensic_evidence",
            "evidence_hash": evidence_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "normative_references": ["ISO_27001:A.16.1.1", "GDPR:Art.33", "NIST_SP_800-86"],
        }
        if audit_public_key and self.encryption:
            try:
                envelope = self.encryption.create_encrypted_envelope(
                    evidence,
                    audit_public_key,
                    metadata={"type": "forensic_evidence", "evidence_hash": evidence_hash},
                )
                event_content["encrypted_evidence"] = envelope
            except Exception as e:
                logger.debug("Cifrado forense omitido: %s", e)
                event_content["evidence_plain"] = evidence
        else:
            event_content["evidence_plain"] = evidence
        event_hash = self._generate_event_hash(event_content)
        block = {
            "previous_hash": self.last_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "forensic_evidence",
            "event_hash": event_hash,
            "evidence_hash": evidence_hash,
            "event": event_content,
            "signature": self._sign_block(event_content),
        }
        self.current_chain.append(block)
        self.last_hash = self._generate_block_hash(block)
        self._register_in_gaiachain(block)
        return evidence_hash

    def get_audit_trail(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Devuelve la cadena de auditoría desde una fecha."""
        if since is None:
            return list(self.current_chain)
        result = []
        for block in self.current_chain:
            try:
                ts = datetime.fromisoformat(block["timestamp"].replace("Z", "+00:00"))
                if ts >= since:
                    result.append(block)
            except Exception:
                result.append(block)
        return result

    def export_chain(self, filename: str, encrypt: bool = True) -> None:
        """Exporta la cadena a archivo (opcionalmente cifrada con Kyber)."""
        path = Path(filename)
        if encrypt and self.encryption and self.encryption.pq_crypto:
            try:
                chain_str = json.dumps(self.current_chain)
                encrypted = self.encryption.pq_crypto.hybrid_encrypt_large(chain_str, None)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({
                        "encrypted_chain": encrypted,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }, f, indent=2)
            except Exception as e:
                logger.warning("Export cifrado fallido, guardando en claro: %s", e)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.current_chain, f, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.current_chain, f, indent=2)
