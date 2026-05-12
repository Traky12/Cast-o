# Checklist — seguridad avanzada (CASTÚO-System)

**Relación:** [PRONTUARIO-MAESTRO-REFUERZO-SEGURIDAD-AVANZADA-2026.md](./PRONTUARIO-MAESTRO-REFUERZO-SEGURIDAD-AVANZADA-2026.md) · [PRONTUARIO-MAESTRO-REFUERZO-INTEGRAL-2026.md](./PRONTUARIO-MAESTRO-REFUERZO-INTEGRAL-2026.md) · [CHECKLIST-REFUERZO-SEGURIDAD.md](./CHECKLIST-REFUERZO-SEGURIDAD.md)

Marca cada ítem cuando exista **evidencia** (captura, ticket, hash de commit).

## Red y descubrimiento

- [ ] LLMNR/mDNS desactivados en hosts Linux relevantes (`resolved.conf` + `resolvectl`)
- [ ] NBT-NS / LLMNR Windows según GPO o registro por interfaz
- [ ] Evidencia `tcpdump` UDP 5355 (y 137 si aplica) en ventana de prueba acordada
- [ ] Reglas de firewall (nftables/cloud) revisadas **sin** bloquear gestión legítima

## Aplicación

- [ ] Inventario de rutas que aceptan datos de sensores; cobertura Pydantic acordada
- [ ] Secretos prod: opción A/B ([PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md))
- [ ] MFA/IdP en superficies definidas por política *(si aplica)*

## Observabilidad e incidentes

- [ ] Métricas Prometheus mínimas operativas donde el servicio las exponga
- [ ] Runbook de incidentes revisado ([RUNBOOK-RESPUESTA-INCIDENTES.md](./RUNBOOK-RESPUESTA-INCIDENTES.md))
- [ ] Retención y minimización de logs alineadas a DPIA

## Cumplimiento

- [ ] DPIA actualizada si cambian tratamientos o nuevas medidas invasivas ([DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md))
