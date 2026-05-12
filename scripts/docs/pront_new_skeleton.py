#!/usr/bin/env python3
"""Genera un PRONT vacío desde docs/deploy/_templates/PRONT-SKELETON.md."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Crea docs/deploy/PRONT-CASTUO-<M>-v<V>-YYYY.md")
    p.add_argument("module", help="Nombre corto del módulo, ej. SIGPAC, N8N")
    p.add_argument("--version", default="1", help="Versión mayor del PRONT, default 1")
    p.add_argument("--subtitle", default="Integración y operación")
    p.add_argument("--scope", default="Módulo (completar)")
    args = p.parse_args()

    root = Path(__file__).resolve().parents[2]
    tpl = root / "docs" / "deploy" / "_templates" / "PRONT-SKELETON.md"
    if not tpl.is_file():
        raise SystemExit(f"No existe plantilla: {tpl}")

    year = date.today().year
    mod = args.module.strip().upper().replace(" ", "_")
    out = root / "docs" / "deploy" / f"PRONT-CASTUO-{mod}-v{args.version}-{year}.md"
    text = tpl.read_text(encoding="utf-8")
    text = text.replace("{MODULE}", mod)
    text = text.replace("{VERSION}", args.version)
    text = text.replace("{DATE}", date.today().strftime("%B %Y"))
    text = text.replace("{SUBTITLE}", args.subtitle)
    text = text.replace("{SCOPE}", args.scope)

    if out.exists():
        raise SystemExit(f"Ya existe: {out}")
    out.write_text(text, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
