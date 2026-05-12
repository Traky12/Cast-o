from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPORT_TEMPLATES = _REPO_ROOT / "templates" / "reports"


def _normalize_event(raw: Any) -> MutableMapping[str, Any]:
    ev: MutableMapping[str, Any] = dict(raw) if isinstance(raw, dict) else dict(raw)
    ev.setdefault("event_type", "")
    ev.setdefault("timestamp", "")
    ev.setdefault("responsible", "")
    ev.setdefault("sigpac_metadata", None)
    ev.setdefault("quality_parameters", {})
    ev.setdefault("compliance", [])
    if not isinstance(ev["quality_parameters"], dict):
        ev["quality_parameters"] = {}
    return ev


def _parse_audit_token_id(raw: Union[int, str, None]) -> Optional[int]:
    if raw is None:
        return None
    try:
        tid = int(str(raw).strip(), 10)
    except (TypeError, ValueError):
        logger.error("token_id inválido (entero positivo esperado): %r", raw)
        return None
    if tid < 1:
        logger.error("token_id debe ser >= 1, recibido %s", tid)
        return None
    return tid


def _optional_report_chain(
    batch_id: str,
    output_path: str,
    compliance_status: str,
    token_id: Optional[Union[int, str]] = None,
) -> None:
    tid = _parse_audit_token_id(token_id)
    if tid is None and token_id is not None:
        return
    if tid is None:
        raw = os.environ.get("CASTUO_AUDIT_REPORT_TOKEN_ID", "").strip()
        if not raw:
            return
        tid = _parse_audit_token_id(raw)
        if tid is None:
            return
    payload: Dict[str, Any] = {
        "tokenId": tid,
        "action": "aemps_audit_report_generated",
        "status": "completed",
        "details": {
            "batch_id": batch_id,
            "output_path": output_path,
            "compliance_status": compliance_status,
        },
        "compliance": {
            "note": "jinja2_template_report",
            "normative_references": ["Reglamento (UE) 2019/1009", "RD 903/2025"],
        },
    }
    try:
        from backend.api.services.gaiachain_service import register_event_in_chain

        register_event_in_chain(payload)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Registro GaiaChain informe fallido batch_id=%s: %s",
            batch_id,
            exc,
            exc_info=True,
        )


class AuditReportGenerator:
    """Renderiza JSON de auditoría desde Jinja2; datos deben venir de fuentes reales (BD, expediente)."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        tdir = templates_dir or _REPORT_TEMPLATES
        self.env = Environment(
            loader=FileSystemLoader(str(tdir)),
            autoescape=select_autoescape(enabled_extensions=()),
        )

    def generate_aemps_report(
        self,
        batch_data: Dict[str, Any],
        output_path: str,
        *,
        token_id: Optional[Union[int, str]] = None,
    ) -> bool:
        try:
            events_in: List[Any] = batch_data.get("events") or []
            events = [_normalize_event(e) for e in events_in]
            template = self.env.get_template("aemps_audit.jinja2")
            generated_at = datetime.now(timezone.utc).isoformat()
            report = template.render(
                normative_notice=(
                    "Las referencias normativas en este JSON son documentales; "
                    "no certifican cumplimiento legal ni agrotécnico."
                ),
                batch_id=batch_data.get("batch_id", ""),
                parcel_id=batch_data.get("parcel_id", ""),
                crop_type=batch_data.get("crop_type", ""),
                events=events,
                water_usage=batch_data.get("water_usage") or {},
                compliance_status=batch_data.get("compliance_status", "unknown"),
                compliance_issues=batch_data.get("compliance_issues") or [],
                generated_at=generated_at,
            )
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            parsed = json.loads(report)
            with out.open("w", encoding="utf-8") as fh:
                json.dump(parsed, fh, ensure_ascii=False, indent=2)
            _optional_report_chain(
                str(batch_data.get("batch_id", "")),
                str(out),
                str(batch_data.get("compliance_status", "unknown")),
                token_id=token_id,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Error al generar informe AEMPS: %s", exc)
            return False
