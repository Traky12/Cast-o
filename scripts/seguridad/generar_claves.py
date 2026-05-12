from __future__ import annotations

import os
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    """
    Genera una clave AES-256 para uso local (offline-first).

    Importante:
    - No comitear claves privadas reales en Git.
    - Este script crea un archivo local en docs/legal/CLAVES/ para despliegues reales.
    """
    root = _root()
    out_dir = root / "docs" / "legal" / "CLAVES"
    out_dir.mkdir(parents=True, exist_ok=True)

    key_path = out_dir / "aes_key.bin"
    if key_path.exists():
        print(f"OK: clave ya existe: {key_path}")
        return 0

    key = os.urandom(32)  # 256-bit
    key_path.write_bytes(key)
    try:
        # Best-effort: limitar permisos (en Windows puede no aplicar igual).
        os.chmod(key_path, 0o600)
    except Exception:
        pass

    print(f"OK: clave AES-256 generada: {key_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

