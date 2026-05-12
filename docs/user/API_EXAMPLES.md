# Ejemplos de API (gateway + backend)

**Versión:** 1.0

Sustituye `BASE` y `TOKEN`.

## Health del gateway

```bash
curl -sk https://BASE/health
```

## Rutas bajo `/api` del backend

El prefijo exacto depende de los routers montados en `backend/main.py` (p. ej. `/iot`, `/api/iot` para hidroponía si el módulo está cargado). El gateway reenvía a `CASTUO_BACKEND_URL/api/...`.

Ejemplo genérico:

```bash
curl -sk "https://BASE/api/iot/estado" -H "Authorization: Bearer TOKEN"
```

Ajusta la ruta consultando la documentación OpenAPI del backend en el puerto directo (`http://localhost:8000/docs`) cuando `BACKEND_AUTH_DISABLED=true`.

## LoRA / GGUF (opcional)

1. Levanta `uvicorn` en `scripts/ai/mistral_lora/app.py` (puerto 8899 recomendado).
2. Define `LORA_UPSTREAM=http://host.docker.internal:8899` (o servicio Docker equivalente).
3. Llama:

```bash
curl -sk "https://BASE/api/lora/infer" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"demo\",\"engine\":\"lora\",\"model_dir\":\"/ruta/en/contenedor\"}"
```

## SIGPAC local (sin API REST ficticia)

```bash
python scripts/integration/sigpac_local_bridge.py ruta/al/feature.geojson --parcel-id REF-001
```
