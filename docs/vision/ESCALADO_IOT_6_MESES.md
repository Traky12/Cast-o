# Escalado IoT: 10.5 ha → 100 ha (30 coops) — Plan 6 meses

De 3 cooperativas actuales a 30 cooperativas. Objetivo **€18K MRR** automatizado.

---

## Fases de escalado (6 meses)

| Fase | Mes | Coops | MRR |
|------|-----|-------|-----|
| Validación | 1 | 3 → 7 | €4K |
| Consolidación | 3 | 7 → 15 | €9K |
| Escala | 6 | 15 → 30 | €18K |

---

## Arquitectura horizontal (ya escalable v1.7.4)

```
┌─ Cooperativa N ─┐
│ iot_monitor.py  │ ── MQTT ──► hidroponia/coop_N/sensors
│ --coop N        │
└─────────────────┘    ↓
                       Backend FastAPI (∞ coops)
                       SQLite / PostgreSQL
```

- **Onboarding:** POST /cooperativas → id N.
- **IoT:** `iot_monitor_3_coops.py --coop N` (systemd castuo-iot-coopN.service).
- **Facturación:** POST /billing/invoice/N (hectáreas desde cooperativas registradas).

---

## Paso 1: Onboarding automático (día 1) — Coop #4 ejemplo

```bash
cd /root/castuo-system

# 1. Registrar cooperativa
curl -X POST http://localhost:8001/cooperativas \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Coop #4 Olivar", "hectareas": 4.0, "cultivo": "olivo"}'

# 2. Servicio systemd (copiar plantilla coop1 → coop4)
cp scripts/systemd/castuo-iot-coop1.service /etc/systemd/system/castuo-iot-coop4.service
sed -i 's/--coop 1/--coop 4/g' /etc/systemd/system/castuo-iot-coop4.service
sed -i 's/coop1/coop4/g' /etc/systemd/system/castuo-iot-coop4.service
systemctl daemon-reload && systemctl enable --now castuo-iot-coop4.service

# 3. Factura automática (4 ha × €140 = €560/mes)
curl -X POST "http://localhost:8001/billing/invoice/4"

# 4. Verificar
curl -s http://localhost:8001/cooperativas | jq length   # → 4
curl -s http://localhost:8001/billing/facturacion | jq 'length'
```

**Tiempo:** ~2 min por cooperativa nueva.

---

## Paso 2: Infra escalable (semana 1)

**Hetzner Cloud ~€20/mes → soporte ~100 coops**

1. **PostgreSQL** (sustituir SQLite en producción):
   ```bash
   docker run -d -p 5432:5432 --name postgres \
     -e POSTGRES_DB=castuo \
     -e POSTGRES_USER=castuo \
     -e POSTGRES_PASSWORD=... \
     postgres:15
   ```

2. **Workers horizontales:** escalar workers IoT (ej. 4 workers × varias coops cada uno).

3. **Load balancer:** Traefik u otro; dashboard ej. localhost:8080.

---

## Paso 3: Adquisición cooperativas

**Canales prioritarios (Extremadura):**

| Canal | Potencial |
|-------|-----------|
| CTAEX Badajoz | ~50 coops en base de datos |
| FUNDÉCYT-PCTEX | ~30 coops agrovoltaico |
| COAG Extremadura | ~200 coops afiliadas |
| PAC Ecorregímenes | Lista oficial 500 ha |
| Ferias agrarias | FERCAM, Agroexpo |

---

## Paso 4: Precio escalado

| Hectáreas | Precio/ha/mes | MRR por coop | Onboarding |
|-----------|----------------|--------------|------------|
| 1–5 ha   | €140/ha       | €140–700     | **2 min** (auto) |
| 6–20 ha  | €120/ha       | €720–2,4K    | **1 día**  |
| 21+ ha   | €100/ha       | €2,1K+       | **1 semana** |

*(Implementar lógica de tramos en billing según ha si se desea.)*

---

## Paso 5: Monitoring escalado

**100 coops → dashboard central**

1. **Grafana:** `docker run` Grafana + datasource MQTT. Panel: N coops × 5 sensores.
2. **Alertas:**  
   - Crítico: coop DOWN → Telegram  
   - Aviso: growth &lt; 9% → Email  
   - Info: nueva coop onboarded → Slack  

*(Integrar con `scripts/alertas_iot_3_coops.sh` y canales deseados.)*

---

## Roadmap 6 meses — €18K MRR

| Hito | Acción | MRR |
|------|--------|-----|
| Semana 1 | Infra Postgres + 2 coops nuevas | €2,5K |
| Mes 1 | 7 coops total + pitch CTAEX | €4K |
| Mes 3 | 15 coops + PERTE €50K | €9K |
| Mes 6 | 30 coops + VC Series A €2M | €18K |

---

## Comando escalado Coop #4 (prueba inmediata)

```bash
# Añadir Coop #4 Olivar (4 ha) — 2 min
curl -X POST "http://localhost:8001/cooperativas" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Coop #4 Olivar", "hectareas": 4.0, "cultivo": "olivo"}'

curl -X POST "http://localhost:8001/billing/invoice/4"

# Systemd (en servidor con permisos)
sudo cp scripts/systemd/castuo-iot-coop1.service /etc/systemd/system/castuo-iot-coop4.service
sudo sed -i 's/--coop 1/--coop 4/g; s/coop1/coop4/g' /etc/systemd/system/castuo-iot-coop4.service
sudo systemctl daemon-reload && sudo systemctl enable --now castuo-iot-coop4.service

# Verificar
./scripts/dashboard_3_coops.sh   # ampliar a 4/4 si dashboard muestra total
curl -s localhost:8001/cooperativas | jq length
curl -s localhost:8001/billing/facturacion | jq 'length'
```

---

## ROI escalado — 6 meses

| Métrica | Actual | Mes 6 |
|---------|--------|--------|
| Cooperativas | 3 | 30 |
| Hectáreas | 10,5 | 100 |
| MRR | €1,5K | €18K |
| Valor plataforma | €25M | **€50M** |

**Subvención:** PERTE + PAC año 1 (objetivo ~€750K).  
**€25M → €50M (+100%)** en valor.

---

## Posicionamiento escalado

**#1 Agrovoltaico SaaS escalable (España)**

- Onboarding 2 min/coop  
- Infra horizontal ∞ coops  
- Monitoring Grafana 100 coops  
- MRR €140/ha/mes recurrente  
- PERTE/PAC subvencionable  

---

**Posicionamiento España 2026:** [TOP3_PLATAFORMAS_ESPANA_2026](TOP3_PLATAFORMAS_ESPANA_2026.md) (#1 Agrovoltaico SaaS, Coop #5 ejemplo).

*[TOP3_PLATAFORMAS_ESPANA_2026](TOP3_PLATAFORMAS_ESPANA_2026.md) · [COOPERATIVAS_3_INTEGRADAS](COOPERATIVAS_3_INTEGRADAS.md) · [FACTURACION_LIVE](FACTURACION_LIVE.md) · [LEGAL_READY_V1.7.3](LEGAL_READY_V1.7.3.md)*
