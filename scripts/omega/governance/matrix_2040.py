#!/usr/bin/env python3
"""
SABIONDA_OMEGA_GLOBAL_2040 — Matriz de gobernanza segura (ISO 38505 + COBIT 2019).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .legal_engine_2040 import AutoAdaptiveLegalEngine
from .sustainability_2040 import SustainabilityBoard


@dataclass
class GovernanceDecision:
    id: str
    committee: str
    decision: str
    timestamp: int
    signatures: list[str] = field(default_factory=list)
    gaiachain_tx: str = ""
    status: str = "pending"


class EthicalAIBoard:
    def validate_decision(self, decision: str, context: dict) -> dict[str, Any]:
        return {"valid": True}

    def apply_decision(self, decision: GovernanceDecision) -> None:
        pass


class QuantumSecurityBoard:
    def validate_decision(self, decision: str, context: dict) -> dict[str, Any]:
        return {"valid": True}

    def apply_security_policy(self, decision: GovernanceDecision) -> None:
        pass


class GaiaChainLogger:
    def __init__(self) -> None:
        self._decisions: dict[str, GovernanceDecision] = {}

    def log_proposal(self, decision: GovernanceDecision) -> str:
        tx = f"tx_gaia_{decision.id}"
        decision.gaiachain_tx = tx
        self._decisions[decision.id] = decision
        return tx

    def update_signatures(self, decision: GovernanceDecision) -> None:
        self._decisions[decision.id] = decision

    def log_approval(self, decision: GovernanceDecision) -> None:
        decision.status = "approved"
        self._decisions[decision.id] = decision

    def get_decision(self, decision_id: str) -> Optional[GovernanceDecision]:
        return self._decisions.get(decision_id)


class GovernanceMatrix:
    def __init__(self) -> None:
        self.committees = {
            "ethics": EthicalAIBoard(),
            "quantum_security": QuantumSecurityBoard(),
            "legal": AutoAdaptiveLegalEngine(),
            "sustainability": SustainabilityBoard(),
        }
        self.decision_log = GaiaChainLogger()
        self.quorum = {
            "ethics": 3,
            "quantum_security": 2,
            "legal": 2,
            "sustainability": 1,
        }

    def propose_decision(
        self,
        committee: str,
        decision: str,
        context: dict[str, Any],
    ) -> str:
        if committee not in self.committees:
            raise ValueError(f"Comité no válido: {committee}")
        comm = self.committees[committee]
        validation = comm.validate_decision(decision, context)
        if not validation.get("valid", True):
            raise ValueError(f"Decisión rechazada: {validation.get('reason', 'unknown')}")
        decision_id = f"gov_{committee}_{int(datetime.utcnow().timestamp())}"
        gov_decision = GovernanceDecision(
            id=decision_id,
            committee=committee,
            decision=decision,
            timestamp=int(datetime.utcnow().timestamp()),
            signatures=[],
            gaiachain_tx="",
        )
        gov_decision.gaiachain_tx = self.decision_log.log_proposal(gov_decision)
        return decision_id

    def sign_decision(
        self,
        decision_id: str,
        member_id: str,
        signature: str,
    ) -> bool:
        decision = self.decision_log.get_decision(decision_id)
        if not decision:
            return False
        if not self._validate_member(decision.committee, member_id):
            return False
        decision.signatures.append(signature)
        if len(decision.signatures) >= self.quorum[decision.committee]:
            decision.status = "approved"
            self.decision_log.log_approval(decision)
            self._execute_decision(decision)
            return True
        self.decision_log.update_signatures(decision)
        return False

    def _validate_member(self, committee: str, member_id: str) -> bool:
        valid_members = {
            "ethics": ["ethics_chair_2040", "ai_ethicist_1", "ai_ethicist_2"],
            "quantum_security": ["qsec_chair_2040", "crypto_expert_1"],
            "legal": ["legal_chair_2040", "compliance_expert_1", "compliance_expert_2"],
            "sustainability": ["sustain_chair_2040"],
        }
        return member_id in valid_members.get(committee, [])

    def _execute_decision(self, decision: GovernanceDecision) -> None:
        if decision.committee == "ethics":
            self.committees["ethics"].apply_decision(decision)
        elif decision.committee == "quantum_security":
            self.committees["quantum_security"].apply_security_policy(decision)
        elif decision.committee == "legal":
            self.committees["legal"].update_compliance_rules(decision)
        elif decision.committee == "sustainability":
            self.committees["sustainability"].update_sustainability_policy(decision)
