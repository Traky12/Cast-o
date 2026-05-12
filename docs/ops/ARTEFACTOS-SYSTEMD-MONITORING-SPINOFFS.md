# Artefactos reales: systemd, monitoring y spin-offs

Separar **lo que el repositorio contiene** de **lo que un briefing operativo afirma** (certificados, ingresos, horarios CET).

## 1. Spin-offs (`spin-offs/`)

Carpetas **roadmap** con README; **no** implican sociedades inscritas en RM. Ver `spin-offs/README.md`.

## 2. Systemd

- Plantillas IoT coops y watchdogs: `scripts/systemd/*.service`
- **Agentes autónomos (solo plantilla en git):** `scripts/systemd/castuo-autonomous-agents.service.example` + `castuo-system.target.example` + `agents.env.example`. La unidad activa `castuo-autonomous-agents.service` se crea en el servidor al copiar la plantilla. Ver `scripts/systemd/README.md` (nota `Type=oneshot` / `--background`).
- **Procedimiento deploy Hetzner:** [PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md](./PRONTUARIO-MAESTRO-DEPLOY-REAL-HETZNER.md) · script `scripts/deploy/bootstrap-hetzner.sh`.

## 3. Grafana / Prometheus

| Artefacto | Ruta |
|-----------|------|
| Dashboard integral (nombre del briefing) | `castu-monitoring/grafana/dashboards/castuo_production_integral.json` |
| Reglas Git / narrativa BioCoin Castúo | `castu-monitoring/prometheus/rules/git.rules.yml` |

“LIVE” y “SYNCED” dependen del **stack desplegado** (`docker compose` / k8s en `castu-monitoring/`), no del solo hecho de existir el JSON en git.

## 4. Lo que el repo **no** incluye como prueba

- `SABIONDA-AUTH-V1.cert`
- Hash de commit como certificación legal
- Revenue €1,2M / 90 días o cobertura LCSP “100%” verificada por software

## 5. Agenda CET (ejemplo interno)

Si se usa un calendario 08:00 / 12:00 / …, guardarlo en **herramienta de proyecto** o calendario compartido; este documento no ejecuta postulaciones ni minting.

---

## 6. Inventario verificable (repo)

| Elemento | Estado en git |
|----------|----------------|
| `castuo-iot-coop{1,2,3}.service` | Presentes |
| `castuo-autonomous-agents.service` | **No** — solo `castuo-autonomous-agents.service.example` |
| `castuo-system.target` | **No** — solo `castuo-system.target.example` |
| `agents.env` en `/etc/` | **No** en repo — plantilla `scripts/systemd/agents.env.example` |
| Grafana `castuo_production_integral.json` | `castu-monitoring/grafana/dashboards/` |
| Prometheus `git.rules.yml` (BioCoin Castúo) | `castu-monitoring/prometheus/rules/` |
| `spin-offs/*` | READMEs roadmap; no constitución mercantil |

**Referencias cruzadas:** [MANIFESTO-CASTUO-SYSTEM-1-0.md](../MANIFESTO-CASTUO-SYSTEM-1-0.md) · [PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md](../legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md) (§5b) · [DPIA-CASTUO-SYSTEM.md](../legal/DPIA-CASTUO-SYSTEM.md)

---

**Legal:** [PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md](../legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md)
