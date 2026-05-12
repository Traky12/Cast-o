# RUNBOOK PRE-PILOT INVERNADERO CASTUO-SYSTEM v2.1

Protocolo operativo automatizado (Go/No-Go + Evidencias + Conexion Prototipo)

Fecha base: 2026-04-03
Alcance: activacion tecnica para conectar el primer invernadero prototipo
Objetivo: validacion automatizada y trazable para due diligence operativa

## Estado Final del Protocolo

Estado validado en repositorio:

1. Runbook con checks ampliados: operativo
2. Evidencias en formato estandar: operativo
3. Resumen Go/No-Go automatizado: operativo
4. Script de conexion de prototipo: implementado (ejecutar tras GO)

## Arquitectura Operativa

Flujo de ejecucion:

1. scripts/runbook-prepilot.sh
2. Verificacion de infraestructura
3. Verificacion de servicios
4. Verificacion de seguridad
5. Generacion de evidencias
6. Criterio Go/No-Go
7. Si GO: conexion del primer invernadero

## Scripts Oficiales

1. Script principal:
	scripts/runbook-prepilot.sh
2. Script post-GO para onboarding de prototipo:
	scripts/connect_first_greenhouse.sh
3. Target de Make:
	make runbook-prepilot

## Ejecucion

### Modo no intrusivo

```bash
bash scripts/runbook-prepilot.sh --skip-start --skip-k8s
```

### Modo operativo completo

```bash
HETZNER_IP=<IP_HETZNER> STRICT=1 make runbook-prepilot
```

### Ejecucion directa estricta

```bash
bash scripts/runbook-prepilot.sh --ip <IP_HETZNER> --strict
```

Variables opcionales soportadas:

1. PUBLIC_API_HEALTH_URL (default: https://api.castuo-system.cloud/health)
2. LOCAL_API_HEALTH_URL (default: http://localhost:8000/health)
3. PROMETHEUS_URL (default: http://localhost:9090)
4. GRAFANA_URL (default: http://localhost:3000)

## Evidencias Generadas

Cada ejecucion crea carpeta en:

artifacts/prepilot/<timestamp>/

Evidencias principales:

1. 00_summary.txt
2. 01_hetzner_server.txt
3. 02_docker_status.txt
4. 03_containers_running.txt
5. 04_api_health.txt
6. 05_mqtt_status.txt
7. 06_redis_ping.txt
8. 07_mariadb_schemas.txt
9. 08_secrets_check.txt
10. 09_tls_certificates.txt
11. 10_prometheus_metrics.txt
12. 11_grafana_dashboards.txt
13. 12_iot_telemetry.txt

Evidencias complementarias internas:

1. 90_start_all_services.txt
2. 91_verify_operational_stack.txt
3. 92_pilot_user_upsert.txt
4. 93_pilot_user_select.txt

## Criterio Go/No-Go

GO:

1. FAIL = 0
2. Servicios criticos funcionales
3. API health operativo
4. Persistencia y telemetria validadas

NO-GO:

1. FAIL > 0
2. En modo strict, si WARN > 0

## Diagnostico Rapido de Bloqueantes

### API health fallando

```bash
docker logs --tail 100 castuo-api
docker ps --filter "name=castuo-api"
docker inspect castuo-api --format='{{.NetworkSettings.Ports}}'
curl -v http://localhost:8000/openapi.json | grep "/health"
docker restart castuo-api
```

### MQTT no detectado

```bash
docker ps --filter "name=mosquitto"
docker compose -f docker-compose.iot.yml up -d mosquitto
docker exec -it castuo-mqtt mosquitto_pub -h localhost -t "test" -m "hello"
docker exec -it castuo-mqtt mosquitto_sub -h localhost -t "test" -v -C 1
```

### Prometheus/Grafana no saludables

```bash
curl -I http://localhost:9090/-/healthy
curl -I http://localhost:3000/api/health
docker logs --tail 100 castuo-prometheus
docker logs --tail 100 castuo-grafana
```

## Seguridad Operativa

1. No exponer secretos en evidencias
2. No commitear .env real
3. Verificar valores no por defecto en .env antes de ejecutar

## Paso Siguiente tras GO

Conectar el primer invernadero prototipo:

```bash
bash scripts/connect_first_greenhouse.sh
```

## Referencias

1. scripts/runbook-prepilot.sh
2. scripts/connect_first_greenhouse.sh
3. tests/test_prepilot_runbook.py
4. Makefile
