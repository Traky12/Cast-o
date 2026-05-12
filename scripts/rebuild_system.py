#!/usr/bin/env python3
"""Verificación de integridad ZIP industrial vs manifiesto SHA-256 (Setup Composer)."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def sha256_zip_member(z: zipfile.ZipFile, name: str) -> str:
    h = hashlib.sha256()
    with z.open(name, "r") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def cmd_verify(zip_path: Path, manifest_path: Path) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = manifest.get("assets") or []
    errors: list[str] = []
    with zipfile.ZipFile(zip_path, "r") as z:
        names = set(z.namelist())
        for a in assets:
            rel = a["path_in_zip"].replace("\\", "/")
            if rel not in names and not any(n.endswith(rel) for n in names):
                errors.append(f"Falta en ZIP: {rel}")
                continue
            key = rel if rel in names else next(n for n in names if n.endswith(rel))
            got = sha256_zip_member(z, key)
            exp = (a.get("sha256_expected") or "").strip().lower()
            if exp.startswith("reemplazar") or not exp or len(exp) != 64:
                errors.append(f"Hash no configurado para {rel}")
                continue
            if got.lower() != exp.lower():
                errors.append(f"TAMPER: {rel} esperado {exp[:16]}... obtenido {got[:16]}...")
    if errors:
        print("INTEGRITY_FAIL", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print("INTEGRITY_OK", len(assets), "activos")
    return 0


def cmd_generate_manifest(zip_path: Path) -> None:
    """Genera JSON de ejemplo con hashes reales (para rellenar manifest oficial)."""
    with zipfile.ZipFile(zip_path, "r") as z:
        entries = []
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if name.endswith((".bin", ".pem", ".py", ".stp")):
                h = sha256_zip_member(z, name)
                entries.append({"path_in_zip": name, "sha256_expected": h, "logical_name": name.split("/")[-1]})
    print(json.dumps({"schema": "castuo.industrial_manifest.v1", "assets": entries}, indent=2))


def main() -> int:
    p = argparse.ArgumentParser(description="CASTUO Setup Composer — integridad ZIP")
    p.add_argument("--zip-path", type=Path, help="Ruta al ZIP industrial")
    p.add_argument("--manifest", type=Path, help="JSON con sha256_expected por asset")
    p.add_argument("--generate-manifest", action="store_true", help="Imprimir manifiesto con hashes del ZIP")
    args = p.parse_args()
    if not args.zip_path or not args.zip_path.is_file():
        print("Uso: --zip-path archivo.zip [--manifest m.json] | --generate-manifest", file=sys.stderr)
        return 2
    if args.generate_manifest:
        cmd_generate_manifest(args.zip_path)
        return 0
    if not args.manifest or not args.manifest.is_file():
        print("--manifest requerido para verificar", file=sys.stderr)
        return 2
    return cmd_verify(args.zip_path, args.manifest)


if __name__ == "__main__":
    raise SystemExit(main())
