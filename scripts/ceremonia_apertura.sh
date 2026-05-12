#!/bin/bash
# CASTÚO-SYSTEM v1.7.0 - Protocolo de Apertura Soberana
# Script de apertura ceremonial para CTAEX. Ejecutar en pantalla; solicita firma PGP del Administrador.
# Uso: ./scripts/ceremonia_apertura.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
MANIFIESTO_SOPS="security/MANIFIESTO_SOBERANIA.md.sops"
TEMP_MANIFEST=".temp_manifest"

clear
echo -e "\e[1;32m"
echo "  ██████╗ █████╗ ███████╗████████╗██╗   ██╗ ██████╗ "
echo " ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██║   ██║██╔═══██╗"
echo " ██║     ███████║███████╗   ██║   ██║   ██║██║   ██║"
echo " ██║     ██╔══██║╚════██║   ██║   ██║   ██║██║   ██║"
echo " ╚██████╗██║  ██║███████║   ██║   ╚██████╔╝╚██████╔╝"
echo "  ╚═════╝╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝  ╚═════╝ "
echo -e "\e[0m"
echo -e "\e[1;33m[SISTEMA]:\e[0m Iniciando Protocolo OMEGA v1.7.0..."
sleep 1
echo -e "\e[1;33m[SEGURIDAD]:\e[0m Detectado Manifiesto Encriptado bajo Root of Trust."
echo -e "\e[1;31m[ADVERTENCIA]:\e[0m Se requiere firma del Administrador Principal (GREGORIO)."
echo ""

if [ ! -f "$MANIFIESTO_SOPS" ]; then
  echo -e "\e[1;31m[ERROR]:\e[0m No existe $MANIFIESTO_SOPS. Ejecuta primero ./scripts/sellar_manifiesto.sh"
  exit 1
fi

if sops -d "$MANIFIESTO_SOPS" > "$TEMP_MANIFEST" 2>/dev/null; then
  echo -e "\e[1;32m[ACCESO CONCEDIDO]:\e[0m Firma validada. Desencriptando Verdad del Sistema..."
  echo "--------------------------------------------------------------------------------"
  sleep 2
  while IFS= read -r line; do
    echo "$line"
    sleep 0.05
  done < "$TEMP_MANIFEST"
  echo "--------------------------------------------------------------------------------"
  rm -f "$TEMP_MANIFEST"
  echo ""
  echo -e "\e[1;34m[ESTADO]:\e[0m Castúo-System está ahora ONLINE bajo supervisión soberana."
else
  echo -e "\e[1;31m[ERROR]:\e[0m Firma inválida. El búnker permanece sellado."
  rm -f "$TEMP_MANIFEST"
  exit 1
fi
