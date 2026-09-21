#!/usr/bin/env python3
"""Fail-closed validator for a CASTÚO capability gate."""
from pathlib import Path
import json
import sys

REQUIRED = [
    "capability", "evidence", "replay", "security",
    "sovereignty", "resilience", "review", "rollback",
]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_binary_gate.py <state.json>")
        return 2
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    states = data.get("states", {})
    missing = [key for key in REQUIRED if key not in states]
    if missing:
        print(json.dumps({"status": "BLOCK", "reason": "MISSING_STATE", "missing": missing}))
        return 1
    values = {key: states[key] is True for key in REQUIRED}
    promote = all(values.values())
    observed = "PROMOTE" if promote else "BLOCK"
    output = {
        "status": observed,
        "promotion": promote,
        "predicate": " && ".join(REQUIRED),
        "states": values,
        "claim": data.get("claim", "NO_CLAIM" if not promote else "REVIEW_REQUIRED"),
    }
    print(json.dumps(output, sort_keys=True))
    return 0 if not promote else 0


if __name__ == "__main__":
    raise SystemExit(main())
