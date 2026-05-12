from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.vegetal_alloys.chemaxon_integration import ChemAxonClient
from backend.vegetal_alloys.database import (
    VegetalAlloy,
    calculate_sustainability,
    get_db,
    init_db,
)

try:
    from backend.energy_audit.witness_minimal import witness_event
except ImportError:
    witness_event = None  # type: ignore[misc, assignment]

router = APIRouter()
_db_ready = False


def _ensure_db() -> None:
    global _db_ready
    if not _db_ready:
        init_db()
        _db_ready = True


def _witness_ref_string(ref: Any) -> str | None:
    if ref is None:
        return None
    if isinstance(ref, dict):
        h = ref.get("hash")
        if isinstance(h, str) and h:
            return h[:256]
        return json.dumps(ref, sort_keys=True, separators=(",", ":"))[:256]
    return str(ref)[:256]


class AlloyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    source_crop: str = Field(..., min_length=1, max_length=80)
    chemical_composition: dict[str, Any]
    physical_properties: dict[str, Any]


class AlloyResponse(BaseModel):
    id: int
    name: str
    source_crop: str
    sustainability_score: float
    witness_ref: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChemAxonBody(BaseModel):
    smiles: str = Field(..., min_length=1, max_length=2048)


@router.post("/alloys/", response_model=AlloyResponse)
def create_alloy(body: AlloyCreate, db: Session = Depends(get_db)) -> AlloyResponse:
    _ensure_db()
    sustainability = calculate_sustainability(body.chemical_composition)
    row = VegetalAlloy(
        name=body.name,
        source_crop=body.source_crop,
        chemical_composition=body.chemical_composition,
        physical_properties=body.physical_properties,
        sustainability_score=sustainability,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    ref: str | None = None
    if witness_event is not None:
        try:
            ref = witness_event(
                {
                    "action": "create_vegetal_alloy",
                    "alloy_id": row.id,
                    "name": row.name,
                    "source_crop": row.source_crop,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "CASTUO-ENERGY-01",
            )
        except Exception:
            ref = None
    wr = _witness_ref_string(ref)
    if wr:
        row.witness_ref = wr
        db.commit()
        db.refresh(row)

    return AlloyResponse.model_validate(row)


@router.get("/alloys/{alloy_id}", response_model=AlloyResponse)
def read_alloy(alloy_id: int, db: Session = Depends(get_db)) -> AlloyResponse:
    _ensure_db()
    row = db.query(VegetalAlloy).filter(VegetalAlloy.id == alloy_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Aleacion no encontrada")
    return AlloyResponse.model_validate(row)


@router.post("/alloys/{alloy_id}/chemaxon")
def analyze_with_chemaxon(alloy_id: int, body: ChemAxonBody, db: Session = Depends(get_db)) -> dict[str, Any]:
    _ensure_db()
    row = db.query(VegetalAlloy).filter(VegetalAlloy.id == alloy_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Aleacion no encontrada")

    client = ChemAxonClient()
    properties = client.calculate_properties(body.smiles)

    if witness_event is not None:
        try:
            witness_event(
                {
                    "action": "chemaxon_analysis",
                    "alloy_id": row.id,
                    "smiles": body.smiles,
                    "properties": properties,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "CASTUO-CHEMAXON-01",
            )
        except Exception:
            pass

    return {
        "alloy_id": row.id,
        "smiles": body.smiles,
        "properties": properties,
        "witness_ref": row.witness_ref,
    }
