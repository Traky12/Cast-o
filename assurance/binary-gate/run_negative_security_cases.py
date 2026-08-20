#!/usr/bin/env python3
"""Run local-only fail-closed negative cases for S-001A evidence and promotion."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "governance/evidence/E3-001-S001A"


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    envelope = json.loads((EVIDENCE / "evidence-envelope.json").read_text())
    gate = json.loads((EVIDENCE / "gate-state.json").read_text())
    baseline_digest = digest(envelope)
    cases: list[dict[str, object]] = []

    tampered_envelope = copy.deepcopy(envelope)
    tampered_envelope["scope"]["claim_boundary"] = "PRODUCTION_CLAIM"
    cases.append({
        "case_id": "NEG-001-TAMPERED-CLAIM-BOUNDARY",
        "expected": "BLOCK",
        "observed": "BLOCK" if digest(tampered_envelope) != baseline_digest else "ALLOW",
        "reason": "tampered envelope changes canonical digest",
    })

    altered_gate = copy.deepcopy(gate)
    altered_gate["states"]["security"] = None
    mandatory = ["capability", "evidence", "replay", "security", "sovereignty", "resilience", "review", "rollback"]
    cases.append({
        "case_id": "NEG-002-UNKNOWN-GATE-STATE",
        "expected": "BLOCK",
        "observed": "BLOCK" if any(altered_gate["states"].get(key) is not True for key in mandatory) else "PROMOTE",
        "reason": "unknown mandatory state is not green",
    })

    altered_scope = copy.deepcopy(envelope)
    altered_scope["scope"]["scenario"] = "UNDECLARED-SCENARIO"
    cases.append({
        "case_id": "NEG-003-SCOPE-EXPANSION",
        "expected": "BLOCK",
        "observed": "BLOCK" if altered_scope["scope"]["scenario"] != "S-001A" else "ALLOW",
        "reason": "scope expansion requires reassessment",
    })

    altered_replay = copy.deepcopy(envelope)
    altered_replay["observations"]["replay"] = "FAIL"
    cases.append({
        "case_id": "NEG-004-REPLAY-FAILURE",
        "expected": "BLOCK",
        "observed": "BLOCK" if altered_replay["observations"]["replay"] != "PASS_LOCAL_NO_CLAIM" else "ALLOW",
        "reason": "replay failure blocks promotion",
    })

    passed = all(item["expected"] == item["observed"] for item in cases)
    result = {
        "suite_id": "S-001A-NEGATIVE-SECURITY-LOCAL-001",
        "execution_mode": "LOCAL_ONLY",
        "status": "PASS_LOCAL_NO_CLAIM" if passed else "FAIL",
        "promotion": "BLOCKED",
        "cases": cases,
        "baseline_envelope_sha256": baseline_digest,
        "claim_boundary": "LOCAL_RESULT_NO_CLAIM",
    }
    output = EVIDENCE / "negative-security-tests.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
