from __future__ import annotations

import hashlib
import json
from typing import Any, cast

try:
    from api.services.blockchain.logger import GaiaChainLogger
except ModuleNotFoundError:  # pragma: no cover
    from services.blockchain.logger import GaiaChainLogger

try:
    from api.database import session as db_session
    from api.models.educational_resource import EducationalResource
except ModuleNotFoundError:  # pragma: no cover
    from database import session as db_session
    from api.models.educational_resource import EducationalResource

SessionLocal: Any = getattr(db_session, "SessionLocal", None)
init_db = db_session.init_db


class EducationalContentValidator:
    """Validador ético y de accesibilidad para recursos educativos."""

    def __init__(self) -> None:
        self.blockchain = GaiaChainLogger()
        self.banned_words = self._load_banned_words()
        self.required_topics_by_age: dict[str, list[str]] = {
            "5-12": ["igualdad", "medio ambiente", "cooperacion"],
            "13-16": ["sostenibilidad", "tecnologia inclusiva", "derechos laborales"],
            "17+": ["etica en ia", "agricultura regenerativa", "derechos humanos"],
        }
        init_db()

    def validate(self, content: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        text = str(content.get("text", "")).lower()

        for word in self.banned_words:
            if word in text:
                issues.append(f"Contiene termino prohibido: {word}")

        age_group = str(content.get("audience", "5-12"))
        required_topics = self.required_topics_by_age.get(age_group, [])
        for topic in required_topics:
            if topic not in text:
                issues.append(f"Falta tema requerido para {age_group}: {topic}")

        images = content.get("images", [])
        if not isinstance(images, list):
            images = []
        for raw_img in cast(list[Any], images):
            if not isinstance(raw_img, dict):
                issues.append("Imagen sin descripcion alternativa accesible")
                continue
            img = cast(dict[str, Any], raw_img)
            if not str(img.get("alt", "")).strip():
                issues.append("Imagen sin descripcion alternativa accesible")

        activities = content.get("activities", [])
        if not isinstance(activities, list):
            activities = []
        for raw_activity in cast(list[Any], activities):
            if not isinstance(raw_activity, dict):
                issues.append("Actividad sin screen_reader_text")
                continue
            activity = cast(dict[str, Any], raw_activity)
            raw_accessibility = activity.get("accessibility", {})
            accessibility: dict[str, Any] = (
                cast(dict[str, Any], raw_accessibility) if isinstance(raw_accessibility, dict) else {}
            )
            if not accessibility.get("screen_reader_text"):
                issues.append("Actividad sin screen_reader_text")

        if issues:
            raise ValueError(f"Contenido invalido: {', '.join(issues)}")

        validated_content = {
            **content,
            "content_hash": self._calculate_hash(content),
            "ethics_validated": True,
        }

        txid = self.blockchain.log_content(
            {
                "content_hash": validated_content["content_hash"],
                "type": "educational_resource",
                "audience": content.get("audience", "5-12"),
                "topic": content.get("topic", "agricultura"),
                "ethics_validated": True,
            }
        )
        validated_content["blockchain_txid"] = txid

        db_id = self.save_to_db(validated_content)
        validated_content["db_id"] = db_id
        return validated_content

    def build_audit_payload(self, content: dict[str, Any]) -> dict[str, Any]:
        normalized = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return {
            "content_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "audience": content.get("audience", "5-12"),
            "topic": content.get("topic", "general"),
            "ready_for_gaiachain": True,
        }

    def save_to_db(self, validated_content: dict[str, Any]) -> int | None:
        if SessionLocal is None:
            return None

        db = SessionLocal()
        try:
            resource = cast(Any, EducationalResource())
            resource.content_hash = validated_content["content_hash"]
            resource.audience = validated_content.get("audience", "5-12")
            resource.topic = validated_content.get("topic", "general")
            resource.content = json.dumps(validated_content, ensure_ascii=False)
            resource.blockchain_txid = validated_content.get("blockchain_txid", "")
            db.add(resource)
            db.commit()
            db.refresh(resource)
            return int(resource.id)
        except Exception:
            db.rollback()
            return None
        finally:
            db.close()

    def _calculate_hash(self, content: dict[str, Any]) -> str:
        normalized = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _load_banned_words(self) -> list[str]:
        return [
            "discriminacion",
            "exclusion",
            "violencia",
            "quimicos toxicos",
            "trabajo infantil",
            "deforestacion ilegal",
        ]


validator = EducationalContentValidator()
