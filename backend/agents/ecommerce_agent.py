# backend/agents/ecommerce_agent.py — Agente E-Commerce (Shopify, Stripe, catálogo). Stub ejecutable.

from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger(__name__)


class ECommerceAgent:
    """Agente de e-commerce: pedidos, pagos, catálogo. Integración Shopify/Stripe por configurar."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.shopify_webhook_url = os.getenv("SHOPIFY_WEBHOOK_URL", "")
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    async def run(self) -> None:
        self.logger.info("Agente E-Commerce iniciado (modo stub). Configurar SHOPIFY_* y STRIPE_* para integración.")
        while True:
            await asyncio.sleep(60)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    agent = ECommerceAgent()
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
