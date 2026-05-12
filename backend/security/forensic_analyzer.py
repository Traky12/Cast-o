# backend/security/forensic_analyzer.py — Análisis forense ético (ISO 27001, GDPR, NIST SP 800-86)

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None
    _NUMPY = False

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    _SKLEARN = True
except ImportError:
    IsolationForest = None
    StandardScaler = None
    _SKLEARN = False

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


def _blake3_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    try:
        return hashlib.blake3(data).hexdigest()
    except AttributeError:
        return hashlib.sha3_512(data).hexdigest()


class ForensicAnalyzer:
    """
    Sistema de análisis forense ético:
    - Detección de anomalías en tiempo real (red y comportamiento)
    - Generación de evidencias auditables
    - Cumplimiento ISO 27001, GDPR, NIST SP 800-86
    """

    THRESHOLDS = {
        "network": {"low": 0.001, "medium": 0.005, "high": 0.01, "critical": 0.05},
        "behavior": {"low": 0.0005, "medium": 0.002, "high": 0.005, "critical": 0.01},
    }

    def __init__(
        self,
        encryption: Any,
        traceability: Any,
    ) -> None:
        self.encryption = encryption
        self.traceability = traceability
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.thresholds = dict(self.THRESHOLDS)
        self.evidence_retention_policy = 90
        self.legal_compliance_mode = "strict"
        self.dynamic_threshold_adjustment = True
        self.historical_metrics: List[Dict[str, Any]] = []
        self.evidence_store: List[Dict] = []
        if _SKLEARN and IsolationForest is not None and StandardScaler is not None:
            self.models["network"] = self._init_advanced_model("network")
            self.models["behavior"] = self._init_advanced_model("behavior")
            self.models["performance"] = self._init_advanced_model("performance")
            self.models["anomaly"] = self._init_advanced_model("anomaly")
            self.scalers["network"] = self.models["network"].get("scaler", StandardScaler())
            self.scalers["behavior"] = self.models["behavior"].get("scaler", StandardScaler())
            self.scalers["performance"] = self.models["performance"].get("scaler", StandardScaler())
        else:
            logger.warning("sklearn no disponible; detección de anomalías limitada")

    def _init_advanced_model(self, model_type: str) -> Dict[str, Any]:
        """Inicializa modelo avanzado con parámetros optimizados por tipo."""
        if IsolationForest is None or StandardScaler is None:
            return {}
        if model_type == "network":
            return {
                "model": IsolationForest(
                    n_estimators=200,
                    max_samples="auto",
                    contamination=0.001,
                    max_features=0.8,
                    bootstrap=True,
                    n_jobs=-1,
                    random_state=42,
                ),
                "scaler": StandardScaler(),
                "features": ["bytes_in", "bytes_out", "packets", "connections", "ports", "protocols"],
                "thresholds": self.thresholds.get("network", self.THRESHOLDS["network"]),
                "compliance": ["NIST_SP_800-94", "ISO_27001:A.12.4.1", "GDPR:Art.32"],
            }
        if model_type == "behavior":
            return {
                "model": IsolationForest(
                    n_estimators=200,
                    max_samples="auto",
                    contamination=0.0005,
                    max_features=0.9,
                    bootstrap=True,
                    n_jobs=-1,
                    random_state=42,
                ),
                "scaler": StandardScaler(),
                "features": ["api_calls", "db_queries", "login_attempts", "session_duration", "resource_access", "geolocation"],
                "thresholds": self.thresholds.get("behavior", self.THRESHOLDS["behavior"]),
                "compliance": ["NIST_SP_800-53", "ISO_27001:A.9.1.2", "GDPR:Art.25"],
            }
        return {
            "model": IsolationForest(
                n_estimators=100,
                max_samples="auto",
                contamination=0.01,
                random_state=42,
                n_jobs=-1,
            ),
            "scaler": StandardScaler(),
            "features": [],
            "thresholds": {},
            "compliance": [],
        }

    def _init_isolation_forest(self) -> Any:
        if IsolationForest is None:
            return None
        return IsolationForest(
            n_estimators=100,
            max_samples="auto",
            contamination=0.01,
            random_state=42,
            n_jobs=-1,
        )

    def register_metric(self, metric: Dict[str, Any]) -> None:
        """Registra métrica para ajuste dinámico de umbrales."""
        self.historical_metrics.append(metric)
        if len(self.historical_metrics) > 10000:
            self.historical_metrics = self.historical_metrics[-10000:]

    def _adjust_thresholds_based_on_history(self) -> None:
        """Ajusta umbrales dinámicamente según métricas históricas recientes."""
        if len(self.historical_metrics) < 1000:
            return
        recent = self.historical_metrics[-1000:]
        anomaly_count = sum(1 for m in recent if m.get("is_anomaly"))
        anomaly_rate = anomaly_count / 1000
        for domain in ("network", "behavior"):
            if domain not in self.thresholds:
                continue
            if anomaly_rate > 0.02:
                for sev in self.thresholds[domain]:
                    self.thresholds[domain][sev] = min(0.05, self.thresholds[domain][sev] * 0.8)
            elif anomaly_rate < 0.005:
                for sev in self.thresholds[domain]:
                    self.thresholds[domain][sev] = min(0.05, self.thresholds[domain][sev] * 1.2)
            if isinstance(self.models.get(domain), dict) and "thresholds" in self.models[domain]:
                self.models[domain]["thresholds"] = dict(self.thresholds[domain])

    def _severity_from_ratio(self, ratio: float, thresholds: Dict[str, float]) -> str:
        if ratio >= thresholds.get("critical", 0.05):
            return "critical"
        if ratio >= thresholds.get("high", 0.01):
            return "high"
        if ratio >= thresholds.get("medium", 0.005):
            return "medium"
        return "low"

    def analyze_network_traffic(self, traffic_data: List[Dict]) -> Tuple[bool, Dict]:
        """
        Analiza tráfico de red en busca de anomalías.
        traffic_data: lista de dicts con al menos timestamp, bytes_in, bytes_out; opcional packets.
        Returns: (is_anomaly, evidence).
        """
        m = self.models.get("network")
        if not traffic_data or not _SKLEARN or not m:
            return False, {}
        model = m.get("model") if isinstance(m, dict) else m
        scaler = m.get("scaler", self.scalers.get("network")) if isinstance(m, dict) else self.scalers.get("network")
        if model is None or scaler is None:
            return False, {}
        try:
            features = []
            for d in traffic_data:
                features.append([
                    float(d.get("bytes_in", 0)),
                    float(d.get("bytes_out", 0)),
                    float(d.get("packets", 0)),
                ])
            features_arr = np.array(features)
            features_norm = scaler.fit_transform(features_arr)
            model.fit(features_norm)
            predictions = model.predict(features_norm)
            anomalies = np.where(predictions == -1)[0]
            if len(anomalies) == 0:
                self.register_metric({"is_anomaly": False, "type": "network", "value": 0})
                return False, {}
            ratio = len(anomalies) / max(len(traffic_data), 1)
            thresholds = m.get("thresholds", self.thresholds.get("network", {})) if isinstance(m, dict) else {}
            severity = self._severity_from_ratio(ratio, thresholds)
            evidence = {
                "type": "network_anomaly",
                "timestamps": [traffic_data[i].get("timestamp", "") for i in anomalies],
                "features": features_norm[anomalies].tolist(),
                "raw_data": [traffic_data[i] for i in anomalies],
                "severity": severity,
            }
            evidence["evidence_hash"] = _blake3_hex(json.dumps(evidence, sort_keys=True))
            if self.traceability:
                self.traceability.register_event({
                    "type": "network_anomaly_detected",
                    "evidence_hash": evidence["evidence_hash"],
                    "severity": evidence["severity"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "normative_references": ["ISO_27001:A.12.4.1", "GDPR:Art.32", "NIST_SP_800-61"],
                })
            self.evidence_store.append(evidence)
            self.register_metric({"is_anomaly": True, "type": "network", "ratio": ratio})
            if self.dynamic_threshold_adjustment:
                self._adjust_thresholds_based_on_history()
            return True, evidence
        except Exception as e:
            logger.exception("Error en análisis de red: %s", e)
            if self.traceability:
                self.traceability.register_event({
                    "type": "forensic_analysis_error",
                    "error": str(e),
                    "severity": "critical",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            return False, {"error": str(e)}

    def analyze_behavior(self, behavior_data: List[Dict]) -> Tuple[bool, Dict]:
        """
        Analiza patrones de comportamiento anómalos.
        behavior_data: lista de dicts con timestamp, api_calls, db_queries; opcional login_attempts.
        """
        m = self.models.get("behavior")
        if not behavior_data or not _SKLEARN or not m:
            return False, {}
        model = m.get("model") if isinstance(m, dict) else m
        scaler = m.get("scaler", self.scalers.get("behavior")) if isinstance(m, dict) else self.scalers.get("behavior")
        if model is None or scaler is None:
            return False, {}
        try:
            features = []
            for d in behavior_data:
                features.append([
                    float(d.get("api_calls", 0)),
                    float(d.get("db_queries", 0)),
                    float(d.get("login_attempts", 0)),
                ])
            features_arr = np.array(features)
            features_norm = scaler.fit_transform(features_arr)
            model.fit(features_norm)
            predictions = model.predict(features_norm)
            anomalies = np.where(predictions == -1)[0]
            if len(anomalies) == 0:
                self.register_metric({"is_anomaly": False, "type": "behavior", "value": 0})
                return False, {}
            ratio = len(anomalies) / max(len(behavior_data), 1)
            thresholds = m.get("thresholds", self.thresholds.get("behavior", {})) if isinstance(m, dict) else {}
            severity = self._severity_from_ratio(ratio, thresholds)
            evidence = {
                "type": "behavior_anomaly",
                "timestamps": [behavior_data[i].get("timestamp", "") for i in anomalies],
                "features": features_norm[anomalies].tolist(),
                "raw_data": [behavior_data[i] for i in anomalies],
                "severity": severity,
            }
            evidence["evidence_hash"] = _blake3_hex(json.dumps(evidence, sort_keys=True))
            if self.traceability:
                self.traceability.register_event({
                    "type": "behavior_anomaly_detected",
                    "evidence_hash": evidence["evidence_hash"],
                    "severity": evidence["severity"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            self.evidence_store.append(evidence)
            self.register_metric({"is_anomaly": True, "type": "behavior", "ratio": ratio})
            if self.dynamic_threshold_adjustment:
                self._adjust_thresholds_based_on_history()
            return True, evidence
        except Exception as e:
            logger.exception("Error en análisis de comportamiento: %s", e)
            if self.traceability:
                self.traceability.register_event({
                    "type": "forensic_analysis_error",
                    "error": str(e),
                    "severity": "critical",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            return False, {"error": str(e)}

    def get_evidence_report(self) -> Dict:
        """Informe de evidencias recolectadas (últimas 10)."""
        return {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_evidences": len(self.evidence_store),
                "normative_compliance": ["ISO_27001:A.16.1.1", "GDPR:Art.33", "NIST_SP_800-86"],
            },
            "evidences": self.evidence_store[-10:],
        }

    def export_evidence(self, output_file: str, recipient_public_key: bytes) -> str:
        """Exporta evidencias a archivo cifrado (sobre con recipient_public_key)."""
        report = self.get_evidence_report()
        envelope = self.encryption.create_encrypted_envelope(
            report,
            recipient_public_key,
            metadata={
                "type": "forensic_evidence_export",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2)
        return output_file
