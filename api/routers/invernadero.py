"""
SABIONDA — Gestión de Invernadero Agrovoltaico Hidropónico
Parámetros reales medibles, alertas automáticas, sin buzzwords.

Módulos:
  - Solución nutritiva (pH, EC, temperatura, O₂ disuelto, NPK)
  - Clima invernadero (CO₂, VPD, T°, HR, DLI)
  - Sistema agrovoltaico (irradiancia, kWh, sombra efectiva)
  - Ciclo de cultivo con registro de lote para trazabilidad QR
  - Auditoría centralizada de cada acción
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from services.blockchain.evidence_register import EvidenceRegistrar
from services.audit import AuditAction, AuditEvent, AuditLogger, AuditSeverity

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/invernadero", tags=["invernadero"])
audit_logger = AuditLogger()


# ─────────────────────────────────────────────────────────────────────────────
# Enumerados con valores reales
# ─────────────────────────────────────────────────────────────────────────────

class EtapaCultivo(str, Enum):
    SEMILLA = "semilla"
    GERMINACION = "germinacion"
    PLANTULA = "plantula"
    VEGETATIVO = "vegetativo"
    FLORACION = "floracion"
    FRUCTIFICACION = "fructificacion"
    MADURACION = "maduracion"
    COSECHA = "cosecha"
    POST_COSECHA = "post_cosecha"


class SistemaCultivo(str, Enum):
    NFT = "NFT"               # Nutrient Film Technique
    DWC = "DWC"               # Deep Water Culture
    AEROPONICO = "aeroponico"
    GOTEO = "goteo"           # Goteo sobre sustrato inerte
    SUSTRATO = "sustrato"     # Fibra de coco, perlita, etc.


class CultivoHidroponico(str, Enum):
    TOMATE = "tomate"
    LECHUGA = "lechuga"
    PIMIENTO = "pimiento"
    PEPINO = "pepino"
    FRESA = "fresa"
    ALBAHACA = "albahaca"
    ESPINACA = "espinaca"
    CILANTRO = "cilantro"


# ─────────────────────────────────────────────────────────────────────────────
# Mixin reutilizable — evita repetir @field_validator en cada modelo con timestamp
# ─────────────────────────────────────────────────────────────────────────────

class _TimestampMixin(BaseModel):
    timestamp: Optional[str] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def _set_timestamp(cls, v: Optional[str]) -> str:
        return v or datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# Rangos óptimos por cultivo (referencia técnica real)
# ─────────────────────────────────────────────────────────────────────────────

RANGOS_OPTIMOS: dict = {
    "tomate":    {"ph": (5.8, 6.3), "ec": (2.0, 4.0), "temp_sol": (18, 22), "co2": (800, 1200), "vpd": (0.8, 1.2)},
    "lechuga":   {"ph": (5.5, 6.2), "ec": (0.8, 1.6), "temp_sol": (18, 22), "co2": (700, 1000), "vpd": (0.4, 0.8)},
    "pimiento":  {"ph": (5.8, 6.3), "ec": (2.0, 3.5), "temp_sol": (20, 24), "co2": (800, 1200), "vpd": (0.8, 1.2)},
    "pepino":    {"ph": (5.5, 6.0), "ec": (1.7, 2.5), "temp_sol": (20, 24), "co2": (800, 1200), "vpd": (0.8, 1.2)},
    "fresa":     {"ph": (5.5, 6.0), "ec": (1.0, 2.0), "temp_sol": (16, 20), "co2": (700, 900),  "vpd": (0.6, 1.0)},
    "albahaca":  {"ph": (5.5, 6.5), "ec": (0.7, 1.4), "temp_sol": (20, 24), "co2": (700, 1000), "vpd": (0.6, 1.0)},
    "espinaca":  {"ph": (6.0, 7.0), "ec": (1.8, 2.3), "temp_sol": (15, 20), "co2": (700, 900),  "vpd": (0.4, 0.8)},
    "cilantro":  {"ph": (6.0, 6.7), "ec": (1.0, 1.8), "temp_sol": (16, 20), "co2": (700, 900),  "vpd": (0.4, 0.8)},
}


def _alertas_solucion(cultivo: str, ph: float, ec: float,
                      temp_sol: float, o2_disuelto: float) -> list[str]:
    alertas = []
    r = RANGOS_OPTIMOS.get(cultivo, {})
    if r:
        ph_min, ph_max = r["ph"]
        ec_min, ec_max = r["ec"]
        ts_min, ts_max = r["temp_sol"]
        if not (ph_min <= ph <= ph_max):
            alertas.append(f"pH {ph} fuera de rango óptimo [{ph_min}-{ph_max}] para {cultivo}")
        if not (ec_min <= ec <= ec_max):
            alertas.append(f"EC {ec} mS/cm fuera de rango óptimo [{ec_min}-{ec_max}] para {cultivo}")
        if not (ts_min <= temp_sol <= ts_max):
            alertas.append(f"Temperatura solución {temp_sol}°C fuera de rango [{ts_min}-{ts_max}]°C")
    if o2_disuelto < 6.0:
        alertas.append(f"O₂ disuelto crítico: {o2_disuelto} mg/L (mínimo: 6.0 mg/L) — riesgo de hipoxia radicular")
    return alertas


def _alertas_clima(cultivo: str, co2_ppm: float, vpd_kpa: float,
                   temp_aire_c: float, hr_pct: float) -> list[str]:
    alertas = []
    r = RANGOS_OPTIMOS.get(cultivo, {})
    if r:
        co2_min, co2_max = r["co2"]
        vpd_min, vpd_max = r["vpd"]
        if not (co2_min <= co2_ppm <= co2_max):
            alertas.append(f"CO₂ {co2_ppm} ppm fuera de rango [{co2_min}-{co2_max}] para {cultivo}")
        if not (vpd_min <= vpd_kpa <= vpd_max):
            alertas.append(f"VPD {vpd_kpa} kPa fuera de rango [{vpd_min}-{vpd_max}] para {cultivo}")
    if temp_aire_c > 32:
        alertas.append(f"Temperatura aire {temp_aire_c}°C: riesgo de golpe de calor")
    if hr_pct > 85:
        alertas.append(f"HR {hr_pct}% excesiva: riesgo de botrytis y mildiu")
    if hr_pct < 40:
        alertas.append(f"HR {hr_pct}% baja: estrés hídrico por transpiración excesiva")
    return alertas


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de Entrada
# ─────────────────────────────────────────────────────────────────────────────

class SolucionNutritivaReading(_TimestampMixin):
    """Lectura puntual de la solución nutritiva en un circuito hidropónico."""
    lote_id: str = Field(..., description="Identificador único del lote de cultivo")
    zona: str = Field(..., description="Zona o canal hidropónico (ej. 'zona-A1')")
    cultivo: CultivoHidroponico
    sistema: SistemaCultivo
    ph: float = Field(..., ge=4.0, le=8.5, description="pH de la solución [4.0-8.5]")
    ec_ms_cm: float = Field(..., ge=0.0, le=10.0, description="Conductividad eléctrica en mS/cm")
    temp_solucion_c: float = Field(..., ge=10.0, le=35.0, description="Temperatura solución nutritiva (°C)")
    o2_disuelto_mg_l: float = Field(..., ge=0.0, le=20.0, description="Oxígeno disuelto (mg/L)")
    nitrogeno_ppm: Optional[float] = Field(None, ge=0, description="N total en ppm")
    fosforo_ppm: Optional[float] = Field(None, ge=0, description="P en ppm")
    potasio_ppm: Optional[float] = Field(None, ge=0, description="K en ppm")
    calcio_ppm: Optional[float] = Field(None, ge=0)
    magnesio_ppm: Optional[float] = Field(None, ge=0)
    caudal_l_h: Optional[float] = Field(None, ge=0, description="Caudal de riego en L/hora")


class ClimaInvernadero(_TimestampMixin):
    """Lectura del clima interior del invernadero."""
    lote_id: str
    zona: str
    cultivo: CultivoHidroponico
    etapa: EtapaCultivo
    co2_ppm: float = Field(..., ge=300, le=3000, description="CO₂ interior en ppm")
    vpd_kpa: float = Field(..., ge=0.0, le=5.0, description="Vapor Pressure Deficit en kPa")
    temp_aire_c: float = Field(..., ge=0.0, le=50.0, description="Temperatura del aire (°C)")
    humedad_relativa_pct: float = Field(..., ge=0.0, le=100.0, description="Humedad relativa (%)")
    dli_mol_m2_dia: Optional[float] = Field(None, ge=0, description="Daily Light Integral mol/m²/día")


class LecturaAgrovoltaica(_TimestampMixin):
    """
    Lectura del sistema agrovoltaico: generación solar y su impacto sobre el cultivo.
    La integración real mide si la sombra de los paneles beneficia o perjudica al cultivo.
    """
    lote_id: str
    panel_id: str = Field(..., description="Identificador del panel o string fotovoltaico")
    irradiancia_w_m2: float = Field(..., ge=0, description="Irradiancia solar incidente (W/m²)")
    kwh_generados: float = Field(..., ge=0, description="kWh generados en el período")
    kwh_autoconsumidos: float = Field(..., ge=0, description="kWh consumidos por el invernadero")
    temperatura_panel_c: float = Field(..., description="Temperatura superficial del panel (°C)")
    cobertura_sombra_pct: float = Field(..., ge=0, le=100, description="% superficie de cultivo bajo sombra de paneles")
    temp_bajo_panel_c: float = Field(..., description="Temperatura del aire bajo panel (°C)")
    temp_zona_abierta_c: float = Field(..., description="Temperatura de zona sin panel (°C)")

    @property
    def delta_temperatura(self) -> float:
        """Reducción de temperatura real gracias al panel: valor positivo = beneficio."""
        return round(self.temp_zona_abierta_c - self.temp_bajo_panel_c, 2)

    @property
    def excedente_kwh(self) -> float:
        return round(self.kwh_generados - self.kwh_autoconsumidos, 3)


class AperturaLote(BaseModel):
    """Registro de apertura de un lote de cultivo hidropónico."""
    explotacion_rea: str
    operador_nif: str
    cultivo: CultivoHidroponico
    variedad: str = Field(..., description="Variedad específica (ej. 'Raf', 'Ramiro', 'Lolla Rossa')")
    sistema: SistemaCultivo
    zona: str
    superficie_m2: float = Field(..., gt=0, description="Superficie del módulo hidropónico (m²)")
    fecha_siembra: date
    semilla_origen: str = Field(..., description="Proveedor y lote de semilla para trazabilidad")
    semilla_certificada: bool = Field(..., description="Semilla certificada sin tratamientos prohibidos")
    sustrato: Optional[str] = Field(None, description="Sustrato utilizado (fibra coco, perlita, lana roca...)")
    eco_certificado: bool = Field(False, description="Producción ecológica: sin pesticidas sintéticos")
    sigpac_ref: Optional[str] = Field(None, description="Referencia SIGPAC de la parcela con invernadero")


class RegistroFitosanitario(BaseModel):
    """
    Registro de cualquier tratamiento fitosanitario (o su ausencia documentada).
    Para certificación sin químicos: registrar inspecciones con tratamiento=None.
    """
    lote_id: str
    fecha: date
    tipo: str = Field(..., description="preventivo | curativo | biocontrol | ninguno")
    producto: Optional[str] = Field(None, description="Nombre comercial (None si no hay tratamiento)")
    materia_activa: Optional[str] = None
    dosis_g_l_por_1000l: Optional[float] = None
    justificacion: str = Field(..., description="Motivo del tratamiento o de la inspección sin tratamiento")
    plazo_seguridad_dias: int = Field(0, ge=0)
    operador_nif: str


class RegistroCosecha(BaseModel):
    """Registro de cosecha: cierra el ciclo productivo del lote y genera el QR final."""
    lote_id: str
    fecha_cosecha: date
    kg_cosechados: float = Field(..., gt=0)
    calibre: Optional[str] = Field(None, description="Categoría de calibre (Extra, Cat.I, Cat.II)")
    brix: Optional[float] = Field(None, ge=0, le=30, description="Grados Brix (dulzor)")
    destino: str = Field(..., description="mercado_local | exportacion | distribuidor | directo_consumidor")
    operador_nif: str
    notas: Optional[str] = None


class SensorData(BaseModel):
    temperatura: float
    humedad: float
    co2: int
    luz: int
    ph: float
    ec: float
    timestamp: str


class ActuadorCommand(BaseModel):
    reason: str = "automatic_rule"


# ─────────────────────────────────────────────────────────────────────────────
# Respuestas
# ─────────────────────────────────────────────────────────────────────────────

class InvernaderoResponse(BaseModel):
    lote_id: str
    accion: str
    estado: str
    alertas: List[str] = []
    payload: dict
    pendiente_firma: bool = True
    aviso: str = "Registro generado para REVISIÓN y FIRMA del operador"
    registrado_en: str


class LoteResponse(BaseModel):
    lote_id: str
    estado: str
    cultivo: str
    variedad: str
    fecha_apertura: str
    hash_apertura: str
    payload: dict


_ACTUATOR_STATE: dict[str, dict[str, str]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Helper de respuesta — evita repetir el mismo patrón en 4 endpoints
# ─────────────────────────────────────────────────────────────────────────────

def _build_invernadero_response(
    *,
    req: _TimestampMixin,
    accion: str,
    alertas: list[str],
    extra: Optional[dict] = None,
    estado_ok: str = "OPTIMO",
    estado_alerta: str = "ALERTA",
    audit_action: Optional[AuditAction] = None,
) -> InvernaderoResponse:
    estado = estado_alerta if alertas else estado_ok
    payload = req.model_dump(mode="json")
    payload["alertas"] = alertas
    if extra:
        payload.update(extra)
    
    # 🔒 AUDITORÍA: Registrar acción si se proporciona audit_action
    timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
    if audit_action and hasattr(req, "lote_id") and hasattr(req, "operador_nif"):
        try:
            audit_event = AuditEvent(
                action=audit_action,
                actor_nif=req.operador_nif,
                actor_role="operador_invernadero",
                resource_type="lote",
                resource_id=req.lote_id,
                severity=AuditSeverity.WARNING if alertas else AuditSeverity.INFO,
                data={
                    "accion": accion,
                    "estado": estado,
                    "alertas": alertas,
                }
            )
            event_id = audit_logger.log_event(audit_event)
            payload["audit_event_id"] = event_id
        except Exception as e:
            logger.error(f"Fallo auditoría {accion} para lote {req.lote_id}: {e}")
    
    return InvernaderoResponse(
        lote_id=payload["lote_id"],
        accion=accion,
        estado=estado,
        alertas=alertas,
        payload=payload,
        registrado_en=timestamp,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/lote/apertura", response_model=LoteResponse,
             summary="Abrir lote de cultivo hidropónico")
async def abrir_lote(req: AperturaLote) -> LoteResponse:
    """
    Crea un nuevo lote de cultivo. Genera el lote_id único que se usará en
    todos los registros posteriores (nutrición, clima, cosecha) y en el QR final.
    """
    lote_id = f"INVH-{req.explotacion_rea}-{req.cultivo.value.upper()}-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "lote_id": lote_id,
        "explotacion_rea": req.explotacion_rea,
        "cultivo": req.cultivo,
        "variedad": req.variedad,
        "sistema": req.sistema,
        "zona": req.zona,
        "superficie_m2": req.superficie_m2,
        "fecha_siembra": req.fecha_siembra.isoformat(),
        "semilla_origen": req.semilla_origen,
        "semilla_certificada": req.semilla_certificada,
        "sustrato": req.sustrato,
        "eco_certificado": req.eco_certificado,
        "sigpac_ref": req.sigpac_ref,
        "apertura_timestamp": now,
    }
    hash_apertura = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()
    
    # 🔒 AUDITORÍA: Registrar apertura de lote en cadena inmutable
    try:
        audit_event = AuditEvent(
            action=AuditAction.APERTURA_LOTE,
            actor_nif=req.operador_nif,
            actor_role="operador_invernadero",
            resource_type="lote",
            resource_id=lote_id,
            severity=AuditSeverity.INFO,
            data={
                "cultivo": req.cultivo.value,
                "variedad": req.variedad,
                "explotacion_rea": req.explotacion_rea,
                "superficie_m2": req.superficie_m2,
                "fecha_siembra": req.fecha_siembra.isoformat(),
                "eco_certificado": req.eco_certificado,
                "hash_apertura": hash_apertura,
            }
        )
        audit_logger.log_event(audit_event)
    except Exception as e:
        logger.error(f"Fallo auditoría apertura para lote {lote_id}: {e}")
    
    return LoteResponse(
        lote_id=lote_id,
        estado="abierto",
        cultivo=req.cultivo,
        variedad=req.variedad,
        fecha_apertura=now,
        hash_apertura=hash_apertura,
        payload=payload,
    )


@router.post("/solucion-nutritiva", response_model=InvernaderoResponse,
             summary="Registrar lectura de solución nutritiva")
async def registrar_solucion_nutritiva(req: SolucionNutritivaReading) -> InvernaderoResponse:
    """
    Registra los parámetros de la solución nutritiva y evalúa si están dentro
    de los rangos óptimos para el cultivo. Genera alertas accionables.
    """
    alertas = _alertas_solucion(
        req.cultivo.value, req.ph, req.ec_ms_cm,
        req.temp_solucion_c, req.o2_disuelto_mg_l,
    )
    return _build_invernadero_response(
        req=req,
        accion="registro_solucion_nutritiva",
        alertas=alertas,
        extra={
            "estado_solucion": "ALERTA" if alertas else "OPTIMO",
            "rangos_referencia": RANGOS_OPTIMOS.get(req.cultivo.value, {}),
        },
        audit_action=AuditAction.REGISTRO_SOLUCION,
    )


@router.post("/clima", response_model=InvernaderoResponse,
             summary="Registrar lectura de clima interior")
async def registrar_clima(req: ClimaInvernadero) -> InvernaderoResponse:
    """
    Registra los parámetros climáticos del invernadero y detecta desviaciones
    de CO₂, VPD, temperatura y humedad respecto a los óptimos por cultivo/etapa.
    """
    alertas = _alertas_clima(
        req.cultivo.value, req.co2_ppm, req.vpd_kpa,
        req.temp_aire_c, req.humedad_relativa_pct,
    )

    # Alerta DLI: si tenemos dato y está bajo para etapa de fructificación
    if req.dli_mol_m2_dia is not None:
        if req.etapa in (EtapaCultivo.FLORACION, EtapaCultivo.FRUCTIFICACION) and req.dli_mol_m2_dia < 15:
            alertas.append(
                f"DLI {req.dli_mol_m2_dia} mol/m²/día insuficiente para {req.etapa.value} "
                f"(mínimo recomendado: 15 mol/m²/día)"
            )

    return _build_invernadero_response(
        req=req,
        accion="registro_clima",
        alertas=alertas,
        extra={"estado_clima": "ALERTA" if alertas else "OPTIMO"},
        audit_action=AuditAction.REGISTRO_CLIMA,
    )


@router.post("/agrovoltaico", response_model=InvernaderoResponse,
             summary="Registrar lectura agrovoltaica")
async def registrar_agrovoltaico(req: LecturaAgrovoltaica) -> InvernaderoResponse:
    """
    Registra producción solar y su impacto real sobre el cultivo.
    Calcula el delta térmico (beneficio de sombra) y el excedente energético.
    """
    alertas = []
    delta_t = req.temp_zona_abierta_c - req.temp_bajo_panel_c
    excedente = round(req.kwh_generados - req.kwh_autoconsumidos, 3)

    if req.cobertura_sombra_pct > 40:
        alertas.append(
            f"Cobertura de sombra {req.cobertura_sombra_pct}% excede 40%: "
            f"revisar impacto sobre DLI del cultivo"
        )
    if req.temperatura_panel_c > 75:
        alertas.append(
            f"Temperatura panel {req.temperatura_panel_c}°C supera 75°C: "
            f"posible reducción de eficiencia fotovoltaica"
        )

    return _build_invernadero_response(
        req=req,
        accion="registro_agrovoltaico",
        alertas=alertas,
        extra={
            "delta_temperatura_c": delta_t,
            "excedente_kwh": excedente,
            "balance_energetico": "excedente" if excedente > 0 else "deficit",
            "beneficio_termico": delta_t > 0,
        },
        estado_ok="OK",
        audit_action=AuditAction.REGISTRO_AGROVOLTAICO,
    )


@router.post("/fitosanitario", response_model=InvernaderoResponse,
             summary="Registrar tratamiento fitosanitario o inspección sin tratamiento")
async def registrar_fitosanitario(req: RegistroFitosanitario) -> InvernaderoResponse:
    """
    Registra cada tratamiento fitosanitario (o su ausencia) del lote.
    Para certificación eco/sin químicos: documentar inspecciones con tipo='ninguno'.
    Cada registro queda firmado para trazabilidad blockchain.
    """
    alertas = []
    if req.tipo == "curativo" and not req.producto:
        raise HTTPException(
            status_code=422,
            detail="Un tratamiento curativo requiere nombre del producto.",
        )
    if req.dosis_g_l_por_1000l and req.dosis_g_l_por_1000l > 500:
        alertas.append("Dosis elevada: verificar ficha técnica y PHI antes de aplicar.")

    payload = req.model_dump(mode="json")
    payload["eco_compatible"] = req.tipo in ("ninguno", "biocontrol", "preventivo") and not req.materia_activa
    payload["alertas"] = alertas

    # 🔒 AUDITORÍA: Registrar tratamiento fitosanitario
    try:
        audit_event = AuditEvent(
            action=AuditAction.REGISTRO_FITOSANITARIO,
            actor_nif=req.operador_nif if hasattr(req, 'operador_nif') else "sistema",
            actor_role="operador_invernadero",
            resource_type="lote",
            resource_id=req.lote_id,
            severity=AuditSeverity.INFO,
            data={
                "tipo_tratamiento": req.tipo,
                "producto": req.producto,
                "eco_compatible": payload["eco_compatible"],
                "fecha_aplicacion": req.fecha_aplicacion.isoformat() if hasattr(req, 'fecha_aplicacion') else None,
            }
        )
        event_id = audit_logger.log_event(audit_event)
        payload["audit_event_id"] = event_id
    except Exception as e:
        logger.error(f"Fallo auditoría fitosanitario para lote {req.lote_id}: {e}")

    return InvernaderoResponse(
        lote_id=req.lote_id,
        accion="registro_fitosanitario",
        estado="OK",
        alertas=alertas,
        payload=payload,
        registrado_en=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/cosecha", response_model=InvernaderoResponse,
             summary="Registrar cosecha y cerrar ciclo del lote")
async def registrar_cosecha(req: RegistroCosecha) -> InvernaderoResponse:
    """
    Cierra el ciclo del lote con los datos de cosecha.
    Este endpoint genera el hash final del lote: es la base del QR que
    recibe el cliente final y que puede verificar en blockchain.
    Registra el lote en GaiaChain para trazabilidad inmutable.
    """
    import tempfile
    
    now = datetime.now(timezone.utc).isoformat()
    payload = req.model_dump(mode="json")
    payload["timestamp_cosecha"] = now

    # Hash de cierre de lote — este valor se embebe en el QR del consumidor
    hash_cierre = hashlib.sha256(
        json.dumps(
            {
                "lote_id": req.lote_id,
                "fecha_cosecha": req.fecha_cosecha.isoformat(),
                "kg_cosechados": req.kg_cosechados,
                "destino": req.destino,
                "timestamp": now,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()

    payload["hash_cierre_lote"] = hash_cierre
    payload["qr_pendiente_generacion"] = True
    
    # Registrar en GaiaChain para trazabilidad inmutable
    try:
        registrar = EvidenceRegistrar()
        # Crear archivo temporal con el payload JSON para registro blockchain
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(payload, tmp)
            tmp_path = tmp.name
        
        try:
            evidence_result = registrar.register_asset(
                asset_path=tmp_path,
                metadata={
                    "lote_id": req.lote_id,
                    "fecha_cosecha": req.fecha_cosecha.isoformat(),
                    "kg_cosechados": req.kg_cosechados,
                    "calibre": req.calibre,
                    "brix": req.brix,
                    "destino": req.destino,
                    "operador_nif": req.operador_nif,
                    "tipo_registro": "cosecha_lote",
                    "timestamp": now,
                },
            )
            payload["blockchain"] = {
                "registered": True,
                "txid": evidence_result["txid"],
                "network": evidence_result.get("network", "gaia_testnet"),
                "timestamp": evidence_result["timestamp"],
            }
        finally:
            import os
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        # Si GaiaChain falla, continuar pero documentar el intento fallido
        payload["blockchain"] = {
            "registered": False,
            "error": str(e),
            "fallback": "local_only",
        }
    
    payload["instruccion"] = (
        f"Llamar a POST /api/v1/trazabilidad/qr/generar con lote_id={req.lote_id} "
        f"y hash_cierre={hash_cierre} para obtener el QR del consumidor final."
    )

    # 🔒 AUDITORÍA: Registrar cierre de cosecha en cadena inmutable
    try:
        audit_event = AuditEvent(
            action=AuditAction.REGISTRO_COSECHA,
            actor_nif=req.operador_nif,
            actor_role="operador_invernadero",
            resource_type="lote",
            resource_id=req.lote_id,
            severity=AuditSeverity.INFO,
            data={
                "kg_cosechados": req.kg_cosechados,
                "calibre": req.calibre,
                "brix": req.brix,
                "destino": req.destino,
                "hash_cierre_lote": hash_cierre,
                "blockchain_registered": payload["blockchain"]["registered"],
                "blockchain_txid": payload["blockchain"].get("txid"),
            }
        )
        event_id = audit_logger.log_event(audit_event)
        payload["audit_event_id"] = event_id
    except Exception as e:
        logger.error(f"Fallo auditoría cosecha para lote {req.lote_id}: {e}")

    return InvernaderoResponse(
        lote_id=req.lote_id,
        accion="cierre_cosecha",
        estado="LOTE_CERRADO",
        alertas=[],
        payload=payload,
        registrado_en=now,
    )


@router.get("/rangos/{cultivo}",
            summary="Consultar rangos óptimos para un cultivo")
async def get_rangos_optimos(cultivo: CultivoHidroponico) -> dict:
    """Devuelve los rangos óptimos de parámetros para el cultivo indicado."""
    rangos = RANGOS_OPTIMOS.get(cultivo.value)
    if not rangos:
        raise HTTPException(status_code=404, detail=f"Cultivo '{cultivo}' no encontrado")
    return {
        "cultivo": cultivo,
        "parametros": {
            "ph": {"min": rangos["ph"][0], "max": rangos["ph"][1], "unidad": "pH"},
            "ec": {"min": rangos["ec"][0], "max": rangos["ec"][1], "unidad": "mS/cm"},
            "temperatura_solucion": {"min": rangos["temp_sol"][0], "max": rangos["temp_sol"][1], "unidad": "°C"},
            "co2": {"min": rangos["co2"][0], "max": rangos["co2"][1], "unidad": "ppm"},
            "vpd": {"min": rangos["vpd"][0], "max": rangos["vpd"][1], "unidad": "kPa"},
            "o2_disuelto": {"min": 6.0, "unidad": "mg/L", "nota": "Mínimo absoluto para todas las especies"},
        },
    }


@router.post("/datos-sensores", summary="Ingesta ambiental rápida para control en tiempo real")
async def registrar_datos_sensores(data: SensorData) -> dict:
    alerts: list[str] = []
    if data.temperatura > 35 or data.temperatura < 10:
        raise HTTPException(status_code=400, detail="Temperatura fuera de rango")
    if data.ph > 7.0 or data.ph < 4.0:
        raise HTTPException(status_code=400, detail="pH fuera de rango")
    if data.humedad > 90 or data.humedad < 20:
        alerts.append("Humedad fuera de objetivo operativo")
    if data.co2 > 2000 or data.co2 < 350:
        alerts.append("CO2 fuera de banda recomendada")
    if data.ec > 3.0 or data.ec < 1.5:
        alerts.append("EC fuera de banda de operación hidropónica")
    return {
        "status": "ok",
        "alerts": alerts,
        "data": data.model_dump(),
    }


@router.post("/actuadores/{tipo}/{estado}", summary="Control manual/automático de actuadores")
async def controlar_actuador(tipo: str, estado: str, command: ActuadorCommand) -> dict:
    allowed_types = {"ventilacion", "riego", "iluminacion", "sombra", "nutrientes", "calefaccion"}
    allowed_states = {"encender", "apagar", "abrir", "cerrar", "ajustar"}

    if tipo not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Actuador no soportado: {tipo}")
    if estado not in allowed_states:
        raise HTTPException(status_code=400, detail=f"Estado no soportado: {estado}")

    applied_at = datetime.now(timezone.utc).isoformat()
    _ACTUATOR_STATE[tipo] = {
        "estado": estado,
        "reason": command.reason,
        "updated_at": applied_at,
    }
    return {
        "status": "ok",
        "tipo": tipo,
        "estado": estado,
        "reason": command.reason,
        "updated_at": applied_at,
    }
