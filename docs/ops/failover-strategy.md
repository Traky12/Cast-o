# Estrategia de failover y alta disponibilidad — CASTÚO-SYSTEM

Documento para **operación y due diligence**: distingue lo **implementado en el repositorio** de lo que es **diseño objetivo** o **pendiente de ingeniería**. Ningún RTO/RPO ni porcentaje de disponibilidad de este archivo sustituye un **informe de piloto** o un **SLA contractual** medido.

---

## 1. Pregunta operativa

**Si el servicio “central” cae, ¿se interrumpe el cultivo?**

La respuesta honesta hoy depende de **qué** consideres central:

| “Central” | Efecto típico hoy | Mitigación en repo / runbook |
|-----------|-------------------|-------------------------------|
| Instancia **n8n-trillizo** (auditoría Markdown) | Deja de registrarse el journal vía webhook; **no** implica por sí sola parar riego si los lazos de control son locales | Otro n8n con mismo volumen `cerebros/auditoria` o restauración desde backup |
| **Postgres cerebros** (`postgres-cerebros`) | Pierdes SQL operativo que vivía solo ahí; flujos n8n que lean/escriban esa BD fallan | `deploy/RUNBOOK-BACKUP-CEREBROS-POSTGRES.md`, `scripts/backup_castuo_cerebros.sh` |
| **Un único n8n “de campo”** por sector sin réplica | Ese sector pierde orquestación hasta recuperación | Réplicas, segundo nodo, procedimiento manual — **no automatizado** en el compose actual |
| **Actuadores / PLC** en la finca | Pueden seguir en lógica local si están cableados para ello | **Fuera de este repo** salvo integraciones que documentes |

**Conclusión para auditoría:** el stack actual **no** incluye un **failover automático** tipo hot-standby entre dos contenedores n8n con conmutación en 30 s. Eso es **objetivo de arquitectura** si se presupuesta e implementa.

---

## 2. Estado verificable en el repositorio

- **Multi-instancia n8n:** `docker-compose.multi-n8n.yml` (varios procesos; no hay por sí mismo elección automática de sustituto si uno cae).
- **Auditoría Trillizo:** `n8n/workflows/01-trillizo-auditoria-basica.json`, volumen `./cerebros/auditoria`.
- **Integridad opcional del POST de auditoría:** HMAC del body canónico (`scripts/n8n/sign_audit_webhook_body.py`, variable `CASTUO_AUDIT_WEBHOOK_SECRET`).
- **Backups:** Postgres + Markdown — `scripts/backup_castuo_cerebros.sh`, `deploy/RUNBOOK-BACKUP-CEREBROS-POSTGRES.md`.
- **Carga / firma:** `scripts/tests/stress_test_313_cores.py`, `scripts/tests/castuo_trillizo_audit_http_stress.py`.
- **Chaos / RTO (laboratorio, sondas HTTP):** `scripts/chaos/castuo_chaos_lab.py`, guía `docs/ops/CHAOS-ENGINEERING-LAB.md` (no implica failover automático del compose por sí solo).
- **SQL de actas (opcional, no cableado al webhook):** `n8n/sql/schema_auditoria_trillizo.sql`.

---

## 3. Diseño objetivo: redundancia N+1 y “shadow core”

### 3.1 Idea de arquitectura (no implementada tal cual en compose)

- Agrupar sectores en **grupos**; por cada *N* núcleos activos, prever **1 nodo en reserva** (cold o hot standby) con **misma imagen** y procedimiento para asumir `SECTOR_ID` / `CORE_ID` del caído.
- **Hot-standby** implica: sincronización de **estado** (volúmenes n8n, credenciales, último offset de telemetría) — hoy los volúmenes `.n8n` son **por contenedor**; duplicar sin diseño provoca bifurcación de estado.

### 3.2 Detección de caída (propuesta)

- **Healthcheck** HTTP del contenedor n8n (Docker `HEALTHCHECK` o probe externo).
- **Proxy delante** (Traefik, nginx, etc.) con **passive health checks** y **failover** a otro upstream cuando el activo deja de responder.
- Umbrales (p. ej. *n* fallos consecutivos) deben definirse y **probarse**; no fijados en código en este repo.

