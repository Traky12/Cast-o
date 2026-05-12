# -*- coding: utf-8 -*-
"""Integración con mercado de carbono (blockchain stub + estimación de precios)."""
from typing import Any, Dict, List, Optional


def estimate_price_eur_per_ton(kg_co2: float) -> float:
    """Estima precio €/ton CO₂ (referencia EU ETS ~80 €/ton)."""
    return (kg_co2 / 1000.0) * 80.0


class CarbonMarket:
    """Listado y venta de créditos (stub; en prod conectar a CarbonCredits.sol)."""

    def __init__(self, blockchain_url: Optional[str] = None):
        self.blockchain_url = blockchain_url

    def list_credits(self, owner_address: str) -> List[Dict[str, Any]]:
        """Lista créditos disponibles (stub)."""
        return []

    def sell_credit(
        self,
        credit_id: int,
        buyer_address: str,
        price_per_ton: float,
    ) -> str:
        """Registra venta en blockchain; devuelve tx_hash (stub)."""
        import hashlib
        data = f"carbon-sell-{credit_id}-{buyer_address}-{price_per_ton}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
