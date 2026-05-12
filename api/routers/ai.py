"""
CASTÚO-SYSTEM™ v3.1 — Endpoint IA predictiva
POST /api/v1/ai/predict  → análisis Mistral + predicciones agro

Autenticación: mismo JWT que /validar_lote (roles: admin, editor, api)
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# Paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

logger = logging.getLogger("castuo.ai")

router = APIRouter(prefix="/api/v1/ai", tags=["ia"])

# ── Auth (reutiliza lógica de skills.py) ─────────────────────────────────────

import time
import jwt as _jwt

_ALLOWED_ROLES = {"admin", "editor", "api"}


def _read_secret(name: str) -> str:
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            pass
    return os.getenv(name, "")


async def _verify_bearer(
    request: "Any" = None,
) -> dict:
    """Mismo middleware JWT que /validar_lote."""
    from fastapi import Request
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

    secret = _read_secret("JWT_SECRET")
    if not secret:
        logger.warning("[AI] JWT_SECRET no configurado — modo dev, sin autenticación")
        return {"sub": "dev", "role": "admin"}

    from fastapi import Request as _Req
    # Inyectado por FastAPI como Depends
    return {"sub": "unknown", "role": "admin"}


# Dependency real
from fastapi import Request as _Request
from fastapi.security import HTTPAuthorizationCredentials as _Creds, HTTPBearer as _Bearer

_bearer_scheme = _Bearer(auto_error=False)


async def _auth(
    credentials: Optional[_Creds] = Depends(_bearer_scheme),
) -> dict:
    secret = _read_secret("JWT_SECRET")
    if not secret:
        logger.warning("[AI] JWT_SECRET no configurado — modo dev")
        return {"sub": "dev", "role": "admin"}

    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header requerido")

    try:
        payload = _jwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except _jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except _jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

    role = payload.get("role", "")
    if role not in _ALLOWED_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Rol '{role}' no autorizado. Requerido: {sorted(_ALLOWED_ROLES)}",
        )
    return payload


# ── Models ────────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    tipo: str = Field(
        ...,
        description="Tipo de predicción: yield_prediction | anomaly_detection | irrigation_advice | livestock_health",
    )
    datos: dict[str, Any] = Field(
        default_factory=dict,
        description="Datos del sensor / contexto agronómico",
    )
    cultivo: Optional[str] = Field(None, description="Especie vegetal o animal analizada")
    parcela_sigpac: Optional[str] = Field(None, description="Referencia SIGPAC")
    consulta_libre: Optional[str] = Field(
        None,
        description="Pregunta en lenguaje natural para análisis con Mistral",
    )


class PredictResponse(BaseModel):
    tipo: str
    resultado: dict[str, Any]
    proveedor_ia: str
    modelo: str
    confianza: Optional[float] = None
    recomendacion: Optional[str] = None
    generado_en: str


# ── Lógica interna ────────────────────────────────────────────────────────────

def _yield_prediction(datos: dict, cultivo: str | None) -> dict:
    """
    Predicción de rendimiento basada en datos ambientales.
    Cuando Mistral no está configurado retorna estimación basada en reglas.
    """
    humedad = float(datos.get("humedad_pct", 65))
    temperatura = float(datos.get("temperatura_c", 22))
    radiacion = float(datos.get("radiacion_par", 400))

    # Índice de condiciones óptimas simplificado (0–1)
    h_score = 1.0 - abs(humedad - 70) / 70
    t_score = 1.0 - abs(temperatura - 22) / 30
    r_score = min(radiacion / 500, 1.0)
    ici = round((h_score + t_score + r_score) / 3, 3)

    rendimiento_base = {
        "lechuga": 4.5,
        "tomate": 12.0,
        "cannabis_medicinal": 0.8,
        "espinaca": 3.0,
    }.get((cultivo or "").lower(), 5.0)

    kg_m2 = round(rendimiento_base * ici, 2)

    return {
        "ici": ici,
        "kg_m2_estimado": kg_m2,
        "kg_m2_optimo": rendimiento_base,
        "eficiencia_pct": round(ici * 100, 1),
        "factores": {
            "humedad_score": round(h_score, 3),
            "temperatura_score": round(t_score, 3),
            "radiacion_score": round(r_score, 3),
        },
    }


def _anomaly_detection(datos: dict) -> dict:
    """
    Detección de anomalías en sensores IoT.
    Compara valores con rangos seguros documentados.
    """
    anomalies = []
    RANGES = {
        "humedad_pct":     (30.0, 95.0),
        "temperatura_c":   (10.0, 40.0),
        "ph":              (5.5, 7.5),
        "co2_ppm":         (300.0, 2000.0),
        "ec_ms_cm":        (0.5, 4.0),
        "presion_bar":     (0.5, 8.0),
    }
    for key, (lo, hi) in RANGES.items():
        if key in datos:
            val = float(datos[key])
            if val < lo:
                anomalies.append({"sensor": key, "valor": val, "limite": lo, "tipo": "bajo"})
            elif val > hi:
                anomalies.append({"sensor": key, "valor": val, "limite": hi, "tipo": "alto"})

    return {
        "anomalias_detectadas": len(anomalies),
        "anomalias": anomalies,
        "estado": "ALERTA" if anomalies else "NORMAL",
    }


def _irrigation_advice(datos: dict, cultivo: str | None) -> dict:
    """Consejo de riego basado en tensión matricial y VPD."""
    tension = float(datos.get("tension_matricial_cb", 20))
    humedad = float(datos.get("humedad_pct", 60))
    temperatura = float(datos.get("temperatura_c", 25))

    # VPD aproximado
    vpd = round((1 - humedad / 100) * 0.6108 * (17.27 * temperatura / (temperatura + 237.3)), 3)

    if tension > 50 or humedad < 45:
        accion = "REGAR_URGENTE"
        dosis_l_m2 = 3.0
    elif tension > 30 or humedad < 60:
        accion = "REGAR"
        dosis_l_m2 = 1.5
    else:
        accion = "NO_REGAR"
        dosis_l_m2 = 0.0

    return {
        "accion": accion,
        "dosis_l_m2": dosis_l_m2,
        "tension_matricial_cb": tension,
        "vpd_kpa": vpd,
        "cultivo": cultivo or "genérico",
    }


def _livestock_health(datos: dict) -> dict:
    """Evaluación de salud animal básica."""
    temperatura = float(datos.get("temperatura_c", 38.5))
    peso = float(datos.get("peso_kg", 500))
    especie = datos.get("especie", "vacuno")

    TEMP_RANGES = {
        "vacuno":  (38.0, 39.5),
        "porcino": (38.0, 39.5),
        "ovino":   (38.5, 40.0),
        "caprino": (38.5, 40.5),
        "aves":    (40.5, 42.0),
    }
    lo, hi = TEMP_RANGES.get(especie, (38.0, 39.5))
    estado = "NORMAL" if lo <= temperatura <= hi else (
        "HIPOTERMIA" if temperatura < lo else "FIEBRE"
    )

    return {
        "especie": especie,
        "temperatura_c": temperatura,
        "peso_kg": peso,
        "estado_sanitario": estado,
        "alerta": estado != "NORMAL",
        "umbral_inferior": lo,
        "umbral_superior": hi,
    }


async def _mistral_analysis(
    tipo: str,
    datos: dict,
    cultivo: str | None,
    consulta: str | None,
    resultado_local: dict,
) -> tuple[str, str, str]:
    """
    Intenta análisis con Mistral AI.
    Si no está configurado, devuelve análisis basado en reglas con disclaimer.
    Returns (proveedor, modelo, recomendacion)
    """
    from config.global_config import MistralConfig
    from services.ai.mistral_client import ChatMessage, MistralClient

    api_key = os.getenv("MISTRAL_API_KEY", "")
    if not api_key:
        rec = _reglas_recomendacion(tipo, resultado_local)
        return "reglas-locales", "castuo-rules-v1", rec

    try:
        cfg = MistralConfig(
            api_key=api_key,
            endpoint=os.getenv("MISTRAL_ENDPOINT", "https://api.mistral.ai/v1"),
            inference_model=os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
            timeout=10,
        )
        client = MistralClient(cfg)
        contexto = (
            f"Tipo de análisis: {tipo}\n"
            f"Cultivo/especie: {cultivo or 'no especificado'}\n"
            f"Datos del sensor: {datos}\n"
            f"Resultado del análisis local: {resultado_local}"
        )
        query = consulta or f"Proporciona recomendaciones concretas para mejorar el resultado del análisis '{tipo}'."

        result = await client.agricultural_analysis(contexto, query)
        await client.close()
        return "mistral-ai", cfg.inference_model, result.content

    except Exception as exc:
        logger.warning("[AI] Mistral no disponible: %s — usando reglas locales", exc)
        rec = _reglas_recomendacion(tipo, resultado_local)
        return "reglas-locales", "castuo-rules-v1", rec


def _reglas_recomendacion(tipo: str, resultado: dict) -> str:
    """Recomendaciones basadas en reglas cuando Mistral no está disponible."""
    if tipo == "yield_prediction":
        ici = resultado.get("ici", 0)
        if ici >= 0.8:
            return "Condiciones óptimas. Mantener parámetros actuales."
        elif ici >= 0.6:
            return "Condiciones moderadas. Revisar humedad y temperatura."
        else:
            return "Condiciones subóptimas. Ajustar riego y climatización urgentemente."

    if tipo == "anomaly_detection":
        anomalias = resultado.get("anomalias_detectadas", 0)
        if anomalias == 0:
            return "Todos los sensores dentro de rangos normales."
        return f"Se detectaron {anomalias} anomalía(s). Revisar sensores afectados y calibrar si necesario."

    if tipo == "irrigation_advice":
        accion = resultado.get("accion", "NO_REGAR")
        if accion == "REGAR_URGENTE":
            return f"Riego urgente recomendado. Dosis: {resultado.get('dosis_l_m2')} L/m²."
        elif accion == "REGAR":
            return f"Aplicar riego preventivo. Dosis: {resultado.get('dosis_l_m2')} L/m²."
        return "No es necesario regar en este momento."

    if tipo == "livestock_health":
        estado = resultado.get("estado_sanitario", "NORMAL")
        if estado == "FIEBRE":
            return "Temperatura corporal elevada. Consultar veterinario y aislar el animal."
        elif estado == "HIPOTERMIA":
            return "Temperatura corporal baja. Proporcionar abrigo y calefacción."
        return "Animal en estado sanitario normal."

    return "Análisis completado. Revisar datos para recomendaciones específicas."


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/predict", response_model=PredictResponse, summary="Predicción IA agronómica")
async def predict(
    req: PredictRequest,
    token: dict = Depends(_auth),
) -> PredictResponse:
    """
    Análisis predictivo con IA para:
    - **yield_prediction**: rendimiento esperado del cultivo
    - **anomaly_detection**: detección de anomalías en sensores IoT
    - **irrigation_advice**: recomendación de riego basada en tensión matricial y VPD
    - **livestock_health**: evaluación sanitaria de ganado

    Sin `MISTRAL_API_KEY` configurado opera en modo local con reglas agronómicas.
    """
    TIPOS = {"yield_prediction", "anomaly_detection", "irrigation_advice", "livestock_health"}
    if req.tipo not in TIPOS:
        raise HTTPException(
            status_code=422,
            detail=f"tipo '{req.tipo}' inválido. Válidos: {sorted(TIPOS)}",
        )

    # Análisis local
    if req.tipo == "yield_prediction":
        resultado = _yield_prediction(req.datos, req.cultivo)
        confianza = resultado.get("ici")
    elif req.tipo == "anomaly_detection":
        resultado = _anomaly_detection(req.datos)
        confianza = 0.95  # reglas deterministas
    elif req.tipo == "irrigation_advice":
        resultado = _irrigation_advice(req.datos, req.cultivo)
        confianza = 0.85
    else:  # livestock_health
        resultado = _livestock_health(req.datos)
        confianza = 0.90

    # Enriquecer con Mistral si disponible
    proveedor, modelo, recomendacion = await _mistral_analysis(
        req.tipo, req.datos, req.cultivo, req.consulta_libre, resultado
    )

    return PredictResponse(
        tipo=req.tipo,
        resultado=resultado,
        proveedor_ia=proveedor,
        modelo=modelo,
        confianza=confianza,
        recomendacion=recomendacion,
        generado_en=datetime.now(timezone.utc).isoformat(),
    )
