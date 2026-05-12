#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INPUT_PACKAGE="${1:-}"

if [[ -z "$INPUT_PACKAGE" ]]; then
  INPUT_PACKAGE="$(ls -1dt artifacts/audit-package-* 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$INPUT_PACKAGE" || ! -d "$INPUT_PACKAGE" ]]; then
  echo "[ERROR] No audit package found. Run: make audit-package-exhaustive" >&2
  exit 1
fi

TS="$(date -u +%Y%m%d-%H%M%S)"
OUT_DIR="artifacts/auditor-delivery-${TS}"
mkdir -p "$OUT_DIR"

INDEX_MD="${OUT_DIR}/01-INDICE-EJECUTIVO.md"
CHECKLIST_MD="${OUT_DIR}/02-CHECKLIST-FIRMABLE.md"
ANEXOS_MD="${OUT_DIR}/03-ANEXOS-EVIDENCIAS.md"
META_TXT="${OUT_DIR}/META.txt"

STATUS="UNKNOWN"
CHECKS="N/A"
if [[ -f "${INPUT_PACKAGE}/summary.json" ]]; then
  STATUS="$(python - <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
try:
    data=json.loads(p.read_text())
    print(data.get("status","UNKNOWN"))
except Exception:
    print("UNKNOWN")
PY
"${INPUT_PACKAGE}/summary.json")"
  CHECKS="$(python - <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
try:
    data=json.loads(p.read_text())
    cp=data.get("checks_passed","?")
    ct=data.get("checks_total","?")
    print(f"{cp}/{ct}")
except Exception:
    print("N/A")
PY
"${INPUT_PACKAGE}/summary.json")"
fi

cat > "$INDEX_MD" <<EOF
# PAQUETE AUDITORIA TRL9 - CASTUO-SYSTEM v2.1

Fecha UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Estado del paquete base: ${STATUS}
Checks: ${CHECKS}

## Alcance de esta entrega

- Validacion operativa TRL9 (ON/OFF GitHub)
- Cumplimiento CTAEX tecnico
- Cumplimiento legal base (RGPD/ISO baseline)
- Evidencias criptograficas de integridad

## Artefactos clave incluidos

- 01-INDICE-EJECUTIVO.md
- 02-CHECKLIST-FIRMABLE.md
- 03-ANEXOS-EVIDENCIAS.md
- Copia del paquete base: $(basename "$INPUT_PACKAGE")

## Verificadores externos (referencial)

| Auditor | Entregable | Estado esperado |
|---|---|---|
| CDTI | Bundle auditoria + checklist | Revision tecnica |
| CTAEX | Bundle + anexos de validacion | Revision de integracion |
| AENOR | Evidencias ISO/RGPD base | Pre-auditoria |

## Nota de alcance

Este dossier acredita evidencia tecnica y operativa reproducible. La certificacion formal externa (ISO/NIS2/CTAEX final) depende de auditoria de terceros.
EOF

cat > "$CHECKLIST_MD" <<EOF
# CHECKLIST FIRMABLE DE ENTREGA

Proyecto: CASTUO-SYSTEM v2.1
Fecha UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Checklist

- [ ] Se adjunta paquete de auditoria exhaustivo
- [ ] Se verifica estado GO en summary.json
- [ ] Se verifica integridad con integrity.sha256
- [ ] Se revisan logs de checks en logs/
- [ ] Se valida cumplimiento CTAEX (gate GO)
- [ ] Se valida cumplimiento legal base (gate GO)
- [ ] Se valida trazabilidad de evidencias (manifest)

## Firmas

- Responsable Tecnico (CTO): ____________________  Fecha: __________
- Responsable Seguridad/Compliance: ______________ Fecha: __________
- Revisor Externo/Auditor: _______________________ Fecha: __________
EOF

{
  echo "# ANEXOS DE EVIDENCIAS"
  echo
  echo "Paquete base: ${INPUT_PACKAGE}"
  echo
  echo "## Archivos relevantes"
  find "$INPUT_PACKAGE" -maxdepth 2 -type f | sort | sed 's#^#- #' 
} > "$ANEXOS_MD"

cp -r "$INPUT_PACKAGE" "$OUT_DIR/"

if command -v sha256sum >/dev/null 2>&1; then
  find "$OUT_DIR" -type f | sort | while read -r f; do sha256sum "$f"; done > "${OUT_DIR}/DELIVERY-INTEGRITY.sha256"
fi

if command -v zip >/dev/null 2>&1; then
  (cd artifacts && zip -rq "$(basename "$OUT_DIR").zip" "$(basename "$OUT_DIR")")
fi

if command -v pandoc >/dev/null 2>&1; then
  pandoc "$INDEX_MD" -o "${OUT_DIR}/01-INDICE-EJECUTIVO.pdf" || true
  pandoc "$CHECKLIST_MD" -o "${OUT_DIR}/02-CHECKLIST-FIRMABLE.pdf" || true
fi

{
  echo "source_package=${INPUT_PACKAGE}"
  echo "delivery_dir=${OUT_DIR}"
  echo "status=${STATUS}"
  echo "checks=${CHECKS}"
} > "$META_TXT"

echo "[OK] Auditor delivery generated: ${OUT_DIR}"
