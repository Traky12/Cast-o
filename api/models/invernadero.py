"""
Pydantic models para módulo Invernadero Agrovoltaico Hidropónico.
Validación de parámetros: pH, EC, O₂, CO₂, VPD, DLI, agrovoltaico.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class CultivoEnum(str, Enum):
    """Cultivos soportados en sistema hidropónico."""
    TOMATE = "tomate"
    LECHUGA = "lechuga"
    PIMIENTO = "pimiento"
    PEPINO = "pepino"
    FRESA = "fresa"


class SistemaRiegoEnum(str, Enum):
    """Sistemas de riego hidropónico."""
    GOTEO = "goteo"
    NFT = "nft"
    DFT = "dft"
    WICK = "wick"


class EtapasCultivoEnum(str, Enum):
    """Etapas fenológicas del cultivo."""
    VEGETATIVO = "vegetativo"
    FLORACION = "floracion"
    FRUCTIFICACION = "fructificacion"


class EstadoEnum(str, Enum):
    """Estados de validación."""
    OK = "OK"
    OPTIMO = "OPTIMO"
    ALERTA = "ALERTA"
    LOTE_CERRADO = "LOTE_CERRADO"


class TipoFitosanitarioEnum(str, Enum):
    """Tipos de tratamiento fitosanitario."""
    NINGUNO = "ninguno"
    PREVENTIVO = "preventivo"
    CURATIVO = "curativo"
    BIOCONTROL = "biocontrol"


class ActuadorEnum(str, Enum):
    """Tipos de actuadores soportados."""
    VENTILACION = "ventilacion"
    RIEGO = "riego"
    OZONO = "ozono"
    CALEFACCION = "calefaccion"


# ─────────────────────────────────────────────────────────────────────────────
# Requests & Responses
# ─────────────────────────────────────────────────────────────────────────────

class AperturaLoteRequest(BaseModel):
    """Apertura de lote nuevo."""
    explotacion_rea: str
    operador_nif: str
    cultivo: CultivoEnum
    variedad: str
    sistema: SistemaRiegoEnum
    zona: str
    superficie_m2: float = Field(..., gt=0)
    fecha_siembra: str  # YYYY-MM-DD
    semilla_origen: str
    semilla_certificada: bool
    sustrato: str
    eco_certificado: bool
    sigpac_ref: Optional[str] = None


class AperturaLoteResponse(BaseModel):
    """Respuesta apertura de lote."""
    lote_id: str
    estado: EstadoEnum
    payload: Dict


class SolucionNutritivaRequest(BaseModel):
    """Parámetros de solución nutritiva."""
    lote_id: str
    zona: str
    cultivo: CultivoEnum
    sistema: SistemaRiegoEnum
    ph: float = Field(..., ge=5.0, le=8.0)
    ec_ms_cm: float = Field(..., gt=0)
    temp_solucion_c: float = Field(..., ge=0, le=40)
    o2_disuelto_mg_l: float = Field(..., gt=0)
    nitrogeno_ppm: float = Field(..., ge=0)
    fosforo_ppm: float = Field(..., ge=0)
    potasio_ppm: float = Field(..., ge=0)
    caudal_l_h: float = Field(..., gt=0)

    @validator("ph")
    def validate_ph(cls, v):
        if v < 5.0 or v > 8.0:
            raise ValueError("pH debe estar entre 5.0 y 8.0")
        return v


class SolucionNutritivaResponse(BaseModel):
    """Respuesta validación solución nutritiva."""
    estado: EstadoEnum
    alertas: List[str]
    payload: Dict


class ClimaInvernaderoRequest(BaseModel):
    """Parámetros de clima de invernadero."""
    lote_id: str
    zona: str
    cultivo: CultivoEnum
    etapa: EtapasCultivoEnum
    co2_ppm: float = Field(..., ge=300, le=2000)
    vpd_kpa: float = Field(..., ge=0.5, le=3.0)
    temp_aire_c: float = Field(..., ge=10, le=40)
    humedad_relativa_pct: float = Field(..., ge=20, le=95)
    dli_mol_m2_dia: float = Field(..., gt=0)


class ClimaInvernaderoResponse(BaseModel):
    """Respuesta validación clima."""
    estado: EstadoEnum
    alertas: List[str]
    payload: Dict


class AgrovoltaicoRequest(BaseModel):
    """Parámetros de sistema agrovoltaico."""
    lote_id: str
    panel_id: str
    irradiancia_w_m2: float = Field(..., ge=0, le=1200)
    kwh_generados: float = Field(..., gt=0)
    kwh_autoconsumidos: float = Field(..., ge=0)
    temperatura_panel_c: float = Field(..., ge=0, le=100)
    cobertura_sombra_pct: float = Field(..., ge=0, le=100)
    temp_bajo_panel_c: float = Field(..., ge=0, le=50)
    temp_zona_abierta_c: float = Field(..., ge=0, le=50)


class AgrovoltaicoResponse(BaseModel):
    """Respuesta validación agrovoltaico."""
    estado: EstadoEnum
    alertas: List[str]
    payload: Dict = Field(
        default_factory=dict,
        description="Calculadas: delta_temperatura_c, beneficio_termico, excedente_kwh, balance_energetico"
    )


class CosechaRequest(BaseModel):
    """Registro de cosecha."""
    lote_id: str
    fecha_cosecha: str  # YYYY-MM-DD
    kg_cosechados: float = Field(..., gt=0)
    calibre: Optional[str] = None
    brix: Optional[float] = None
    destino: str
    operador_nif: str


class CosechaResponse(BaseModel):
    """Respuesta registro cosecha."""
    estado: EstadoEnum
    payload: Dict


class RangosOptimosResponse(BaseModel):
    """Rangos óptimos para un cultivo."""
    cultivo: CultivoEnum
    parametros: Dict[str, Dict]  # {"ph": {"min": 5.8, "max": 6.3}, ...}


class FitosanitarioRequest(BaseModel):
    """Registro de tratamiento fitosanitario."""
    lote_id: str
    fecha: str  # YYYY-MM-DD
    tipo: TipoFitosanitarioEnum
    justificacion: str
    producto: Optional[str] = None
    operador_nif: str

    @validator("producto")
    def validate_curativo_requires_producto(cls, v, values):
        if "tipo" in values and values["tipo"] == TipoFitosanitarioEnum.CURATIVO:
            if not v:
                raise ValueError("Tipo CURATIVO requiere especificar producto")
        return v


class FitosanitarioResponse(BaseModel):
    """Respuesta registro fitosanitario."""
    estado: EstadoEnum
    payload: Dict


class DatosSensoresRequest(BaseModel):
    """Datos de sensores IoT."""
    temperatura: float = Field(..., ge=0, le=50)
    humedad: float = Field(..., ge=0, le=100)
    co2: float = Field(..., ge=300, le=2000)
    luz: float = Field(..., ge=0, le=2000)
    ph: float = Field(..., ge=5, le=8)
    ec: float = Field(..., ge=0, le=5)
    timestamp: str  # ISO 8601

    @validator("temperatura")
    def validate_temperatura(cls, v):
        if v < 10 or v > 40:
            raise ValueError("Temperatura fuera de rango (10-40°C)")
        return v


class DatosSensoresResponse(BaseModel):
    """Respuesta ingesta de sensores."""
    status: str  # "ok" o error
    alerts: List[str]
    payload: Optional[Dict] = None


class ActuadorControlRequest(BaseModel):
    """Comando de control de actuador."""
    reason: str  # Causa del control


class ActuadorControlResponse(BaseModel):
    """Respuesta control de actuador."""
    tipo: ActuadorEnum
    estado: str  # "encender", "apagar"
    timestamp: datetime
    payload: Dict


# ─────────────────────────────────────────────────────────────────────────────
# Rangos óptimos por cultivo (constantes)
# ─────────────────────────────────────────────────────────────────────────────

RANGOS_OPTIMOS = {
    "tomate": {
        "ph": {"min": 5.8, "max": 6.3},
        "ec": {"min": 2.0, "max": 3.5, "unidad": "mS/cm"},
        "o2_disuelto": {"min": 6.0, "max": 10.0, "unidad": "mg/L"},
        "temp_solucion": {"min": 18, "max": 22, "unidad": "°C"},
        "dli": {"floracion": {"min": 17, "max": 22}, "vegetativo": {"min": 12, "max": 18}},
        "co2": {"min": 800, "max": 1200, "unidad": "ppm"},
    },
    "lechuga": {
        "ph": {"min": 6.0, "max": 6.8},
        "ec": {"min": 1.0, "max": 1.8, "unidad": "mS/cm"},
        "o2_disuelto": {"min": 7.0, "max": 10.0, "unidad": "mg/L"},
        "temp_solucion": {"min": 16, "max": 20, "unidad": "°C"},
        "dli": {"vegetativo": {"min": 10, "max": 15}},
        "co2": {"min": 600, "max": 1000, "unidad": "ppm"},
    },
    "pimiento": {
        "ph": {"min": 5.8, "max": 6.3},
        "ec": {"min": 2.0, "max": 3.0, "unidad": "mS/cm"},
        "o2_disuelto": {"min": 6.0, "max": 10.0, "unidad": "mg/L"},
        "temp_solucion": {"min": 20, "max": 24, "unidad": "°C"},
        "dli": {"floracion": {"min": 16, "max": 21}},
        "co2": {"min": 800, "max": 1200, "unidad": "ppm"},
    },
    "pepino": {
        "ph": {"min": 5.8, "max": 6.2},
        "ec": {"min": 2.0, "max": 3.2, "unidad": "mS/cm"},
        "o2_disuelto": {"min": 6.0, "max": 10.0, "unidad": "mg/L"},
        "temp_solucion": {"min": 20, "max": 24, "unidad": "°C"},
        "dli": {"floracion": {"min": 17, "max": 23}},
        "co2": {"min": 900, "max": 1300, "unidad": "ppm"},
    },
    "fresa": {
        "ph": {"min": 5.8, "max": 6.5},
        "ec": {"min": 1.2, "max": 2.0, "unidad": "mS/cm"},
        "o2_disuelto": {"min": 7.0, "max": 10.0, "unidad": "mg/L"},
        "temp_solucion": {"min": 18, "max": 22, "unidad": "°C"},
        "dli": {"floracion": {"min": 15, "max": 20}},
        "co2": {"min": 700, "max": 1100, "unidad": "ppm"},
    },
}
