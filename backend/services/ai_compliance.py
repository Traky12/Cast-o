# -*- coding: utf-8 -*-
"""Validación de modelos de IA según Regulación (UE) 2024/1689 (AI Act)."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


def _optional_sklearn():
    try:
        from sklearn.metrics import accuracy_score, f1_score
        return accuracy_score, f1_score
    except ImportError:
        return None, None


def _optional_joblib():
    try:
        import joblib
        return joblib
    except ImportError:
        return None


class AIModelValidation(BaseModel):
    """Valida que el modelo cumpla requisitos del AI Act UE (sistemas de alto riesgo)."""

    model_path: str
    test_data: List[Any] = []
    test_labels: List[Any] = []
    min_accuracy: float = 0.95  # Umbral según AI Act para sistemas de alto riesgo
    min_f1: float = 0.90

    def validate(self) -> Dict[str, Any]:
        """Valida que el modelo cumpla con los requisitos del AI Act UE."""
        joblib = _optional_joblib()
        accuracy_score, f1_score = _optional_sklearn()

        if joblib is None or accuracy_score is None:
            return {
                "status": "skipped",
                "message": "sklearn/joblib no instalados. pip install scikit-learn joblib",
                "ai_act_compliance": False,
            }

        try:
            model = joblib.load(self.model_path)
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "ai_act_compliance": False,
            }

        if not self.test_data or not self.test_labels:
            return {
                "status": "skipped",
                "message": "test_data o test_labels vacíos",
                "ai_act_compliance": False,
            }

        predictions = model.predict(self.test_data)
        accuracy = float(accuracy_score(self.test_labels, predictions))
        f1 = float(f1_score(self.test_labels, predictions, average="weighted"))

        if accuracy < self.min_accuracy or f1 < self.min_f1:
            return {
                "status": "non_compliant",
                "accuracy": accuracy,
                "f1_score": f1,
                "min_accuracy": self.min_accuracy,
                "min_f1": self.min_f1,
                "ai_act_compliance": False,
                "message": (
                    f"Modelo no cumple AI Act: Accuracy={accuracy:.2f} (mínimo {self.min_accuracy}), "
                    f"F1={f1:.2f} (mínimo {self.min_f1})"
                ),
            }

        return {
            "status": "compliant",
            "accuracy": accuracy,
            "f1_score": f1,
            "ai_act_compliance": True,
        }
