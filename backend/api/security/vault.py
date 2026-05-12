# backend/api/security/vault.py
"""Gestión de secretos con HashiCorp Vault (EU/OSS). En desarrollo sin VAULT_ADDR devuelve mocks."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

try:
    import hvac
    _HAS_HVAC = True
except ImportError:
    _HAS_HVAC = False


class VaultClient:
    def __init__(self) -> None:
        self.vault_enabled = os.getenv("VAULT_ADDR") is not None and _HAS_HVAC
        self._client: Any = None
        if self.vault_enabled:
            try:
                self._client = hvac.Client(
                    url=os.getenv("VAULT_ADDR", "http://vault:8200"),
                    token=os.getenv("VAULT_TOKEN"),
                )
                if not self._client.is_authenticated():
                    raise RuntimeError("Vault client not authenticated")
                logger.info("Vault client initialized successfully")
            except Exception as e:
                logger.warning("Vault initialization error: %s", e)
                self.vault_enabled = False
                self._client = None

    def get_secret(self, path: str, key: Optional[str] = None) -> Any:
        """Obtiene un secreto de Vault. En modo dev sin Vault devuelve mocks."""
        if not self.vault_enabled:
            logger.warning("Vault disabled, returning mock secrets")
            mock = {
                "gaiachain_private_key": "mock-private-key-for-dev",
                "ipfs_api_key": "mock-ipfs-key-for-dev",
                "jwt_signing_key": "mock-jwt-key-for-dev",
            }
            return mock.get(key, mock) if key else mock

        try:
            path = path.strip().lstrip("/").replace("secret/", "")
            secret = self._client.secrets.kv.v2.read_secret_version(path=path)
            data = secret["data"]["data"]
            return data[key] if key else data
        except Exception as e:
            logger.error("Error accessing Vault: %s (GDPR Art. 32)", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error accessing secure storage",
            ) from e

    def sign_data(self, data: str) -> Dict[str, Any]:
        """Firma datos con Transit Engine de Vault."""
        if not self.vault_enabled:
            logger.warning("Vault disabled, returning mock signature")
            return {
                "signature": "mock-signature-" + (data[:10] if len(data) >= 10 else data),
                "algorithm": "mock-rsa-2048",
                "compliance": {"iso_27001": "A.10.1.1 (simulado)", "gdpr": "Art. 32 (simulado)"},
            }

        try:
            import base64
            plaintext_b64 = base64.b64encode(data.encode("utf-8")).decode("ascii")
            response = self._client.write(
                "transit/sign/consent_signing_key",
                input=plaintext_b64,
            )
            return {
                "signature": response["data"].get("signature", ""),
                "algorithm": "rsa-2048-sha256",
                "compliance": {
                    "iso_27001": "A.10.1.1",
                    "gdpr": "Art. 32",
                    "ley_3_2023": "Art. 10",
                },
            }
        except Exception as e:
            logger.error("Signing error: %s (ISO 27001 A.10.1.2)", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating signature",
            ) from e

    def verify_signature(self, data: str, signature: str) -> bool:
        """Verifica una firma con Vault."""
        if not self.vault_enabled:
            return True

        try:
            import base64
            plaintext_b64 = base64.b64encode(data.encode("utf-8")).decode("ascii")
            response = self._client.write(
                "transit/verify/consent_signing_key",
                input=plaintext_b64,
                signature=signature,
            )
            return response["data"].get("valid", False)
        except Exception as e:
            logger.error("Verification error: %s", e)
            return False


vault = VaultClient()
