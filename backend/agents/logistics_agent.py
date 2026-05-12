# backend/agents/logistics_agent.py — Agente Logística (Packlink, SEUR, rutas). Stub ejecutable.

from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger(__name__)


class LogisticsAgent:
    """Agente de logística: envíos, Packlink/SEUR, optimización de rutas."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.packlink_api_key = os.getenv("PACKLINK_API_KEY", "")
        self.seur_webhook_url = os.getenv("SEUR_WEBHOOK_URL", "")

    async def run(self) -> None:
        self.logger.info("Agente Logística iniciado (modo stub). Configurar PACKLINK_API_KEY para envíos.")
        while True:
            await asyncio.sleep(60)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    agent = LogisticsAgent()
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
