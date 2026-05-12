#!/usr/bin/env bash
set -euo pipefail

# Uso: ./scoring.sh <frecuencia 1-5> <criticidad 1-5> <roi 1-5>
if [[ $# -ne 3 ]]; then
  echo "Uso: $0 <frecuencia 1-5> <criticidad 1-5> <roi 1-5>"
  exit 1
fi

f="$1"
c="$2"
r="$3"

for v in "$f" "$c" "$r"; do
  if ! [[ "$v" =~ ^[1-5]$ ]]; then
    echo "Error: todos los valores deben estar entre 1 y 5"
    exit 1
  fi
done

p=$((f + c + r))
echo "Prioridad total: $p"
if (( p >= 10 )); then
  echo "Decision: crear skill prioritaria"
else
  echo "Decision: mover a backlog"
fi
