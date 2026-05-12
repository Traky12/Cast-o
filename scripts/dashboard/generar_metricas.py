from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class MetricSet:
    generated_at_utc: str
    docs: dict
    scripts: dict
    badges: dict
    placeholders: dict


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _count_files(base: Path, pattern: str) -> int:
    if not base.exists():
        return 0
    return sum(1 for _ in base.rglob(pattern))


def _count_placeholders(base: Path) -> int:
    if not base.exists():
        return 0
    total = 0
    for md in base.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        total += text.count("PLACEHOLDER:")
    return total


def generar_metricas() -> MetricSet:
    root = _root()

    edu_docs = [
        root / "docs" / "cuento-castuo-sabionda",
        root / "docs" / "lengua-comun",
        root / "docs" / "castuo-educacion-2040",
    ]

    docs_count = sum(_count_files(d, "*.md") for d in edu_docs)
    placeholders_count = sum(_count_placeholders(d) for d in edu_docs)

    scripts_educ = root / "scripts" / "educacion"
    scripts_count = _count_files(scripts_educ, "*.py")

    badges_dir = root / "docs" / "lengua-comun" / "BADGES"
    badges_svg = _count_files(badges_dir, "*.svg")

    now = datetime.now(timezone.utc).isoformat()

    return MetricSet(
        generated_at_utc=now,
        docs={"markdown_files": docs_count},
        scripts={"educacion_py_files": scripts_count},
        badges={"svg_files": badges_svg},
        placeholders={"count": placeholders_count},
    )


def main() -> int:
    root = _root()
    out_dir = root / "docs" / "lengua-comun" / "DASHBOARD"
    out_dir.mkdir(parents=True, exist_ok=True)

    metricas = generar_metricas()
    out_path = out_dir / "metricas.json"
    out_path.write_text(json.dumps(asdict(metricas), ensure_ascii=False, indent=2), encoding="utf-8")

    print(str(out_path.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

