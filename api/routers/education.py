from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from metrics.prometheus import record_active_users, record_lesson_view
    from services.activitypub_server import ActivityPubServer
    from services.education_content_validator import EducationalContentValidator
    from services.ethics_policy import enforce_ethical_equity_text
except ModuleNotFoundError:  # pragma: no cover
    from api.metrics.prometheus import record_active_users, record_lesson_view
    from api.services.activitypub_server import ActivityPubServer
    from api.services.education_content_validator import EducationalContentValidator
    from api.services.ethics_policy import enforce_ethical_equity_text

router = APIRouter(prefix="/api/v1/education", tags=["Education"])
validator = EducationalContentValidator()
activitypub = ActivityPubServer()


def _empty_object_list() -> list[dict[str, Any]]:
    return []


class EducationContentRequest(BaseModel):
    text: str = Field(..., min_length=1)
    audience: str = Field(default="5-12")
    topic: str = Field(default="general")
    images: list[dict[str, Any]] = Field(default_factory=_empty_object_list)
    activities: list[dict[str, Any]] = Field(default_factory=_empty_object_list)


class PublishEducationPayload(BaseModel):
    text: str = Field(min_length=10)
    topic: str = Field(default="agricultura sostenible", min_length=2, max_length=200)
    audience: str = Field(default="5-12", pattern=r"^(5-12|13-16|17\+)$")
    images: list[dict[str, Any]] = Field(default_factory=_empty_object_list)
    activities: list[dict[str, Any]] = Field(default_factory=_empty_object_list)


class LessonViewRequest(BaseModel):
    age_group: str = Field(default="5-12")
    topic: str = Field(default="general")


class ActiveUsersRequest(BaseModel):
    region: str = Field(default="global")
    count: int = Field(..., ge=0)


@router.post("/validate")
async def validate_education_content(payload: EducationContentRequest) -> dict[str, Any]:
    enforce_ethical_equity_text(payload.text, context="/api/v1/education/validate")
    try:
        validated_content = validator.validate(payload.model_dump())
        audit = validator.build_audit_payload(payload.model_dump())
        return {
            "valid": True,
            "issues": [],
            "audit": audit,
            "content_hash": validated_content["content_hash"],
            "blockchain_txid": validated_content.get("blockchain_txid"),
            "db_id": validated_content.get("db_id"),
            "ethics_validated": validated_content.get("ethics_validated", False),
        }
    except ValueError as exc:
        return {
            "valid": False,
            "issues": [str(exc)],
            "audit": validator.build_audit_payload(payload.model_dump()),
            "content_hash": None,
            "blockchain_txid": None,
            "db_id": None,
            "ethics_validated": False,
        }


@router.get("/example-content")
async def example_content() -> dict[str, Any]:
    return {
        "text": "En esta leccion aprenderemos como las plantas necesitan agua y luz para crecer. Todos podemos contribuir a cuidar el medio ambiente desde la igualdad y la cooperacion.",
        "audience": "5-12",
        "topic": "huertos escolares",
        "images": [
            {
                "url": "/images/planta.jpg",
                "alt": "Ilustracion de una planta creciendo en un huerto escolar con ninos de diferentes origenes trabajando juntos.",
            }
        ],
        "activities": [
            {
                "type": "juego",
                "description": "Arrastra gotas de agua a las plantas para mantener la humedad adecuada.",
                "accessibility": {
                    "keyboard_nav": True,
                    "screen_reader_text": "Juego: Riega la planta. Usa las flechas para moverte y la barra espaciadora para regar.",
                },
            }
        ],
    }


@router.post("/publish")
def publish_educational_resource(payload: PublishEducationPayload) -> dict[str, Any]:
    enforce_ethical_equity_text(payload.text, context="/api/v1/education/publish")
    try:
        validated_content = validator.validate(payload.model_dump())
        broadcast_result = activitypub.broadcast_educational_resource(validated_content)
        return {
            "status": "published",
            "resource": {
                "id": validated_content.get("db_id"),
                "content_hash": validated_content["content_hash"],
                "blockchain_txid": validated_content.get("blockchain_txid"),
            },
            "distribution": broadcast_result,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/lesson-view")
async def register_lesson_view(payload: LessonViewRequest) -> dict[str, Any]:
    record_lesson_view(payload.age_group, payload.topic)
    return {"status": "OK", "tracked": True}


@router.post("/active-users")
async def register_active_users(payload: ActiveUsersRequest) -> dict[str, Any]:
    record_active_users(payload.region, payload.count)
    return {"status": "OK", "tracked": True}
