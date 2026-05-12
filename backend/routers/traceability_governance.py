# -*- coding: utf-8 -*-
"""Trazabilidad corcho premium (Segureja) + motor CIS (Nodo Edge)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.traceability.cis_calculator import CISImpactRequest, ImpactCalculator
from backend.traceability.cork_models import CorkExtractionEventCreate, CorkExtractionEventStored
from backend.traceability import cork_store

router = APIRouter(prefix="/traceability", tags=["Trazabilidad y Gobernanza"])


class CorkEventAuditSummary(BaseModel):
    total_events: int
    last_tree_uuid: UUID | None = None


@router.post(
    "/cork-extraction-events",
    response_model=CorkExtractionEventStored,
    summary="Registrar extracción corcho (PQC + GaiaChain)",
)
async def create_cork_event(body: CorkExtractionEventCreate) -> CorkExtractionEventStored:
    return cork_store.append_event(body)


@router.get(
    "/cork-extraction-events",
    response_model=list[CorkExtractionEventStored],
    summary="Listado auditables (recientes)",
)
async def list_cork_events(limit: int = Query(200, ge=1, le=2000)) -> list[CorkExtractionEventStored]:
    return list(cork_store.list_events(limit))


@router.get(
    "/cork-extraction-events/tree/{tree_uuid}",
    response_model=list[CorkExtractionEventStored],
    summary="Historial por alcornoque",
)
async def cork_events_by_tree(tree_uuid: UUID) -> list[CorkExtractionEventStored]:
    return cork_store.by_tree(tree_uuid)


@router.post("/cis/calculate", summary="Créditos CIS desde métricas Edge")
async def calculate_cis(body: CISImpactRequest):
    return ImpactCalculator.compute_detailed(body)


@router.get("/cork-extraction-events/audit-summary", response_model=CorkEventAuditSummary)
async def cork_audit_summary():
    evs = cork_store.list_events(1)
    last = evs[-1].tree_uuid if evs else None
    return CorkEventAuditSummary(total_events=cork_store.count_events(), last_tree_uuid=last)
