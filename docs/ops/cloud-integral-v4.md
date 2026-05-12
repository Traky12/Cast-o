# CASTUO-SYSTEM CLOUD INTEGRAL v4.0

## Objetivo
Despliegue aditivo y no destructivo con perfiles cloud soberanos UE (core, observability, iot, ai), validaciones GO/NO-GO y runbook operativo.

## Artefactos
- docker-compose.cloud.yml
- .env.cloud.example
- scripts/cloud-deploy.sh
- tests/cloud/cloud_validator.py

## Perfiles de despliegue
- core: api, postgres, n8n
- iot: mosquitto
- ai: openclaw-agente
- observability: prometheus, grafana
- local-vault: vault de laboratorio

## Flujo de despliegue (staging)
1. Copiar variables de entorno:
   - cp .env.cloud.example .env.cloud
2. Crear secretos en host:
   - mkdir -p secrets
   - printf "token" > secrets/vault_token
   - printf "iot-token" > secrets/iot_bearer
   - printf "mistral-key" > secrets/mistral_key
   - printf "sabionda-key" > secrets/sabionda_key
3. Validar configuración:
   - python tests/cloud/cloud_validator.py --env-file .env.cloud
4. Desplegar:
   - ./scripts/cloud-deploy.sh --env-file .env.cloud --profile core --profile iot --profile ai --profile observability

## GO/NO-GO
GO
- cloud_validator.py termina con exit code 0
- docker compose config valida el overlay cloud
- endpoint /health responde 200
- contenedores core en estado up

NO-GO
- faltan variables críticas (POSTGRES_PASSWORD, N8N_PASSWORD, VAULT_ADDR)
- faltan secretos requeridos para arranque seguro
- /health no responde o servicios en restart loop

## Operación diaria
- Revisar logs API:
  - docker compose -f docker-compose.cloud.yml --env-file .env.cloud logs -f api
- Revisar estado:
  - docker compose -f docker-compose.cloud.yml --env-file .env.cloud ps
- Rotación de secretos:
  - actualizar archivos en ./secrets y recrear servicios afectados

## Rollback rápido
- Mantener despliegue base existente (docker-compose.yml) sin cambios.
- Bajar solo overlay cloud:
  - docker compose -f docker-compose.cloud.yml --env-file .env.cloud down

## Notas de seguridad
- No guardar secretos en .env.cloud.example
- Usar *_FILE y Docker secrets siempre que sea posible
- Opción de variables en claro solo para laboratorio temporal
