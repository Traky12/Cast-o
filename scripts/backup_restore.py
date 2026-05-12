#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copia de seguridad y restauración de backend/db/water_ctaex_usage.db."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.water_ctaex_plans import db_path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups"


def create_backup() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"water_ctaex_usage_{ts}.db"
    shutil.copy2(str(db_path()), str(dest))
    return dest


def restore_backup(src: Path) -> None:
    shutil.copy2(str(src), str(db_path()))


def list_backups() -> list[Path]:
    if not BACKUP_DIR.is_dir():
        return []
    return sorted(BACKUP_DIR.glob("water_ctaex_usage_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Backup / restore SQLite water CTAEX")
    p.add_argument("--backup", action="store_true")
    p.add_argument("--restore", metavar="FILE")
    p.add_argument("--list", action="store_true", dest="list_backups")
    args = p.parse_args()

    if args.backup:
        out = create_backup()
        print(out)
    elif args.restore:
        restore_backup(Path(args.restore))
        print("Restaurado desde", args.restore)
    elif args.list_backups:
        for b in list_backups():
            m = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{b.name}\t{m}")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
