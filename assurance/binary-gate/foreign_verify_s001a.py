#!/usr/bin/env python3
"""Foreign verifier: checks semantic equivalence without importing CASTÚO code."""
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: foreign_verify_s001a.py <fixture.json> <result.json>")
        return 2
    fixture = json.loads(Path(sys.argv[1]).read_text())
    result = json.loads(Path(sys.argv[2]).read_text())
    expected_events = [item["event"] for item in fixture["events"]]
    expected_states = [item["expected_state"] for item in fixture["events"]]
    checks = {
        "scenario_id": result.get("scenario_id") == fixture["scenario_id"],
        "fixture_id": result.get("fixture_id") == fixture["fixture_id"],
        "event_sequence": result.get("observed_sequence") == expected_events,
        "state_sequence": result.get("observed_states") == expected_states,
        "invariants": result.get("invariants") == fixture["expected_invariants"],
        "no_production_claim": result.get("claim_boundary") == "LOCAL_RESULT_NO_CLAIM" and not result.get("invariants", {}).get("production_claim", True),
    }
    status = "PASS_FOREIGN_SEMANTIC_REPLAY" if all(checks.values()) else "BLOCK_FOREIGN_REPLAY"
    print(json.dumps({"status": status, "checks": checks}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
