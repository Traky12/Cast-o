from __future__ import annotations

import pytest

from backend.patrimonio.xai_ledger import (
    XAILedgerLogV1,
    compute_event_anchor_hash,
    genesis_ledger_hash,
    sign_anchor_with_eth_dev_key,
    verify_log_chain,
)

eth_account = pytest.importorskip("eth_account")


def test_chain_genesis_then_two_events():
    sk = eth_account.Account.create().key.hex()
    g = genesis_ledger_hash()
    d1 = {
        "action": "REDUCE_THRUST",
        "reason_code": "RESONANCE_14HZ",
        "natural_language_explanation": "Reducción motor 3: resonancia arco medio punto ~14 Hz.",
    }
    t1 = {"motor_3_pct": 42, "vib_mm_s": 0.48}
    canon1, a1 = XAILedgerLogV1.build_pending(
        event_id="URN:CASTUO:LOG:2026:0001",
        timestamp="2026-03-18T08:00:00Z",
        unit_id="NANO-01",
        decision=d1,
        telemetry_snapshot=t1,
        parent_ledger_hash=g,
        mission_id="CRIPTA-SILENCIO",
    )
    assert compute_event_anchor_hash(g, canon1) == a1
    sig1 = sign_anchor_with_eth_dev_key(a1, sk)
    log1 = XAILedgerLogV1.seal(
        event_id="URN:CASTUO:LOG:2026:0001",
        timestamp="2026-03-18T08:00:00Z",
        unit_id="NANO-01",
        decision=d1,
        telemetry_snapshot=t1,
        parent_ledger_hash=g,
        signature_hex=sig1,
        mission_id="CRIPTA-SILENCIO",
    )
    d2 = {
        "action": "ABORT_PENETRATION",
        "reason_code": "THR_VIB_LIMIT",
        "natural_language_explanation": "Vibración > 0.5 mm/s en superficie frágil.",
    }
    sig2 = sign_anchor_with_eth_dev_key(
        XAILedgerLogV1.build_pending(
            event_id="URN:CASTUO:LOG:2026:0002",
            timestamp="2026-03-18T09:15:00Z",
            unit_id="NANO-03-ALFA",
            decision=d2,
            telemetry_snapshot={"lidar_confidence": 0.98},
            parent_ledger_hash=log1.event_anchor_hash,
        )[1],
        sk,
    )
    log2 = XAILedgerLogV1.seal(
        event_id="URN:CASTUO:LOG:2026:0002",
        timestamp="2026-03-18T09:15:00Z",
        unit_id="NANO-03-ALFA",
        decision=d2,
        telemetry_snapshot={"lidar_confidence": 0.98},
        parent_ledger_hash=log1.event_anchor_hash,
        signature_hex=sig2,
    )
    ok, msg = verify_log_chain([log1.to_committed_dict(), log2.to_committed_dict()])
    assert ok, msg


def test_verify_fails_on_tamper():
    g = genesis_ledger_hash()
    d = {"action": "X", "reason_code": "Y", "natural_language_explanation": "z"}
    log = XAILedgerLogV1.seal(
        event_id="URN:CASTUO:LOG:2026:0999",
        timestamp="2026-01-01T00:00:00Z",
        unit_id="NANO-X",
        decision=d,
        telemetry_snapshot={},
        parent_ledger_hash=g,
        signature_hex="0x00",
    )
    d2 = log.to_committed_dict()
    d2["decision"] = {**d, "action": "TAMPERED"}
    ok, msg = verify_log_chain([d2])
    assert not ok
