# Plan de Excelencia Operativa (30-60-90 dias)

## P0 (30 dias)
- Persistencia IoT en TimescaleDB/PostgreSQL.
- Autenticacion obligatoria para ingesta IoT.
- Integracion basica TRACES con reintentos.

## P1 (60 dias)
- Vault/KMS en produccion con rotacion.
- Alertmanager + on-call.
- Automatizacion MQTT/TLS (rotacion cert/ACL).

## P2 (90 dias)
- SLOs y metricas de negocio.
- Resiliencia avanzada bridge (backoff + DLQ durable).
- Consolidacion completa de dependencies lockfile.
