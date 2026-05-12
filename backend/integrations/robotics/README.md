# Robótica y señales (laboratorio Castúo)

**Ámbito:** módulos Python importables desde el monolito; **no** sustituyen ROS2, GNU Radio Companion ni firmware de campo.

## Módulos

| Archivo | Rol |
|--------|-----|
| `signal_manager.py` | Muestras sintéticas + cifrado simétrico AES-256-GCM (`ROBOT_SIGNAL_SYMMETRIC_KEY`). |
| `security_layer.py` | Sellado/firma vía `backend.security.pq_crypto` (Kyber+DEM si `pqcrypto` está instalado). |
| `evolution_engine.py` | GA ligero integrado; `evolve_with_deap()` opcional. |
| `robot_traceability.py` | `build_robot_evolution_audit_payload()` → `register_event_in_chain`. |

## Variables de entorno

- `ROBOT_SIGNAL_SYMMETRIC_KEY`: hex 64 o base64 (32 bytes) para muestras PCM selladas.
- `CASTUO_ROBOTICS_LAB=1`: permite arranque **sin** clave simétrica (clave efímera; solo laboratorio).
- `CASTUO_SNN_CACHE_REDIS_URL`: si está definida (`redis://…`), caché de `hydro_infer_dict` con inferencia **determinista por semilla** (coherente con hit/miss). Requiere `pip install redis`.
- **TTL caché SNN:** `CASTUO_SNN_CACHE_TTL_SECONDS` (entero ≥30) **tiene prioridad**. Si no, `CASTUO_SNN_CACHE_SEASON` ∈ `verano` (600s), `invierno` (300s), `primavera`/`otoño` (450s); si no hay estación, default **300s**. Función: `snn_cache_ttl_seconds()` en `neuromorphic_edge.py`. Ajustar con hit-rate y criterio agronómico, no solo calendario.

### Política de TTL para caché SNN

| Estación | TTL (s) | Variable de entorno | Ejemplo de uso |
|----------|---------|---------------------|----------------|
| Verano | 600 | `CASTUO_SNN_CACHE_SEASON=verano` | `export CASTUO_SNN_CACHE_SEASON=verano` |
| Invierno | 300 | `CASTUO_SNN_CACHE_SEASON=invierno` | `export CASTUO_SNN_CACHE_SEASON=invierno` |
| Primavera / otoño | 450 | `CASTUO_SNN_CACHE_SEASON=primavera` u `otoño` | `$env:CASTUO_SNN_CACHE_SEASON = "primavera"` (PowerShell) |
| Default (sin estación) | 300 | *(no fijar `SEASON`)* | Opcional: `export CASTUO_SNN_CACHE_TTL_SECONDS=300` para fijar 300 s explícitamente |

**Notas:** `CASTUO_SNN_CACHE_TTL_SECONDS` (entero ≥30) **sobrescribe** el TTL por estación. Los tests usan `monkeypatch` y no requieren exportar variables en el shell.

#### Ejemplos de uso

**1. TTL de verano (600 s)**

```bash
# Linux / macOS
export CASTUO_SNN_CACHE_SEASON="verano"
```

```powershell
# Windows PowerShell
$env:CASTUO_SNN_CACHE_SEASON = "verano"
```

**2. Override numérico (ej. 900 s)**

```bash
export CASTUO_SNN_CACHE_TTL_SECONDS=900
```

```powershell
$env:CASTUO_SNN_CACHE_TTL_SECONDS = "900"
```

**3. Staging:** definir variables en el mismo shell o servicio systemd / compose **antes** de arrancar el worker que carga `neuromorphic_edge`.

- `CASTUO_PROMETHEUS_METRICS=1`: expone `GET /metrics` en el lab stub e histogramas de latencia/`riego_ml` en inferencia. Requiere `prometheus_client`.

