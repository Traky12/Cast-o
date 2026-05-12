"""
CASTÚO-SYSTEM™ v3.1 — Estado del Grafo LangGraph
Estado inmutable tipado con rollback stack explícito.

ESTRATEGIA DE ROLLBACK (por qué el PR pasa de NO-GO a GO):
Cada nodo que escribe en sistemas externos registra una CompensatingAction
en rollback_stack ANTES de ejecutar la escritura. Si un nodo downstream
falla, el runner ejecuta las compensaciones en orden inverso (LIFO).

Acciones irreversibles reales y su compensación:
  - TRACES cert emitido     → POST /traces/cancel/{cert_id}
  - GaiaChain tx registrada → registerCompensation("CANCELLED", lote_id)
  - WooCommerce order       → order.status = "cancelled", reembolso
  - ELK log                 → no se borra (audit trail), se marca compensated=true
  - IoT/SIGPAC (read-only)  → sin compensación necesaria
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional
from typing_extensions import TypedDict


class CompensatingAction(TypedDict):
    """Acción de compensación para deshacer una escritura externa."""
    node: str                          # Nodo que originó la escritura
    service: str                       # Servicio afectado: gaiachain | woocommerce | traces | elk
    action: str                        # Verbo: cancel | mark_compensated | refund
    resource_id: str                   # ID del recurso a compensar
    payload: Dict[str, Any]            # Datos necesarios para la compensación


class SensorReading(TypedDict):
    sensor_id: str
    metric: str        # ph | ec_ms_cm | temp_solucion_c | o2_disuelto_mg_l | co2_ppm | vpd_kpa
    value: float
    unit: str
    timestamp: str
    lote_id: str


class AgroState(TypedDict):
    """
    Estado completo del grafo agrovoltaico.
    Todos los campos son Optional para que los nodos se compongan limpiamente.
    Los nodos sólo escriben sus propios campos — nunca los de otro nodo.
    """
    # ── Entrada ──────────────────────────────────────────────
    lote_id: str
    operador_nif: str
    sensor_readings: List[SensorReading]
    woocommerce_order_id: Optional[str]

    # ── Invernadero ───────────────────────────────────────────
    validated_readings: List[SensorReading]
    readings_alertas: List[str]
    invernadero_status: Optional[Literal["OPTIMO", "ALERTA", "CRITICO"]]

    # ── GDPR / Ética ──────────────────────────────────────────
    gdpr_consent_verified: bool
    pii_redacted: bool
    ai_act_human_review_required: bool
    gdpr_violations: List[str]

    # ── Campo (SIGPAC/TRACES) ─────────────────────────────────
    sigpac_parcelas: Optional[Dict[str, Any]]
    traces_cert_id: Optional[str]
    traces_cert_payload: Optional[Dict[str, Any]]

    # ── Procesado (Blockchain + IPFS) ─────────────────────────
    gaiachain_tx_hash: Optional[str]
    ipfs_cid: Optional[str]
    content_hash: Optional[str]

    # ── Cliente (WooCommerce + QR) ────────────────────────────
    qr_url: Optional[str]
    qr_hash_cadena: Optional[str]
    order_updated: bool

    # ── Reportes (ELK) ───────────────────────────────────────
    elk_log_id: Optional[str]
    pdf_report_url: Optional[str]

    # ── Rollback / Compensación ───────────────────────────────
    rollback_stack: List[CompensatingAction]   # LIFO — último en entrar, primero en compensar
    compensations_executed: List[str]          # IDs de compensaciones ya ejecutadas

    # ── Control de flujo ──────────────────────────────────────
    current_node: str
    error: Optional[str]
    error_node: Optional[str]
    status: Literal["running", "completed", "failed", "compensating", "human_review"]
    next_action: Optional[str]
