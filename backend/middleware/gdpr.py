# -*- coding: utf-8 -*-
"""Middleware GDPR (RGPD): enmascaramiento de datos personales según Art. 25 + Barreras v6.1."""
from __future__ import annotations

import json
import re
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from backend.security.pii_masking import mask_pii_in_dict
except ImportError:
    mask_pii_in_dict = None


def _mask_nif(value: str) -> str:
    """Enmascara NIF: solo últimos 4 caracteres visibles (Art. 25 RGPD)."""
    if not value or len(value) < 4:
        return "****"
    return "*****" + value[-4:]


def _mask_email(value: str) -> str:
    """Enmascara email: primeros 2 + **** + dominio (ej: ab****@ctaex.es)."""
    if not value or "@" not in value:
        return "****@****"
    match = re.match(r"^(.{2}).*(@.*)$", value)
    if match:
        return match.group(1) + "****" + match.group(2)
    return "****" + value[value.index("@"):]


def _mask_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Aplica enmascaramiento a user_data (nif, email, phone) y PII ampliado v6.1."""
    if "user_data" in data and isinstance(data.get("user_data"), dict):
        user = data["user_data"]
        if "nif" in user and user["nif"]:
            user = {**user, "nif": _mask_nif(str(user["nif"]))}
        if "email" in user and user["email"]:
            user = {**user, "email": _mask_email(str(user["email"]))}
        if "phone" in user and user.get("phone"):
            user = {**user, "phone": "****" + str(user["phone"])[-4:]}
        data = {**data, "user_data": user}
    # Barreras v6.1: passport, credit_card, dni, nie, ip, geolocation
    if mask_pii_in_dict and isinstance(data, dict):
        data = mask_pii_in_dict(data)
    return data


class GDPRMiddleware(BaseHTTPMiddleware):
    """Enmascara datos personales en respuestas JSON (RGPD Art. 25: privacidad por diseño)."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        content_type = response.headers.get("content-type", "") or ""
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body.decode("utf-8"))
            masked = _mask_user_data(data)
            if masked != data:
                return Response(
                    content=json.dumps(masked, ensure_ascii=False).encode("utf-8"),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json",
                )
        except (json.JSONDecodeError, TypeError):
            pass
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=content_type.split(";")[0].strip() or "application/json",
        )
