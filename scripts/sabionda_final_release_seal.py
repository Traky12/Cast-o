#!/usr/bin/env python3
"""
Sello Sabionda: genera o verifica SABIONDA_FINAL_RELEASE.log (SHA-256).
  python scripts/sabionda_final_release_seal.py
  python scripts/sabionda_final_release_seal.py --verify
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_NAME = "SABIONDA_FINAL_RELEASE.log"
SCAN_DIRS = ("docs", "contracts", "castuo_manifest")
SKIP_PARTS = frozenset(
    {".git", "__pycache__", "node_modules", ".pytest_cache", "venv", ".venv", "dist", "build"}
)
KERNEL_FILES = ("SYSTEM_PROMPT.md", "SUMMARY.md", "FINAL_VALIDATION_REPORT.md")
SHA_LINE = re.compile(r"^SHA256 ([a-f0-9]{64})\s+(.+)$")


def _skip(path: Path) -> bool:
    return any(p in SKIP_PARTS for p in path.parts)


def file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files() -> list[Path]:
    out: list[Path] = []
    for name in SCAN_DIRS:
        base = ROOT / name
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dp = Path(dirpath)
            if _skip(dp):
                dirnames.clear()
                continue
            dirnames[:] = [d for d in dirnames if d not in SKIP_PARTS]
            for fn in filenames:
                fp = dp / fn
                if fp.suffix.lower() in {".pyc", ".pyo"}:
                    continue
                try:
                    if fp.is_file():
                        out.append(fp)
                except OSError:
                    pass
    return sorted(out)


def parse_log_hashes(log_path: Path) -> dict[str, str]:
    """rel_path -> expected sha256"""
    if not log_path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SHA_LINE.match(line.strip())
        if m:
            out[m.group(2).strip()] = m.group(1)
    return out


def cmd_generate() -> int:
    lines: list[str] = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append("# SABIONDA_FINAL_RELEASE.log")
    lines.append(f"# Generado: {ts} UTC")
    lines.append("# ID certificado: EXT-CAS-2026-001-GM (SABIONDA-AUTH-V1)")
    lines.append("# Estado: LOCKDOWN / READY-FOR-DEPLOY")
    lines.append("")
    lines.append("## KERNEL LOCK (constitución agentes)")
    for rel in KERNEL_FILES:
        p = ROOT / rel
        if p.is_file():
            lines.append(f"SHA256 {file_sha256(p)}  {rel}")
        else:
            lines.append(f"MISSING  {rel}")
    lines.append("")
    lines.append("## BLACKOUT por defecto")
    sop = ROOT / "docs" / "security" / "BLACKOUT-RECOVERY-SOP.md"
    if sop.is_file():
        lines.append(f"SHA256 {file_sha256(sop)}  docs/security/BLACKOUT-RECOVERY-SOP.md")
    lines.append("")
    lines.append("## Integridad por directorio (docs/, contracts/, castuo_manifest/)")
    files = collect_files()
    for fp in files:
        rel = fp.relative_to(ROOT).as_posix()
        try:
            lines.append(f"SHA256 {file_sha256(fp)}  {rel}")
        except OSError as e:
            lines.append(f"ERROR {rel}  {e}")
    lines.append("")
    lines.append(f"# Total archivos hasheados: {len(files)}")
    out_path = ROOT / LOG_NAME
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Escrito {out_path} ({len(files)} archivos + kernel)")
    return 0


def cmd_verify() -> int:
    log_path = ROOT / LOG_NAME
    expected = parse_log_hashes(log_path)
    if not expected:
        print("ERROR: No existe o está vacío SABIONDA_FINAL_RELEASE.log", file=sys.stderr)
        return 2

    ok, fail = 0, 0
    kernel_ok = True
    print("=== KERNEL LOCK ===")
    for rel in KERNEL_FILES:
        p = ROOT / rel
        exp = expected.get(rel)
        if not exp:
            print(f"  SKIP (no en log): {rel}")
            continue
        if not p.is_file():
            print(f"  BREACH MISSING: {rel}")
            kernel_ok = False
            fail += 1
            continue
        cur = file_sha256(p)
        if cur == exp:
            print(f"  MATCH {rel}")
            ok += 1
        else:
            print(f"  BREACH {rel}")
            kernel_ok = False
            fail += 1

    print("=== BLACKOUT ===")
    bpath = "docs/security/BLACKOUT-RECOVERY-SOP.md"
    exp_b = expected.get(bpath)
    blackout_ok = False
    if exp_b and (ROOT / bpath).is_file():
        cur = file_sha256(ROOT / bpath)
        if cur == exp_b:
            print(f"  MATCH {bpath}")
            ok += 1
            blackout_ok = True
        else:
            print(f"  BREACH {bpath}")
            fail += 1
    elif exp_b:
        print(f"  BREACH missing file {bpath}")
        fail += 1

    print("=== ÁRBOL (resumen) ===")
    tree_ok = tree_bad = tree_miss = 0
    for rel, exp in sorted(expected.items()):
        if rel in KERNEL_FILES or rel == bpath:
            continue
        p = ROOT / rel
        if not p.is_file():
            tree_miss += 1
            fail += 1
        elif file_sha256(p) != exp:
            tree_bad += 1
            fail += 1
        else:
            tree_ok += 1
    tree_total = tree_ok + tree_bad + tree_miss
    print(f"  {tree_ok}/{tree_total} archivos coinciden con el log", end="")
    if tree_bad or tree_miss:
        print(f" (faltan o alterados: {tree_miss + tree_bad})")
    else:
        print()
    print("")
    print(f"KERNEL LOCK: {'MATCH' if kernel_ok else 'BREACH'}")
    print(f"BLACKOUT SOP: {'VALID' if blackout_ok else 'REVISAR'}")
    print(f"Archivos en árbol auditados vs log: {tree_ok}/{tree_total}")
    print(f"Fallos totales: {fail}")
    if fail:
        print("Estado: BREACH — regenerar log tras cambios legítimos: python scripts/sabionda_final_release_seal.py")
        return 1
    print("Estado: LOCKED (coherente con último sello en log)")
    print("EU compliance (referencial en código/manifiesto): revisar castuo_manifest/sovereignty.py + .cert")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Sello Sabionda EXT-CAS-2026-001-GM")
    ap.add_argument("--verify", action="store_true", help="Verificar disco vs SABIONDA_FINAL_RELEASE.log")
    args = ap.parse_args()
    return cmd_verify() if args.verify else cmd_generate()


if __name__ == "__main__":
    raise SystemExit(main())
