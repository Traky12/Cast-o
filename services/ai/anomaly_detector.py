"""
CASTÚO-SYSTEM™ v3.1 — Detección de Anomalías y Predicción de Cosecha
Motor de IA para invernadero agrovoltaico hidropónico.

Componentes:
  1. GreenhouseAnomalyDetector  — IsolationForest para detección de anomalías
     en lecturas de sensores (temperatura, humedad, CO₂, VPD, pH, EC)
  2. HarvestPredictor           — Estimación de rendimiento (kg/m²) basada en
     parámetros ambientales y de cultivo. LSTM en producción, reglas locales
     cuando sklearn/TensorFlow no están disponibles.
  3. RuleBasedAnalyzer          — Análisis determinista sin ML: umbral + tendencia

Dependencias opcionales:
    pip install scikit-learn>=1.3.0 numpy>=1.24.0

Sin estas dependencias, el sistema usa el analizador basado en reglas.
"""

from __future__ import annotations

import hashlib
import logging
import math
from datetime import datetime, timezone
from typing import Any

import numpy as np

logger = logging.getLogger("castuo.anomaly_detector")

try:
    from sklearn.ensemble import IsolationForest  # type: ignore
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.info("[anomaly_detector] scikit-learn no disponible — usando análisis por reglas")


# ── Umbrales de referencia ─────────────────────────────────────────────────────

SENSOR_RANGES: dict[str, tuple[float, float]] = {
    "temperatura_c":       (10.0, 40.0),
    "humedad_pct":         (30.0, 95.0),
    "co2_ppm":             (300.0, 3000.0),
    "vpd_kpa":             (0.0,  5.0),
    "ph":                  (4.0,  8.5),
    "ec_ms_cm":            (0.0,  10.0),
    "o2_disuelto_mg_l":    (0.0,  20.0),
    "irradiancia_w_m2":    (0.0,  1500.0),
}

# Rendimientos de referencia por cultivo (kg/m²/ciclo) en condiciones óptimas
RENDIMIENTO_REFERENCIA: dict[str, float] = {
    "tomate":   35.0,
    "lechuga":   4.0,
    "pimiento": 10.0,
    "pepino":   20.0,
    "fresa":     3.5,
    "albahaca":  2.0,
    "espinaca":  2.5,
    "cilantro":  1.8,
}


# ── Resultado de anomalía ──────────────────────────────────────────────────────

class AnomalyResult:
    def __init__(
        self,
        es_anomalia: bool,
        score: float,
        variables_criticas: list[str],
        metodo: str,
        descripcion: str,
        timestamp: str,
    ):
        self.es_anomalia = es_anomalia
        self.score = score
        self.variables_criticas = variables_criticas
        self.metodo = metodo
        self.descripcion = descripcion
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            "es_anomalia":         self.es_anomalia,
            "score":               round(self.score, 4),
            "variables_criticas":  self.variables_criticas,
            "metodo":              self.metodo,
            "descripcion":         self.descripcion,
            "timestamp":           self.timestamp,
        }


class HarvestPrediction:
    def __init__(
        self,
        cultivo: str,
        rendimiento_estimado_kg_m2: float,
        confianza_pct: float,
        dias_para_cosecha: int,
        factores: dict[str, float],
        metodo: str,
        timestamp: str,
    ):
        self.cultivo = cultivo
        self.rendimiento_estimado_kg_m2 = rendimiento_estimado_kg_m2
        self.confianza_pct = confianza_pct
        self.dias_para_cosecha = dias_para_cosecha
        self.factores = factores
        self.metodo = metodo
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        return {
            "cultivo":                      self.cultivo,
            "rendimiento_estimado_kg_m2":   round(self.rendimiento_estimado_kg_m2, 2),
            "confianza_pct":                round(self.confianza_pct, 1),
            "dias_para_cosecha":            self.dias_para_cosecha,
            "factores":                     {k: round(v, 3) for k, v in self.factores.items()},
            "metodo":                       self.metodo,
            "timestamp":                    self.timestamp,
        }


# ── Detector de anomalías IsolationForest ──────────────────────────────────────

