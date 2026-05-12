# CASTUO-SYSTEM CLOUD INTEGRAL v4.1

Runbook operativo no destructivo para despliegue soberano UE con perfiles IaaS/PaaS/SaaS y backbone IoT Wireless Logic (Conexa EU).

## 1) Objetivo

- Implementar un overlay cloud aditivo sin modificar los `docker-compose` existentes.
- Separar despliegue por perfiles: `core`, `observability`, `iot`, `ai`.
- Mantener controles de legalidad/operación con validaciones GO/NO-GO.

## 2) Artefactos de v4.1

- `docker-compose.cloud.yml`
- `.env.cloud.example`
- `config/mosquitto.cloud.conf`
- `scripts/cloud-deploy.sh`
- `tests/cloud/cloud_validator.py`

## 3) Prerrequisitos

- Docker + Docker Compose plugin instalados.
- Secretos locales en `./secrets/`:
  - `vault_token`
  - `iot_bearer`
  - `mistral_key`
  - `sabionda_key`
  - `wireless_logic_token` (obligatorio para perfil `iot`)
- Archivo de entorno:
  - `cp .env.cloud.example .env.cloud`
  - rellenar credenciales y endpoints reales.

## 4) Perfiles y alcance

- `core`: API principal + Vault.
- `observability`: Prometheus + Grafana.
- `iot`: broker MQTT/MQTTS + `iot-processor` conectado a Wireless Logic.
- `ai`: orquestador de inferencia y supervisión Sabionda.

## 5) Despliegue recomendado

### Staging (rápido)

```bash
bash scripts/cloud-deploy.sh staging core,observability
```

### Staging completo

```bash
bash scripts/cloud-deploy.sh staging core,observability,iot,ai
```

### Producción (controlado)

```bash
bash scripts/cloud-deploy.sh prod core,observability,iot,ai
```

Opciones útiles de despliegue:

```bash
bash scripts/cloud-deploy.sh staging core,observability --env-file .env.cloud --dry-run
bash scripts/cloud-deploy.sh staging core,observability,iot,ai --env-file .env.cloud --rollback-on-error
bash scripts/cloud-deploy.sh staging iot --env-file .env.cloud --skip-healthcheck
```

## 6) Validación GO/NO-GO

Ejecutar:

```bash
python tests/cloud/cloud_validator.py --env-file .env.cloud --compose-file docker-compose.cloud.yml
```

Criterios GO:

- Configuración compose válida.
- Secretos requeridos presentes.
- Variables críticas definidas (`VAULT_ADDR`, `S3_BUCKET_LOGS`, `GAIA_X_RPC`, `ALLOWED_ORIGINS`).
- Perfiles válidos detectados.
- Si se usa `iot`: credenciales Wireless Logic y `wireless_logic_token` presentes.

Criterios NO-GO:

- Faltan secretos.
- `.env.cloud` incompleto.
- `docker compose config` con errores.

## 7) Flujo operativo IoT (Wireless Logic)

1. Sensores publican por MQTT/MQTTS hacia `iot-bridge`.
2. `iot-processor` consume tópico `${MQTT_TOPIC}`.
3. Procesamiento y forward a backend CASTUO + trazabilidad externa (`TRACES_HYPERLEDGER_URL`).
4. API principal consolida estado en `/health`.

Smoke test E2E (publicar -> ingerir -> reenviar):

```bash
bash scripts/cloud-iot-smoke.sh .env.cloud docker-compose.cloud.yml castuo/sensors/smoke
```

## 8) Operación continua

- Revisar `docker compose ps` cada despliegue.
- Confirmar `healthcheck` de API en `${API_HEALTH_PATH}`.
- Confirmar Prometheus en `${PROMETHEUS_PORT}` y Grafana en `${GRAFANA_PORT}`.
- Confirmar puertos MQTT `1883` y MQTTS `8883` abiertos según política.
- Rotar tokens de `./secrets/*` por política interna.
- Usar atajos `make cloud-validate`, `make cloud-up-all`, `make cloud-iot-smoke`.

## 9) Rollback seguro (no destructivo)

```bash
docker compose -f docker-compose.cloud.yml --env-file .env.cloud down
```

No elimina ni altera otros stacks del repositorio.
