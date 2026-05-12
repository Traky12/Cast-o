# Stack FOSS + soberanía UE (activación de prontuarios)

*Conecta servicios **código abierto** habitualmente desplegados en **territorio UE** con lo descrito en [MARCO-LEGAL-SOBERANIA-UE-2026.md](../legal/MARCO-LEGAL-SOBERANIA-UE-2026.md) y el prontuario de [análisis crítico](./PRONTUARIO-ANALISIS-CRITICO-CONEXIONES-SISTEMA-2026.md). La “europeidad” la aporta el **hosting y el DPA**, no la licencia sola.*

**Orquestación n8n:** [PRONTUARIO-AUTOMATIZACION-N8N-2026.md](./PRONTUARIO-AUTOMATIZACION-N8N-2026.md) · [Conexiones completas](./PRONTUARIO-CONEXIONES-COMPLETAS-AUTOMATIZACION-2026.md)

---

## 1. Mapa de ficheros Compose (repo)

| Capa | Fichero | Componentes FOSS (imagenes referencia) |
|------|---------|----------------------------------------|
| Datos + variables soberanía | `docker-compose.eu-sovereignty.yml` | PostgreSQL 16 Alpine |
| Monitorización | `docker-compose.monitor.yml` | Prometheus, Grafana, Alertmanager |
| Cadena (opcional) | `docker-compose.gaiachain.yml` | Nodo GaiaChain (ajustar imagen/version) |
| IdP + proxy + secretos (opcional) | `docker-compose.eu-oss.yml` | Traefik, Keycloak, Vault *(Vault: revisar licencia BSL; ver §3)* |

---

## 2. Arranque mínimo recomendado (UE)

Desde la raíz del repositorio:

```bash
# 1) Variables (copiar y editar)
cp .env.eu-sovereignty.example .env

# 2) Base de datos residencia UE (servidor/VPS en UE)
docker compose -f docker-compose.eu-sovereignty.yml --env-file .env up -d

# 3) Monitoreo (Prometheus/Grafana/Alertmanager — FOSS)
docker compose -f docker-compose.monitor.yml --env-file .env up -d

# 4) Nodo cadena si aplica (RPC en UE)
docker compose -f docker-compose.gaiachain.yml --env-file .env up -d
```

En Windows (PowerShell), mismo orden con rutas del repo; Docker Desktop debe usar **WSL2** o motor Linux coherente con despliegue UE.

---

## 3. Licencias y matices “100 % abierto”

- **PostgreSQL, Prometheus, Grafana, Alertmanager, Keycloak:** ampliamente usados en sector público y empresas UE; licencias **OSI** (BSD, Apache 2.0, AGPL Grafana).
- **Traefik:** MIT; empresa francesa (despliegue UE recomendado).
- **Hashicorp Vault:** versiones recientes bajo **BSL**; si se exige **OSI estricto**, valorar **OpenBAO** u otro almacén de secretos acordado con el DPO.

**Copernicus / Sentinel:** datos públicos programa **ESA/UE**; credenciales en `COPERNICUS_*` (ver `eu_data_sovereignty.py`).

---

## 4. Variables que “encienden” el prontuario técnico

| Variable | Efecto |
|----------|--------|
| `CASTUO_EU_DATA_SOVEREIGNTY=1` | Modo estricto satelital (sin Landsat en catálogo; hosts Copernicus). |
| `COPERNICUS_USER` / `COPERNICUS_PASSWORD` | Descarga OData DHuS / CDSE según `COPERNICUS_DHUS_BASE`. |
| `DB_HOST` | Apunta al servicio `postgres` (`postgres` en red compose) o a RDS/instancia UE. |
| `GAIA_CHAIN_RPC_URL` | RPC del nodo en jurisdicción UE. |

---

## 5. Validación

```bash
PYTHONPATH=. pytest tests/energy_audit/test_eu_data_sovereignty.py -v
PYTHONPATH=. pytest tests/models/test_system_admin_playbook.py -q
```

---

*Sin VPS en UE y sin contrato/DPA, el compose solo orquesta imagenes: el RGPD se cumple en el contrato y en el mapa de tratamientos.*
