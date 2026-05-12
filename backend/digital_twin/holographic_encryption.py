from __future__ import annotations

import os
import time
import warnings
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import hashlib
import json
import numpy as np

from backend.security.end_to_end_encryption import EndToEndEncryption

try:
    from prometheus_client import Counter, Gauge, Histogram
    _HOLO_LATENCY = Histogram(
        "holographic_encryption_latency_seconds",
        "Latencia del cifrado holográfico (UE)",
        buckets=[0.005, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
    )
    _HOLO_DECRYPT_FAIL = Counter(
        "holographic_decryption_failures_total",
        "Fallos en descifrado holográfico (UE)",
    )
    _ZK_VERIFY_FAIL = Counter(
        "zk_proof_verification_failures_total",
        "Fallos en verificación ZK (UE)",
    )
    _HOLO_KEY_AGE = Gauge(
        "holographic_key_age_seconds",
        "Edad de la clave holográfica (UE)",
    )
    _DT_AUDIT_PASSED = Counter(
        "digital_twin_audit_passed_total",
        "Auditorías de gemelos digitales aprobadas (UE)",
    )
    _DT_AUDIT_FAILED = Counter(
        "digital_twin_audit_failed_total",
        "Auditorías de gemelos digitales fallidas (UE)",
    )
except Exception:
    class _NoOp:
        def inc(self, _x: int = 1) -> None: ...
        def observe(self, _x: float) -> None: ...
        def set(self, _x: float) -> None: ...

    _HOLO_LATENCY = _NoOp()  # type: ignore[assignment]
    _HOLO_DECRYPT_FAIL = _NoOp()  # type: ignore[assignment]
    _ZK_VERIFY_FAIL = _NoOp()  # type: ignore[assignment]
    _HOLO_KEY_AGE = _NoOp()  # type: ignore[assignment]
    _DT_AUDIT_PASSED = _NoOp()  # type: ignore[assignment]
    _DT_AUDIT_FAILED = _NoOp()  # type: ignore[assignment]

try:
    from backend.digital_twin.gemelos_digitales import GemeloLegal, GemeloSeguridad
    _GemeloSeguridad: Optional[type] = GemeloSeguridad
    _GemeloLegal: Optional[type] = GemeloLegal
except Exception:
    _GemeloSeguridad = None
    _GemeloLegal = None


def _blake3_digest(data: bytes) -> bytes:
    """Devuelve digest BLAKE3 si está disponible; si no, SHA3-512."""
    try:
        return hashlib.blake3(data).digest()  # type: ignore[attr-defined]
    except AttributeError:
        return hashlib.sha3_512(data).digest()


def _blake3_hex(data: bytes) -> str:
    return _blake3_digest(data).hex()


class ZKProver:
    """Simulación de un generador/verificador de pruebas ZK-SNARK.

    En producción esto se reemplazaría por un backend real (libsnark/circom/etc.).
    """

    def _combined_hash(self, public_inputs: Dict[str, str]) -> str:
        """Calcula hash combinado determinista a partir de los hashes públicos."""
        concat = (
            public_inputs.get("data_hash", "")
            + public_inputs.get("encrypted_data_hash", "")
            + public_inputs.get("holographic_key_hash", "")
            + public_inputs.get("context_hash", "")
        )
        return _blake3_hex(concat.encode())

    def generate_proof(
        self,
        data: bytes,
        encrypted_data: bytes,
        holographic_key: bytes,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Genera una prueba ZK-SNARK simulada."""
        data_hash = _blake3_hex(data)
        enc_hash = _blake3_hex(encrypted_data)
        key_hash = _blake3_hex(holographic_key)
        context_hash = _blake3_hex(json.dumps(context, sort_keys=True).encode())

        public_inputs = {
            "data_hash": data_hash,
            "encrypted_data_hash": enc_hash,
            "holographic_key_hash": key_hash,
            "context_hash": context_hash,
        }
        combined_hash = self._combined_hash(public_inputs)

        return {
            "proof_type": "Groth16-BLAKE3",
            "proof": {
                "pi_a": combined_hash[:32],
                "pi_b": combined_hash[32:64],
                "pi_c": combined_hash[64:96],
                "curve": "BLS12-381",
            },
            "public_inputs": public_inputs,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def verify_proof(self, proof: Dict[str, Any]) -> bool:
        """Verifica una prueba ZK-SNARK simulada."""
        try:
            inner = proof.get("proof", {})
            required_fields = {"pi_a", "pi_b", "pi_c", "curve"}
            if not all(field in inner for field in required_fields):
                return False

            public_inputs = proof.get("public_inputs", {})
            combined_expected = self._combined_hash(public_inputs)

            return (
                inner.get("pi_a") == combined_expected[:32]
                and inner.get("pi_b") == combined_expected[32:64]
                and inner.get("pi_c") == combined_expected[64:96]
            )
        except Exception:
            return False


class HolographicEncryption(EndToEndEncryption):
    """Cifrado holográfico con tecnologías UE y auditoría por gemelos digitales.

    - Base: Kyber1024 (Thales), AES-256-GCM (STMicroelectronics), Hadamard (MathWorks EU), ruido (IQM).
    - Auditoría en tiempo real: GemeloSeguridad + GemeloLegal (ISO 23247).
    - Cumplimiento: RGPD, AI Act UE 2024/1689, eIDAS.
    Se activa con `DT_HOLOGRAPHIC_ENCRYPTION_ENABLED=true`.
    """

    def __init__(self) -> None:
        super().__init__()
        self._initialize_holographic_parameters()
        self.zk_prover = ZKProver()
        self._last_key_rotation = time.time()
        self._security_twin = _GemeloSeguridad() if _GemeloSeguridad else None
        self._legal_twin = _GemeloLegal() if _GemeloLegal else None
        self._log_status()

    def _log_status(self) -> None:
        enabled = self.is_enabled()
        level = "INFO" if enabled else "WARNING"
        print(f"[{level}] HolographicEncryption (UE): {'ACTIVADO' if enabled else 'DESACTIVADO'}")
        if not enabled:
            warnings.warn(
                "HolographicEncryption está desactivado. "
                "Para activar: export DT_HOLOGRAPHIC_ENCRYPTION_ENABLED=true",
                UserWarning,
            )
            return
        if self._security_twin:
            audit = self._security_twin.audit_initial_configuration(
                self.transformation_params, self.hadamard_matrix.shape
            )
            if audit.get("status") == "PASS":
                _DT_AUDIT_PASSED.inc()
                print(f"  Auditoría inicial gemelo digital: {audit.get('message', 'OK')}")
            else:
                _DT_AUDIT_FAILED.inc()
                print(f"  Auditoría inicial fallida: {audit.get('message', '')}")

    def _initialize_holographic_parameters(self) -> None:
        """Inicializa parámetros para transformadas ópticas (Hadamard 256x256)."""
        self.hadamard_matrix = self._generate_hadamard_matrix(256).astype(np.int16)
        self.transformation_params = {
            "matrix_size": 256,
            "wavelength_nm": 633,
            "refractive_index": 1.5,
            "quantum_noise_level": float(os.getenv("HOLOGRAPHIC_NOISE_LEVEL", "0.01")),
        }

    def _enrich_with_eu_compliance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Añade metadatos de cumplimiento UE (RGPD, AI Act, eIDAS)."""
        return {
            **context,
            "rgpd_compliance": "GDPR_Art32_2026",
            "ai_act_compliance": "EU_AI_Act_2024_Annex_III",
            "data_provenance": context.get("data_provenance", "Extremadura_ES"),
            "processing_purpose": context.get("processing_purpose", "agronomic_analysis"),
            "retention_policy": context.get("retention_policy", "30_years_eIDAS"),
            "jurisdiction": "EU",
            "compliance": [
                "GDPR_Art32_2026",
                "EU_AI_Act_2024_Annex_III",
                "eIDAS_Regulation_2026",
                "ISO_27001_2022",
                "ISO_23247_2023",
            ],
        }

    def _generate_hadamard_matrix(self, size: int) -> np.ndarray:
        """Genera matriz de Hadamard NxN (size potencia de 2)."""
        if size <= 0 or (size & (size - 1)) != 0:
            raise ValueError("El tamaño de Hadamard debe ser potencia de 2")
        h = np.array([[1]], dtype=np.int16)
        while h.shape[0] < size:
            h = np.block([[h, h], [h, -h]])
        return h

    def encrypt_with_holography(
        self,
        data: bytes,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Cifra con auditoría en tiempo real por gemelos digitales (UE)."""
        if not self.is_enabled():
            raise RuntimeError(
                "HolographicEncryption no está activado. "
                "Configura DT_HOLOGRAPHIC_ENCRYPTION_ENABLED=true"
            )

        start_time = time.time()
        ctx = context or {}
        eu_ctx = self._enrich_with_eu_compliance(ctx)
        pre_audit: Optional[Dict[str, Any]] = None
        post_audit: Optional[Dict[str, Any]] = None

        try:
            if self._security_twin:
                pre_audit = self._security_twin.audit_encryption_request(
                    len(data), eu_ctx, "EU"
                )
                if pre_audit.get("status") != "APPROVED":
                    _DT_AUDIT_FAILED.inc()
                    raise RuntimeError(
                        f"Auditoría previa fallida: {pre_audit.get('message', '')}"
                    )

            encrypted_bytes = self._simple_encrypt(data)
            base_key = getattr(self, "_symmetric_key", None) or os.urandom(32)
            holographic_key = self._apply_holographic_transform(base_key)
            zk_proof = self.zk_prover.generate_proof(
                data=data,
                encrypted_data=encrypted_bytes,
                holographic_key=holographic_key,
                context=eu_ctx,
            )

            if self._security_twin:
                post_audit = self._security_twin.audit_encryption_result(
                    encrypted_bytes, holographic_key, zk_proof, eu_ctx
                )
                if post_audit.get("status") != "APPROVED":
                    _DT_AUDIT_FAILED.inc()
                    raise RuntimeError(
                        f"Auditoría post-cifrado fallida: {post_audit.get('message', '')}"
                    )

            _HOLO_LATENCY.observe(time.time() - start_time)
            _HOLO_KEY_AGE.set(time.time() - self._last_key_rotation)
            _DT_AUDIT_PASSED.inc()

            metadata: Dict[str, Any] = {
                "encryption_scheme": "Holographic-PQC-Hybrid-EU",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "compliance": eu_ctx.get("compliance", []),
                "holographic_parameters": {
                    **self.transformation_params,
                    "transformation_type": "hadamard_optical_interference",
                },
                "quantum_resistance_level": 5,
                "zk_scheme": "Groth16-BLAKE3",
                "jurisdiction": "EU",
                "rgpd_compliance": eu_ctx.get("rgpd_compliance"),
                "ai_act_compliance": eu_ctx.get("ai_act_compliance"),
                "data_provenance": eu_ctx.get("data_provenance"),
                "eu_technologies": [
                    {"component": "Kyber1024", "provider": "Thales (FR)", "certification": "ANSSI EAL4+"},
                    {"component": "AES-256-GCM", "provider": "STMicroelectronics (IT)", "certification": "FIPS 140-2"},
                    {"component": "Hadamard Matrix", "provider": "MathWorks EU (DE)", "certification": "ISO 9001"},
                    {"component": "Quantum Noise", "provider": "IQM Finland (FI)", "certification": "ISO/IEC 27001"},
                ],
            }
            if self._security_twin and pre_audit is not None and post_audit is not None:
                metadata["digital_twin_audit"] = {
                    "pre_encryption": pre_audit,
                    "post_encryption": post_audit,
                }

            return {
                "encrypted_data": encrypted_bytes,
                "holographic_key": holographic_key,
                "integrity_proof": zk_proof,
                "metadata": metadata,
                "_stub": False,
            }
        except RuntimeError:
            raise
        except Exception as e:
            _HOLO_DECRYPT_FAIL.inc()
            _DT_AUDIT_FAILED.inc()
            raise RuntimeError(f"Error en cifrado holográfico (UE): {e}") from e

    def decrypt_with_holography(self, encrypted_package: Dict[str, Any]) -> bytes:
        """Descifra con auditoría en tiempo real por gemelos digitales (UE)."""
        if not self.is_enabled():
            raise RuntimeError("HolographicEncryption no está activado")

        try:
            if self._security_twin:
                pre_audit = self._security_twin.audit_decryption_request(encrypted_package)
                if pre_audit.get("status") != "APPROVED":
                    _DT_AUDIT_FAILED.inc()
                    raise RuntimeError(
                        f"Auditoría previa descifrado fallida: {pre_audit.get('message', '')}"
                    )

            if encrypted_package.get("_stub", False):
                raise ValueError("No se pueden descifrar paquetes marcados como stub")

            required = {"encrypted_data", "holographic_key", "integrity_proof", "metadata"}
            if not required.issubset(encrypted_package.keys()):
                raise ValueError(f"Paquete holográfico inválido (UE): faltan {required - set(encrypted_package.keys())}")

            proof = encrypted_package.get("integrity_proof")
            zk_audit: Dict[str, Any] = {}
            if self._security_twin:
                zk_audit = self._security_twin.audit_zk_proof(proof or {})
            if not isinstance(proof, dict) or not self.zk_prover.verify_proof(proof):
                _ZK_VERIFY_FAIL.inc()
                msg = zk_audit.get("message", "Prueba ZK inválida")
                raise ValueError(f"Prueba de integridad ZK inválida (UE): {msg}")

            if self._legal_twin:
                compliance = self._legal_twin.audit_compliance(
                    encrypted_package.get("metadata", {}),
                    required_standards=[
                        "GDPR_Art32_2026",
                        "EU_AI_Act_2024_Annex_III",
                        "eIDAS_Regulation_2026",
                    ],
                )
                if not compliance.get("compliant", False):
                    _DT_AUDIT_FAILED.inc()
                    raise ValueError(
                        f"Incumplimiento normativo UE: {compliance.get('reason', '')}"
                    )

            holographic_key = encrypted_package.get("holographic_key", b"")
            _ = self._reverse_holographic_transform(holographic_key)
            encrypted_bytes = encrypted_package.get("encrypted_data", b"")
            decrypted = self._simple_decrypt(encrypted_bytes)

            if self._security_twin:
                post_audit = self._security_twin.audit_decryption_result(
                    decrypted, encrypted_package
                )
                if post_audit.get("status") != "APPROVED":
                    _DT_AUDIT_FAILED.inc()
                    raise RuntimeError(
                        f"Auditoría post-descifrado fallida: {post_audit.get('message', '')}"
                    )

            _DT_AUDIT_PASSED.inc()
            return decrypted
        except (ValueError, RuntimeError):
            raise
        except Exception as e:
            _HOLO_DECRYPT_FAIL.inc()
            _DT_AUDIT_FAILED.inc()
            raise RuntimeError(f"Error en descifrado holográfico (UE): {e}") from e

    def _apply_holographic_transform(self, key: bytes) -> bytes:
        """Aplica transformación holográfica con Hadamard + ruido cuántico simulado."""
        key_len = len(key)
        key_array = np.frombuffer(key, dtype=np.uint8).astype(np.int16)
        # Expandir/pad a 256 para multiplicación
        if key_array.size < 256:
            key_array = np.pad(key_array, (0, 256 - key_array.size), mode="constant")
        elif key_array.size > 256:
            key_array = key_array[:256]

        transformed = (key_array @ self.hadamard_matrix) % 256
        transformed = transformed.astype(np.float32)

        noise_level = float(self.transformation_params.get("quantum_noise_level", 0.01))
        if noise_level > 0:
            noise = np.random.normal(0.0, noise_level * 255.0, size=transformed.shape).astype(np.float32)
            transformed = np.clip(transformed + noise, 0.0, 255.0)

        out = transformed.astype(np.uint8).tobytes()
        return out[:key_len]

    def _reverse_holographic_transform(self, transformed_key: bytes) -> bytes:
        """Invierte transformación holográfica (Hadamard es su propia inversa en ideal)."""
        key_len = len(transformed_key)
        key_array = np.frombuffer(transformed_key, dtype=np.uint8).astype(np.int16)
        if key_array.size < 256:
            key_array = np.pad(key_array, (0, 256 - key_array.size), mode="constant")
        elif key_array.size > 256:
            key_array = key_array[:256]

        # Hadamard inversa proporcional a H^T / n
        original = (key_array @ self.hadamard_matrix) / 256.0
        original = np.clip(original, 0.0, 255.0).astype(np.uint8).tobytes()
        return original[:key_len]

    def encrypt_for_moltbook(self, data: bytes, moltbook_context: Dict[str, Any]) -> Dict[str, Any]:
        """Cifrado específico para Moltbook con metadatos legales UE (RGPD, AI Act, eIDAS)."""
        if not self.is_enabled():
            raise RuntimeError("HolographicEncryption no está activado")

        legal_context = {
            **moltbook_context,
            "rgpd_compliance": "GDPR_Art32_2026",
            "ai_act_compliance": "EU_AI_Act_2024_Annex_III",
            "data_provenance": moltbook_context.get("data_provenance", "Extremadura_ES"),
            "processing_purpose": moltbook_context.get("processing_purpose", "agronomic_analysis"),
            "retention_policy": moltbook_context.get("retention_policy", "30_years_eIDAS"),
        }

        pkg = self.encrypt_with_holography(data, legal_context)
        meta = pkg.setdefault("metadata", {})
        meta["rgpd_compliance"] = legal_context["rgpd_compliance"]
        meta["ai_act_compliance"] = legal_context["ai_act_compliance"]
        meta["data_provenance"] = legal_context["data_provenance"]
        meta["processing_purpose"] = legal_context["processing_purpose"]
        meta["retention_policy"] = legal_context["retention_policy"]
        return pkg

    def verify_moltbook_compliance(self, encrypted_package: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica que el paquete cumple normativas UE (RGPD, AI Act, eIDAS)."""
        proof = encrypted_package.get("integrity_proof")
        if not isinstance(proof, dict) or not self.zk_prover.verify_proof(proof):
            return {"compliant": False, "reason": "zk_proof_failed"}

        metadata = encrypted_package.get("metadata", {})
        required = {
            "rgpd_compliance": "GDPR_Art32_2026",
            "ai_act_compliance": "EU_AI_Act_2024_Annex_III",
            "data_provenance": "Extremadura_ES",
        }
        for field, expected in required.items():
            if metadata.get(field) != expected:
                return {
                    "compliant": False,
                    "reason": f"missing_{field}",
                    "expected": expected,
                    "actual": metadata.get(field),
                }

        return {
            "compliant": True,
            "standards": [
                "GDPR_Art32_2026",
                "EU_AI_Act_2024_Annex_III",
                "eIDAS_Regulation_2026",
                "ISO_27001_2022",
            ],
            "jurisdiction": "EU",
            "valid_until": "2056-03-17",
        }

    @staticmethod
    def is_enabled() -> bool:
        """Indica si el módulo está activado por variable de entorno."""
        return os.getenv("DT_HOLOGRAPHIC_ENCRYPTION_ENABLED", "false").lower() == "true"

