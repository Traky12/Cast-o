"""
CASTÚO-SYSTEM™ v3.1 — Router Actuadores
Control REST de actuadores del invernadero agrovoltaico hidropónico.

Endpoints:
  POST /api/v1/actuadores/control           — Controlar un actuador
  POST /api/v1/actuadores/emergencia        — Parada de emergencia (todos los actuadores)
  GET  /api/v1/actuadores/estado            — Estado actual de todos los actuadores
  GET  /api/v1/actuadores/historial         — Historial de eventos recientes
  POST /api/v1/actuadores/automatico        — Ejecutar recomendación automática por sensor
  GET  /api/v1/actuadores/sombra/ajuste     — Calcular ajuste de sombra agrovoltaica

Autenticación: JWT HS256 — roles requeridos: admin | editor
"""

from __future__ import annotations

import sys
import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from services.actuators.actuator_controller import (
    ActuatorController,
    Actuador,
    Accion,
    get_controller,
    recomendar_accion_temperatura,
    recomendar_accion_ph,
    recomendar_accion_ec,
    recomendar_sombra_agrovoltaica,
)
from services.energy.modbus_client import calculate_shadow_adjustment

router = APIRouter(prefix="/api/v1/actuadores", tags=["actuadores"])
_bearer = HTTPBearer(auto_error=False)


# ── Auth ───────────────────────────────────────────────────────────────────────

def _verify_jwt(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """JWT HS256 — idéntico al patrón del resto de routers."""
    import jwt as pyjwt
    import os

    def _secret() -> str:
        path = os.getenv("JWT_SECRET_FILE", "")
        if path:
            try:
                with open(path) as f:
                    return f.read().strip()
            except OSError:
                pass
        return os.getenv("JWT_SECRET", "")

    secret = _secret()
    if not secret:
        return {"sub": "dev-mode", "role": "admin"}

    if not credentials:
        raise HTTPException(status_code=401, detail="Token JWT requerido")

    try:
        payload = pyjwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Token inválido: {exc}")

    role = payload.get("role", "")
    if role not in ("admin", "editor"):
        raise HTTPException(status_code=403, detail=f"Rol '{role}' sin permiso de control de actuadores")

    return payload


# ── Modelos ────────────────────────────────────────────────────────────────────

class ControlRequest(BaseModel):
    actuador: str = Field(
        ...,
        description="Nombre del actuador",
        examples=["ventilacion", "acido", "sombra"],
    )
    accion: str = Field(
        ...,
        description="Acción a ejecutar",
        examples=["encender", "apagar", "ajustar", "pulso"],
    )
    zona: str = Field("general", description="Zona del invernadero")
    valor: Optional[float] = Field(
        None,
        description="Valor numérico: % para ventilación/sombra, ml para dosificadoras",
    )
    duracion_seg: Optional[int] = Field(
        None,
        description="Duración del pulso en segundos (solo para accion='pulso')",
    )
    triggered_by: str = Field("manual", description="Origen del comando: manual | ia | n8n | nodered")


class AutomaticoRequest(BaseModel):
    """Ejecuta la recomendación automática a partir de la lectura de un sensor."""
    zona: str = Field("general")
    temperatura_c: Optional[float] = None
    temp_min: Optional[float] = Field(None, description="Temperatura mínima óptima (°C)")
    temp_max: Optional[float] = Field(None, description="Temperatura máxima óptima (°C)")
    ph: Optional[float] = None
    ph_min: Optional[float] = None
    ph_max: Optional[float] = None
    ec_ms_cm: Optional[float] = None
    ec_min: Optional[float] = None
    ec_max: Optional[float] = None
    luz_par_umol: Optional[float] = None
    cultivo: str = "tomate"
    cobertura_sombra_actual_pct: Optional[float] = Field(None)


class ControlResponse(BaseModel):
    ok: bool
    actuador: str
    accion: str
    zona: str
    valor: Optional[float] = None
    mqtt_published: bool
    timestamp: str
    mensaje: Optional[str] = None


class EmergenciaResponse(BaseModel):
    ok: bool
    accion: str
    zona: str
    actuadores_apagados: int
    timestamp: str


class EstadoResponse(BaseModel):
    estado: dict
    timestamp: str
    total_actuadores: int
    actuadores_activos: int


class SombraAjusteResponse(BaseModel):
    accion: str
    nueva_cobertura_pct: float
    delta_pct: float
    luz_actual: float
    luz_optima: float
    motivo: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/control", response_model=ControlResponse,
             summary="Controlar un actuador del invernadero")
