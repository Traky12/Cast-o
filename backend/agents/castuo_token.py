from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RewardEvent:
    bandeja: str
    crop: str
    decision: str
    yield_grams: Optional[float]
    wallet_address: str


class CastuoTokenClient:
    """
    Fachada mínima para el contrato ERC-20 CASTUO en la red elegida.

    Igual que el cliente de VeChain, este módulo asume un microservicio
    intermedio (o un worker off-chain) que se encarga de firmar y enviar
    las transacciones reales al contrato.
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("CASTUO_TOKEN_GATEWAY_URL", "").rstrip("/")
        self.api_key = api_key or os.getenv("CASTUO_TOKEN_API_KEY")

    def reward_farmer(self, event: RewardEvent) -> None:
        """
        Calcula y emite la recompensa asociada a un evento agronómico.
        Implementación placeholder: delegada a un servicio externo.
        """
        if not self.base_url or not event.wallet_address:
            return

        # Aquí se podría enviar una petición HTTP a un servicio que:
        # - consulta el modelo de tokenomics.json
        # - computa los CASTUO a emitir
        # - llama al contrato ERC-20 con las credenciales adecuadas
        return

