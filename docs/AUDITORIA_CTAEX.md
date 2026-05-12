# Plan de Auditoria - CASTUO-SYSTEM (THC)

## 1) Matriz RACI

| Tarea | Responsable | Aprobador | Consultado | Informado | Evidencia |
|---|---|---|---|---|---|
| Contratar VPS UE | Admin Sistemas | Director TI | DevOps | Legal | Contrato proveedor + IP servidor |
| Configurar dominio/TLS | Admin Sistemas | Director TI | - | Legal | `curl -I https://castuo.ctaex.es` |
| Desplegar stack Docker | DevOps | Admin Sistemas | - | Director TI | `docker-compose ps` |
| Configurar WireGuard | Admin Sistemas | Director TI | DevOps | - | `wg show` |
| Configurar SSH + MFA | Admin Sistemas | Director TI | - | - | Evidencia de login MFA |
| Validar `spectra_estimations` | DevOps | Admin Sistemas | QA | - | `psql ... SELECT ...` |
| Probar endpoints THC | QA | DevOps | - | Director TI | `curl /thc/estimate` y `curl /thc/validate_lims` |
| Configurar GaiaChain real | DevOps | Admin Sistemas | Equipo Blockchain | - | endpoint nodo responde |
| Validar LIMS con muestras | QA | DevOps | LIMS | Director TI | informe de validacion |
| Programar backups | Admin Sistemas | Director TI | - | - | `crontab -l` + evidencia rclone |
| Activar Prometheus/Grafana | DevOps | Admin Sistemas | - | - | `curl /metrics` y reglas cargadas |
| Capacitar equipo tecnico | Soporte | Director TI | DevOps | Tecnicos | acta firmada |

## 2) Hitos y evidencias obligatorias

| Hito | Evidencia requerida | Plazo objetivo |
|---|---|---|
| Infraestructura desplegada | `docker-compose ps` + `curl -I https://castuo.ctaex.es` | Dia 2 |
| Trazabilidad operativa | evidencia en `spectra_estimations` + `gaiachain_tx` | Dia 3 |
| Acceso remoto seguro | `wg show` + verificacion SSH con MFA | Dia 4 |
| Backups activos | `crontab -l` + listado en Scaleway | Dia 4 |
| Monitorizacion operativa | `curl http://localhost:9090/metrics` + reglas | Dia 5 |
| Validacion LIMS real | informe con muestras reales | Dia 6 |
| Capacitacion cerrada | acta de capacitacion firmada | Dia 7 |

## 3) Criterios de exito

1. Registro de estimaciones y validaciones en PostgreSQL + GaiaChain.
2. Sin alertas criticas sostenidas durante ventana de estabilizacion.
3. Backup restaurable verificado en prueba controlada.
4. Equipo tecnico formado y con procedimientos documentados.
