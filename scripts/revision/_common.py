from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW | INFO
    category: str
    file: str
    message: str
    hint: str | None = None


def workspace_root() -> Path:
    # We keep it simple: this file lives in scripts/revision/
    # and the repo root is two levels up.
    return Path(__file__).resolve().parents[2]


def is_markdown(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".markdown"}


def as_posix_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()

