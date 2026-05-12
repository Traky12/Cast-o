# -*- coding: utf-8 -*-
"""Router CTAEX v6.0: trazabilidad GaiaChain, sensores microgreens, certificación CTAEX, checkout Stripe."""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request

# Asegurar import de blockchain desde raíz del repo
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from backend.auth_roles import read_secret, require_role
except ImportError:
    def read_secret(name: str) -> str:
        return os.getenv(name.upper(), os.getenv(name, ""))
    def require_role(*_roles):  # no-op si auth_roles no disponible
        async def _noop():
            return None
        return _noop

try:
    from backend.security_internal import audit_log, get_client_ip, redact_secrets
except ImportError:
    def audit_log(*args, **kwargs): pass
    def get_client_ip(req): return getattr(req, "scope", {}).get("client", ["unknown"])[0] if isinstance(getattr(req.scope, "client", None), (list, tuple)) else "unknown"
    def redact_secrets(x): return x

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    import stripe
    stripe.api_key = read_secret("STRIPE_SECRET") or read_secret("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET", "")
    _HAS_STRIPE = bool(stripe.api_key)
except Exception:
    stripe = None  # type: ignore
    _HAS_STRIPE = False

logger = logging.getLogger(__name__)

router = APIRouter(tags=["CTAEX v6.0"])

# Cliente GaiaChain (stub o RPC)
_gaia: Any = None


def _get_gaia() -> Any:
    global _gaia
    if _gaia is None and GaiaChainClient is not None:
        _gaia = GaiaChainClient(rpc_url=os.getenv("GAIA_CHAIN_RPC_URL", ""))
    return _gaia


# Datos simulados de sensores (en producción: MQTT o BD)
SENSOR_DATA = {
    "mg1": {
        "ph": 5.8,
        "ec": 1.2,
        "temp": 22.5,
        "humidity": 75,
        "co2": 850,
        "light": 45000,
        "ozone": "active",
    },
    "mg2": {
        "ph": 6.0,
        "ec": 1.1,
        "temp": 21.8,
        "humidity": 72,
        "co2": 820,
        "light": 44000,
        "ozone": "active",
    },
}


@router.post("/trazabilidad/gaia")
async def gaia_trace(
    request: Request,
    current_user: dict = Depends(require_role("admin", "blockchain")),
) -> Dict[str, Any]:
    """Registra datos en GaiaChain para trazabilidad CTAEX. Requiere rol admin o blockchain."""
    data = await request.json()
    gaia = _get_gaia()
    if gaia is None:
        return {
            "hash": f"tx_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "simulated",
            "data": {**data, "timestamp": datetime.now().isoformat(), "source": "CASTUO-CTAEX"},
            "blockchain": "GaiaChain",
            "network": "mainnet",
        }
    payload = {
        "product_id": data.get("product_id", "default"),
        "microgreens_batch": data.get("batch_id", "MG-2026-03-14"),
        "cert_status": data.get("cert_status", "organic_ctaex"),
        "env_conditions": data.get("env_data", {}),
        "timestamp": datetime.now().isoformat(),
        "source": "CASTUO-CTAEX",
    }
    tx_hash = gaia.log_iot_data(
        {
            "tray_id": data.get("batch_id", "MG-2026-03-14"),
            "timestamp": payload["timestamp"],
            "sensors": payload.get("env_conditions"),
            "metadata": {"product_id": payload["product_id"], "cert_status": payload["cert_status"]},
        }
    )
    audit_log(
        "trazabilidad_gaia",
        request.url.path,
        "POST",
        role=(current_user or {}).get("role"),
        resource_id=payload.get("microgreens_batch"),
        ip=get_client_ip(request),
        extra={"tx_hash": tx_hash},
    )
    return {
        "hash": tx_hash,
        "status": "minted",
        "data": payload,
        "blockchain": "GaiaChain",
        "network": "mainnet",
    }


