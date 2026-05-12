# backend/ai/secure_federated_learning.py — Coordinador FL con cifrado E2E y trazabilidad

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None
    _NUMPY = False

try:
    from backend.security.end_to_end_encryption import EndToEndEncryption
    _E2E = True
except ImportError:
    EndToEndEncryption = None
    _E2E = False

try:
    from backend.compliance.immutable_traceability import ImmutableTraceability
    _TRACE = True
except ImportError:
    ImmutableTraceability = None
    _TRACE = False


class SecureFederatedLearningCoordinator:
    """
    Coordinador FL con cifrado end-to-end y trazabilidad inmutable.
    Requiere encryption (EndToEndEncryption). traceability es opcional y se construye
    a partir de encryption si no se proporciona.
    """

    def __init__(
        self,
        encryption: Any,
        traceability: Optional[Any] = None,
    ) -> None:
        if encryption is None:
            raise ValueError("El parámetro 'encryption' es obligatorio")
        self.encryption = encryption
        self.traceability = traceability or (
            ImmutableTraceability(self.encryption)
            if ("ImmutableTraceability" in globals() and ImmutableTraceability is not None)
            else None
        )
        self.node_public_keys: Dict[str, bytes] = {}
        self.local_private_key, self.local_public_key = self.encryption.generate_key_pair()
        self.defense_system: Optional[Any] = None

    async def register_node(self, node_id: str, public_key: bytes) -> None:
        """Registra un nodo participante con su clave pública."""
        self.node_public_keys[node_id] = public_key
        logger.info("Nodo registrado: %s", node_id)

    async def secure_coordinate_round(self, local_model: Dict[str, Any], round_id: str) -> Dict[str, Any]:
        """
        Coordina una ronda FL: sobre cifrado del modelo local, registro en trazabilidad
        (solo si existe), simulación de peers, agregación y descifrado verificado.
        Devuelve solo el modelo agregado (equivalente a verify_and_decrypt_envelope(...)[0]).
        """
        if not self.encryption:
            raise RuntimeError("Encryption requerido")
        try:
            # 1. Crear sobre cifrado para modelo local
            model_envelope = self.encryption.create_encrypted_envelope(
                local_model,
                self.local_public_key,
                metadata={"round_id": round_id, "node_id": "coordinator", "model_type": local_model.get("type", "default")},
            )
            # 2. Registrar en trazabilidad (solo si existe)
            if self.traceability:
                self.traceability.register_event({
                    "type": "fl_round_start",
                    "round_id": round_id,
                    "model_hash": model_envelope["integrity"]["hash"],
                    "normative_references": ["GDPR:Art.25", "EU_AI_Act:Anexo_IV"],
                })
            # 3. Simular compartir con peers
            peer_envelopes = await self._share_with_peers(local_model, model_envelope, round_id)
            # 4. Agregar modelos cifrados
            aggregated_envelope = await self._aggregate_encrypted_models(peer_envelopes, round_id)
            # 5. Descifrar y verificar
            aggregated_model, valid = self.encryption.verify_and_decrypt_envelope(
                aggregated_envelope,
                self.local_private_key,
            )
            if not valid:
                raise ValueError("Modelo agregado inválido (falló verificación de integridad)")
            if self.traceability:
                self.traceability.register_event({
                    "type": "fl_round_complete",
                    "round_id": round_id,
                    "model_hash": aggregated_envelope["integrity"]["hash"],
                    "participants": len(peer_envelopes),
                    "normative_references": ["ISO_27001:A.12.4.1", "GDPR:Art.30"],
                })
            if self.defense_system:
                model_analysis = await self._analyze_model_security(aggregated_model)
                if model_analysis.get("is_anomaly"):
                    defense_response = await self.defense_system.detect_and_respond(
                        (True, model_analysis["evidence"])
                    )
                    if self.traceability:
                        self.traceability.register_event({
                            "type": "model_security_issue_handled",
                            "round_id": round_id,
                            "response": defense_response,
                            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                        })
            return aggregated_model
        except Exception as e:
            logger.error("Error en ronda segura FL: %s", e)
            if self.traceability:
                self.traceability.register_event({
                    "type": "fl_round_error",
                    "round_id": round_id,
                    "error": str(e),
                    "severity": "critical",
                    "normative_references": ["ISO_27001:A.16.1.1"],
                })
            raise

    async def _share_with_peers(
        self,
        local_model: Dict[str, Any],
        model_envelope: Dict[str, Any],
        round_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Simula compartir modelo cifrado con nodos (en producción: message bus).
        Cada peer genera un modelo con la misma estructura que el local, lo cifra para
        el coordinador y el sobre se re-cifra para transporte.
        """
        peer_envelopes: List[Dict[str, Any]] = []
        weights_structure = local_model.get("weights", {})
        for node_id, _public_key in self.node_public_keys.items():
            # Simular modelo de peer (misma estructura que el local)
            if _NUMPY and np is not None and weights_structure:
                w = {}
                for layer in weights_structure:
                    arr = weights_structure[layer]
                    shape = list(np.asarray(arr).shape) if hasattr(arr, "__len__") else [10]
                    w[layer] = np.random.randn(*shape).tolist() if shape else [0.0]
                peer_model = {"weights": w, "confidence": 0.95}
            else:
                peer_model = {
                    "weights": {k: [0.0] for k in weights_structure} if weights_structure else {},
                    "confidence": 0.95,
                }
            # Crear sobre cifrado del peer (para que el coordinador pueda descifrarlo)
            peer_envelope = self.encryption.create_encrypted_envelope(
                peer_model,
                self.local_public_key,
                metadata={"round_id": round_id, "node_id": node_id, "model_type": "default"},
            )
            # Re-cifrar el sobre para transporte
            reencrypted = self.encryption.encrypt_hybrid(
                json.dumps(peer_envelope).encode(),
                self.local_public_key,
            )
            peer_envelopes.append({
                "node_id": node_id,
                "encrypted_envelope": reencrypted,
                "metadata": peer_envelope["metadata"],
            })
        return peer_envelopes

    async def _aggregate_encrypted_models(
        self,
        peer_envelopes: List[Dict[str, Any]],
        round_id: str,
    ) -> Dict[str, Any]:
        """Descifra sobres de peers, agrega modelos y devuelve sobre cifrado del resultado."""
        if not self.encryption:
            raise RuntimeError("Encryption requerido")
        decrypted_envelopes: List[Dict[str, Any]] = []
        for peer_data in peer_envelopes:
            try:
                decrypted_bytes = self.encryption.decrypt_hybrid(
                    peer_data["encrypted_envelope"],
                    self.local_private_key,
                )
                envelope = json.loads(decrypted_bytes.decode())
                model, valid = self.encryption.verify_and_decrypt_envelope(
                    envelope,
                    self.local_private_key,
                )
                if not valid:
                    logger.warning("Sobre inválido del nodo %s", peer_data["node_id"])
                    continue
                decrypted_envelopes.append(envelope)
            except Exception as e:
                logger.warning("Error descifrando peer %s: %s", peer_data.get("node_id"), e)
                continue
        if not decrypted_envelopes:
            raise ValueError("No hay modelos válidos de peers")
        peer_models: List[Dict[str, Any]] = []
        for envelope in decrypted_envelopes:
            model, valid = self.encryption.verify_and_decrypt_envelope(
                envelope,
                self.local_private_key,
            )
            if valid:
                peer_models.append(model)
            else:
                logger.warning("Modelo inválido en sobre de %s", envelope.get("metadata", {}).get("node_id"))
        if not peer_models:
            raise ValueError("Ningún modelo de peer válido")
        from backend.ai.federated_learning import FederatedLearningCoordinator
        fl_coordinator = FederatedLearningCoordinator(
            use_he=False,
            use_dbscan=True,
            use_quality_weights=True,
        )
        aggregated_model = fl_coordinator._weighted_average_models(peer_models)
        return self.encryption.create_encrypted_envelope(
            aggregated_model,
            self.local_public_key,
            metadata={
                "round_id": round_id,
                "aggregation_method": "secure_weighted_average",
                "participants": len(peer_models),
                "normative_compliance": ["EU_AI_Act:Anexo_IV", "ISO_27001:A.10.1.1"],
            },
        )

    def enable_defense_system(self, defense_system: Any) -> None:
        """Habilita el sistema de defensa federado."""
        self.defense_system = defense_system
        if self.traceability:
            self.traceability.register_event({
                "type": "defense_system_enabled",
                "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "normative_references": ["ISO_27001:A.13.2.1", "GDPR:Art.32", "EU_AI_Act:Anexo_IV"],
            })

    def _generate_model_hash(self, model: Dict[str, Any]) -> str:
        import hashlib
        s = json.dumps(model, sort_keys=True, default=str)
        try:
            return hashlib.blake3(s.encode()).hexdigest()
        except AttributeError:
            return hashlib.sha3_512(s.encode()).hexdigest()

    async def _analyze_model_security(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el modelo agregado en busca de anomalías de seguridad."""
        features: List[float] = []
        weights = model.get("weights") or {}
        for layer_name, w in weights.items():
            if _NUMPY and np is not None:
                arr = np.asarray(w)
                features.extend([float(np.mean(arr)), float(np.std(arr)), float(np.max(arr)), float(np.min(arr)), float(arr.size)])
            else:
                flat = w if isinstance(w, list) else [w]
                if flat:
                    features.extend([sum(flat) / len(flat), max(flat), min(flat), float(len(flat))])
        evidence = {
            "type": "model_anomaly",
            "features": features,
            "model_hash": self._generate_model_hash(model),
            "severity": "medium",
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
        is_anomaly = any(abs(f) > 1000 for f in features) if features else False
        if is_anomaly:
            evidence["severity"] = "high"
            evidence["anomalous_features"] = [i for i, f in enumerate(features) if abs(f) > 1000]
        return {"is_anomaly": is_anomaly, "evidence": evidence}
