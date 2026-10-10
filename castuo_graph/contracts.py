"""Typed CASTÚO agent contracts.

Contracts are validation objects, not promotion authority. A valid object does
not imply external evidence, independent review or production readiness.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ClaimBoundary = Literal[
    "LOCAL_RESULT_NO_CLAIM",
    "EVIDENCE_SCOPED",
    "EXTERNAL_VERIFICATION_PENDING",
    "FIELD_EVIDENCE_REQUIRED",
    "NO_CLAIM",
]
PromotionDecision = Literal["ALLOW", "REVIEW", "DENY", "QUARANTINE", "BLOCKED"]


class AgentContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contract_id: str = Field(min_length=1)
    capability_id: str = Field(min_length=1)
    graph_version: str = Field(min_length=1)
    allowed_actions: list[str] = Field(min_length=1)
    forbidden_actions: list[str] = Field(min_length=1)
    human_approval_required: bool = True
    rollback_required: bool = True
    claim_boundary: ClaimBoundary = "LOCAL_RESULT_NO_CLAIM"


class ToolContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_id: str = Field(min_length=1)
    side_effect_class: Literal["READ_ONLY", "DURABLE_WRITE", "IRREVERSIBLE_WRITE"]
    idempotency_required: bool = True
    compensation_required: bool = True
    evidence_event_required: bool = True
    allowed_resources: list[str] = Field(min_length=1)


class RunContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1)
    thread_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    graph_version: str = Field(min_length=1)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    checkpoint_required: bool = True
    resume_allowed: bool = True


class EvidenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    package_id: str = Field(min_length=1)
    capability_id: str = Field(min_length=1)
    commit: str = Field(min_length=7)
    artifacts: dict[str, str] = Field(min_length=1)
    replay_reference: str = Field(min_length=1)
    independence: Literal["NOT_ESTABLISHED", "PENDING", "ESTABLISHED"] = "NOT_ESTABLISHED"
    claim_boundary: ClaimBoundary = "LOCAL_RESULT_NO_CLAIM"
    production_claim: bool = False
    promotion: Literal["BLOCKED", "REVIEW", "ALLOW"] = "BLOCKED"


class PromotionContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=1)
    decision: PromotionDecision = "BLOCKED"
    capability: bool = False
    evidence: bool = False
    replay: bool = False
    security: bool = False
    sovereignty: bool = False
    resilience: bool = False
    review: bool = False
    rollback: bool = False
    reviewer: str | None = None

    def is_promotable(self) -> bool:
        return self.decision == "ALLOW" and all(
            (
                self.capability,
                self.evidence,
                self.replay,
                self.security,
                self.sovereignty,
                self.resilience,
                self.review,
                self.rollback,
            )
        ) and bool(self.reviewer)