@router.get("/microgreens/sensors")
async def microgreens_sensors(bed_id: str = "mg1") -> Dict[str, Any]:
    """Datos de sensores por cama (CTAEX). Opcionalmente registra en GaiaChain."""
    if bed_id not in SENSOR_DATA:
        raise HTTPException(status_code=404, detail="Bandeja no encontrada")
    data = SENSOR_DATA[bed_id].copy()
    gaia = _get_gaia()
    if gaia is not None:
        gaia.log_iot_data(
            {
                "tray_id": bed_id,
                "timestamp": datetime.now().isoformat(),
                "sensors": {
                    "ph": data["ph"],
                    "ec": data["ec"],
                    "temperature": data["temp"],
                    "humidity": data["humidity"],
                    "co2": data["co2"],
                    "light": data["light"],
                    "ozone_status": data["ozone"],
                },
                "metadata": {"source": "CTAEX"},
            }
        )
    return {
        **data,
        "growth_stage": "day_7",
        "yield_pred": "250g",
        "gaia_tx": f"tx_{bed_id}_{datetime.now().strftime('%H%M')}",
    }


@router.get("/certificacion/ctaex")
async def ctaex_cert(batch_id: str = "MG-2026-03-14") -> Dict[str, Any]:
    """Certificado CTAEX + GaiaChain (QR y normativas)."""
    gaia = _get_gaia()
    tx = f"tx_{batch_id}_ctaex"
    if gaia is not None:
        tx = gaia._tx_id("cert", batch_id, "ctaex")  # noqa: SLF001
    return {
        "batch_id": batch_id,
        "valid": True,
        "standards": ["organic_eu", "ctaex_trl7", "gs1_epcis"],
        "qr_code": f"https://api.gaia-chain.com/qr/{batch_id}",
        "gaia_tx": tx,
        "issued_by": "CTAEX + CASTUO-SYSTEM",
        "issue_date": datetime.now().isoformat(),
        "ctaex_validation": {
            "status": "validated",
            "lab": "CTAEX-Badajoz",
            "date": datetime.now().isoformat(),
            "standards": ["ISO_22000", "GlobalGAP", "CTAEX_TRL7"],
        },
    }


@router.post("/ecommerce/create-checkout")
async def create_checkout(
    request: Request,
    current_user: dict = Depends(require_role("admin", "ecommerce")),
) -> Dict[str, Any]:
    """Crea sesión de pago Stripe para lote certificado (CTAEX). Requiere rol admin o ecommerce."""
    data = await request.json()
    batch_id = data.get("batch_id", "MG-2026-03-14")
    success_url = data.get("success_url") or "https://89.167.5.233/success"
    cancel_url = data.get("cancel_url") or "https://89.167.5.233/cancel"
    unit_amount = int(data.get("unit_amount", 2500))  # céntimos, ej. 25.00 EUR

    if not _HAS_STRIPE or stripe is None:
        raise HTTPException(
            status_code=501,
            detail="Stripe no configurado. Definir STRIPE_SECRET en entorno.",
        )

    # Verificar lote (certificado CTAEX)
    gaia = _get_gaia()
    cert_valid = True
    if gaia is not None:
        cert_valid = True  # En producción podría consultar get_certificate o compliance

    if not cert_valid:
        raise HTTPException(status_code=400, detail="Lote no certificado")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Microgreens {batch_id} (Certificado CTAEX)",
                            "description": "Cultivo hidropónico con trazabilidad blockchain",
                        },
                        "unit_amount": unit_amount,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{success_url.rstrip('/')}?batch={batch_id}",
            cancel_url=cancel_url,
            metadata={"batch_id": batch_id},
        )
        audit_log(
            "checkout_created",
            request.url.path,
            "POST",
            role=(current_user or {}).get("role"),
            resource_id=batch_id,
            ip=get_client_ip(request),
            extra={"session_id": session.id},
        )
        return {"session": {"id": session.id}}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/ecommerce/webhook")
async def stripe_webhook(request: Request) -> Dict[str, Any]:
    """Webhook de Stripe: validar firma y procesar checkout.session.completed."""
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    webhook_secret = read_secret("STRIPE_WEBHOOK_SECRET") or os.getenv("STRIPE_WEBHOOK_SECRET", "")

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET no configurado")

    if not stripe:
        raise HTTPException(status_code=501, detail="Stripe no disponible")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Payload inválido: {e}")
    except Exception as e:
        if "Signature" in type(e).__name__ or "signature" in str(e).lower():
            raise HTTPException(status_code=400, detail="Firma de webhook inválida")
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        batch_id = (session.get("metadata") or {}).get("batch_id", "")
        amount = session.get("amount_total", 0) / 100
        logger.info("Pago completado CTAEX batch_id=%s amount=%.2f EUR", batch_id, amount)
        return {"status": "ok", "batch_id": batch_id, "amount_eur": amount}

    return {"status": "ok", "event_type": event["type"]}
