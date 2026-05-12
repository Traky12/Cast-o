#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# CASTÚO-SYSTEM™ v3.1 — Script de Backup
#
# Hace copia de seguridad de:
#   - PVC de datos (QR registry, PDFs, certificados)
#   - Base de datos PostgreSQL
#   - Configuración Kubernetes (ConfigMaps, no Secrets)
#
# Uso:
#   ./scripts/backup.sh                    # backup completo
#   ./scripts/backup.sh --db-only          # solo PostgreSQL
#   ./scripts/backup.sh --k8s-only         # solo manifests K8s
#   ./scripts/backup.sh --restore <file>   # restaurar desde backup
#
# Crontab sugerido (diario a las 2:00 AM):
#   0 2 * * * /opt/castuo-system/scripts/backup.sh >> /var/log/castuo-backup.log 2>&1
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Configuración ──────────────────────────────────────────────────────────────
NS="${CASTUO_NAMESPACE:-castuo-system}"
BACKUP_DIR="${BACKUP_DIR:-/backups/castuo}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%dT%H%M%S)
BACKUP_NAME="castuo-backup-${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# PostgreSQL (si está configurado)
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-castuo_db}"
DB_USER="${POSTGRES_USER:-castuo}"
DB_PASS="${POSTGRES_PASSWORD:-}"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓${NC} $1"; }
err()  { echo -e "${RED}  ✗${NC} $1"; }
warn() { echo -e "${YELLOW}  ⚠${NC} $1"; }
info() { echo -e "    $1"; }

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  CASTÚO Backup — $(date '+%Y-%m-%d %H:%M:%S')          ║"
echo "╚═══════════════════════════════════════════════════════╝"

# ── Modo restore ──────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--restore" ]]; then
    RESTORE_FILE="${2:-}"
    if [[ -z "$RESTORE_FILE" || ! -f "$RESTORE_FILE" ]]; then
        err "Uso: $0 --restore <ruta-al-backup.tar.gz>"
        exit 1
    fi
    echo "⏮  Restaurando desde: $RESTORE_FILE"
    mkdir -p "${BACKUP_DIR}/restore_${TIMESTAMP}"
    tar -xzf "$RESTORE_FILE" -C "${BACKUP_DIR}/restore_${TIMESTAMP}"
    ok "Backup extraído en ${BACKUP_DIR}/restore_${TIMESTAMP}"
    echo ""
    echo "Pasos manuales requeridos:"
    echo "  1. kubectl cp <pod>:/data ← ${BACKUP_DIR}/restore_${TIMESTAMP}/pvc-data/"
    echo "  2. psql -h $DB_HOST -U $DB_USER $DB_NAME < ${BACKUP_DIR}/restore_${TIMESTAMP}/postgres_dump.sql"
    exit 0
fi

# ── Crear directorio de backup ────────────────────────────────────────────────
mkdir -p "$BACKUP_PATH"
info "Destino: $BACKUP_PATH"

