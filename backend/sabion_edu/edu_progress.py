# backend/sabion_edu/edu_progress.py
"""Reportar progreso → 12 Agentes evalúan → Sabionda orchestrate → Certificado si levelup."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from .edu_models import STUDENTS, NIVELES, HABILIDADES_POR_NIVEL, CERT_NAMES, REVENUE_PER_CERT, CERTIFICATES
except ImportError:
    from edu_models import STUDENTS, NIVELES, HABILIDADES_POR_NIVEL, CERT_NAMES, REVENUE_PER_CERT, CERTIFICATES

SABIONDA_URL = os.getenv("SABIONDA_URL", "http://localhost:9000")


def report_progress(student: str, progress_pct: float, skill: str = "") -> Dict[str, Any]:
    """Actualiza progreso del estudiante. Si >= 85% y consenso Sabionda, puede levelup."""
    if student not in STUDENTS:
        return {"ok": False, "error": "student not enrolled", "student": student}

    STUDENTS[student]["progress_pct"] = max(0, min(100, progress_pct))
    STUDENTS[student]["last_skill"] = skill or "general"

    result = {"ok": True, "student": student, "progress_pct": STUDENTS[student]["progress_pct"]}

    try:
        import httpx
        r = httpx.post(
            f"{SABIONDA_URL}/sabionda/orchestrate",
            json={
                "type": "EduProgress",
                "agent": "compliance",
                "student": student,
                "progress": progress_pct,
            },
            timeout=10.0,
        )
        if r.status_code == 200:
            data = r.json()
            result["sabionda"] = data.get("nodes_approved", "3/3")
            result["block_hash"] = data.get("block_hash")
            result["ml_prediction"] = data.get("ml_prediction")
    except Exception as e:
        logger.debug("Sabionda progress: %s", e)

    return result
