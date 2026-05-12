# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.thc_estimator import THCEstimator

router = APIRouter()


class THCEstimateRequest(BaseModel):
    batch_id: Optional[str] = Field(default=None, min_length=1)
    plant_id: str = Field(..., min_length=1)
    zone_id: str = Field("default")
    spectrum: List[float] = Field(..., min_length=157, max_length=157)


class LIMSValidationRequest(BaseModel):
    batch_id: str = Field(..., min_length=1)
    lab_certificate: str = Field(..., min_length=1)
    thc_validated: float = Field(..., ge=0.0, le=100.0)
    validation_method: str = Field("HPLC")


_EST: Optional[THCEstimator] = None


def _coeff_path() -> str:
    return os.getenv("THC_COEFFS_PATH", os.path.join("backend", "models", "thc_coefficients.npz"))


def _get_estimator() -> THCEstimator:
    global _EST
    if _EST is None:
        _EST = THCEstimator()
        p = _coeff_path()
        if os.path.exists(p):
            _EST.load_coefficients(p)
    return _EST


@router.post("/estimate")
async def estimate_thc(body: THCEstimateRequest) -> Dict[str, Any]:
    try:
        est = _get_estimator()
        data = await est.estimate_and_register(
            batch_id=body.batch_id,
            plant_id=body.plant_id,
            zone_id=body.zone_id,
            spectrum=body.spectrum,
        )
        return {"status": "success", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/validate_lims")
async def validate_lims(body: LIMSValidationRequest) -> Dict[str, Any]:
    try:
        est = _get_estimator()
        data = await est.validate_lims(
            batch_id=body.batch_id,
            lab_certificate=body.lab_certificate,
            thc_validated=body.thc_validated,
            validation_method=body.validation_method,
        )
        return {"status": "success", "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

