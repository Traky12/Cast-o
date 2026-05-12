#!/usr/bin/env python3
"""
Verifica la integridad de la cadena de trazabilidad.
- Comprueba hashes y firmas
- Opcional: exportar cadena y cobertura normativa
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from backend.compliance.immutable_traceability import ImmutableTraceability
    from backend.security.end_to_end_encryption import EndToEndEncryption
except ImportError as e:
    print("Error importando módulos:", e, file=sys.stderr)
    sys.exit(1)


def _check_normative_coverage(chain: List[Dict[str, Any]]) -> Dict[str, int]:
    coverage: Dict[str, int] = {}
    for block in chain:
        event = block.get("event", block)
        for norm in event.get("normative_references", []):
            coverage[norm] = coverage.get(norm, 0) + 1
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificador de cadena de trazabilidad")
    parser.add_argument("--since", help="Fecha inicial (YYYY-MM-DD)")
    parser.add_argument("--export", help="Exportar cadena a archivo")
    parser.add_argument("--verify", action="store_true", help="Verificar integridad de la cadena")
    args = parser.parse_args()

    encryption = EndToEndEncryption()
    traceability = ImmutableTraceability(encryption)

    if args.since:
        try:
            since_date = datetime.strptime(args.since, "%Y-%m-%d")
            chain = traceability.get_audit_trail(since=since_date)
        except ValueError:
            print("Formato de fecha inválido. Usar YYYY-MM-DD.", file=sys.stderr)
            return 1
    else:
        chain = list(traceability.current_chain)

    if args.verify:
        if traceability.verify_chain():
            print("Cadena de trazabilidad válida")
        else:
            print("Errores en la cadena de trazabilidad.", file=sys.stderr)
            return 1

    if args.export:
        traceability.export_chain(args.export, encrypt=True)
        print("Cadena exportada a", args.export)

    print("\nResumen de la cadena:")
    print("- Bloques:", len(chain))
    if chain:
        last = chain[-1]
        print("- Último hash:", last.get("event_hash", "N/A"))
    norms = _check_normative_coverage(chain)
    print("- Normativas cubiertas:", len(norms))
    if norms:
        print("\nCumplimiento normativo:")
        for norm, count in sorted(norms.items(), key=lambda x: -x[1]):
            print(f"  - {norm}: {count} eventos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
