# -*- coding: utf-8 -*-
"""Orquestación de registro / consulta de clientes para agentes (Claude Code EU-first)."""

from __future__ import annotations

import logging
import os
from typing import Any

from backend.services.water_billing import register_billing_customer
from backend.services.water_ctaex_plans import get_usage_report, hash_api_key

logger = logging.getLogger(__name__)


class AIAccountManager:
    def __init__(self) -> None:
        self.enabled = os.getenv("AI_ACCOUNT_MANAGER_ENABLED", "0").strip() in ("1", "true", "True")

    def register_customer(
        self,
        *,
        api_key: str,
        plan_id: str,
        customer_name: str,
        customer_email: str,
    ) -> dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled", "message": "AI Account Manager not enabled"}

        try:
            row = register_billing_customer(
                api_key=api_key.strip(),
                plan_id=plan_id.strip().lower(),
                customer_name=customer_name,
                customer_email=customer_email,
            )
            return {
                "status": "success",
                "api_key_hash": hash_api_key(api_key.strip()),
                **row,
            }
        except ValueError as e:
            logger.warning("Registro IA rechazado: %s", e)
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.exception("Error en registro IA")
            return {"status": "error", "message": str(e)}

    def update_customer_plan(self, api_key: str, new_plan_id: str) -> dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled", "message": "AI Account Manager not enabled"}
        return {
            "status": "not_implemented",
            "message": "Actualizar plan vía MISMA vía que /subscription/register (UPSERT) o WATER_API_KEY_TO_PLAN",
            "hint": "register_billing_customer con nueva plan_id",
        }

    def get_customer_usage(self, api_key: str, *, limit: int = 500) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        kh = hash_api_key(api_key.strip())
        for item in get_usage_report(limit=limit, plan_id=None):
            if item.get("key_hash") == kh:
                return item
        return None
