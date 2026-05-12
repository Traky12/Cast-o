# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional

import numpy as np
from prometheus_client import Counter, Gauge

try:
    from backend.database import get_db_connection, is_postgres_available
except ImportError:
    get_db_connection = None
    is_postgres_available = lambda: False
from backend.services.gaia_chain import GaiaChainService

# Métricas operativas de estimación/validación THC.
THC_ESTIMATIONS_TOTAL = Counter(
    "thc_estimations_total",
    "Total de estimaciones THC",
    ["status"],
)
THC_ESTIMATIONS_PENDING = Gauge(
    "thc_estimations_pending",
    "Estimaciones THC pendientes de validación LIMS",
)
THC_VALIDATIONS_TOTAL = Counter(
    "thc_validations_total",
    "Total de validaciones LIMS",
    ["status"],
)
THC_ESTIMATION_ERRORS_TOTAL = Counter(
    "thc_estimation_errors_total",
    "Errores durante estimaciones THC",
)


def _canonical_hash(spectrum: List[float]) -> str:
    arr = np.asarray(spectrum, dtype=np.float32)
    return hashlib.sha256(arr.tobytes()).hexdigest()


class THCEstimator:
    """Estimador preliminar THC (PLS 1 componente, numpy puro)."""

    def __init__(self) -> None:
        self.weights: Optional[np.ndarray] = None
        self.mean_x: Optional[np.ndarray] = None
        self.mean_y: Optional[float] = None
        self.gaia = GaiaChainService()

    def is_trained(self) -> bool:
        return self.weights is not None and self.mean_x is not None and self.mean_y is not None

    def load_coefficients(self, path: str) -> None:
        data = np.load(path)
        self.weights = data["weights"].astype(np.float32)
        self.mean_x = data["mean_x"].astype(np.float32)
        self.mean_y = float(data["mean_y"])

    def save_coefficients(self, path: str) -> None:
        if not self.is_trained():
            raise ValueError("Modelo no entrenado")
        np.savez(path, weights=self.weights, mean_x=self.mean_x, mean_y=self.mean_y)

    def train_pls_1c(self, X: np.ndarray, y: np.ndarray) -> float:
        if X.ndim != 2 or X.shape[1] != 157:
            raise ValueError("X debe tener forma [n, 157]")
        if y.ndim != 1 or y.shape[0] != X.shape[0]:
            raise ValueError("y debe tener forma [n] alineada con X")
        self.mean_x = np.mean(X, axis=0).astype(np.float32)
        self.mean_y = float(np.mean(y))
        Xc = (X - self.mean_x).astype(np.float32)
        yc = (y - self.mean_y).astype(np.float32)
        cov = Xc.T @ yc
        norm = float(np.linalg.norm(cov))
        if norm <= 0:
            raise ValueError("No se puede entrenar: covarianza nula")
        w = cov / norm
        t = Xc @ w
        denom = float(t @ t)
        if denom <= 0:
            raise ValueError("No se puede entrenar: componente degenerado")
        c = float((t @ yc) / denom)
        self.weights = (c * w).astype(np.float32)
        pred = self.predict(X)
        rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
        return rmse

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained():
            raise ValueError("Modelo no entrenado")
        if X.ndim != 2 or X.shape[1] != 157:
            raise ValueError("X debe tener forma [n, 157]")
        return (X.astype(np.float32) - self.mean_x) @ self.weights + self.mean_y  # type: ignore[operator]

    def _ensure_table(self) -> None:
        if not is_postgres_available() or not get_db_connection:
            return
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS spectra_estimations (
                        id SERIAL PRIMARY KEY,
                        batch_id VARCHAR(64) NOT NULL,
                        plant_id VARCHAR(64),
                        zone_id VARCHAR(64),
                        spectrum_hash VARCHAR(64) NOT NULL,
                        thc_estimate DOUBLE PRECISION,
                        thc_validated DOUBLE PRECISION,
                        validation_method VARCHAR(64),
                        lab_certificate VARCHAR(128),
                        gaiachain_tx VARCHAR(128),
                        status VARCHAR(32) DEFAULT 'PENDING_VALIDATION',
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        metadata JSONB,
                        UNIQUE(batch_id, spectrum_hash)
                    );
                    CREATE INDEX IF NOT EXISTS idx_spectra_batch ON spectra_estimations(batch_id);
                    CREATE INDEX IF NOT EXISTS idx_spectra_plant ON spectra_estimations(plant_id);
                    """
                )
            conn.commit()
        finally:
            conn.close()

    def _store_estimation(
        self,
        *,
        batch_id: str,
        plant_id: str,
        zone_id: str,
        spectrum_hash: str,
        thc_estimate: float,
        gaiachain_tx: Optional[str],
        metadata: Dict[str, Any],
    ) -> None:
        if not is_postgres_available() or not get_db_connection:
            return
        self._ensure_table()
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO spectra_estimations
                    (batch_id, plant_id, zone_id, spectrum_hash, thc_estimate, gaiachain_tx, status, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, 'PENDING_VALIDATION', %s::jsonb)
                    ON CONFLICT (batch_id, spectrum_hash) DO UPDATE
                    SET thc_estimate = EXCLUDED.thc_estimate,
                        gaiachain_tx = EXCLUDED.gaiachain_tx,
                        status = EXCLUDED.status,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    """,
                    (
                        batch_id,
                        plant_id,
                        zone_id,
                        spectrum_hash,
                        float(thc_estimate),
                        gaiachain_tx,
                        json.dumps(metadata),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    async def estimate_and_register(
        self,
        *,
        plant_id: str,
        spectrum: List[float],
        zone_id: str = "default",
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if len(spectrum) != 157:
            THC_ESTIMATION_ERRORS_TOTAL.inc()
            raise ValueError("El espectro debe tener 157 valores (930-2500nm cada 10nm).")
        if not self.is_trained():
            THC_ESTIMATION_ERRORS_TOTAL.inc()
            raise ValueError("Modelo no entrenado. Carga coeficientes o entrena antes.")

        spectrum_hash = _canonical_hash(spectrum)
        thc_estimate = float(self.predict(np.asarray([spectrum], dtype=np.float32))[0])
        final_batch_id = batch_id or f"THC-EST-{plant_id}-{int(time.time())}"
        payload = {
            "batch_id": final_batch_id,
            "plant_id": plant_id,
            "zone_id": zone_id,
            "spectrum_hash": spectrum_hash,
            "thc_estimate": round(thc_estimate, 2),
            "status": "PENDING_VALIDATION",
            "timestamp": int(time.time()),
        }

        batch_data = {
            "batch_id": final_batch_id,
            "strain_id": f"plant:{plant_id}",
            "thc_percentage": max(0.0, thc_estimate),
            "cbd_percentage": 0.0,
            "weight_kg": 0.0,
            "lab_results": {
                "event_type": "THC_ESTIMATION",
                "zone_id": zone_id,
                "plant_id": plant_id,
                "spectrum_hash_sha256": spectrum_hash,
                "status": "PENDING_VALIDATION",
            },
            "account_id": os.getenv("THC_ESTIMATOR_ACCOUNT_ID", "sabionda-nano"),
        }

        tx_hash: Optional[str] = None
        try:
            res = await self.gaia.register_batch(batch_data)
            tx_hash = res.get("transaction_hash")
        except Exception:
            tx_hash = None

        self._store_estimation(
            batch_id=final_batch_id,
            plant_id=plant_id,
            zone_id=zone_id,
            spectrum_hash=spectrum_hash,
            thc_estimate=thc_estimate,
            gaiachain_tx=tx_hash,
            metadata={"sensor_type": "NIR_930_2500nm"},
        )

        THC_ESTIMATIONS_TOTAL.labels(status="pending").inc()
        THC_ESTIMATIONS_PENDING.inc()

        return {
            **payload,
            "gaiachain_tx": tx_hash,
            "next_step": {
                "description": "Para certificación AEMPS, validar antes en LIMS.",
                "validate_lims_endpoint": "/thc/validate_lims",
                "certify_endpoint": "/cannabis/certify_aemps",
            },
            "warnings": [
                "Estimación preliminar: NO es certificado AEMPS.",
                "Requiere validación LIMS para cerrar trazabilidad.",
            ],
        }

    async def validate_lims(
        self,
        *,
        batch_id: str,
        lab_certificate: str,
        thc_validated: float,
        validation_method: str = "HPLC",
    ) -> Dict[str, Any]:
        if not is_postgres_available() or not get_db_connection:
            raise RuntimeError("PostgreSQL no configurado para validar LIMS (DB_HOST/DB_PASSWORD)")

        self._ensure_table()
        conn = get_db_connection()
        row = None
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM spectra_estimations WHERE batch_id = %s ORDER BY created_at DESC LIMIT 1", (batch_id,))
                row = cur.fetchone()
                if not row:
                    raise ValueError("batch_id no encontrado")

                cur.execute(
                    """
                    UPDATE spectra_estimations
                    SET status = 'VALIDATED_BY_LIMS',
                        thc_validated = %s,
                        validation_method = %s,
                        lab_certificate = %s,
                        updated_at = NOW()
                    WHERE batch_id = %s
                    """,
                    (float(thc_validated), validation_method, lab_certificate, batch_id),
                )
            conn.commit()
        finally:
            conn.close()

        linked_tx = row.get("gaiachain_tx") if isinstance(row, dict) else None
        ev = {
            "batch_id": batch_id,
            "status": "VALIDATED_BY_LIMS",
            "thc_validated": float(thc_validated),
            "validation_method": validation_method,
            "lab_certificate": lab_certificate,
            "timestamp": int(time.time()),
            "linked_tx": linked_tx,
        }
        tx_hash: Optional[str] = None
        try:
            res = await self.gaia.register_batch(
                {
                    "batch_id": f"{batch_id}-LIMS",
                    "strain_id": f"lims:{batch_id}",
                    "thc_percentage": max(0.0, float(thc_validated)),
                    "cbd_percentage": 0.0,
                    "weight_kg": 0.0,
                    "lab_results": ev,
                    "account_id": os.getenv("THC_ESTIMATOR_ACCOUNT_ID", "sabionda-nano"),
                }
            )
            tx_hash = res.get("transaction_hash")
        except Exception:
            tx_hash = None

        # Gauge no baja de cero por seguridad.
        if THC_ESTIMATIONS_PENDING._value.get() > 0:  # type: ignore[attr-defined]
            THC_ESTIMATIONS_PENDING.dec()
        THC_ESTIMATIONS_TOTAL.labels(status="validated").inc()
        THC_VALIDATIONS_TOTAL.labels(status="success").inc()

        return {
            "status": "VALIDATED_BY_LIMS",
            "batch_id": batch_id,
            "thc_validated": float(thc_validated),
            "validation_method": validation_method,
            "lab_certificate": lab_certificate,
            "gaiachain_tx": tx_hash,
            "next_step": {
                "description": "Para certificación AEMPS, usar /cannabis/certify_aemps.",
                "endpoint": "/cannabis/certify_aemps",
                "required_data": ["batch_id", "strain_id", "thc_percentage", "cbd_percentage", "lab_results"],
            },
        }