async def controlar_actuador(
    req: ControlRequest,
    _jwt: dict = Depends(_verify_jwt),
) -> ControlResponse:
    """
    Envía un comando a un actuador del invernadero vía MQTT.
    El estado queda registrado en memoria y en InfluxDB (si está configurado).
    """
    # Validar enum valores
    valid_actuadores = {a.value for a in Actuador}
    valid_acciones = {a.value for a in Accion}

    if req.actuador not in valid_actuadores:
        raise HTTPException(
            status_code=422,
            detail=f"Actuador '{req.actuador}' no válido. Opciones: {sorted(valid_actuadores)}",
        )
    if req.accion not in valid_acciones:
        raise HTTPException(
            status_code=422,
            detail=f"Acción '{req.accion}' no válida. Opciones: {sorted(valid_acciones)}",
        )
    if req.accion == Accion.AJUSTAR.value and req.valor is None:
        raise HTTPException(status_code=422, detail="La acción 'ajustar' requiere 'valor'")
    if req.accion == Accion.PULSO.value and req.valor is None:
        raise HTTPException(status_code=422, detail="La acción 'pulso' requiere 'valor' (ml o segundos)")

    ctrl = get_controller()
    result = ctrl.control(
        actuador=req.actuador,
        accion=req.accion,
        zona=req.zona,
        valor=req.valor,
        duracion_seg=req.duracion_seg,
        triggered_by=req.triggered_by,
    )

    # Persistir en InfluxDB (no bloqueante)
    try:
        from services.influxdb.influx_writer import get_writer
        get_writer().write_actuator_event(
            actuador=req.actuador,
            accion=req.accion,
            zona=req.zona,
            triggered_by=req.triggered_by,
            valor=req.valor,
        )
    except Exception:
        pass  # InfluxDB no disponible no interrumpe el control

    return ControlResponse(
        ok=result["ok"],
        actuador=result["actuador"],
        accion=result["accion"],
        zona=result["zona"],
        valor=result.get("valor"),
        mqtt_published=result["mqtt_published"],
        timestamp=result["timestamp"],
        mensaje=f"Comando enviado: {req.accion} {req.actuador} en {req.zona}",
    )


@router.post("/emergencia", response_model=EmergenciaResponse,
             summary="Parada de emergencia — apaga todos los actuadores")