**Nota:** El “Trillizo” en este proyecto es **una instancia n8n** que persiste Markdown; **no** existe en el repo un servicio llamado “Trillizo” que haga *heartbeat* a 313 instancias cada 5 s. Eso sería un **componente nuevo** (monitor + alertas).

### 3.3 Conmutación (switchover) — protocolo operativo (borrador)

1. **Aislar** el nodo fallido en el proxy (dejar de enviar tráfico).
2. **Promover** standby: arrancar contenedor (o activar réplica) con variables de entorno del núcleo sustituido.
3. **Reconciliar estado:** última telemetría en Postgres, último comando OT documentado — según **tu** fuente de verdad (SQL, SCADA, journal). El journal Markdown **no** sustituye por sí solo un historial completo de válvulas sin diseño de campos/eventos.
4. **Verificar** que emisores de webhooks usan el **mismo** secreto HMAC si aplica y que el endpoint activo es el nuevo.

---

## 4. Rol del HMAC en recuperación (alcance real)

- El HMAC del payload hacia `audit-trigger` prueba **integridad** del cuerpo respecto a quien comparte el secreto; **no** sustituye autenticación fuerte de cada sensor ni elimina todos los vectores de “inyección” en otros puntos del sistema.
- Una **rotación de claves** exige procedimiento (Vault, SOPS, etc.) y ventana de doble clave; **no** está automatizada en el flujo actual del firmador Python.
- Durante failover, el riesgo de **órdenes no deseadas** se reduce con **proxy + TLS + lista blanca de emisores + HMAC en mensajes críticos**, no solo con auditoría posterior.

---

## 5. RPO / RTO (objetivos vs medición)

| Métrica | Significado | En este documento |
|---------|-------------|------------------|
| **RPO** | Pérdida máxima de datos aceptable | Depende de frecuencia de backup y de si hay replicación Postgres **sincrónica** (no incluida por defecto). “RPO 0” **no** está garantizado por el compose actual. |
| **RTO** | Tiempo máximo de indisponibilidad | Un valor tipo “&lt; 30 s” exige **medición** tras implementar proxy + standby + pruebas; aquí solo es **objetivo de diseño** si se aprueba presupuesto. |

Los backups documentados mejoran **recuperación ante desastre**; no son por sí mismos **HA en caliente**.

---

## 6. Métricas que sí puede exigir un auditor

- Resultados de **pruebas de restauración** (pg_restore + journal) con fecha y responsable.
- Resultados de **stress HTTP** (`castuo_trillizo_audit_http_stress.py`) en entorno que refleje producción.
- **Diagrama** de dependencias: qué cae si falla DNS, disco, red entre finca y CPD.
- **SLA** solo como **contrato medido**, no como línea en markdown.

---

## 7. Roadmap para “cerrar el círculo” (ingeniería)

1. **Definir** qué servicio es crítico por capa (auditoría vs control vs datos SQL).
2. **Añadir** proxy con healthchecks y, si aplica, segundo upstream n8n por rol.
3. **Postgres:** replicación o al menos backup automatizado + prueba trimestral de restore.
4. **Estado n8n:** decidir si el standby comparte volumen (riesgos de corrupción concurrente) o **export/import** de workflows + credenciales gestionadas externamente.
5. **Monitorización** externa (Prometheus, Uptime Kuma, etc.) con alertas — fuera del alcance mínimo actual del compose multi-n8n.
6. **Actuadores:** enlazar explícitamente con `backend/security/ot_actuator_guard.py` o PLC según despliegue.

---

## 8. Relación con narrativa comercial

Cualquier valoración económica o claims tipo “autoinmunidad total” deben **apoyarse** en los ítems medibles anteriores. Este archivo **no** incluye cifras de mercado ni SLA numéricos como garantías.

---

*Rutas relativas a la raíz del repositorio Castuo-System.*
