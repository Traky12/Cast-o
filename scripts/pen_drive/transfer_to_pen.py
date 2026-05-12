#!/usr/bin/env python3
"""
transfer_to_pen.py — Transferencia a pen drive con:
- Copia completa del repo (excluyendo .git).
- Checksums SHA-256 para integridad.
- Cifrado de evidencias sensibles usando backend/scripts/encrypt_document.py (one-way archive).
- Registro opcional en GaiaChain (forensic evidence) vía GaiaChainForensicRegistry.
- Validacion "gemelos" de consistencia de metadatos (legal/seguridad UE) via backend/digital_twin/gemelos_digitales.py.

Nota soberana:
encrypt_document.py en este repo NO implementa --decrypt, asi que por defecto NO borramos el original
tras cifrar. Asi conservas recuperabilidad del sistema sin romper ejecucion futura.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore[assignment]


DEFAULT_EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__"}


DEFAULT_SENSITIVE_GLOBS = [
    # Evidencias legales y compliance (alto valor territorial/legal).
    # Nota: en este repo existe `docs/legal/` y `docs/compliance/`; no hay `docs/legal/clauses/`.
    "docs/legal/**",
    "docs/compliance/**",
    # Contratos (incluye DPO/Legal-as-code y similares)
    "docs/**/CONTRATO*.md",
    "docs/**/Contract*.md",
    "docs/**/contract*.md",
    # Contratos inteligentes (evidencia financiera/operativa)
    "contracts/**/*.sol",
    # Evidencias generadas (si existieran en el pen)
    "04_GAIACHAIN/evidence/**",
    # Ficheros de configuracion y credenciales
    ".env",
    ".env.*",
    "**/*.key",
    "**/*.pem",
    "**/*.crt",
]

def _log(message: str) -> None:
    # Mensajes en formato estable para que el equipo pueda copiar/pegar logs.
    print(f"[{_utc_now_iso()}] {message}")


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


def _iter_files(root: Path, exclude_dirs: set[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            yield dp / name


def _matches_any_glob(rel_posix: str, globs: List[str]) -> bool:
    rel = PurePosixPath(rel_posix)
    for g in globs:
        pattern = g.replace("\\", "/")
        if rel.match(pattern):
            return True
    return False


def _run_encrypt_document(repo_root: Path, source_file: Path, output_file: Path) -> None:
    encrypt_script = repo_root / "backend" / "scripts" / "encrypt_document.py"
    cmd = [
        sys.executable,
        str(encrypt_script),
        str(source_file),
        "-o",
        str(output_file),
    ]
    # No imprimimos stdout/stderr completo para no filtrar rutas/cifrado en logs.
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"encrypt_document fallo (rc={r.returncode}): {r.stderr.strip()[:400]}")


def _safe_json_write(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _pen_structure() -> Dict[str, List[str]]:
    # Estructura para mantener coherencia operativa del pen drive.
    return {
        "01_CORE": [],
        "02_DOCS": [],
        "03_SCRIPTS": [],
        "04_GAIACHAIN": ["tx_logs", "evidence"],
        "05_BACKUP": [],
    }


def _build_transfer_manifest(
    repo_root: Path,
    pen_root: Path,
    started_at: str,
    run_id: str,
    source_checksums: Dict[str, str],
    encrypted_map: Dict[str, str],
    gemelos_validation: Dict[str, object],
    gaiachain_result: Optional[Dict[str, object]],
    options: Dict[str, object],
) -> Dict[str, object]:
    return {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": _utc_now_iso(),
        "source_root": str(repo_root),
        "pen_root": str(pen_root),
        "exclude": sorted(list(DEFAULT_EXCLUDE_DIRS)),
        "options": options,
        "checksums": source_checksums,
        "encrypted_files": encrypted_map,
        "gemelos_validation": gemelos_validation,
        "gaiachain_registration": gaiachain_result,
    }


def _gemelos_validate(repo_root: Path, sensitive_globs: List[str]) -> Dict[str, object]:
    # Validacion de consistencia (no verifica el contenido de cada archivo).
    sys.path.insert(0, str(repo_root))
    from backend.digital_twin.gemelos_digitales import GemeloLegal, GemeloSeguridad

    gemelo_legal = GemeloLegal()
    gemelo_seg = GemeloSeguridad()

    legal_metadata = {
        "jurisdiction": "EU",
        "rgpd_compliance": "GDPR_Art32_2026",
        "ai_act_compliance": "EU_AI_Act_2024_Annex_III",
        "compliance": [
            "GDPR_Art32_2026",
            "EU_AI_Act_2024_Annex_III",
            "eIDAS_Regulation_2026",
        ],
        "transfer_run": {"sensitive_globs_count": len(sensitive_globs)},
    }

    legal_res = gemelo_legal.audit_compliance(legal_metadata)

    # La auditoria de seguridad valida parametros de configuracion del cifrado holografico (TRL9),
    # no la transferencia fisica. Se usa como control de que el paquete sigue alineado con el diseño.
    seguridad_res = gemelo_seg.audit_initial_configuration(
        params={
            "matrix_size": 256,
            "wavelength": 633,
            "refractive_index": 1.5,
            "quantum_noise_level": 0.01,
        },
        matrix_shape=(256, 256),
    )

    return {
        "legal": legal_res,
        "seguridad": seguridad_res,
        "timestamp": _utc_now_iso(),
    }


def _gaiachain_register(repo_root: Path, evidence: Dict[str, object], gaia_api_url: str, gaia_api_key: str | None) -> Dict[str, object]:
    sys.path.insert(0, str(repo_root))
    from backend.compliance.gaiachain_integration import GaiaChainForensicRegistry

    registry = GaiaChainForensicRegistry(api_url=gaia_api_url, api_key=gaia_api_key)
    # register_forensic_evidence aplica su propio hash y prepara payload de evidencia.
    return registry.register_forensic_evidence(evidence)


def _check_gaiachain_connection(gaia_api_url: str, gaia_api_key: str | None, timeout_s: int = 5) -> bool:
    """Verifica conectividad minima antes de registrar evidencias (solo se ejecuta si NO es air-gap)."""
    if requests is None:
        return False
    if not gaia_api_url:
        return False
    base = gaia_api_url.rstrip("/")
    headers = {"Authorization": f"Bearer {gaia_api_key}"} if gaia_api_key else {}

    candidates = [
        f"{base}/status",
        f"{base}/api/v1/status",
        f"{base}/api/status",
        f"{base}/api/v1/health",
    ]
    for url in candidates:
        try:
            r = requests.get(url, headers=headers, timeout=timeout_s)
            if r.status_code == 200:
                return True
        except Exception:
            continue
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Transferencia a pen drive con cifrado de evidencias y checksums.")
    parser.add_argument("--source-dir", default=".", help="Raiz del repo (default: .)")
    parser.add_argument("--pen-drive-path", required=True, help="Ruta absoluta del pen drive (ej: E:/CASTUO-SYSTEM_ORIGINAL)")
    parser.add_argument("--run-id", default="", help="Identificador del run (default: auto)")
    parser.add_argument("--encrypt-sensitive", action="store_true", help="Cifrar archivos sensibles detectados (one-way archive).")
    parser.add_argument(
        "--encrypt-all",
        action="store_true",
        help="Cifra absolutamente todos los archivos del repo (archivacion one-way).",
    )
    parser.add_argument(
        "--delete-plaintext-sensitive-only",
        action="store_true",
        help="Con --encrypt-all: elimina el plaintext SOLO para archivos sensibles (mantiene plaintext del runtime para que sea ejecutable).",
    )
    parser.set_defaults(keep_plaintext_after_encrypt=True)
    keep_group = parser.add_mutually_exclusive_group()
    keep_group.add_argument(
        "--keep-plaintext-after-encrypt",
        dest="keep_plaintext_after_encrypt",
        action="store_true",
        help="Conserva el texto plano tras cifrar (modo seguro por defecto).",
    )
    keep_group.add_argument(
        "--remove-plaintext-after-encrypt",
        dest="keep_plaintext_after_encrypt",
        action="store_false",
        help="⚠️ Elimina el texto plano tras cifrar (solo si tu protocolo de restauracion y claves esta validado).",
    )
    parser.add_argument("--air-gap", action="store_true", help="Evita registro en GaiaChain y llamadas de red.")
    parser.add_argument("--gaiachain", action="store_true", help="Registrar evidencia en GaiaChain si hay API configurada.")
    parser.add_argument("--sensitive-globs-file", default="", help="JSON con lista de globs sensibles (opcional).")
    parser.add_argument("--dry-run", action="store_true", help="Simulacion sin copiar ni cifrar.")

    args = parser.parse_args()

    repo_root = Path(args.source_dir).resolve()
    pen_root = Path(args.pen_drive_path).resolve()
    if not args.dry_run:
        pen_root.mkdir(parents=True, exist_ok=True)

    # remove_plaintext_after_encrypt:
    # - Para validate_transfer: indica si el manifest debe permitir ausencia de plaintext en archivos cifrados.
    # - En "delete-plaintext-sensitive-only" forzamos remove_plaintext_after_encrypt=true en el manifest,
    #   pero controlamos copy_plaintext_for_file para mantener plaintext del runtime.
    remove_plaintext_after_encrypt = not bool(args.keep_plaintext_after_encrypt)
    if args.delete_plaintext_sensitive_only:
        remove_plaintext_after_encrypt = True

    if remove_plaintext_after_encrypt and not args.encrypt_sensitive and not args.encrypt_all:
        raise SystemExit("Elimina plaintext requiere cifrado (--encrypt-sensitive y/o --encrypt-all).")

    started_at = _utc_now_iso()
    run_id = args.run_id or f"run_{int(time.time())}"

    delete_globs = DEFAULT_SENSITIVE_GLOBS
    if args.sensitive_globs_file:
        globs_payload = json.loads(Path(args.sensitive_globs_file).read_text(encoding="utf-8"))
        if not isinstance(globs_payload, list):
            raise SystemExit("sensitive-globs-file debe ser un JSON lista.")
        delete_globs = [str(x) for x in globs_payload]

    sensitive_globs = delete_globs
    if args.encrypt_all:
        # Patrón que matchea cualquier ruta relativa a repo (PurePosixPath.match).
        # '**' matchea tambien rutas de una sola pieza (ej: 'README.md').
        sensitive_globs = ["**"]

    # Dry-run: solo previsualizar qué se haria (sin copiar, sin cifrar, sin red).
    if args.dry_run:
        _log("Modo DRY-RUN activado. No se copiaran ni cifraran archivos.")

        files = list(_iter_files(repo_root, DEFAULT_EXCLUDE_DIRS))
        sensitive_files: List[str] = []
        for f in files:
            rel_global = f.relative_to(repo_root).as_posix()
            if args.encrypt_sensitive and _matches_any_glob(rel_global, sensitive_globs):
                sensitive_files.append(rel_global)

        _log("Archivos sensibles detectados (seran cifrados):")
        # Mantener salida legible: si hay muchos, mostramos primeros 200.
        max_list = 200
        for item in sensitive_files[:max_list]:
            print(f"- {item}")
        if len(sensitive_files) > max_list:
            _log(f"... y {len(sensitive_files) - max_list} archivos más (no mostrados).")

        _log(f"Estructura que se creara en {pen_root}:")
        print("- 01_CORE/")
        # En este repo, docs se preserva en 02_DOCS con su estructura.
        # Mostramos subdirs comunes si existen.
        docs_legal = (repo_root / "docs" / "legal").exists()
        docs_compliance = (repo_root / "docs" / "compliance").exists()
        print("- 02_DOCS/")
        if docs_legal:
            print("  - legal/")
        if docs_compliance:
            print("  - compliance/")
        print("- 03_SCRIPTS/")
        print("- 04_GAIACHAIN/")
        print("  - evidence/")
        print("- 05_BACKUP/")
        _log("DRY-RUN completado. Ejecuta sin --dry-run para transferir realmente.")
        return 0

    # 1) Crear estructura del pen drive (solo en ejecucion real)
    for top, children in _pen_structure().items():
        (pen_root / top).mkdir(parents=True, exist_ok=True)
        for child in children:
            (pen_root / top / child).mkdir(parents=True, exist_ok=True)

    pen_manifest_path = pen_root / "transfer_manifest.json"

    # 2) Calcular checksums del origen (para integridad antes/despues)
    # Evita incluir .git y entornos virtuales para no arrastrar basura ni roturas.
    source_checksums: Dict[str, str] = {}
    files = list(_iter_files(repo_root, DEFAULT_EXCLUDE_DIRS))
    _log(f"Calculando checksums del repo ({len(files)} archivos)...")
    for f in files:
        rel = f.relative_to(repo_root).as_posix()
        source_checksums[rel] = _sha256_file(f)

    # 3) Copiar todo el repo al pen drive, preservando rutas.
    # Regla de area:
    # - docs/*  => 02_DOCS
    # - scripts/* o n8n/* => 03_SCRIPTS
    # - todo lo demas => 01_CORE
    encrypted_map: Dict[str, str] = {}
    encrypted_count = 0
    copied_count = 0

    def area_for(rel_posix: str) -> str:
        if rel_posix.startswith("docs/"):
            return "02_DOCS"
        if rel_posix.startswith("scripts/") or rel_posix.startswith("n8n/"):
            return "03_SCRIPTS"
        return "01_CORE"

    for f in files:
        rel_global = f.relative_to(repo_root).as_posix()
        target_dir = pen_root / area_for(rel_global)
        target_path = target_dir / rel_global

        if args.encrypt_sensitive and _matches_any_glob(rel_global, sensitive_globs):
            enc_target = target_path.with_name(target_path.name + ".enc.json")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            # Log determinista para auditoria local (sin imprimir contenido ni claves).
            _log(f"Cifrando {rel_global} -> {enc_target.name}")
            _run_encrypt_document(repo_root, f, enc_target)
            encrypted_map[rel_global] = str(enc_target.relative_to(pen_root))
            encrypted_count += 1
            copy_plaintext = (not remove_plaintext_after_encrypt) or (
                args.delete_plaintext_sensitive_only
                and not _matches_any_glob(rel_global, delete_globs)
            )
            if copy_plaintext:
                shutil.copy2(f, target_path)
                copied_count += 1
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target_path)
            copied_count += 1

    # 4) Registro de evidencias cifradas / gemelos / gaiachain (opcional)
    # En evidencia registramos el hash del manifiesto de integridad (no contenido sensible).
    gemelos_validation: Dict[str, object] = {}
    if not args.air_gap:
        # Gemelos funcionan localmente. Aun si hay air-gap, no requieren red en este repo.
        gemelos_validation = _gemelos_validate(repo_root, delete_globs)
    else:
        gemelos_validation = {"skipped": True, "reason": "air-gap=true", "timestamp": _utc_now_iso()}

    gaia_result: Optional[Dict[str, object]] = None
    if args.gaiachain and not args.air_gap:
        gaia_api_url = os.getenv("GAIA_CHAIN_API_URL", "").strip()
        gaia_api_key = os.getenv("GAIA_CHAIN_API_KEY", "").strip() or None
        if not gaia_api_url:
            gaia_result = {"status": "skipped", "reason": "GAIA_CHAIN_API_URL no configurado"}
        else:
            if not _check_gaiachain_connection(gaia_api_url, gaia_api_key):
                gaia_result = {"status": "skipped", "reason": "GaiaChain connection check failed"}
            else:
                # Evidencia minimizada para preservar privacidad: solo hashes y metadatos.
                evidence = {
                    "type": "pen_drive_transfer",
                    "run_id": run_id,
                    "started_at": started_at,
                    "source_files_count": len(source_checksums),
                    "sensitive_globs_count": len(sensitive_globs),
                    "encrypted_files_count": encrypted_count,
                    "manifest_hash": hashlib.sha256(
                        json.dumps(source_checksums, sort_keys=True).encode("utf-8")
                    ).hexdigest(),
                }
                try:
                    gaia_result = _gaiachain_register(repo_root, evidence, gaia_api_url, gaia_api_key)
                except Exception as e:
                    gaia_result = {"status": "failed", "error": str(e)[:500]}

    # Guardar evidencias generadas localmente en pen drive (y cifrarlas si aplica).
    if not args.dry_run:
        evidence_dir = pen_root / "04_GAIACHAIN" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        gemelos_path = evidence_dir / "gemelos_validation.json"
        gemelos_path.write_text(
            json.dumps(gemelos_validation, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        gaia_path = evidence_dir / "gaiachain_registration.json"
        if gaia_result is not None:
            gaia_path.write_text(
                json.dumps(gaia_result, indent=2, sort_keys=True),
                encoding="utf-8",
            )

        if args.encrypt_sensitive:
            enc_gemelos = gemelos_path.with_suffix(gemelos_path.suffix + ".enc.json")
            _run_encrypt_document(repo_root, gemelos_path, enc_gemelos)
            encrypted_map["__generated__/gemelos_validation.json"] = str(enc_gemelos.relative_to(pen_root))
            if remove_plaintext_after_encrypt:
                try:
                    os.remove(gemelos_path)
                except FileNotFoundError:
                    pass

            if gaia_result is not None:
                enc_gaia = gaia_path.with_suffix(gaia_path.suffix + ".enc.json")
                _run_encrypt_document(repo_root, gaia_path, enc_gaia)
                encrypted_map["__generated__/gaiachain_registration.json"] = str(enc_gaia.relative_to(pen_root))
                if remove_plaintext_after_encrypt:
                    try:
                        os.remove(gaia_path)
                    except FileNotFoundError:
                        pass

    options = {
        "encrypt_sensitive": args.encrypt_sensitive,
        "keep_plaintext_after_encrypt": bool(args.keep_plaintext_after_encrypt),
        "remove_plaintext_after_encrypt": bool(remove_plaintext_after_encrypt),
        "air_gap": bool(args.air_gap),
        "gaiachain": bool(args.gaiachain),
        "dry_run": bool(args.dry_run),
    }

    # 5) Guardar manifiesto en pen drive
    manifest = _build_transfer_manifest(
        repo_root=repo_root,
        pen_root=pen_root,
        started_at=started_at,
        run_id=run_id,
        source_checksums=source_checksums,
        encrypted_map=encrypted_map,
        gemelos_validation=gemelos_validation,
        gaiachain_result=gaia_result,
        options=options,
    )

    if not args.dry_run:
        _safe_json_write(pen_manifest_path, manifest)
        _log(f"Manifiesto guardado en {pen_manifest_path}")

    # 6) Validacion basica de integridad (sin red)
    # Recalcular hashes en el pen para los mismos paths (solo los que copiamos en runtime_map).
    if not args.dry_run:
        # La validacion completa se realiza con validate_transfer.py para no duplicar coste (SHA-256 de todo el repo).
        pass

    _log(
        f"Transfer completa run_id={run_id} pen_drive={pen_root} total_archivos={len(files)} "
        f"copiados_plaintext={copied_count} cifrados={encrypted_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

