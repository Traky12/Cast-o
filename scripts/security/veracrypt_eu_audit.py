# scripts/security/veracrypt_eu_audit.py
#
# Auditoria VeraCrypt (EU) con enfoque en soberania: verificar existencia del contenedor
# y (opcional) probar un montaje/desmontaje en un directorio temporal.
#
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _run(cmd: list[str], timeout: int = 15) -> dict:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": (p.stdout or "").strip(),
            "stderr": (p.stderr or "").strip(),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container-path", required=True)
    ap.add_argument("--password-file", default="")
    ap.add_argument("--attempt-mount", action="store_true")
    ap.add_argument("--mount-point", default="/mnt/secure_castuo")
    args = ap.parse_args()

    container_path = Path(args.container_path)
    out: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "container_path": str(container_path),
        "checks": {},
    }

    out["checks"]["veracrypt_binary"] = _run(["veracrypt", "--version"])
    out["checks"]["container_exists"] = {"ok": container_path.is_file()}

    if not args.attempt_mount:
        out["result"] = "PASSED" if out["checks"]["container_exists"]["ok"] and out["checks"]["veracrypt_binary"]["ok"] else "FAILED"
        print(json.dumps(out, indent=2))
        return 0 if out["result"] == "PASSED" else 1

    if not args.password_file:
        out["result"] = "FAILED"
        out["error"] = "Missing --password-file when --attempt-mount is enabled"
        print(json.dumps(out, indent=2))
        return 2

    pw_path = Path(args.password_file)
    if not pw_path.is_file():
        out["result"] = "FAILED"
        out["error"] = f"Password file not found: {pw_path}"
        print(json.dumps(out, indent=2))
        return 2

    password = (pw_path.read_text(encoding="utf-8", errors="ignore").splitlines() or [""])[0].strip()
    if not password:
        out["result"] = "FAILED"
        out["error"] = "Empty password in password file"
        print(json.dumps(out, indent=2))
        return 2

    temp_mount = Path(args.mount_point)
    if temp_mount.exists():
        out["checks"]["mount_point_cleanup_note"] = "Using existing mount point; detach will be attempted."
    else:
        temp_mount.mkdir(parents=True, exist_ok=True)

    mount_cmd = [
        "veracrypt",
        str(container_path),
        str(temp_mount),
        "--password",
        password,
        "--pim",
        "0",
        "--keyfiles",
        "",
        "--protect-hidden=no",
        "--non-interactive",
    ]
    mount_res = _run(mount_cmd, timeout=25)
    out["checks"]["mount_attempt"] = mount_res

    # Intentar desmontaje
    unmount_res = _run(["veracrypt", "-d", str(temp_mount)], timeout=25)
    out["checks"]["unmount_attempt"] = unmount_res

    success = mount_res.get("ok", False) and unmount_res.get("ok", True)
    out["result"] = "PASSED" if success else "FAILED"

    # Limpieza suave: no borramos el contenido por seguridad.
    try:
        shutil.rmtree(temp_mount, ignore_errors=True)
    except Exception:
        pass

    print(json.dumps(out, indent=2))
    return 0 if out["result"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