# ── 1. Backup PVC via kubectl cp ─────────────────────────────────────────────
if [[ "${1:-}" != "--db-only" && "${1:-}" != "--k8s-only" ]]; then
    echo ""
    echo "── 1. PVC Data Backup ──────────────────────────────────"

    if command -v kubectl &>/dev/null; then
        POD=$(kubectl get pod -n "$NS" -l app=castuo-api \
            -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

        if [[ -n "$POD" ]]; then
            mkdir -p "${BACKUP_PATH}/pvc-data"
            kubectl cp "${NS}/${POD}:/data" "${BACKUP_PATH}/pvc-data/" 2>/dev/null && \
                ok "PVC /data copiado → ${BACKUP_PATH}/pvc-data/" || \
                warn "No se pudo copiar /data del pod $POD"
        else
            warn "No se encontraron pods castuo-api en namespace $NS"
        fi
    else
        warn "kubectl no disponible — saltando backup de PVC"
    fi
fi

# ── 2. Backup PostgreSQL ──────────────────────────────────────────────────────
if [[ "${1:-}" != "--k8s-only" ]]; then
    echo ""
    echo "── 2. PostgreSQL Backup ────────────────────────────────"

    if command -v pg_dump &>/dev/null && [[ -n "$DB_PASS" ]]; then
        PGPASSWORD="$DB_PASS" pg_dump \
            -h "$DB_HOST" -p "$DB_PORT" \
            -U "$DB_USER" "$DB_NAME" \
            --no-password \
            -f "${BACKUP_PATH}/postgres_dump.sql" 2>/dev/null && \
            ok "PostgreSQL dump → ${BACKUP_PATH}/postgres_dump.sql" || \
            warn "pg_dump falló — verificar conexión a $DB_HOST:$DB_PORT"
    elif command -v kubectl &>/dev/null; then
        # Backup via kubectl exec (dentro del cluster)
        PG_POD=$(kubectl get pod -n "$NS" -l app=postgres \
            -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
        if [[ -n "$PG_POD" ]]; then
            kubectl exec -n "$NS" "$PG_POD" -- \
                pg_dump -U "$DB_USER" "$DB_NAME" \
                > "${BACKUP_PATH}/postgres_dump.sql" 2>/dev/null && \
                ok "PostgreSQL dump via kubectl → ${BACKUP_PATH}/postgres_dump.sql" || \
                warn "No se pudo hacer dump de PostgreSQL"
        else
            warn "Pod PostgreSQL no encontrado en namespace $NS"
        fi
    else
        warn "pg_dump y kubectl no disponibles — saltando backup de BD"
    fi
fi

# ── 3. Backup ConfigMaps K8s (no Secrets) ─────────────────────────────────────
if [[ "${1:-}" != "--db-only" ]]; then
    echo ""
    echo "── 3. Kubernetes ConfigMaps ────────────────────────────"

    if command -v kubectl &>/dev/null; then
        mkdir -p "${BACKUP_PATH}/k8s"
        kubectl get configmap -n "$NS" -o yaml > "${BACKUP_PATH}/k8s/configmaps.yaml" 2>/dev/null && \
            ok "ConfigMaps exportados" || warn "No se pudieron exportar ConfigMaps"
        kubectl get deployment,service,ingress,hpa,pvc -n "$NS" -o yaml \
            > "${BACKUP_PATH}/k8s/workloads.yaml" 2>/dev/null && \
            ok "Workloads exportados" || warn "No se pudieron exportar workloads"
    else
        warn "kubectl no disponible — saltando backup K8s"
    fi
fi

# ── 4. Comprimir backup ───────────────────────────────────────────────────────
echo ""
echo "── 4. Comprimir ────────────────────────────────────────"
ARCHIVE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
tar -czf "$ARCHIVE" -C "$BACKUP_DIR" "$BACKUP_NAME"
SIZE=$(du -sh "$ARCHIVE" | cut -f1)
ok "Archivo creado: $ARCHIVE ($SIZE)"
rm -rf "$BACKUP_PATH"

# ── 5. Limpieza de backups antiguos ──────────────────────────────────────────
echo ""
echo "── 5. Limpieza (retención ${RETENTION_DAYS} días) ────────────────"
DELETED=$(find "$BACKUP_DIR" -name "castuo-backup-*.tar.gz" \
    -mtime "+${RETENTION_DAYS}" -print -delete 2>/dev/null | wc -l)
if [[ "$DELETED" -gt 0 ]]; then
    ok "Eliminados $DELETED backups antiguos (>${RETENTION_DAYS} días)"
else
    info "No hay backups que eliminar"
fi

# ── Resumen ───────────────────────────────────────────────────────────────────
echo ""
TOTAL=$(find "$BACKUP_DIR" -name "castuo-backup-*.tar.gz" | wc -l)
echo "═══════════════════════════════════════════════════════"
ok "Backup completado: $ARCHIVE"
info "Total backups almacenados: $TOTAL"
info "Retención: $RETENTION_DAYS días"
echo "═══════════════════════════════════════════════════════"
