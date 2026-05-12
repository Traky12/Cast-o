from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def demo_root() -> Path:
    return Path(os.getenv("DEMO_TRL101_DATA_DIR", str(_REPO_ROOT / "data" / "demo_trl101")))


def cert_dir() -> Path:
    return demo_root() / "certificates"


def invoice_dir() -> Path:
    return demo_root() / "invoices"


def ensure_demo_dirs() -> None:
    cert_dir().mkdir(parents=True, exist_ok=True)
    invoice_dir().mkdir(parents=True, exist_ok=True)
