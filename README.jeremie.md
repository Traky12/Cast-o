# CASTÚO-SYSTEM JEREMIE/CTAEX (v4.3)

Stack **PostgreSQL + API (events/compliance/audit) + OpenEPCIS** para demo CTAEX 17/03 y cumplimiento JEREMIE.

## Estructura

- `api/` — FastAPI: `/health`, `/events`, `/compliance`, `/audit` (Bearer token)
- `init/01-schema.sql` — Tabla `events` (GS1 EPCIS) + `audit_log` + trigger
- `scripts/` — `generate_ssl.sh`, `backup_script.sh`, `demo_script.sh`, `demo_ctaex.sh`
- `.env.jeremie` — Variables de entorno (copiar a `.env` para compose)
- `docker-compose.jeremie.yml` — Servicios postgres, api, openepcis

## Despliegue rápido

```bash
# 1. Variables
cp .env.jeremie .env

# 2. Levantar
docker-compose -f docker-compose.jeremie.yml up -d --build

# 3. Esperar health y probar
sleep 15
curl -s -H "Authorization: Bearer ctaex17_jeremie_token" http://localhost:8000/health | jq
curl -s http://localhost:8000/compliance | jq
```

## Demo 7 min (CTAEX)

```bash
chmod +x scripts/demo_script.sh scripts/demo_ctaex.sh
export API_TOKEN=ctaex17_jeremie_token
./scripts/demo_script.sh
# o
./scripts/demo_ctaex.sh
```

## Crear evento GS1 EPCIS

```bash
curl -X POST http://localhost:8000/events \
  -H "Authorization: Bearer ctaex17_jeremie_token" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "packing",
    "epc_list": ["urn:epc:id:sgtin:305555.00001.1"],
    "quantity": 100,
    "read_point": "urn:epc:id:sgln:305555.00001.0",
    "biz_step": "urn:epcglobal:cbv:bizstep:packing",
    "metadata": {"cultivo": "sorgo", "finca": "CTAEX-50ha"}
  }'
```

## SSL (opcional)

```bash
chmod +x scripts/generate_ssl.sh
./scripts/generate_ssl.sh
# Luego en docker-compose.jeremie.yml descomentar volúmenes ssl y POSTGRES_SSL_MODE=verify-full
```

## Backups

```bash
export POSTGRES_PASSWORD=ctaex17_ssl_2026_jeremie POSTGRES_DB=castuo_jeremie POSTGRES_USER=castuo_user
chmod +x scripts/backup_script.sh
./scripts/backup_script.sh
# Backups en ./backups/
```
