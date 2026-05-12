#!/usr/bin/env bash
set -euo pipefail

until pg_isready -h timescaledb -p 5432 -U castuo; do
  echo "Esperando a TimescaleDB..."
  sleep 2
done

psql -h timescaledb -U castuo -d castuo_iot -f /docker-entrypoint-initdb.d/init.sql
echo "TimescaleDB inicializado"
