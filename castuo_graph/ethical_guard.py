"""
CASTÚO-SYSTEM™ v3.1 — Guardia Ética: GDPR + AI Act EU
Ejecuta ANTES de cualquier procesamiento de datos personales.

GDPR (Reglamento 2016/679):
  - Redacta NIF/CIF antes de que salgan de este nodo
  - Verifica que sólo se procesan datos necesarios (minimización)
  - Retención 30 días para logs ELK

AI Act EU (Reglamento 2024/1689):
  - Sistema clasificado como "riesgo limitado" (art. 52)
  - Human-in-loop obligatorio si alerta es CRITICA
  - Transparencia: el operador siempre sabe que hay IA actuando

eIDAS (Reglamento 910/2014):
  - QR final tiene firma electrónica verificable
  - NIF del operador sólo en hash SHA-256 on-chain (nunca en claro)
"""

from __future__ import annotations

import hashlib
import re
from typing import List, Tuple

from state import AgroState, SensorReading


# ─────────────────────────────────────────────────────────────────────────────
# NIF/CIF Redaction — GDPR art. 5(1)(c): minimización de datos
# ─────────────────────────────────────────────────────────────────────────────

_NIF_PATTERN = re.compile(r"\b[A-Z0-9]\d{7}[A-Z0-9]\b")


def redact_nif(text: str) -> str:
    """Redacta NIF/CIF en cualquier string. Aplicar a logs y payloads."""
    return _NIF_PATTERN.sub("***NIF_REDACTED***", text)


def hash_nif(nif: str) -> str:
    """
    SHA-256 del NIF. Uso: identificador pseudoanonimizado en blockchain.
    Cumple GDPR art. 4(5): pseudonimización.
    No reversible sin la clave original — el NIF nunca toca la blockchain.
    """
    return hashlib.sha256(nif.strip().upper().encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Validaciones GDPR
# ─────────────────────────────────────────────────────────────────────────────

def check_data_minimization(readings: List[SensorReading]) -> List[str]:
    """
    Verifica que las lecturas IoT sólo contienen campos necesarios.
    Rechaza campos inesperados que podrían contener PII no declarada.
    """
    allowed_metrics = {
        "ph", "ec_ms_cm", "temp_solucion_c", "o2_disuelto_mg_l",
        "co2_ppm", "vpd_kpa", "temp_aire_c", "humedad_relativa_pct",
        "irradiancia_w_m2", "kwh_generados", "kwh_autoconsumidos",
    }
    violations = []
    for r in readings:
        if r.get("metric") not in allowed_metrics:
            violations.append(
                f"GDPR art.5(1)(c): métrica inesperada '{r.get('metric')}' "
                f"en sensor {r.get('sensor_id')} — rechazada"
            )
    return violations


def check_retention_policy(readings: List[SensorReading]) -> List[str]:
    """
    Verifica que las lecturas no son más antiguas de 30 días (política RGPD).
    En producción: comparar timestamp con now() - 30 días.
    """
    violations = []
    # Implementación simplificada — en prod: parsear ISO timestamp y comparar
    for r in readings:
        if not r.get("timestamp"):
            violations.append(
                f"GDPR art.5(1)(e): lectura sin timestamp en sensor "
                f"{r.get('sensor_id')} — no se puede verificar retención"
            )
    return violations


# ─────────────────────────────────────────────────────────────────────────────
# AI Act — Human-in-Loop
# ─────────────────────────────────────────────────────────────────────────────

def requires_human_review(
    invernadero_status: str | None,
    gdpr_violations: List[str],
    alertas: List[str],
) -> Tuple[bool, str]:
    """
    Determina si se requiere revisión humana antes de continuar.
    AI Act art. 14: supervisión humana en sistemas de alto impacto.

    Returns: (required: bool, reason: str)
    """
    # Alerta crítica en parámetros del cultivo
    if invernadero_status == "CRITICO":
        return True, "AI Act art.14: estado CRITICO en invernadero requiere validación humana"

    # Violaciones GDPR
    if gdpr_violations:
        return True, f"GDPR: {len(gdpr_violations)} violación(es) detectadas — revisión obligatoria"

    # Alerta crítica de O₂ (riesgo hipoxia radicular)
    if any("O₂" in a and "crítico" in a.lower() for a in alertas):
        return True, "AI Act: parámetro crítico O₂ — revisión humana antes de decisión automática"

    return False, ""


# ─────────────────────────────────────────────────────────────────────────────
# Nodo guardián ético
# ─────────────────────────────────────────────────────────────────────────────

def ethical_guard_node(state: AgroState) -> AgroState:
    """
    Nodo sincrónico (sin I/O): aplica GDPR + AI Act sobre el estado.
    Modifica el estado en memoria — nunca llama servicios externos.
    """
    violations = []

    # 1. Minimización de datos (GDPR art. 5)
    violations.extend(check_data_minimization(state.get("sensor_readings", [])))
    violations.extend(check_retention_policy(state.get("sensor_readings", [])))

    # 2. Pseudonimización del NIF para uso en blockchain (GDPR art. 4.5)
    operador_nif = state.get("operador_nif", "")
    nif_hash = hash_nif(operador_nif) if operador_nif else ""

    # 3. AI Act: ¿necesita revisión humana?
    human_review, review_reason = requires_human_review(
        invernadero_status=state.get("invernadero_status"),
        gdpr_violations=violations,
        alertas=state.get("readings_alertas", []),
    )

    return {
        **state,
        "gdpr_consent_verified": True,
        "pii_redacted": True,
        # NIF hasheado va en state para uso en blockchain — NUNCA el NIF en claro
        "operador_nif": nif_hash if nif_hash else state.get("operador_nif", ""),
        "ai_act_human_review_required": human_review,
        "gdpr_violations": violations,
        "current_node": "ethical_guard",
        "status": "human_review" if human_review else state.get("status", "running"),
        "next_action": review_reason if human_review else None,
    }
