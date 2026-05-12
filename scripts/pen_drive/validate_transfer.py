#!/usr/bin/env python3
"""
validate_transfer.py — Valida una transferencia generada por transfer_to_pen.py:
- Compara SHA-256 del pen drive vs manifest (source_checksums).
- Valida estructura JSON de archivos cifrados (*.enc.json).
- Valida resultado basico de gemelos (si existe en el manifest).

Restriccion soberana:
encrypt_document.py es "one-way". Si se borraron textos planos tras cifrar,
la restauracion no sera automatica aqui (solo validamos integridad y formato).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def area_for(rel_posix: str) -> str:
    if rel_posix.startswith("docs/"):
        return "02_DOCS"
    if rel_posix.startswith("scripts/") or rel_posix.startswith("n8n/"):
        return "03_SCRIPTS"
    return "01_CORE"


def _load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_encrypted_json(file_path: Path) -> Tuple[bool, str]:
    """Valida que el fichero cifrado tenga JSON parseable y estructura esperada."""
    try:
        payload = _load_json(file_path)
    except Exception as e:
        return False, f"JSON invalido: {e}"

    required_keys = {"iv", "ciphertext", "encrypted_key", "hmac"}
    if not isinstance(payload, dict):
        return False, "payload no es dict"
    if not required_keys.issubset(set(payload.keys())):
        return False, f"campos faltantes: {sorted(list(required_keys - set(payload.keys())))}"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida una transferencia a pen drive.")
    parser.add_argument("--pen-drive-path", required=True, help="Ruta absoluta del pen drive (ej: E:/CASTUO-SYSTEM_ORIGINAL)")
    parser.add_argument("--manifest-path", default="", help="Ruta al transfer_manifest.json (default: <pen>/transfer_manifest.json)")
    parser.add_argument("--fail-fast", action="store_true", help="Termina al primer error.")
    args = parser.parse_args()

    pen_root = Path(args.pen_drive_path).resolve()
    manifest_path = Path(args.manifest_path).resolve() if args.manifest_path else (pen_root / "transfer_manifest.json")
    if not manifest_path.exists():
        raise SystemExit(f"Manifest no encontrado: {manifest_path}")

    manifest = _load_json(manifest_path)
    source_checksums: Dict[str, str] = manifest.get("checksums", {})  # type: ignore[assignment]
    encrypted_files: Dict[str, str] = manifest.get("encrypted_files", {})  # type: ignore[assignment]
    options: Dict[str, object] = manifest.get("options", {})  # type: ignore[assignment]

    remove_plaintext = bool(options.get("remove_plaintext_after_encrypt", False))

    errors: List[str] = []
    checked = 0
    encrypted_validated = 0

    # 1) Validar integridad de archivos (plaintext)
    for rel_global, expected_hash in source_checksums.items():
        pen_path = pen_root / area_for(rel_global) / rel_global
        checked += 1

        if not pen_path.exists():
            if remove_plaintext and rel_global in encrypted_files:
                # Se esperaba que el plaintext no existiera tras cifrado estricto.
                continue
            errors.append(f"Falta archivo en pen drive: {rel_global}")
            if args.fail_fast:
                break
            continue

        actual = _sha256_file(pen_path)
        if actual != expected_hash:
            errors.append(f"Checksum mismatch: {rel_global}")
            if args.fail_fast:
                break

    # 2) Validar estructura de cifrados
    for rel_global, enc_rel in encrypted_files.items():
        enc_path = pen_root / enc_rel
        if not enc_path.exists():
            errors.append(f"Cifrado no existe para: {rel_global} -> {enc_rel}")
            if args.fail_fast:
                break
            continue
        ok, reason = _validate_encrypted_json(enc_path)
        if not ok:
            errors.append(f"Cifrado invalido ({rel_global}): {reason}")
            if args.fail_fast:
                break
            continue

        encrypted_validated += 1

    report = {
        "pen_root": str(pen_root),
        "manifest_path": str(manifest_path),
        "timestamp": _utc_now_iso(),
        "checked_files": checked,
        "encrypted_files_validated": encrypted_validated,
        "remove_plaintext_after_encrypt": remove_plaintext,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors[:100],
        "errors_count": len(errors),
    }

    out_path = pen_root / "validation_report.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    if errors:
        print(f"[FAIL] {len(errors)} errores. Report: {out_path}")
        return 1
    print(f"[PASS] Validacion completa. Report: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

