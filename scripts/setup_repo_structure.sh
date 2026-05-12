#!/usr/bin/env bash
set -euo pipefail

# Prepara estructura legal/operativa del repositorio para TRL10-TRL13.
# Conserva archivos existentes para no perder trazabilidad documental.

REPO_ROOT="${REPO_ROOT:-$(pwd)}"
LEGAL_DIR="${REPO_ROOT}/docs/legal"
TRL10_DIR="${LEGAL_DIR}/TRL10"
SCRIPTS_DIR="${REPO_ROOT}/scripts"
DOCS_DIR="${REPO_ROOT}/docs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}$1${NC}"; }
log_warn() { echo -e "${YELLOW}$1${NC}"; }

create_dirs() {
  log_info "Creando estructura de directorios..."
  mkdir -p "${LEGAL_DIR}" "${TRL10_DIR}" "${SCRIPTS_DIR}" "${DOCS_DIR}"
  mkdir -p "${LEGAL_DIR}/TRL11" "${LEGAL_DIR}/TRL12" "${LEGAL_DIR}/TRL13"
  mkdir -p "${LEGAL_DIR}/plantillas" "${LEGAL_DIR}/cumplimiento"
  mkdir -p "${SCRIPTS_DIR}/deploy" "${SCRIPTS_DIR}/backup" "${SCRIPTS_DIR}/legal"
  mkdir -p "${DOCS_DIR}/technical" "${DOCS_DIR}/operations"
}

write_if_missing() {
  local target_file="$1"
  local mode="${2:-644}"
  if [[ -f "${target_file}" ]]; then
    log_warn "Se mantiene archivo existente: ${target_file}"
    return 0
  fi
  cat > "${target_file}"
  chmod "${mode}" "${target_file}"
  log_info "Creado: ${target_file}"
}

create_placeholders() {
  log_info "Creando placeholders solo donde falten archivos..."

  write_if_missing "${TRL10_DIR}/contrato_ctaex_20260320.md" <<'EOF'
---
# CONTRATO DE LICENCIA DE USO NO EXCLUSIVA CASTUO-SYSTEM TRL9
Documento base de referencia para CTAEX.
---
EOF

  write_if_missing "${TRL10_DIR}/contrato_ctaex_final_20260320.md" <<'EOF'
---
# CONTRATO DE LICENCIA DE USO NO EXCLUSIVA CASTUO-SYSTEM TRL9 (VERSION FINAL)
Incluye anexos legales y clausulas revisadas.
---
EOF

  write_if_missing "${TRL10_DIR}/sla_20260320.md" <<'EOF'
---
# ACUERDO DE NIVEL DE SERVICIO (SLA) CASTUO-SYSTEM
Plantilla base de SLA.
---
EOF

  write_if_missing "${TRL10_DIR}/politica_privacidad_gdpr_2026.md" <<'EOF'
---
# POLITICA DE PRIVACIDAD CASTUO-SYSTEM
Plantilla base GDPR 2026.
---
EOF

  write_if_missing "${TRL10_DIR}/terminos_servicio_suscripciones.md" <<'EOF'
---
# TERMINOS DE SERVICIO CASTUO-SYSTEM
Plantilla base para suscripciones SaaS.
---
EOF

  write_if_missing "${TRL10_DIR}/checklist_iso_9001_2025.md" <<'EOF'
---
# CHECKLIST PARA CERTIFICACION ISO 9001:2025
Plantilla operativa para seguimiento de certificacion.
---
EOF

  write_if_missing "${REPO_ROOT}/docker-compose.prod.yml" <<'EOF'
version: "3.8"
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    restart: unless-stopped
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    restart: unless-stopped
EOF
}

create_helper_scripts() {
  write_if_missing "${SCRIPTS_DIR}/generate_legal_pdfs.sh" 755 <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
INPUT_DIR="docs/legal/TRL10"
OUTPUT_DIR="docs/legal/TRL10/pdfs"
mkdir -p "${OUTPUT_DIR}"
for file in "${INPUT_DIR}"/*.md; do
  pandoc "${file}" -o "${OUTPUT_DIR}/$(basename "${file}" .md).pdf" --pdf-engine=pdflatex
done
EOF

  if [[ -f "${SCRIPTS_DIR}/deploy_hetzner.sh" ]]; then
    chmod +x "${SCRIPTS_DIR}/deploy_hetzner.sh" || true
  fi
}

main() {
  log_info "=== INICIO setup_repo_structure ==="
  create_dirs
  create_placeholders
  create_helper_scripts
  log_info "=== ESTRUCTURA LISTA ==="
  log_warn "Siguiente paso recomendado:"
  log_warn "1) Revisa .env.production"
  log_warn "2) Ejecuta scripts/generate_legal_pdfs.sh"
  log_warn "3) Ejecuta scripts/deploy_hetzner.sh"
}

main "$@"

