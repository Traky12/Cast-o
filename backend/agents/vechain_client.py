from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import httpx


class VeChainClient:
    """
    Cliente mínimo para escribir logs en una API gateway que hable con VeChain.

    Este módulo NO firma transacciones directamente; asume un backend intermedio
    (por ejemplo, un microservicio propio o un proveedor third-party) expuesto
    vía HTTP al que se le envía el payload SIEX + SHA256.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_s: float = 10.0,
    ) -> None:
        self.base_url = base_url or os.getenv("VECHAIN_GATEWAY_URL", "").rstrip("/")
        self.api_key = api_key or os.getenv("VECHAIN_API_KEY")
        self.timeout_s = timeout_s

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def log_siex_record(self, record: Dict[str, Any]) -> None:
        """
        Envía un registro SIEX + decisión a la pasarela VeChain.

        En producción, esta pasarela debería encargarse de:
        - empaquetar el registro en el formato del smart contract
        - firmar la transacción
        - hacer broadcast a la red VeChain
        """
        if not self.base_url:
            return

        url = f"{self.base_url}/siex/log"
        payload = json.dumps(record, ensure_ascii=False)

        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                client.post(url, headers=self._headers(), content=payload.encode("utf-8"))
        except Exception:
            # Falla en blockchain no debe tumbar la decisión agronómica.
            return