**Nombres Prometheus reales** (para `grep` / Grafana): `castuo_neuro_hydro_infer_seconds`, `castuo_neuro_riego_ml` (no existen métricas `castuo_snn_*` en el código actual). Ambos son **Histogram** en `lab_metrics_optional.py` (distribución de latencias y de `riego_ml`), no Gauge de “último valor”.

```bash
# Lab en 8011 con métricas activas
curl -sS http://127.0.0.1:8011/metrics | grep castuo_neuro
```

```powershell
(Invoke-WebRequest http://127.0.0.1:8011/metrics).Content | Select-String castuo_neuro
```

**Tests TRL6 (caché):** `test_snn_cache_hit_reproducible`, `test_snn_cache_ttl_expiry` en `tests/integrations/test_neuromorphic_redis_cache.py`.

### Neuromórfica, memristores (concepto) vs simulación en repo

Marco **orientativo** (SNN, materiales, diagrama Mermaid, límites TRL): [NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md](../../../docs/integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md).  
En el clon: **simulación** `HydroponicsSNN` + caché Redis opcional + métricas; **no** ensayo físico de TiO₂/Nb₂O₅.

| Métrica | Tipo | Ejemplo consulta |
|---------|------|------------------|
| `castuo_neuro_hydro_infer_seconds` | Histogram | `curl -sS http://127.0.0.1:8011/metrics \| grep castuo_neuro_hydro` |
| `castuo_neuro_riego_ml` | Histogram | `curl -sS http://127.0.0.1:8011/metrics \| grep castuo_neuro_riego` |

## Cadena / auditoría

Tras un checkpoint de evolución:

```python
from backend.api.services.gaiachain_service import register_event_in_chain
from backend.integrations.robotics import EvolutionEngine, build_robot_evolution_audit_payload

engine = EvolutionEngine()
state = engine.evolve(generations=5)
payload = build_robot_evolution_audit_payload(
    token_id=900001,
    robot_id="ROBOT-LAB-01",
    state_or_checkpoint=state,
)
tx = register_event_in_chain(payload)
```

## GNU Radio / SDR

Ver [GNU_RADIO.md](./GNU_RADIO.md): integración real depende de hardware y política espectral; no se embebe en CI.

## Dependencias opcionales

`requirements-optional.txt` (DEAP, NumPy para extensiones).

## Stub HTTP (laboratorio): `POST /api/robotics/lab/snapshot`

**Puerto recomendado:** `8011` si ya tienes PEI-002 en `8010`.

Desde la raíz del repo:

```powershell
$env:CASTUO_ROBOTICS_LAB_BEARER_TOKEN = "dev-secreto"
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn backend.integrations.robotics.lab_stub_app:app --host 127.0.0.1 --port 8011
```

Prueba cliente: `scripts/windows/Test-PEI001-RoboticsLab-Stub.ps1` (ajusta `CASTUO_ROBOTICS_LAB_URL` si usas otro host/puerto).

**Respuesta:** `status`, `tx_id: null`, `gaia_chain_digest` = SHA-256 del **cuerpo JSON canónico** recibido (no del informe PEI-001 crudo salvo que envíes el mismo JSON como cuerpo).

**Auth:** `CASTUO_ROBOTICS_LAB_BEARER_TOKEN`; o `CASTUO_ROBOTICS_LAB=1` sin token (solo dev, inseguro).

### `POST /api/robotics/lab/neuromorphic/hydroponics/infer`

Cuerpo JSON: `humedad`, `ph`, `ec`, `luz_umol` (opcionales con defaults). Respuesta: `riego_ml`, `power_uW`, `chain_seal` (firma Dilithium sobre payload canónico vía `pq_crypto`), `eco_alloy`, `inference`.

- `CASTUO_ECO_ALLOY`: etiqueta material (default `Cs2AgBiBr6`).
- `CASTUO_NEUROMORPHIC_LAB=1`: al hacer `log_snapshot`, si `metadata` incluye `humedad`/`ph`/`ec`, se añade `neuromorphic_inference` (requiere también `CASTUO_ROBOTICS_LAB=1` para clave simétrica si aplica).

### Docker (lab)

