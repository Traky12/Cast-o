#!/usr/bin/env python3
"""
Genera metadatos sin datos personales (derecho al olvido, GDPR Art. 17).
Elimina Propietario, DNI, Email de attributes; mantiene parcelaId, coordinates, certifications, etc.
Opcional: sube a IPFS y devuelve nuevo hash.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

PERSONAL_FIELDS = {"Propietario", "propietario", "DNI", "dni", "Email", "email", "Correo", "correo"}


def erase_personal_data(metadata: dict) -> dict:
    """Devuelve copia de metadata sin atributos personales."""
    out = {
        "name": metadata.get("name", ""),
        "description": metadata.get("description", ""),
        "image": metadata.get("image", ""),
        "attributes": [
            attr for attr in metadata.get("attributes", [])
            if attr.get("trait_type") not in PERSONAL_FIELDS
        ],
        "certifications": metadata.get("certifications", []),
    }
    return out


def upload_to_ipfs(data: dict) -> str | None:
    """Sube JSON a IPFS; devuelve hash o None si no disponible."""
    try:
        from ipfshttpclient import connect
        client = connect("/dns/ipfs.infura.io/tcp/5001/https")
        result = client.add_json(data)
        if isinstance(result, str):
            return result
        if isinstance(result, (list, tuple)) and result:
            r = result[0]
            return r.get("Hash") or r.get("hash") if isinstance(r, dict) else str(r)
        return None
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Borrar datos personales de metadatos (GDPR Art. 17)")
    parser.add_argument("input_json", help="Ruta al JSON de metadatos o '-' para stdin")
    parser.add_argument("-o", "--output", default="-", help="Salida JSON (default: stdout)")
    parser.add_argument("--upload-ipfs", action="store_true", help="Subir resultado a IPFS y mostrar hash")
    args = parser.parse_args()

    if args.input_json == "-":
        metadata = json.load(sys.stdin)
    else:
        with open(args.input_json, encoding="utf-8") as f:
            metadata = json.load(f)

    new_metadata = erase_personal_data(metadata)
    out = json.dumps(new_metadata, indent=2, ensure_ascii=False)

    if args.upload_ipfs:
        ipfs_hash = upload_to_ipfs(new_metadata)
        if ipfs_hash:
            print(ipfs_hash, file=sys.stderr)
            new_metadata["_ipfs_hash"] = ipfs_hash
            out = json.dumps(new_metadata, indent=2, ensure_ascii=False)

    if args.output == "-":
        print(out)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
