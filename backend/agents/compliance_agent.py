# backend/agents/compliance_agent.py — Agente Cumplimiento (ISO 27001, GDPR, EU AI Act). Stub ejecutable.

from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger(__name__)


class ComplianceAgent:
    """Agente de cumplimiento normativo: ISO 27001, GDPR, NIS2, EU AI Act, Ley 3/2023."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.normatives_path = os.getenv("CASTUO_NORMATIVES_PATH", "")

    async def run(self) -> None:
        self.logger.info("Agente Cumplimiento iniciado (modo stub). Cargar normativas con --load-normatives.")
        while True:
            await asyncio.sleep(60)


def main() -> None:
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    if "--load-normatives" in sys.argv:
        logging.info("Cargar normativas: configurar CASTUO_NORMATIVES_PATH y scripts en backend/scripts/")
    agent = ComplianceAgent()
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
