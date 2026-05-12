#!/usr/bin/env bash
set -euo pipefail

# Convierte documentos legales TRL10 de Markdown a PDF y Word.
# Diseñado para dejar evidencia documental lista para firma y archivo.

INPUT_DIR="${INPUT_DIR:-docs/legal/TRL10}"
OUTPUT_DIR="${OUTPUT_DIR:-docs/legal/TRL10/pdfs}"
REFERENCE_DOC="${REFERENCE_DOC:-scripts/legal_template.docx}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    log "ERROR: falta dependencia '$1'."
    exit 1
  }
}

ensure_reference_doc() {
  if [[ -f "${REFERENCE_DOC}" ]]; then
    return 0
  fi

  log "Plantilla Word no encontrada en ${REFERENCE_DOC}. Creando plantilla minima con pandoc..."
  mkdir -p "$(dirname "${REFERENCE_DOC}")"
  local tmp_md
  tmp_md="$(mktemp)"
  cat > "${tmp_md}" <<'EOF'
# Plantilla legal CASTUO-SYSTEM

Documento de referencia para exportacion DOCX.
EOF
  pandoc "${tmp_md}" -o "${REFERENCE_DOC}"
  rm -f "${tmp_md}"
}

convert_to_pdf() {
  local input_file="$1"
  local base_name output_file
  base_name="$(basename "${input_file}" .md)"
  output_file="${OUTPUT_DIR}/${base_name}.pdf"

  log "Convirtiendo ${input_file} -> ${output_file}"
  pandoc "${input_file}" -o "${output_file}" \
    --pdf-engine=pdflatex \
    --variable=geometry:margin=1in \
    --variable=fontsize:12pt \
    --variable=mainfont:"DejaVu Sans" \
    --variable=monofont:"DejaVu Sans Mono" \
    --variable=documentclass:scrartcl \
    --metadata=title:"${base_name//_/ }" \
    --metadata=author:"Gregorio Jimenez Bodes" \
    --metadata=date:"$(date +%d/%m/%Y)"
}

convert_to_word() {
  local input_file="$1"
  local base_name output_file
  base_name="$(basename "${input_file}" .md)"
  output_file="${OUTPUT_DIR}/${base_name}.docx"

  log "Convirtiendo ${input_file} -> ${output_file}"
  pandoc "${input_file}" -o "${output_file}" \
    --reference-doc="${REFERENCE_DOC}"
}

main() {
  require_cmd pandoc
  require_cmd pdflatex

  if [[ ! -d "${INPUT_DIR}" ]]; then
    log "ERROR: no existe directorio de entrada ${INPUT_DIR}"
    exit 1
  fi

  mkdir -p "${OUTPUT_DIR}"
  ensure_reference_doc

  local found=0
  shopt -s nullglob
  for file in "${INPUT_DIR}"/*.md; do
    found=1
    convert_to_pdf "${file}"
    convert_to_word "${file}"
  done
  shopt -u nullglob

  if [[ "${found}" -eq 0 ]]; then
    log "WARN: no se encontraron .md en ${INPUT_DIR}"
    exit 0
  fi

  log "Listo: documentos generados en ${OUTPUT_DIR}"
}

main "$@"

