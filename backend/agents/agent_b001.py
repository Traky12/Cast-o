from __future__ import annotations

from typing import Any, Dict

from ..models import SabiondaDecision, SabiondaRequest
from .vechain_client import VeChainClient
from .castuo_token import CastuoTokenClient, RewardEvent


class AgentB001:
    """
    Agente especializado para la bandeja B001.

    Envuelve la lógica de negocio sabionda + side-effects:
    - logging SIEX en blockchain (VeChain)
    - emisión de recompensas CASTUO según yield / buenas prácticas
    - hooks para bots de mensajería (Telegram/WhatsApp)
    """

    def __init__(self) -> None:
        self.vechain = VeChainClient()
        self.token_client = CastuoTokenClient()

    def after_decision(
        self,
        request: SabiondaRequest,
        decision: SabiondaDecision,
        wallet_address: str | None = None,
        yield_grams: float | None = None,
    ) -> None:
        siex_record: Dict[str, Any] = {
            "bandeja": request.bandeja,
            "crop": request.crop,
            "ph": request.ph,
            "ec": request.ec,
            "temp": request.temp,
            "humidity": request.humidity,
            "decision": decision.decision,
            "o3_target": decision.o3_target,
            "log_message": decision.log_message,
            "sha256": decision.sha256,
        }
        self.vechain.log_siex_record(siex_record)

        if wallet_address and yield_grams is not None:
            event = RewardEvent(
                bandeja=request.bandeja,
                crop=request.crop,
                decision=decision.decision,
                yield_grams=yield_grams,
                wallet_address=wallet_address,
            )
            self.token_client.reward_farmer(event)

