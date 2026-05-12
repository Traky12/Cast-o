---
name: "Incidente de Sincronizacion - Agente"
about: "Reportar fallo en sincronizacion de agentes"
title: "[INCIDENTE] Fallo sincronizacion agente: <breve_descripcion>"
labels: ["incident", "sync-failure"]
assignees: ["sabionda-team"]
---

## Contexto
- Agente afectado: [flujo-trabajo-autonomo / captacion-clientes / atencion-cliente-24h / creacion-apps-dashboards]
- Fecha/Hora: [YYYY-MM-DD HH:MM:SS]
- Entorno: [staging / production]
- Error observado: [mensaje exacto]

## Evidencia minima obligatoria
```bash
# 1) Estado de sincronizacion
git status --porcelain
git log --oneline -5

# 2) Logs de error
cat logs/sync-failure-$(date +%Y%m%d).log

# 3) Metricas de sincronizacion
bash scripts/metrics-sync.sh | grep castuo_agent_sync

# 4) Preflight
bash scripts/preflight.sh
```

## Acciones inmediatas
- [ ] Contencion: bloquear cambios en rama afectada
- [ ] Investigacion: ejecutar scripts/chaos-test-sync.sh
- [ ] Recuperacion: ejecutar scripts/reconcile.sh --dry-run
- [ ] Notificacion: alertar a Sabionda y equipo DPO
- [ ] Documentacion: actualizar .github/AGENT-SYNC-HARDENING.md si aplica

## Metricas post-incidente
- Time to Detect (TTD): [HH:MM]
- Time to Resolve (TTR): [HH:MM]
- MTTR (ultimos 30 dias): [promedio]
