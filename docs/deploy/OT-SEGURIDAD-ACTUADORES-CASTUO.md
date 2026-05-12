# Seguridad OT — protección de actuadores (CASTÚO-SYSTEM)

Barrera **lógica** entre la API (`/api/actuators/control`) y la intención de campo (PLC, MQTT, Modbus). Complementa — no sustituye — segmentación IT/OT, parada de hardware y lógica en el PLC maestro.

**Implementación:** `backend/config/actuators_config.py` · `backend/security/ot_actuator_guard.py` · `backend/services/edge_service.py` · `backend/routers/hydro_remote.py` · métricas `ot_remote_writes_disabled`, `ot_kill_switch_active`, `castuo_ot_actuator_denials_total`, `ot_critical_actuator_commands_total`.

## Controles activos

| Control | Variable / comportamiento |
|---------|---------------------------|
| Kill-switch energización | `OT_ACTUATOR_KILLSWITCH=true` → bloquea **state=true**; permite **apagado** y **emergency_stop** |
| Desactivar escrituras remotas | `OT_REMOTE_ACTUATOR_WRITES=false` → sin energizar desde API; PLC/borde sigue siendo autoridad |
| Bloqueo total API | `OT_ACTUATOR_BLOCK_ALL_API=true` → rechaza cualquier comando de actuador por estas rutas |
| Actuadores críticos | `OT_CRITICAL_ACTUATOR_IDS` (defecto: `valvula_agua`, `valvula_nutrientes`) → energizar solo con roles Keycloak **admin** o **owner** |
| Anti ráfaga | `OT_ACTUATOR_RATE_MAX` / `OT_ACTUATOR_RATE_WINDOW_S` |
| Parada remota API | `OT_EMERGENCY_API_ENABLED=false` deshabilita `POST .../emergency_stop` (usar E-stop físico) |
| Auditoría | Logs `ot_actuator_audit` + denegaciones contabilizadas |

## Matriz piloto (rellenar con datos reales)

| Sensor / actuador | Protocolo | Topic / registro | Ruta API / PLC | Responsable | Zona |
|-------------------|-----------|------------------|----------------|-------------|------|
| Sensor pH | MQTT | `hydro/ph` | lectura SaaS `/hydroponics-saas/sensor-readings` | Técnico | |
| Bomba dosificadora | Modbus TCP | Holding `0x...` | **PLC** (no público); API solo orquestación si policy OT lo permite | Operador | |
| Inversor | SunSpec / Modbus | — | Gateway OT aislado | Ingeniero eléctrico | |
| Válvula riego | MQTT / BACnet | — | PLC + política crítica | Riego | |
| Irradiancia | MQTT | `agrovolt/irrad` | Ingesta + gemelo | PV | |

## Avance hacia TRL 9 (control agrovoltaico + hidroponía)

1. **Documentar** esta matriz por explotación y enlazar cada actuador a un **punto único de verdad** (PLC o edge certificado).
2. **Producción:** `OT_REMOTE_ACTUATOR_WRITES` solo `true` cuando el **gateway OT** valide firma, ventana temporal y estado del proceso.
3. **Red:** VLAN OT, bastión, sin exposición directa de PLC a Internet; API en DMZ con TLS mutuo hacia edge.
4. **Observabilidad:** desplegar Prometheus/Grafana y alertar sobre `castuo_ot_actuator_denials_total` y rechazos 403.
5. **Pruebas de campo:** validar E-stop físico por encima de cualquier lógica en nube.

## Datos agrovoltaicos (campo → Postgres)

- Tabla `agrovoltaic_observations` (`init-db/003_agrovoltaic_observations.sql`).
- API: `POST /agrovoltaic/observations`, `GET /agrovoltaic/zones/{zone_id}/shadow-factor` (header `X-API-KEY` alineada con hidroponía SaaS).

## Verificación producción

- `./deploy/verify_production.sh` (métricas OT, POST agrovoltaico opcional, Prom/Grafana opcionales).

## Referencias

- Integración general: [INTEGRACION-COMPLETA-N8N-HETZNER-ARSYS-GITHUB-MISTRAL-CASTUO.md](./INTEGRACION-COMPLETA-N8N-HETZNER-ARSYS-GITHUB-MISTRAL-CASTUO.md)
- Arquitectura acceso remoto: [ARQUITECTURA-ACCESO-REMOTO-CTAEX.md](./ARQUITECTURA-ACCESO-REMOTO-CTAEX.md)