class GreenhouseAnomalyDetector:
    """
    Detector de anomalías para lecturas de sensores del invernadero.

    Usa IsolationForest (sklearn) cuando está disponible, o un analizador
    basado en umbrales estadísticos cuando no lo está.

    Flujo:
      1. fit(histórico)  — entrenar con datos normales
      2. detect(lectura) — clasificar nueva lectura
    """

    # Features esperadas en orden fijo para el modelo
    FEATURES = ["temperatura_c", "humedad_pct", "co2_ppm", "vpd_kpa", "ph", "ec_ms_cm"]

    def __init__(self, contamination: float = 0.05) -> None:
        self._contamination = contamination
        self._model: Any = None
        self._trained = False
        self._training_mean: dict[str, float] = {}
        self._training_std: dict[str, float] = {}

    def fit(self, readings: list[dict]) -> None:
        """
        Entrena el detector con lecturas históricas normales.
        readings: lista de dicts con keys = FEATURES
        """
        if not readings:
            return

        X = self._to_matrix(readings)
        if X is None or len(X) < 10:
            logger.warning("[anomaly_detector] Menos de 10 muestras — fit omitido")
            return

        # Calcular estadísticos para el analizador de reglas
        for i, feat in enumerate(self.FEATURES):
            col = X[:, i]
            self._training_mean[feat] = float(np.mean(col))
            self._training_std[feat]  = float(np.std(col)) or 1.0

        if _SKLEARN_AVAILABLE:
            self._model = IsolationForest(
                contamination=self._contamination,
                random_state=42,
                n_estimators=100,
            )
            self._model.fit(X)
            self._trained = True
            logger.info(
                "[anomaly_detector] IsolationForest entrenado con %d muestras (contamination=%.2f)",
                len(X), self._contamination,
            )
        else:
            self._trained = True
            logger.info("[anomaly_detector] Estadísticos de reglas calculados con %d muestras", len(X))

    def detect(self, reading: dict) -> AnomalyResult:
        """Detecta si una lectura es anómala."""
        now = datetime.now(timezone.utc).isoformat()
        variables_criticas: list[str] = []

        if self._trained and self._model and _SKLEARN_AVAILABLE:
            X = self._to_matrix([reading])
            if X is not None:
                pred = self._model.predict(X)
                score = float(self._model.score_samples(X)[0])
                es_anomalia = pred[0] == -1
                variables_criticas = self._identify_critical_features(reading)
                return AnomalyResult(
                    es_anomalia=es_anomalia,
                    score=score,
                    variables_criticas=variables_criticas,
                    metodo="isolation_forest",
                    descripcion=self._build_description(es_anomalia, variables_criticas),
                    timestamp=now,
                )

        # Fallback: análisis por umbrales (±3σ o rangos absolutos)
        return self._rule_based_detect(reading, now)

    def _rule_based_detect(self, reading: dict, now: str) -> AnomalyResult:
        variables_criticas = []
        score = 0.0

        for feat in self.FEATURES:
            val = reading.get(feat)
            if val is None:
                continue
            rng = SENSOR_RANGES.get(feat)
            if rng and not (rng[0] <= val <= rng[1]):
                variables_criticas.append(feat)
                score -= 0.5
                continue
            # Z-score si tenemos estadísticos entrenados
            if feat in self._training_mean:
                z = abs(val - self._training_mean[feat]) / self._training_std[feat]
                if z > 3.0:
                    variables_criticas.append(feat)
                    score -= min(0.5, (z - 3) * 0.1)

        es_anomalia = bool(variables_criticas)
        return AnomalyResult(
            es_anomalia=es_anomalia,
            score=score,
            variables_criticas=variables_criticas,
            metodo="reglas_umbrales",
            descripcion=self._build_description(es_anomalia, variables_criticas),
            timestamp=now,
        )

    def _to_matrix(self, readings: list[dict]) -> Any:
        rows = []
        for r in readings:
            row = []
            for feat in self.FEATURES:
                val = r.get(feat)
                if val is None:
                    return None  # Datos incompletos — abortar
                row.append(float(val))
            rows.append(row)
        return np.array(rows)

    def _identify_critical_features(self, reading: dict) -> list[str]:
        """Identifica variables fuera de rangos absolutos o con z-score alto."""
        critical = []
        for feat in self.FEATURES:
            val = reading.get(feat)
            if val is None:
                continue
            rng = SENSOR_RANGES.get(feat)
            if rng and not (rng[0] <= val <= rng[1]):
                critical.append(feat)
            elif feat in self._training_mean:
                z = abs(val - self._training_mean[feat]) / self._training_std[feat]
                if z > 2.5:
                    critical.append(feat)
        return critical

    @staticmethod
    def _build_description(es_anomalia: bool, variables: list[str]) -> str:
        if not es_anomalia:
            return "Lectura dentro de parámetros normales"
        vars_str = ", ".join(variables) if variables else "patrón global"
        return f"Anomalía detectada — variables críticas: {vars_str}"


