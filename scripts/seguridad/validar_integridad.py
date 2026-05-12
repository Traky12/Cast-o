from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class HashEntry:
    path: str
    sha256: str


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(paths: list[Path], root: Path) -> list[HashEntry]:
    entries: list[HashEntry] = []
    for p in paths:
        if not p.exists() or not p.is_file():
            continue
        rel = p.resolve().relative_to(root.resolve()).as_posix()
        entries.append(HashEntry(path=rel, sha256=sha256_file(p)))
    return sorted(entries, key=lambda e: e.path)


def default_targets(root: Path) -> list[Path]:
    targets: list[Path] = []
    targets.extend((root / "scripts" / "educacion").glob("*.py"))
    targets.extend((root / "scripts" / "revision").glob("*.py"))
    targets.extend((root / "scripts" / "dashboard").glob("*.py"))
    targets.extend((root / "scripts" / "seguridad").glob("*.py"))
    return targets


def main() -> int:
    root = _root()
    entries = build_manifest(default_targets(root), root)
    out = root / "docs" / "lengua-comun" / "DASHBOARD" / "integridad.sha256.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([asdict(e) for e in entries], indent=2), encoding="utf-8")
    print(str(out.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

