"""
SABIONDA — Gestión de Invernadero Agrovoltaico Hidropónico
Parámetros reales medibles, alertas automáticas, sin buzzwords.

Módulos:
  - Solución nutritiva (pH, EC, temperatura, O₂ disuelto, NPK)
  - Clima invernadero (CO₂, VPD, T°, HR, DLI)
  - Sistema agrovoltaico (irradiancia, kWh, sombra efectiva)
  - Ciclo de cultivo con registro de lote para trazabilidad QR
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/api/v1/invernadero", tags=["invernadero"])


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

class SolucionNutritivaReading(BaseModel):
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
    timestamp: Optional[str] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def set_timestamp(cls, v: Optional[str]) -> str:
        return v or datetime.now(timezone.utc).isoformat()


class ClimaInvernadero(BaseModel):
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
    timestamp: Optional[str] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def set_timestamp(cls, v: Optional[str]) -> str:
        return v or datetime.now(timezone.utc).isoformat()


class LecturaAgrovoltaica(BaseModel):
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
    timestamp: Optional[str] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def set_timestamp(cls, v: Optional[str]) -> str:
        return v or datetime.now(timezone.utc).isoformat()

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
    estado = "ALERTA" if alertas else "OPTIMO"

    payload = req.model_dump()
    payload["alertas"] = alertas
    payload["estado_solucion"] = estado
    payload["rangos_referencia"] = RANGOS_OPTIMOS.get(req.cultivo.value, {})

    return InvernaderoResponse(
        lote_id=req.lote_id,
        accion="registro_solucion_nutritiva",
        estado=estado,
        alertas=alertas,
        payload=payload,
        registrado_en=req.timestamp or datetime.now(timezone.utc).isoformat(),
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

    estado = "ALERTA" if alertas else "OPTIMO"
    payload = req.model_dump()
    payload["alertas"] = alertas
    payload["estado_clima"] = estado

    return InvernaderoResponse(
        lote_id=req.lote_id,
        accion="registro_clima",
        estado=estado,
        alertas=alertas,
        payload=payload,
        registrado_en=req.timestamp or datetime.now(timezone.utc).isoformat(),
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

    payload = req.model_dump()
    payload["delta_temperatura_c"] = delta_t
    payload["excedente_kwh"] = excedente
    payload["balance_energetico"] = "excedente" if excedente > 0 else "deficit"
    payload["beneficio_termico"] = delta_t > 0
    payload["alertas"] = alertas

    return InvernaderoResponse(
        lote_id=req.lote_id,
        accion="registro_agrovoltaico",
        estado="ALERTA" if alertas else "OK",
        alertas=alertas,
        payload=payload,
        registrado_en=req.timestamp or datetime.now(timezone.utc).isoformat(),
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
    """
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
    payload["instruccion"] = (
        f"Llamar a POST /api/v1/trazabilidad/qr/generar con lote_id={req.lote_id} "
        f"y hash_cierre={hash_cierre} para obtener el QR del consumidor final."
    )

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
