---
title: "Checklist Sabionda - Puerta de Aceptacion"
---

# Checklist Pre-Merge para Agentes

## Requisitos minimos
- [ ] Preflight OK (sin errores criticos)
- [ ] Metricas de sincronizacion: castuo_agent_sync_errors == 0
- [ ] Drift detection: castuo_agent_drift_detection == 0
- [ ] Autenticacion Sabionda: status == authenticated (si endpoint configurado)
- [ ] Supervision soberana: evidencia y logs en infraestructura UE
- [ ] Trazabilidad: evidencia en logs/agent-actions-YYYYMMDD.json

## Bloqueos
- [ ] Fallo en preflight -> BLOQUEAR MERGE
- [ ] Drift no resuelto -> BLOQUEAR MERGE
- [ ] Errores de sincronizacion > 3 en ultimas 24h -> BLOQUEAR MERGE

## Documentacion
- [ ] Runbook .github/AGENT-SYNC-HARDENING.md actualizado
- [ ] Evidencia de pruebas de caos en logs/chaos-test-*.log
- [ ] Metricas exportadas (castuo_agent_sync_errors, castuo_agent_drift_detection)
