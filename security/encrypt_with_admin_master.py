#!/usr/bin/env python3
"""
Cifrar/descifrar archivos o stdin con la clave maestra del administrador general.
Uso:
  echo -n "secreto" | python3 security/encrypt_with_admin_master.py encrypt   → base64
  python3 security/encrypt_with_admin_master.py encrypt -i archivo.txt -o archivo.enc
  python3 security/encrypt_with_admin_master.py decrypt -i archivo.enc -o archivo.txt
Requiere: ADMIN_MASTER_KEY en env, o /run/secrets/admin_master_key, o security/.admin_master_key
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Raíz repo para importar admin_master_layer
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from security.admin_master_layer import decrypt as _decrypt, encrypt as _encrypt


def main():
    parser = argparse.ArgumentParser(description="Cifrar/descifrar con clave maestra administrador")
    parser.add_argument("mode", choices=("encrypt", "decrypt"), help="encrypt | decrypt")
    parser.add_argument("-i", "--input", type=str, default=None, help="Archivo de entrada (default: stdin)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Archivo de salida (default: stdout)")
    args = parser.parse_args()
    if args.input:
        data = Path(args.input).read_bytes()
    else:
        data = sys.stdin.buffer.read()
    try:
        if args.mode == "encrypt":
            out = _encrypt(data)
        else:
            out = _decrypt(data)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    if args.output:
        Path(args.output).write_bytes(out)
    else:
        sys.stdout.buffer.write(out if isinstance(out, bytes) else out.encode("utf-8"))


if __name__ == "__main__":
    main()
