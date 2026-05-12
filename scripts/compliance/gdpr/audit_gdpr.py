#!/usr/bin/env python3
"""
Comprobaciones mínimas sobre un JSON (¿quedan IPs o emails en claro obvio?).
No sustituye auditoría legal ni pentest.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _walk(obj: Any, path: str = "") -> list[str]:
    issues: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            kl = k.lower()
            if kl in ("ip_address", "ip", "client_ip") and v not in (None, ""):
                issues.append(f"{p}: campo IP presente")
            if kl == "email" and isinstance(v, str) and "@" in v and "." in v and len(v) < 80:
                if not re.fullmatch(r"[a-f0-9]{64}", v.lower()):
                    issues.append(f"{p}: posible email en claro")
            issues.extend(_walk(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            issues.extend(_walk(v, f"{path}[{i}]"))
    return issues


def check_anonymization(dataset_path: str | Path) -> bool:
    path = Path(dataset_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    issues = _walk(data)
    if issues:
        for i in issues:
            print(i)
        return False
    return True


def main() -> None:
    p = argparse.ArgumentParser(description="Chequeo básico post-anonimización.")
    p.add_argument("--dataset", type=Path, required=True)
    args = p.parse_args()
    ok = check_anonymization(args.dataset)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
