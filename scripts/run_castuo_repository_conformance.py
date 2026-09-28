"""Run the canonical CASTUO repository conformance validator.

This adapter intentionally contains no vocabulary or promotion semantics. The
source of truth is the validator shipped by castuo-evolution.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("castuo_canonical_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description="Run canonical CASTUO V1.0 conformance")
    parser.add_argument("--standard-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("artifacts/castuo-repository-conformance.json"))
    args = parser.parse_args()

    validator_path = args.standard_root / "scripts" / "validate_repository_conformance.py"
    if not validator_path.is_file():
        raise SystemExit(f"BLOCKED:canonical_validator_missing:{validator_path}")
    module = load_validator(validator_path)
    findings = module.validate(args.repository_root.resolve())
    blocked = any(item.startswith("BLOCKED:") for item in findings)
    status = "BLOCKED" if blocked else ("WARNING" if findings else "PASS")
    report = {
        "standard": "CASTUO-REPOSITORY-STANDARD-V1.0",
        "validator_source": str(validator_path),
        "repository_root": str(args.repository_root.resolve()),
        "status": status,
        "findings": findings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "semantic_owner": "castuo-evolution",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
