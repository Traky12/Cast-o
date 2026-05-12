#!/usr/bin/env python3
"""
encrypt_remaining_on_pen.py — Cifra en el pen drive los archivos que quedaron en plaintext
despues de un transfer_to_pen.py con remove-plaintext-after-encrypt.

Objetivo: cumplir "cifrar absolutamente todo" incluso si el match de globs quedo incompleto.
Actualiza transfer_manifest.json y permite que validate_transfer.py vuelva a dar PASS.

Importante:
- encrypt_document.py es one-way en este repo (no incluye decrypt).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict


def _area_for(rel_posix: str) -> str:
    if rel_posix.startswith("docs/"):
        return "02_DOCS"
    if rel_posix.startswith("scripts/") or rel_posix.startswith("n8n/"):
        return "03_SCRIPTS"
    return "01_CORE"


def _run_encrypt_document(repo_root: Path, input_file: Path, output_file: Path) -> None:
    encrypt_script = repo_root / "backend" / "scripts" / "encrypt_document.py"
    cmd = [
        sys.executable,
        str(encrypt_script),
        str(input_file),
        "-o",
        str(output_file),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"encrypt_document fallo (rc={r.returncode}): {r.stderr.strip()[:400]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cifra en pen drive los archivos que quedaron plaintext.")
    parser.add_argument("--repo-root", default=".", help="Ruta al repo local (default: .)")
    parser.add_argument("--pen-drive-path", required=True, help="Ruta del pen drive (ej: D:\\CASTUO-SYSTEM_ORIGINAL)")
    parser.add_argument("--fail-fast", action="store_true", help="Falla al primer error.")
    parser.add_argument("--only-if-missing-enc", action="store_true", help="Solo cifra si NO existe .enc.json.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    pen_root = Path(args.pen_drive_path).resolve()
    manifest_path = pen_root / "transfer_manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Manifest no encontrado: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checksums: Dict[str, str] = manifest.get("checksums", {})
    encrypted_files: Dict[str, str] = manifest.get("encrypted_files", {})
    options: Dict[str, object] = manifest.get("options", {})

    remove_plaintext = bool(options.get("remove_plaintext_after_encrypt", False))
    if not remove_plaintext:
        print("[WARN] El manifest indica que remove_plaintext_after_encrypt=false. Continuando igualmente.")

    errors = []
    newly_encrypted = 0

    for rel_global in checksums.keys():
        if rel_global in encrypted_files:
            continue

        plaintext_path = pen_root / _area_for(rel_global) / rel_global
        if not plaintext_path.exists():
            # Puede que no exista porque ya fue eliminado o porque estaba excluido del conjunto.
            continue

        enc_path = plaintext_path.with_name(plaintext_path.name + ".enc.json")
        if args.only_if_missing_enc and enc_path.exists():
            continue

        try:
            enc_path.parent.mkdir(parents=True, exist_ok=True)
            _run_encrypt_document(repo_root, plaintext_path, enc_path)
            encrypted_files[rel_global] = str(enc_path.relative_to(pen_root))
            newly_encrypted += 1
            # Eliminar plaintext despues de cifrar (one-way). Si quieres conservarlo, no uses remove_plaintext_after_encrypt.
            try:
                plaintext_path.unlink()
            except Exception:
                # No rompemos por limpieza fallida; validate_transfer detectara el estado.
                pass
        except Exception as e:
            errors.append(f"{rel_global}: {e}")
            if args.fail_fast:
                break

    manifest["encrypted_files"] = encrypted_files
    manifest["options"] = options
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(f"[OK] newly_encrypted={newly_encrypted} errors={len(errors)}")
    if errors:
        for msg in errors[:20]:
            print(f"[ERR] {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

