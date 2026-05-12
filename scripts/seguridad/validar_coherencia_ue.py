from __future__ import annotations

"""
Validaciones mínimas (UE) sin dependencias externas.

Objetivo:
- detectar placeholders legales críticos
- asegurar que el bloque educativo mantiene enlaces internos válidos (delegado a scripts/revision)

No es una certificación legal: es un guardarraíl operativo.
"""

import argparse
import json
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _count_placeholders(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for md in path.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        total += text.count("PLACEHOLDER:")
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Validador coherencia legal UE (offline-first).")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Bloquea despliegue si hay placeholders/plantillas pendientes.",
    )
    args = parser.parse_args()

    root = _root()
    legal = root / "docs" / "legal"
    registro = legal / "REGISTRO-DE-ACTIVIDADES.json"
    dpia_md = legal / "DPIA-CASTUO-SYSTEM.md"
    dpia_pdf = legal / "DPIA-CASTUO-SYSTEM.pdf"
    dpia_sig = legal / "DPIA-CASTUO-SYSTEM.pdf.p7s"
    claves_dir = legal / "CLAVES"
    aes_key = claves_dir / "aes_key.bin"
    manifiesto = root / "docs" / "lengua-comun" / "DASHBOARD" / "integridad.sha256.json"

    placeholders = _count_placeholders(legal)
    print("docs/legal placeholders:", placeholders)

    # Si no hay docs/legal aún, no bloqueamos (modo repo incompleto).
    if not legal.exists():
        print("WARN: falta docs/legal/ (no se puede validar coherencia legal).")
        return 0

    # Detectar si el registro sigue en modo plantilla.
    registro_es_plantilla = True
    if registro.exists():
        try:
            data = json.loads(registro.read_text(encoding="utf-8", errors="replace"))
            actividades = data.get("actividades", [])
            if actividades and isinstance(actividades, list):
                # Plantilla si contiene PLACEHOLDER o estado plantilla.
                raw = registro.read_text(encoding="utf-8", errors="replace")
                registro_es_plantilla = ("PLACEHOLDER:" in raw) or ('"estado": "plantilla"' in raw)
            else:
                registro_es_plantilla = True
        except Exception:
            registro_es_plantilla = True

    if registro_es_plantilla:
        print("WARN: REGISTRO-DE-ACTIVIDADES.json parece plantilla (pendiente de entradas reales).")

    if not dpia_md.exists():
        print("WARN: falta DPIA-CASTUO-SYSTEM.md (placeholder).")

    if not manifiesto.exists():
        print("WARN: falta integridad.sha256.json (genera con scripts/seguridad/generar_manifiesto.py).")

    if not aes_key.exists():
        print("WARN: falta docs/legal/CLAVES/aes_key.bin (genera con scripts/seguridad/generar_claves.py).")

    if not dpia_pdf.exists():
        print("WARN: falta DPIA-CASTUO-SYSTEM.pdf (esperable hasta firma).")
    if not dpia_sig.exists():
        print("WARN: falta DPIA-CASTUO-SYSTEM.pdf.p7s (firma).")

    # Modo "despliegue real": bloquea si quedan placeholders/plantillas o faltan artefactos mínimos.
    if args.strict:
        blockers = []
        if placeholders > 0:
            blockers.append("PLACEHOLDER en docs/legal/")
        if registro_es_plantilla:
            blockers.append("REGISTRO-DE-ACTIVIDADES.json sigue en plantilla")
        if not aes_key.exists():
            blockers.append("falta aes_key.bin")
        if not manifiesto.exists():
            blockers.append("falta integridad.sha256.json")
        if not dpia_pdf.exists():
            blockers.append("falta DPIA-CASTUO-SYSTEM.pdf firmado")
        if not dpia_sig.exists():
            blockers.append("falta DPIA-CASTUO-SYSTEM.pdf.p7s (firma QES)")
        if blockers:
            print("BLOCK:", "; ".join(blockers))
            return 1

    print("OK: coherencia legal mínima (UE) sin bloqueos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

