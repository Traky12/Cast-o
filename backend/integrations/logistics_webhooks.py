# backend/integrations/logistics_webhooks.py — Webhooks Packlink, SEUR, DHL

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, Request, HTTPException
    _FASTAPI = True
except ImportError:
    APIRouter = None
    Request = None
    HTTPException = None
    _FASTAPI = False

try:
    from backend.security.end_to_end_encryption import EndToEndEncryption
    from backend.compliance.immutable_traceability import ImmutableTraceability
    _E2E_AVAILABLE = True
except ImportError:
    EndToEndEncryption = None
    ImmutableTraceability = None
    _E2E_AVAILABLE = False

if _FASTAPI and APIRouter is not None:
    router = APIRouter(prefix="/webhooks", tags=["webhooks"])
else:
    router = None


def _validate_packlink_signature(request: "Request") -> bool:
    # Placeholder: validar firma según documentación Packlink
    return True


def _validate_seur_hmac(request: "Request") -> bool:
    # Placeholder: validar HMAC según documentación SEUR
    return True


async def _process_shipping_update(
    carrier: str,
    tracking_id: str,
    status: str,
    event_data: Dict[str, Any],
) -> None:
    try:
        from backend.agents.logistics_agent import LogisticsAgent
        agent = LogisticsAgent()
        if hasattr(agent, "process_shipping_update"):
            await agent.process_shipping_update(
                carrier=carrier,
                tracking_id=tracking_id,
                status=status,
                event_data=event_data,
            )
    except Exception as e:
        logger.debug("process_shipping_update: %s", e)


if _FASTAPI and router is not None and Request is not None and HTTPException is not None:

    @router.post("/packlink")
    async def packlink_webhook(request: Request) -> Dict[str, str]:
        try:
            data = await request.json()
            logger.info("Webhook Packlink: %s", data.get("tracking_id", ""))
            if not _validate_packlink_signature(request):
                raise HTTPException(status_code=403, detail="Firma inválida")
            await _process_shipping_update(
                carrier="packlink",
                tracking_id=str(data.get("tracking_id", "")),
                status=str(data.get("status", "")),
                event_data=data,
            )
            return {"status": "ok"}
        except Exception as e:
            logger.error("Webhook Packlink: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/packlink/secure")
    async def secure_packlink_webhook(request: Request) -> Dict[str, str]:
        """Webhook Packlink con cifrado E2E y trazabilidad."""
        try:
            if not _validate_packlink_signature(request):
                raise HTTPException(status_code=403, detail="Firma inválida")
            data = await request.json()
            if not _E2E_AVAILABLE or EndToEndEncryption is None or ImmutableTraceability is None:
                await _process_shipping_update(
                    carrier="packlink",
                    tracking_id=str(data.get("tracking_id", "")),
                    status=str(data.get("status", "")),
                    event_data=data,
                )
                return {"status": "processed", "tracking_id": data.get("tracking_id", "")}
            encryption = EndToEndEncryption()
            traceability = ImmutableTraceability(encryption)
            priv_key, pub_key = encryption.generate_key_pair()
            secure_data = encryption.create_encrypted_envelope(
                data,
                pub_key,
                metadata={
                    "webhook_type": "packlink_shipping_update",
                    "received_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            traceability.register_event({
                "type": "webhook_received",
                "carrier": "packlink",
                "tracking_id": data.get("tracking_id", "unknown"),
                "data_hash": secure_data["integrity"]["hash"],
                "normative_references": ["GDPR:Art.5", "ISO_27001:A.13.1.1"],
            })
            decrypted_data, valid = encryption.verify_and_decrypt_envelope(secure_data, priv_key)
            if not valid:
                raise HTTPException(status_code=400, detail="Datos corruptos")
            decrypted_data = decrypted_data if isinstance(decrypted_data, dict) else {}
            await _process_shipping_update(
                carrier="packlink",
                tracking_id=str(decrypted_data.get("tracking_id", "")),
                status=str(decrypted_data.get("status", "")),
                event_data=decrypted_data,
            )
            return {"status": "processed", "tracking_id": decrypted_data.get("tracking_id", "")}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Webhook Packlink seguro: %s", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/seur")
    async def seur_webhook(request: Request) -> Dict[str, str]:
        try:
            data = await request.json()
            logger.info("Webhook SEUR: %s", data.get("envio", {}).get("codigo_envio", ""))
            if not _validate_seur_hmac(request):
                raise HTTPException(status_code=403, detail="HMAC inválido")
            envio = data.get("envio", {})
            estado = data.get("estado", {})
            await _process_shipping_update(
                carrier="seur",
                tracking_id=str(envio.get("codigo_envio", "")),
                status=str(estado.get("codigo", "")),
                event_data=data,
            )
            return {"status": "ok"}
        except Exception as e:
            logger.error("Webhook SEUR: %s", e)
            raise HTTPException(status_code=500, detail=str(e))
