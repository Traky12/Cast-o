from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from castuo_graph.contracts import (
    AgentContract,
    EvidenceManifest,
    PromotionContract,
    RunContract,
    ToolContract,
)


def test_agent_contract_is_bounded_by_default():
    contract = AgentContract(
        contract_id="AGENT-S001A-001",
        capability_id="S-001A",
        graph_version="casto-langgraph-3.1.0-durable-sqlite-v1",
        allowed_actions=["detect", "suggest"],
        forbidden_actions=["promote_claim", "access_secret", "irreversible_action"],
    )
    assert contract.human_approval_required is True
    assert contract.rollback_required is True
    assert contract.claim_boundary == "LOCAL_RESULT_NO_CLAIM"


def test_tool_contract_requires_side_effect_controls():
    contract = ToolContract(
        tool_id="traces.emit",
        side_effect_class="IRREVERSIBLE_WRITE",
        allowed_resources=["traces.certificates"],
    )
    assert contract.idempotency_required is True
    assert contract.compensation_required is True
    assert contract.evidence_event_required is True


def test_run_contract_requires_sha256_and_checkpoint():
    contract = RunContract(
        run_id="run-1",
        thread_id="thread-1",
        idempotency_key="idem-1",
        graph_version="graph-1",
        started_at=datetime.now(timezone.utc),
        input_sha256="a" * 64,
    )
    assert contract.checkpoint_required is True
    assert contract.resume_allowed is True

    with pytest.raises(ValidationError):
        RunContract(
            run_id="run-1",
            thread_id="thread-1",
            idempotency_key="idem-1",
            graph_version="graph-1",
            input_sha256="not-a-sha",
        )


def test_evidence_manifest_cannot_claim_production_by_default():
    manifest = EvidenceManifest(
        package_id="E3-001",
        capability_id="S-001A",
        commit="a" * 40,
        artifacts={"fixture": "b" * 64},
        replay_reference="replay://E3-001",
    )
    assert manifest.production_claim is False
    assert manifest.promotion == "BLOCKED"


def test_promotion_is_fail_closed_until_every_gate_and_reviewer_pass():
    contract = PromotionContract(request_id="PROMO-001")
    assert contract.is_promotable() is False

    complete = PromotionContract(
        request_id="PROMO-002",
        decision="ALLOW",
        capability=True,
        evidence=True,
        replay=True,
        security=True,
        sovereignty=True,
        resilience=True,
        review=True,
        rollback=True,
        reviewer="authorized-reviewer",
    )
    assert complete.is_promotable() is True
