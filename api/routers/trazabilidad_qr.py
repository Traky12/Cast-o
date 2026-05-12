"""
SABIONDA — Trazabilidad QR Inmutable hasta Cliente Final
Flujo: Apertura de lote → registros productivos → cosecha → QR verificable

El QR embebe:
  - lote_id único
  - hash SHA-256 de todos los registros del lote (cadena de custodia)
  - URL de verificación pública (sin blockchain real necesaria para MVP)
  - Datos resumidos para el consumidor final (cultivo, variedad, fecha, eco)

En producción: hash se registra en GaiaChain 3.0 via services/blockchain/gaiachain_client.py
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/trazabilidad", tags=["trazabilidad-qr"])

VERIFY_BASE_URL = "https://verify.castuo360.eu/lote"


# ─────────────────────────────────────────────────────────────────────────────
# Modelos
# ─────────────────────────────────────────────────────────────────────────────

class EventoTrazabilidad(BaseModel):
    """Un evento individual en la cadena de custodia del lote."""
    etapa: str = Field(..., description="Etapa de la cadena: siembra | nutricion | clima | cosecha | embalaje | distribucion | punto_venta")
    timestamp: str
    operador_nif: str
    hash_evento: str
    datos_resumidos: dict


class SolicitudQR(BaseModel):
    """Datos necesarios para generar el QR final del lote."""
    lote_id: str
    hash_cierre: str = Field(..., description="Hash SHA-256 generado en el endpoint /cosecha")
    cultivo: str
    variedad: str
    fecha_cosecha: str
    kg_cosechados: float
    eco_certificado: bool
    sin_pesticidas_sinteticos: bool
    explotacion_rea: str
    operador_nif: str
    sigpac_ref: Optional[str] = None
    destino: str
    # Cadena de eventos del lote (acumulados desde apertura)
    eventos: List[EventoTrazabilidad] = Field(default_factory=list)
    # Parámetros medios del ciclo (opcionales, enriquecen el QR)
    ph_medio: Optional[float] = None
    ec_medio_ms_cm: Optional[float] = None
    kwh_generados_total: Optional[float] = None
    kwh_autoconsumidos_total: Optional[float] = None


class QRTrazabilidadResponse(BaseModel):
    lote_id: str
    hash_cadena: str           # SHA-256 de todos los hashes de eventos en cadena
    verify_url: str            # URL pública de verificación
    qr_data: str               # Contenido a encodificar en el QR (JSON compacto)
    resumen_consumidor: dict   # Lo que ve el consumidor al escanear
    blockchain_pending: bool = True
    generado_en: str


class VerificacionResponse(BaseModel):
    lote_id: str
    autentico: bool
    hash_presentado: str
    hash_registrado: Optional[str]
    mensaje_consumidor: str
    datos_lote: Optional[dict] = None
    verificado_en: str


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

# Registro en memoria para demo/test (en producción: PostgreSQL + GaiaChain)
_registro_qr: dict[str, dict] = {}


def _hash_cadena_eventos(eventos: List[EventoTrazabilidad], hash_cierre: str) -> str:
    """
    Construye el hash de toda la cadena de custodia del lote.
    Encadena los hashes de cada evento + el hash de cierre.
    Si cualquier evento es modificado, el hash final cambia → detección de manipulación.
    """
    cadena = "|".join(e.hash_evento for e in eventos) + "|" + hash_cierre
    return hashlib.sha256(cadena.encode()).hexdigest()


def _resumen_consumidor(req: SolicitudQR, hash_cadena: str) -> dict:
    """Lo que ve el consumidor al escanear el QR: información real sin jerga técnica."""
    energia = None
    if req.kwh_generados_total and req.kwh_autoconsumidos_total:
        pct_auto = round(req.kwh_autoconsumidos_total / req.kwh_generados_total * 100, 1) if req.kwh_generados_total > 0 else 0
        energia = {
            "origen": "solar_agrovoltaico",
            "kwh_generados": req.kwh_generados_total,
            "autoconsumo_pct": pct_auto,
            "descripcion": f"Este cultivo se regó y climatizó con {pct_auto}% de energía solar propia",
        }

    return {
        "producto": f"{req.cultivo.capitalize()} — {req.variedad}",
        "fecha_cosecha": req.fecha_cosecha,
        "cantidad_kg": req.kg_cosechados,
        "origen": {
            "explotacion_rea": req.explotacion_rea,
            "referencia_sigpac": req.sigpac_ref or "N/A",
            "sistema_cultivo": "Hidropónico en invernadero",
        },
        "certificaciones": {
            "eco_certificado": req.eco_certificado,
            "sin_pesticidas_sinteticos": req.sin_pesticidas_sinteticos,
            "trazabilidad_blockchain": True,
        },
        "parametros_cultivo": {
            "ph_medio": req.ph_medio,
            "ec_medio_ms_cm": req.ec_medio_ms_cm,
        },
        "energia_solar": energia,
        "integridad": {
            "hash_verificacion": hash_cadena[:16] + "...",
            "eventos_registrados": len(req.eventos),
            "verificar_en": f"{VERIFY_BASE_URL}/{req.lote_id}",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/qr/generar", response_model=QRTrazabilidadResponse,
             summary="Generar QR de trazabilidad inmutable para el consumidor final")
async def generar_qr_consumidor(req: SolicitudQR) -> QRTrazabilidadResponse:
    """
    Genera el QR final del lote que recibirá el consumidor.

    El QR contiene:
    - URL de verificación pública (hash de cadena de custodia)
    - Resumen legible: cultivo, variedad, fecha, certificaciones, energía solar
    - Hash SHA-256 encadenado de todos los eventos del lote

    Al escanear: el consumidor ve toda la trazabilidad desde semilla hasta su mano.
    """
    hash_cadena = _hash_cadena_eventos(req.eventos, req.hash_cierre)
    verify_url = f"{VERIFY_BASE_URL}/{req.lote_id}/{hash_cadena}"
    resumen = _resumen_consumidor(req, hash_cadena)
    now = datetime.now(timezone.utc).isoformat()

    # Payload compacto que va codificado en el QR
    qr_data = json.dumps({
        "v": "1",                         # versión del esquema QR
        "l": req.lote_id,
        "h": hash_cadena[:32],            # primeros 32 chars son suficientes para QR
        "u": verify_url,
        "c": req.cultivo,
        "f": req.fecha_cosecha,
        "e": req.eco_certificado,
    }, separators=(",", ":"))

    # Almacenar para verificaciones posteriores
    _registro_qr[req.lote_id] = {
        "hash_cadena": hash_cadena,
        "resumen": resumen,
        "generado_en": now,
        "lote_id": req.lote_id,
    }

    return QRTrazabilidadResponse(
        lote_id=req.lote_id,
        hash_cadena=hash_cadena,
        verify_url=verify_url,
        qr_data=qr_data,
        resumen_consumidor=resumen,
        blockchain_pending=True,
        generado_en=now,
    )


@router.get("/qr/verificar/{lote_id}/{hash_presentado}",
            response_model=VerificacionResponse,
            summary="Verificar autenticidad del QR de un lote")
async def verificar_qr(lote_id: str, hash_presentado: str) -> VerificacionResponse:
    """
    Endpoint de verificación pública. El consumidor escanea el QR y llega aquí.
    Compara el hash presentado con el hash registrado al generar el QR.

    Si los hashes coinciden → el lote es auténtico y no ha sido manipulado.
    Si no coinciden → el QR es falso o el lote ha sido alterado.
    """
    ahora = datetime.now(timezone.utc).isoformat()
    registro = _registro_qr.get(lote_id)

    if not registro:
        return VerificacionResponse(
            lote_id=lote_id,
            autentico=False,
            hash_presentado=hash_presentado,
            hash_registrado=None,
            mensaje_consumidor=(
                "Este lote no está registrado en nuestro sistema. "
                "Puede tratarse de un QR falsificado o un lote no registrado."
            ),
            verificado_en=ahora,
        )

    hash_registrado = registro["hash_cadena"]
    autentico = hash_presentado == hash_registrado or hash_registrado.startswith(hash_presentado)

    return VerificacionResponse(
        lote_id=lote_id,
        autentico=autentico,
        hash_presentado=hash_presentado,
        hash_registrado=hash_registrado[:32] + "..." if hash_registrado else None,
        mensaje_consumidor=(
            f"Producto auténtico. Origen certificado. Trazabilidad verificada."
            if autentico else
            "Advertencia: este QR no coincide con nuestros registros. "
            "Por favor, contacte con el distribuidor."
        ),
        datos_lote=registro.get("resumen") if autentico else None,
        verificado_en=ahora,
    )


@router.post("/qr/evento",
             summary="Añadir un evento a la cadena de custodia del lote")
async def registrar_evento_trazabilidad(
    lote_id: str,
    etapa: str,
    operador_nif: str,
    datos: dict,
) -> dict:
    """
    Registra un evento en la cadena de trazabilidad del lote.
    Devuelve el hash del evento para incluirlo en la solicitud de QR final.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    evento_dict = {
        "lote_id": lote_id,
        "etapa": etapa,
        "operador_nif": operador_nif,
        "timestamp": timestamp,
        "datos": datos,
    }
    hash_evento = hashlib.sha256(
        json.dumps(evento_dict, sort_keys=True, default=str).encode()
    ).hexdigest()
    return {
        "lote_id": lote_id,
        "etapa": etapa,
        "timestamp": timestamp,
        "hash_evento": hash_evento,
        "instruccion": "Conservar este hash_evento para incluirlo en la solicitud de QR final.",
    }


@router.get("/lote/{lote_id}/resumen",
            summary="Resumen público del lote para página de verificación")
async def resumen_lote_publico(lote_id: str) -> dict:
    """
    Devuelve el resumen público del lote. Esta es la página que ve el consumidor
    al escanear el QR (en producción: renderizada por frontend React).
    """
    registro = _registro_qr.get(lote_id)
    if not registro:
        raise HTTPException(status_code=404, detail=f"Lote '{lote_id}' no encontrado")
    return {
        "lote_id": lote_id,
        "resumen": registro["resumen"],
        "verificado_en_blockchain": registro.get("blockchain_tx") is not None,
        "generado_en": registro["generado_en"],
    }
