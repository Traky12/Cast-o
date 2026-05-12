# backend/ai/federated_learning.py — Coordinador de federated learning (agregación, validación, EU AI Act)

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None
    _NUMPY = False

try:
    from backend.security.pq_crypto import PostQuantumCrypto
    _CRYPTO = True
except ImportError:
    PostQuantumCrypto = None
    _CRYPTO = False

try:
    from backend.ai.secure_aggregation import HomomorphicAggregator
    _HE_AGG = True
except ImportError:
    HomomorphicAggregator = None
    _HE_AGG = False

try:
    from backend.ai.outlier_detection import AdvancedOutlierDetector
    _DBSCAN_AVAILABLE = True
except ImportError:
    AdvancedOutlierDetector = None
    _DBSCAN_AVAILABLE = False

try:
    from backend.ai.model_quality import ModelQualityMetrics
    _QUALITY_AVAILABLE = True
except ImportError:
    ModelQualityMetrics = None
    _QUALITY_AVAILABLE = False

try:
    from backend.ai.he_optimization import HEPerformanceOptimizer
    _HE_OPT_AVAILABLE = True
except ImportError:
    HEPerformanceOptimizer = None
    _HE_OPT_AVAILABLE = False


class FederatedLearningCoordinator:
    """
    Coordinador de federated learning: descubrimiento de peers, agregación de modelos.
    Cumplimiento EU AI Act Anexo IV.
    """

    def __init__(
        self,
        cache_ttl: int = 3600,
        use_he: bool = False,
        optimize_he: bool = False,
        use_dbscan: bool = False,
        use_quality_weights: bool = False,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.crypto = PostQuantumCrypto() if _CRYPTO else None
        self.peers: List[Dict[str, Any]] = []
        self.model_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = cache_ttl
        self.use_he = use_he and _HE_AGG and HomomorphicAggregator is not None
        self.optimize_he = optimize_he and _HE_OPT_AVAILABLE and HEPerformanceOptimizer is not None and self.use_he
        if self.use_he:
            if self.optimize_he:
                params = HEPerformanceOptimizer.find_optimal_parameters(1000)
                self.he_aggregator = HomomorphicAggregator(
                    poly_modulus_degree=params.get("poly_modulus_degree", 8192),
                    coeff_mod_bit_sizes=params.get("coeff_mod_bit_sizes"),
                    scale=2**40,
                )
            else:
                self.he_aggregator = HomomorphicAggregator()
        else:
            self.he_aggregator = None
        self.use_dbscan = use_dbscan and _DBSCAN_AVAILABLE and AdvancedOutlierDetector is not None
        self.outlier_detector = AdvancedOutlierDetector(eps=0.3) if self.use_dbscan else None
        self.use_quality_weights = use_quality_weights and _QUALITY_AVAILABLE and ModelQualityMetrics is not None

    def _calculate_model_hash(self, model_data: Dict[str, Any]) -> str:
        """Calcula el hash de un modelo para validación de integridad."""
        data_for_hash = {
            k: v for k, v in model_data.items()
            if k not in ("hash", "aggregation_metadata", "signature", "public_key")
        }
        try:
            return hashlib.blake3(json.dumps(data_for_hash, sort_keys=True).encode()).hexdigest()
        except AttributeError:
            return hashlib.sha3_512(json.dumps(data_for_hash, sort_keys=True).encode()).hexdigest()

    def _get_cached_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Devuelve el modelo desde cache si es válido (TTL + integridad)."""
        if model_name not in self.model_cache:
            return None
        entry = self.model_cache[model_name]
        if (datetime.now(timezone.utc).timestamp() - entry["timestamp"]) > self.cache_ttl:
            self.logger.debug("Cache expirada para %s", model_name)
            del self.model_cache[model_name]
            return None
        if not self._validate_model_integrity(entry["model"]):
            self.logger.warning("Modelo en cache corrupto para %s", model_name)
            del self.model_cache[model_name]
            return None
        return entry["model"]

    def _cache_model(self, model_name: str, model_data: Dict[str, Any]) -> None:
        """Almacena un modelo en cache con su hash."""
        model_data["hash"] = self._calculate_model_hash(model_data)
        self.model_cache[model_name] = {
            "model": model_data,
            "timestamp": datetime.now(timezone.utc).timestamp(),
            "hash": model_data["hash"],
        }
        self.logger.debug("Modelo %s almacenado en cache (TTL: %ss)", model_name, self.cache_ttl)

    async def discover_peers(self) -> List[Dict]:
        script = os.path.join(os.path.dirname(__file__), "..", "scripts", "discover_peers.py")
        if os.path.isfile(script):
            try:
                r = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run([os.environ.get("PYTHON", "python"), script], capture_output=True, text=True, timeout=15),
                )
                if r.returncode == 0 and r.stdout:
                    self.peers = json.loads(r.stdout).get("peers", [])
            except Exception as e:
                self.logger.debug("discover_peers: %s", e)
        return self.peers

    async def _run_coordination_round(
        self,
        local_models: Dict[str, Any],
        min_participants: int = 3,
        timeout: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """Ejecuta una ronda de coordinación sin usar cache."""
        peers = await self.discover_peers()
        if len(peers) < min_participants - 1:
            self.logger.warning("Peers insuficientes para federated round")
            return None
        share_tasks = [
            self._share_models_with_peer(peer, local_models, timeout=max(60, timeout - 120))
            for peer in peers[: min_participants - 1]
        ]
        results = await asyncio.gather(*share_tasks, return_exceptions=True)
        valid = [r for r in results if isinstance(r, dict) and r]
        if len(valid) < min_participants - 1:
            return None
        return self._aggregate_models([local_models] + valid)

    async def _secure_coordinate_round(
        self,
        local_models: Dict[str, Any],
        min_participants: int = 3,
        timeout: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """Ronda de coordinación con cifrado homomórfico: agregar sin exponer pesos en claro."""
        if not self.he_aggregator or not _NUMPY:
            return await self._run_coordination_round(local_models, min_participants, timeout)
        peers = await self.discover_peers()
        if len(peers) < min_participants - 1:
            self.logger.warning("Peers insuficientes para federated round (HE)")
            return None
        share_tasks = [
            self._share_models_with_peer(peer, local_models, timeout=max(60, timeout - 120))
            for peer in peers[: min_participants - 1]
        ]
        results = await asyncio.gather(*share_tasks, return_exceptions=True)
        valid = [r for r in results if isinstance(r, dict) and r]
        if len(valid) < min_participants - 1:
            return None
        all_models_list = [local_models] + valid
        aggregated = {}
        for model_name in local_models.keys():
            models_for_name = [m[model_name] for m in all_models_list if model_name in m and isinstance(m.get(model_name), dict)]
            if not models_for_name or not all(self._validate_model_integrity(m) for m in models_for_name):
                continue
            if not self._validate_model_outliers(models_for_name):
                self.logger.warning("Outliers en %s (HE); se omite", model_name)
                continue
            try:
                agg_weights = {}
                for wkey in models_for_name[0].get("weights", {}):
                    encrypted = [
                        self.he_aggregator.encrypt_weights(m["weights"][wkey])
                        for m in models_for_name
                    ]
                    if hasattr(encrypted[0], "decrypt"):
                        agg_enc = self.he_aggregator.aggregate_encrypted(encrypted)
                        dec = self.he_aggregator.decrypt_weights(agg_enc)
                        agg_weights[wkey] = (dec.tolist() if hasattr(dec, "tolist") else list(dec))
                    else:
                        if _NUMPY:
                            agg_weights[wkey] = np.mean(encrypted, axis=0).tolist()
                        else:
                            n = len(encrypted)
                            agg_weights[wkey] = [sum(x) / n for x in zip(*encrypted)]
                out = {
                    "weights": agg_weights,
                    "confidence": sum(m.get("confidence", 1.0) for m in models_for_name) / len(models_for_name),
                    "aggregation_metadata": {
                        "method": "homomorphic_encryption",
                        "participants": len(models_for_name),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "normative_compliance": {"EU_AI_Act": "Anexo IV", "ISO_27001": "A.10.1.1"},
                    },
                }
                out["hash"] = self._calculate_model_hash(out)
                aggregated[model_name] = out
            except Exception as e:
                self.logger.error("Agregación HE para %s: %s", model_name, e)
        return aggregated if aggregated else None

    async def coordinate_round(
        self,
        local_models: Dict[str, Any],
        min_participants: int = 3,
        timeout: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """Coordinación de ronda con cache (TTL + validación de hash)."""
        try:
            cached_results = {}
            for model_name in local_models.keys():
                cached = self._get_cached_model(model_name)
                if cached is not None:
                    cached_results[model_name] = cached
                    self.logger.info("Cache hit para %s", model_name)
            if len(cached_results) >= len(local_models):
                return cached_results
            if self.use_he and self.he_aggregator:
                result = await self._secure_coordinate_round(local_models, min_participants, timeout)
            else:
                result = await self._run_coordination_round(local_models, min_participants, timeout)
            if result:
                for model_name, model_data in result.items():
                    self._cache_model(model_name, model_data)
                for k, v in cached_results.items():
                    if k not in result:
                        result[k] = v
                return result
            return cached_results if cached_results else None
        except Exception as e:
            self.logger.error("Error en coordinación con cache: %s", e)
            return await self._run_coordination_round(local_models, min_participants, timeout)

    async def _share_models_with_peer(self, peer: Dict, models: Dict, timeout: int = 240) -> Optional[Dict]:
        if not self.crypto:
            return None
        payload = {"models": models, "sender": "local", "timestamp": datetime.now(timezone.utc).isoformat()}
        payload["signature"] = self.crypto.dilithium_sign(json.dumps(models, sort_keys=True))
        script = os.path.join(os.path.dirname(__file__), "..", "scripts", "share_models_with_peer.py")
        if not os.path.isfile(script):
            return None
        try:
            r = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [os.environ.get("PYTHON", "python"), script, "--peer", peer.get("id", ""), "--payload", json.dumps(payload)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                ),
            )
            if r.returncode != 0 or not r.stdout:
                return None
            data = json.loads(r.stdout)
            if self._verify_peer_response(data):
                return data.get("models")
        except Exception as e:
            self.logger.debug("share_models_with_peer: %s", e)
        return None

    def _verify_peer_response(self, response: Dict) -> bool:
        if not self.crypto or "signature" not in response:
            return False
        try:
            models_str = json.dumps(response.get("models", {}), sort_keys=True)
            return self.crypto.dilithium_verify(models_str, response["signature"])
        except Exception:
            return False

    def _validate_model_integrity(self, model_data: Dict[str, Any]) -> bool:
        """Comprueba integridad del modelo (hash, opcional firma)."""
        try:
            if "hash" not in model_data:
                self.logger.warning("Modelo sin hash de integridad")
                return False
            data_for_hash = {k: v for k, v in model_data.items() if k not in ("hash", "aggregation_metadata", "signature", "public_key")}
            try:
                calculated = hashlib.blake3(json.dumps(data_for_hash, sort_keys=True).encode()).hexdigest()
            except AttributeError:
                calculated = hashlib.sha3_512(json.dumps(data_for_hash, sort_keys=True).encode()).hexdigest()
            if calculated != model_data["hash"]:
                self.logger.warning("Hash de modelo no coincide")
                return False
            if "signature" in model_data and self.crypto:
                msg = json.dumps(data_for_hash, sort_keys=True)
                if not self.crypto.dilithium_verify(msg, model_data["signature"]):
                    self.logger.warning("Firma del modelo inválida")
                    return False
            return True
        except Exception as e:
            self.logger.error("Validación de integridad: %s", e)
            return False

    def _validate_model_outliers(self, models: List[Dict], threshold: float = 3.0) -> bool:
        """Detecta outliers en pesos con Z-score (requiere numpy)."""
        if not models or not _NUMPY:
            return True
        try:
            weights_key = next(iter(models[0].get("weights", {})), None)
            if not weights_key:
                return True
            weights = [m["weights"][weights_key] for m in models if isinstance(m.get("weights", {}).get(weights_key), list)]
            if not weights:
                return True
            arr = np.array(weights)
            mean = np.mean(arr, axis=0)
            std = np.std(arr, axis=0)
            std[std == 0] = 1
            z = np.abs((arr - mean) / std)
            if np.max(z) > threshold:
                self.logger.warning("Outliers detectados (Z-score max > %s)", threshold)
                return False
            return True
        except Exception as e:
            self.logger.debug("Outliers check: %s", e)
            return True

    def _validate_model_structure(self, models: List[Dict]) -> None:
        """Comprueba que todos los modelos tienen la misma estructura y dimensiones."""
        if not models:
            raise ValueError("No hay modelos para agregar")
        ref_keys = set(models[0].keys())
        for i, model in enumerate(models[1:], 1):
            if set(model.keys()) != ref_keys:
                raise ValueError("Modelos con estructuras diferentes")
        if "weights" not in models[0]:
            raise ValueError("Modelos sin clave weights")
        ref_wkeys = set(models[0]["weights"].keys())
        for model in models[1:]:
            if set(model["weights"].keys()) != ref_wkeys:
                raise ValueError("Estructura de pesos diferente entre modelos")
            for wkey in ref_wkeys:
                if len(model["weights"][wkey]) != len(models[0]["weights"][wkey]):
                    raise ValueError(f"Dimensiones diferentes en {wkey}")

    def _weighted_average_models(self, models: List[Dict]) -> Dict[str, Any]:
        """Agregación optimizada con NumPy y validación de estructura y pesos."""
        if not models:
            return {}
        try:
            if _NUMPY:
                self._validate_model_structure(models)
            if self.use_quality_weights and ModelQualityMetrics is not None:
                norm = ModelQualityMetrics.quality_weights(models)
            else:
                confidences = [m.get("confidence", 1.0) for m in models]
                total = sum(confidences)
                norm = [c / total for c in confidences] if total > 0 else [1.0 / len(models)] * len(models)
            out = {}
            for key in models[0]:
                if key == "weights":
                    agg_w = {}
                    for wkey in models[0]["weights"]:
                        try:
                            if _NUMPY:
                                layer_weights = np.array([m["weights"][wkey] for m in models], dtype=float)
                                if not np.isfinite(layer_weights).all():
                                    raise ValueError(f"Pesos no finitos en {wkey}")
                                w_np = np.array(norm, dtype=float)
                                aggregated_weight = np.average(layer_weights, axis=0, weights=w_np)
                                agg_w[wkey] = aggregated_weight.tolist()
                            else:
                                agg_w[wkey] = [
                                    sum(norm[i] * models[i]["weights"][wkey][j] for i in range(len(models)))
                                    for j in range(len(models[0]["weights"][wkey]))
                                ]
                        except Exception:
                            agg_w[wkey] = models[0]["weights"][wkey]
                    out["weights"] = agg_w
                elif key == "confidence":
                    out["confidence"] = sum(norm[i] * models[i].get("confidence", 1.0) for i in range(len(models)))
                elif key not in ("aggregation_metadata", "hash", "signature"):
                    idx = int(np.argmax(confidences)) if _NUMPY else 0
                    out[key] = models[idx][key]
            out["aggregation_metadata"] = {
                "method": "weighted_average",
                "participants": len(models),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "confidence_weights": norm,
                "normative_compliance": {
                    "EU_AI_Act": "Anexo IV (Registro de modelos de alto riesgo)",
                    "ISO_27001": "A.10.1.1 (Control de activos)",
                },
            }
            out["hash"] = self._calculate_model_hash(out)
            return out
        except Exception as e:
            self.logger.error("Error en agregación ponderada: %s", e)
            return max(models, key=lambda x: float(x.get("confidence", 0)))

    def _aggregate_models(self, all_models: List[Dict]) -> Optional[Dict[str, Any]]:
        """Agrega modelos con validación de integridad y outliers."""
        if not all_models:
            return None
        aggregated = {}
        model_names = set()
        for peer_models in all_models:
            model_names.update(peer_models.keys())
        for model_name in model_names:
            valid = []
            for peer_models in all_models:
                if model_name not in peer_models:
                    continue
                m = peer_models[model_name]
                if isinstance(m, dict) and self._validate_model_integrity(m):
                    valid.append(m)
            if not valid:
                self.logger.warning("No hay modelos válidos para %s", model_name)
                continue
            if self.use_dbscan and self.outlier_detector:
                valid = self.outlier_detector.filter_valid_models(valid)
                if not valid:
                    self.logger.warning("Todos los modelos de %s marcados como outliers (DBSCAN)", model_name)
                    continue
            elif not self._validate_model_outliers(valid):
                self.logger.warning("Outliers en %s; se omite agregación", model_name)
                continue
            aggregated[model_name] = self._weighted_average_models(valid)
        return aggregated if aggregated else None
