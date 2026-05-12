#!/usr/bin/env python3
"""
Pseudonimización / supresión de campos típicos en JSON (apoyo RGPD; no es asesoría legal).

Uso:
  python data_anonymization.py --input data/raw_queries.json --output data/anonymized_queries.json
  python data_anonymization.py --input data/raw.json --output data/out.json --salt "secreto"
  python data_anonymization.py --input data/raw.json --output data/out.json --synthetic-names
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

Json = Union[Dict[str, Any], List[Any]]

SENSITIVE_DROP = ("ip_address", "location", "phone", "address", "dni", "documento")


def _hash(value: str, salt: str) -> str:
    return hashlib.sha256((value + (salt or "")).encode("utf-8")).hexdigest()


def anonymize_query(query: Dict[str, Any], salt: Optional[str] = None, *, synthetic_names: bool = False) -> Dict[str, Any]:
    """Anonimiza un objeto (consulta / fila)."""
    s = salt or ""
    anonymized = dict(query)

    if "email" in anonymized and isinstance(anonymized["email"], str):
        anonymized["email"] = _hash(anonymized["email"], s)
    if "student_id" in anonymized and isinstance(anonymized["student_id"], str):
        anonymized["student_id"] = _hash(anonymized["student_id"], s)
    if "name" in anonymized and isinstance(anonymized["name"], str):
        if synthetic_names:
            try:
                from faker import Faker

                anonymized["name"] = Faker(locale="es_ES").name()
            except ImportError:
                anonymized["name"] = _hash(anonymized["name"], s)
        else:
            anonymized["name"] = _hash(anonymized["name"], s)

    for field in SENSITIVE_DROP:
        anonymized.pop(field, None)
    return anonymized


def anonymize_dataset(
    input_path: str | Path,
    output_path: str | Path,
    salt: Optional[str] = None,
    synthetic_names: bool = False,
) -> None:
    inp, out = Path(input_path), Path(output_path)
    data = json.loads(inp.read_text(encoding="utf-8"))
    if isinstance(data, list):
        out_list = [
            anonymize_query(q, salt, synthetic_names=synthetic_names) for q in data if isinstance(q, dict)
        ]
        result: Json = out_list
    elif isinstance(data, dict):
        result = anonymize_query(data, salt, synthetic_names=synthetic_names)
    else:
        raise TypeError("JSON raíz debe ser lista u objeto")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Pseudonimizar JSON (RGPD apoyo).")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--salt", type=str, default=None, help="Sal opcional para hashing (string)")
    p.add_argument("--synthetic-names", action="store_true", help="Nombres sintéticos (requiere faker)")
    args = p.parse_args()
    anonymize_dataset(args.input, args.output, args.salt, args.synthetic_names)
    print(f"Dataset anonimizado guardado en {args.output}")


if __name__ == "__main__":
    main()

anonymize_record = anonymize_query