# ── Predictor de cosecha ───────────────────────────────────────────────────────

class HarvestPredictor:
    """
    Estimación de rendimiento de cosecha basada en condiciones ambientales.

    Modelo de producción: eficiencia factorizada sobre rendimiento de referencia.
    En producción, sustituir por un modelo LSTM entrenado con datos históricos.
    """

    def predict(
        self,
        cultivo: str,
        temp_media_c: float,
        co2_medio_ppm: float,
        dli_medio_mol_m2_dia: float,
        ec_medio_ms_cm: float,
        dias_cultivo: int,
        superficie_m2: float = 1.0,
    ) -> HarvestPrediction:
        """
        Estima el rendimiento total y el % de confianza.

        Retorna una HarvestPrediction con kg/m², días estimados hasta cosecha
        y desglose de factores limitantes.
        """
        now = datetime.now(timezone.utc).isoformat()
        rendimiento_ref = RENDIMIENTO_REFERENCIA.get(cultivo.lower(), 10.0)

        # Factor temperatura (curva gaussiana con pico en 22°C)
        f_temp = math.exp(-0.01 * (temp_media_c - 22.0) ** 2)

        # Factor CO₂ (efecto Michaelis-Menten simplificado, saturación ~1200 ppm)
        f_co2 = co2_medio_ppm / (co2_medio_ppm + 400.0)

        # Factor luz DLI (logarítmico, referencia 20 mol/m²/día)
        f_luz = min(1.0, math.log1p(dli_medio_mol_m2_dia) / math.log1p(20.0))

        # Factor EC (gaussiana, pico en óptimo del cultivo)
        EC_OPTIMOS = {
            "tomate": 3.0, "lechuga": 1.2, "pimiento": 2.75, "pepino": 2.1,
            "fresa": 1.5, "albahaca": 1.0, "espinaca": 2.0, "cilantro": 1.4,
        }
        ec_opt = EC_OPTIMOS.get(cultivo.lower(), 2.0)
        f_ec = math.exp(-0.15 * (ec_medio_ms_cm - ec_opt) ** 2)

        # Rendimiento estimado (todos los factores son multiplicativos)
        factor_global = f_temp * f_co2 * f_luz * f_ec
        rendimiento_kg_m2 = round(rendimiento_ref * factor_global, 2)

        # Confianza: mayor con valores en rango, menor en extremos
        confianza = round(factor_global * 85 + 15, 1)  # 15–100%

        # Días hasta cosecha (estimación por cultivo y etapa)
        CICLOS_DIAS = {
            "tomate": 90, "lechuga": 45, "pimiento": 100, "pepino": 60,
            "fresa": 90, "albahaca": 30, "espinaca": 40, "cilantro": 35,
        }
        ciclo_total = CICLOS_DIAS.get(cultivo.lower(), 60)
        dias_restantes = max(0, ciclo_total - dias_cultivo)

        return HarvestPrediction(
            cultivo=cultivo,
            rendimiento_estimado_kg_m2=rendimiento_kg_m2,
            confianza_pct=min(100.0, confianza),
            dias_para_cosecha=dias_restantes,
            factores={
                "temperatura":   round(f_temp, 3),
                "co2":           round(f_co2, 3),
                "luz_dli":       round(f_luz, 3),
                "ec_nutrientes": round(f_ec, 3),
                "global":        round(factor_global, 3),
            },
            metodo="reglas_factorizadas_v1",
            timestamp=now,
        )


# ── Instancias globales ────────────────────────────────────────────────────────

_detector_instance: GreenhouseAnomalyDetector | None = None
_predictor_instance: HarvestPredictor | None = None


def get_detector() -> GreenhouseAnomalyDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = GreenhouseAnomalyDetector()
    return _detector_instance


def get_predictor() -> HarvestPredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = HarvestPredictor()
    return _predictor_instance