async def emergencia_stop(
    zona: str = "all",
    _jwt: dict = Depends(_verify_jwt),
) -> EmergenciaResponse:
    """
    Parada de emergencia inmediata. Apaga todos los actuadores de la zona
    indicada (o todos si zona='all'). El evento queda registrado.
    """
    ctrl = get_controller()
    result = ctrl.emergencia_stop(zona=zona)
    return EmergenciaResponse(
        ok=result["ok"],
        accion="emergencia_stop",
        zona=zona,
        actuadores_apagados=result["actuadores_apagados"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/estado", response_model=EstadoResponse,
            summary="Estado actual de todos los actuadores")
async def get_estado(
    zona: Optional[str] = None,
    _jwt: dict = Depends(_verify_jwt),
) -> EstadoResponse:
    """Retorna el estado en memoria de cada actuador con su última acción."""
    ctrl = get_controller()
    estado = ctrl.get_status(zona=zona)
    activos = sum(1 for v in estado.values() if v.get("on", False))
    return EstadoResponse(
        estado=estado,
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_actuadores=len(estado),
        actuadores_activos=activos,
    )


@router.get("/historial",
            summary="Historial de los últimos eventos de actuación")
async def get_historial(
    limit: int = 50,
    _jwt: dict = Depends(_verify_jwt),
) -> dict:
    """Retorna los últimos N eventos de control (máximo 500 en memoria)."""
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit debe estar entre 1 y 500")
    ctrl = get_controller()
    events = ctrl.get_history(limit=limit)
    return {
        "total": len(events),
        "eventos": events,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/automatico",
             summary="Ejecutar recomendación automática basada en lectura de sensores")
async def control_automatico(
    req: AutomaticoRequest,
    _jwt: dict = Depends(_verify_jwt),
) -> dict:
    """
    Analiza los parámetros recibidos y aplica las acciones correctoras
    recomendadas automáticamente (temperatura, pH, EC, sombra).

    Retorna la lista de acciones ejecutadas y las que no fueron necesarias.
    """
    ctrl = get_controller()
    acciones_ejecutadas = []
    sin_accion = []

    # Control de temperatura
    if req.temperatura_c is not None:
        t_min = req.temp_min or 18.0
        t_max = req.temp_max or 28.0
        rec = recomendar_accion_temperatura(req.temperatura_c, t_min, t_max)
        if rec:
            r = ctrl.control(
                actuador=rec["actuador"], accion=rec["accion"],
                zona=req.zona, valor=rec.get("valor"), triggered_by="automatico",
            )
            acciones_ejecutadas.append({**r, "motivo": rec["motivo"]})
        else:
            sin_accion.append({"sensor": "temperatura", "motivo": f"Temperatura {req.temperatura_c}°C en rango [{t_min}-{t_max}]°C"})

    # Control de pH
    if req.ph is not None:
        ph_min = req.ph_min or 5.5
        ph_max = req.ph_max or 6.5
        rec = recomendar_accion_ph(req.ph, ph_min, ph_max)
        if rec:
            r = ctrl.control(
                actuador=rec["actuador"], accion=rec["accion"],
                zona=req.zona, valor=rec.get("valor"),
                duracion_seg=rec.get("duracion_seg"), triggered_by="automatico",
            )
            acciones_ejecutadas.append({**r, "motivo": rec["motivo"]})
        else:
            sin_accion.append({"sensor": "ph", "motivo": f"pH {req.ph} en rango [{ph_min}-{ph_max}]"})

    # Control de EC
    if req.ec_ms_cm is not None:
        ec_min = req.ec_min or 1.5
        ec_max = req.ec_max or 3.0
        rec = recomendar_accion_ec(req.ec_ms_cm, ec_min, ec_max)
        if rec:
            r = ctrl.control(
                actuador=rec["actuador"], accion=rec["accion"],
                zona=req.zona, valor=rec.get("valor"),
                duracion_seg=rec.get("duracion_seg"), triggered_by="automatico",
            )
            acciones_ejecutadas.append({**r, "motivo": rec["motivo"]})
        else:
            sin_accion.append({"sensor": "ec", "motivo": f"EC {req.ec_ms_cm} mS/cm en rango [{ec_min}-{ec_max}]"})

    # Control de sombra agrovoltaica
    if req.luz_par_umol is not None:
        rec = recomendar_sombra_agrovoltaica(
            luz_actual_umol=req.luz_par_umol,
            cultivo=req.cultivo,
            cobertura_actual_pct=req.cobertura_sombra_actual_pct or 20.0,
        )
        if rec:
            r = ctrl.control(
                actuador=rec["actuador"], accion=rec["accion"],
                zona=req.zona, valor=rec.get("valor"), triggered_by="automatico",
            )
            acciones_ejecutadas.append({**r, "motivo": rec["motivo"]})
        else:
            sin_accion.append({"sensor": "luz_par", "motivo": f"Luz PAR {req.luz_par_umol} μmol/m²/s en rango"})

    return {
        "ok": True,
        "zona": req.zona,
        "acciones_ejecutadas": len(acciones_ejecutadas),
        "sin_accion_requerida": len(sin_accion),
        "detalle": {
            "ejecutadas": acciones_ejecutadas,
            "sin_accion": sin_accion,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/sombra/ajuste", response_model=SombraAjusteResponse,
            summary="Calcular ajuste óptimo de sombra agrovoltaica")
async def calcular_ajuste_sombra(
    luz_par_umol: float,
    cultivo: str = "tomate",
    cobertura_actual_pct: float = 20.0,
) -> SombraAjusteResponse:
    """
    Calcula el ajuste recomendado de la pantalla de sombra para maximizar
    la producción fotovoltaica sin comprometer el DLI del cultivo.
    No requiere autenticación (lectura de recomendación).
    """
    resultado = calculate_shadow_adjustment(
        luz_par_actual=luz_par_umol,
        cultivo=cultivo,
        cobertura_actual_pct=cobertura_actual_pct,
    )
    return SombraAjusteResponse(**resultado)


@router.get("/actuadores-disponibles",
            summary="Listar todos los actuadores y acciones disponibles")
async def listar_actuadores() -> dict:
    """Retorna el catálogo de actuadores y acciones soportadas. Sin autenticación."""
    return {
        "actuadores": [
            {"id": a.value, "descripcion": _actuador_desc(a.value)} for a in Actuador
        ],
        "acciones": [
            {"id": a.value, "descripcion": _accion_desc(a.value)} for a in Accion
        ],
    }


def _actuador_desc(a: str) -> str:
    desc = {
        "ventilacion":     "Control de ventiladores (temperatura/HR)",
        "calefaccion":     "Sistema de calefacción",
        "riego":           "Bombas de riego hidropónico",
        "iluminacion_led": "Iluminación LED suplementaria (PWM)",
        "sombra":          "Pantallas de sombra motorizadas (agrovoltaico)",
        "nutrientes_a":    "Bomba peristáltica nutrientes concentrado A",
        "nutrientes_b":    "Bomba peristáltica nutrientes concentrado B",
        "acido":           "Bomba dosificadora de ácido (bajada pH)",
        "base":            "Bomba dosificadora de base (subida pH)",
        "co2_inyeccion":   "Inyección de CO₂ enriquecido",
    }
    return desc.get(a, a)


def _accion_desc(a: str) -> str:
    desc = {
        "encender":   "Activar el actuador",
        "apagar":     "Desactivar el actuador",
        "pulso":      "Activar N segundos y apagar (dosificadoras)",
        "ajustar":    "Ajustar a valor% (ventiladores PWM, sombra %)",
        "emergencia": "Parada de emergencia",
    }
    return desc.get(a, a)
