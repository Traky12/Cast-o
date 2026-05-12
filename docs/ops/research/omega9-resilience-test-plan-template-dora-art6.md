# Plan de pruebas de resiliencia (DORA Art. 6)

*(Omega-9. Fecha guia: 15/05/2026.)*

## 1) Objetivo

Validar que el laboratorio Omega-9 puede **recuperar operaciones criticas en &lt; 2 h** tras incidentes (DORA Art. 6), midiendo en entorno **aislado** (no asumir cumplimiento hasta informe).

## 2) Escenarios de prueba

| ID | Nombre | Descripcion | Herramientas | Metrica de exito |
|---|---|---|---|---|
| RT-001 | Ataque DDoS | Simular denegacion de servicio a nodos GaiaChain **de laboratorio** o mock. | Locust + Chaos Mesh | Recuperacion en &lt; 30 min |
| RT-002 | Fuga de datos | Script que intenta exfiltrar datos **desde sandbox** (controlado). | Wazuh + harness interno | Deteccion en &lt; 5 min |
| RT-003 | Fallo de HSM | Desconexion simulada de modulo de hardware (Thales Luna u otro). | Ansible | Recuperacion en &lt; 1 h |
| RT-004 | Corrupcion de datos | Alteracion maliciosa **simulada** de registro en GaiaChain (entorno de prueba). | Script Python | Deteccion en &lt; 1 min |

**Nota sobre herramientas**

> - **Metasploit no es un requisito**: usar *harness interno* para simulaciones acotadas.  
> - **Locust** solo contra **endpoints autorizados** (ej. `https://staging.gaiachain.castuo-system.eu` si existe; si no, mock interno).  
> - **Chaos Mesh** limitado al namespace `chaos-testing` (o equivalente aprobado).

## 3) Checklist

| Accion | Responsable | Estado |
|---|---|---|
| Configurar entorno de prueba | Equipo de Infraestructura | ✅ |
| Ejecutar escenario RT-001 | Equipo de Seguridad | Pendiente |
| Monitorear metricas en Grafana | Equipo de Operaciones | Pendiente |
| Validar recuperacion | Equipo de Seguridad | Pendiente |
| Documentar resultados en GaiaChain | Equipo de Blockchain | Pendiente |

## 4) Procedimiento y witness (referencia rapida)

```bash
kubectl create namespace chaos-testing
bash scripts/ops/research/recover-from-ddos.sh
bash scripts/ops/research/Register-LabEvidence.sh --file resilience_test_results.json
```

Enlaces: [`omega9-certification-evidence-table-template.md`](omega9-certification-evidence-table-template.md), [`omega9-notarization-procedure-2026.md`](omega9-notarization-procedure-2026.md), [`../../../scripts/ops/research/recover-from-ddos.sh`](../../../scripts/ops/research/recover-from-ddos.sh).
