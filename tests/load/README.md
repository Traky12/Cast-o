# Pruebas de carga (Locust) — Aleaciones vegetales

## Requisitos

- API Castuo en marcha (`uvicorn` u orquestador).
- `pip install locust`
- Dependencias del backend: `sqlalchemy` (ver `backend/vegetal_alloys/requirements-extra.txt`).

## Ejecucion local

Desde la raiz del repo:

```bash
locust -f tests/load/locustfile.py --host=http://127.0.0.1:8000
```

Abrir la UI en `http://127.0.0.1:8089`, fijar usuarios y tasa de arranque segun capacidad del entorno.

## Headless (CI o servidor)

```bash
locust -f tests/load/locustfile.py --host=http://STAGING_HOST --headless -u 500 -r 50 -t 5m
```

Ajustar `-u` (usuarios) y `-r` (spawn/s) sin asumir millones de usuarios: el techo lo marcan nodos, red, PostgreSQL/SQLite y workers de la API.

## Kubernetes (staging)

1. Crear ConfigMap desde el fichero real (evita duplicar codigo en YAML):

   ```bash
   kubectl create configmap locust-vegetal-scripts --from-file=locustfile.py=tests/load/locustfile.py -n staging --dry-run=client -o yaml | kubectl apply -f -
   ```

2. Aplicar manifiesto: `kubectl apply -f k8s/locust-staging.yaml`

3. Port-forward al master si no hay LoadBalancer: `kubectl port-forward svc/locust-master 8089:8089`

## ChemAxon

Sin `CHEMAXON_BASE_URL` y `CHEMAXON_API_KEY`, el backend usa **mock determinista**; la ruta `/chemaxon` sigue siendo util para medir latencia de la API, no del vendor.
