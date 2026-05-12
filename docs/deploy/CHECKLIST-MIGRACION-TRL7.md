# Checklist — migración infra soberana / cierre TRL7 *(orientativo)*

**Relación:** [PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md](./PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md)

*TRL7 aquí = criterios **internos** acordados con evidencia; no certificación oficial por marcar casillas.*

## Pre-migración

- [ ] Inventario de datos, regiones y subencargados (RGPD Art. 28 si aplica)
- [ ] DPIA revisada si cambia ubicación o proveedores ([DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md))
- [ ] Plan de rollback y ventana de mantenimiento
- [ ] Secretos A/B en destino ([PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md))

## Migración

- [ ] DNS/TLS y certificados válidos en nuevo perímetro
- [ ] PostgreSQL: backup + restore verificado; replicación si HA
- [ ] Redis: persistencia y TTL alineados a `snn_cache_ttl_seconds()` en despliegue
- [ ] `pytest -m trl6` (o gate acordado) en verde contra entorno objetivo

## Post-migración

- [ ] SLO/uptime medidos en ventana acordada (p. ej. 30 días)
- [ ] Latencia `castuo_neuro_hydro_infer_seconds` vs baseline archivado
- [ ] LLMNR/hardening red en hosts admin ([prontuario evolución](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) §2)
- [ ] Runbook incidentes actualizado ([RUNBOOK-RESPUESTA-INCIDENTES.md](./RUNBOOK-RESPUESTA-INCIDENTES.md))
- [ ] Acta de cierre firmada por responsable técnico + DPO si aplica
