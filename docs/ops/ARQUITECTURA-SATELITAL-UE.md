# ARQUITECTURA SATELITAL OPEN-SOURCE UE (CASTUO-SYSTEM)

## Objetivo
Definir un perfil satelital soberano UE para gestionar informacion agraria con
fuentes abiertas (Copernicus, EUMETSAT, SIGPAC/SIEX), analitica reproducible,
trazabilidad auditable y operacion validable.

## 1. Fuentes de datos
- Copernicus Data Space (Sentinel-1/2/3): observacion de cultivos.
- EUMETSAT: meteorologia y alertas tempranas.
- SIGPAC/SIEX: enriquecimiento territorial y trazabilidad administrativa.

## 2. Ingestion y formato
- Formato base: STAC + COG.
- Worker de ingesta: services/satellite/ingestion/stac_worker.py
- Output: catalogos JSON normalizados para pipeline posterior.

## 3. Analitica
- Worker NDVI: services/satellite/analytics/ndvi_worker.py
- API NDVI (stats por imagen): services/satellite/api/main.py
- Indices objetivo (fase siguiente): NDVI, NDMI, EVI.

## 4. Soberania y gobierno de datos
- Region: UE (Hetzner hel1/fsn1 o equivalente UE-only).
- Cifrado en transito (TLS) y en reposo.
- Retencion y minimizacion RGPD.
- Evidencia auditable via hash analitico en GaiaChain.

## 5. Despliegue de referencia

### Docker local
```bash
docker compose -f docker-compose.satellite.yml up -d --build
curl http://localhost:8010/health
```

### Kubernetes
```bash
kubectl apply -f k8s/satellite/configmap.yaml
kubectl apply -f k8s/satellite/deployment.yaml
kubectl apply -f k8s/satellite/service.yaml
kubectl apply -f k8s/satellite/hpa.yaml
```

## 6. Troubleshooting Windows (local)

### Error ModuleNotFoundError: jose
```powershell
pip install "python-jose[cryptography]" python-multipart
```

### Pytest lento/bloqueado por plugins externos
```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
pytest -p pytest_asyncio backend/routers/test_*.py -v
```

### Uvicorn reload con menos ruido
```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
```

### Recomendaciones de estabilidad
- Evitar `pip freeze > requirements.txt` global del venv.
- Mantener dependencias en ficheros dedicados del repo.
- Preferir Python 3.12 para compatibilidad de stack.
- Evitar ejecutar desde carpetas sincronizadas con OneDrive para cargas pesadas.

## 7. Excelencia operativa (GO total)

1. Completar secretos reales en `.env`.
2. Conectar kubectl con credencial real:
   - `bash scripts/configure-kubectl-hetzner.sh`
3. Ejecutar validacion integral:
```bash
bash scripts/go-total.sh --env-file .env
```

## 8. Politica reconcile dry-run por rama
- En `feat/*`: report-only para drift detectado en dry-run.
- En ramas no `feat/*`: comportamiento estricto (bloquea por drift/error).
- Implementado en target `reconcile-check` del Makefile.
