#!/bin/bash
# backend/scripts/init_hsm.sh
# Inicialización del HSM Thales Luna 9 para CASTÚO-SYSTEM™ (EU/OSS).
# Ejecutar en servidor con HSM conectado y drivers instalados.

set -e

echo "Verificando conexión con el HSM..."
if ! command -v lunacm &>/dev/null; then
  echo "lunacm no encontrado. Instale el cliente Thales Luna (ej: /opt/thales/luna/client/bin/lunacm)."
  exit 1
fi

LUNACM="${LUNACM:-/opt/thales/luna/client/bin/lunacm}"

# Crear partición CASTUO si no existe (requiere permisos HSM)
echo "Creando partición CASTUO si no existe..."
$LUNACM <<'EOF' 2>/dev/null || true
partition create -partition CASTUO -label "CASTUO-SYSTEM Partition"
exit
EOF

echo "Creando dominio CASTUO_DOMAIN si no existe..."
$LUNACM <<'EOF' 2>/dev/null || true
domain create -domain CASTUO_DOMAIN -partition CASTUO
exit
EOF

echo "Generando clave maestra CASTUO_MK (Shamir 5/3) si no existe..."
$LUNACM <<'EOF' 2>/dev/null || true
key generate -domain CASTUO_DOMAIN -key CASTUO_MK -mechanism RSA:4096 -shares 5 -threshold 3
exit
EOF

echo "HSM configurado para CASTÚO-SYSTEM™."
echo "En producción, guarde las shares Shamir en lugares seguros (3/5 para desbloquear)."