```bash
docker compose -f docker-compose.robotics-neuro.yml up --build
```

Imagen: `backend/integrations/robotics/Dockerfile.lab` (contexto = raíz del repo).

### Scan3D → Print (lab)

| Método | Ruta |
|--------|------|
| POST | `/api/robotics/lab/scan3d/scan` — JSON `{ filename, points, format }` (simulación) |
| POST | `/api/robotics/lab/scan3d/scan/upload` — cuerpo binario (p. ej. `application/octet-stream`); `Content-Disposition: filename=` opcional |
| POST | `/api/robotics/lab/scan3d/print` — job FDM simulado; `volume_cm3` opcional; `apply_neuro_hints` usa `HydroponicsSNN.optimize_print_params_from_volume` |

Respuestas incluyen **`chain_seal`** (Dilithium). GCode real y OctoPrint fuera del stub.

Script: `scripts/windows/Test-Scan3D-Print.ps1`. Compose dedicado: `docker-compose.scan3d.yml` (puerto **8012**).

### GaiaChain (opcional, mismo contrato que el monolito)

| Variable | Efecto |
|----------|--------|
| `CASTUO_ROBOTICS_LAB_CHAIN_REGISTER` | `1` → intenta `register_event_in_chain` tras snapshot / print job |
| `GAIA_CHAIN_RPC`, `GAIA_CHAIN_AUDIT_CONTRACT`, `GAIA_CHAIN_AUDIT_ABI`, `GAIA_CHAIN_PRIVATE_KEY` | Igual que `backend/api/config.py` (no usar `CASTUO_GAIA_CHAIN_RPC` duplicado) |
| `CASTUO_ROBOTICS_LAB_CHAIN_TOKEN_ID` | `tokenId` por defecto si el JSON no trae `token_id` / `chain_token_id` |
| `CASTUO_ROBOTICS_LAB_CHAIN_INCLUDE_PARCEL_ID` | `1` → incluye `parcel_ref` en `details` on-chain (DPIA) |

Orquestación local: `scripts/windows/Test-Complete-RoboticsLab.ps1`.

**Health / cadena (sin Bearer):** `GET /health` devuelve `chain_status`: `disabled` | `ready` | `misconfigured` y `neuromorphic_lab` (bool). Ejemplo: `curl -s http://127.0.0.1:8011/health`.

### TRL6 / TRL7 — pruebas y despliegue (trazabilidad)

| Artefacto | Uso |
|-----------|-----|
| `pytest.ini` | Marcadores `trl6`, `trl7` |
| `python -m pytest -m trl6 -q` | Gate lab + vault + playbook + cadena opt-in |
| `scripts/windows/Invoke-TRL6-Validation.ps1` | Pytest + `Test-Complete-RoboticsLab.ps1` (param `-LabUrl` para **8012**); `-Evidence` → JUnit + `manifest.json` |
| `scripts/windows/Export-TRL6-Evidence.ps1` | Solo gate `trl6` + `reports/trl6/junit.xml` + manifiesto verificable |
| `scripts/posix/export_trl6_evidence.sh` | Equivalente POSIX |
| `scripts/posix/trl6-validate.sh` | Solo pytest en Linux/macOS |
| `docs/legal/INFORME-EVIDENCIA-TRL6-PLANTILLA.md` | Informe humano para DPO / expediente (datos = manifiesto + JUnit) |
| `secrets/README.md` | Ficheros bearer locales sin Opción C en git |
| `docs/deploy/CHECKLIST-TRL6-HETZNER-STAGING.md` | Cronología DPO → Hetzner → health |
| `docs/deploy/ROADMAP-TRL6-TRL7-CODE.md` | Qué falta típico para TRL7 |
| `docs/deploy/CHECKLIST-INTEGRACIONES-MEJORAS-2026.md` | Matriz P1–P3 (SNN, TraceChain, métricas, legal) |

Plantilla env VPS: `docs/deploy/robotics-lab-hetzner.env.example`.
