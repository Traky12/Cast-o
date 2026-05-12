# Staging — Inicialización y validación ISO 27001

Scripts para preparar el entorno de staging (Vault sin HSM, ZAP, backend, auto-rotate) y soporte a la certificación ISO 27001.

## Uso

1. **Configurar variables:** copiar `.env.staging` desde la raíz (o crear desde `.env.example`) y rellenar `VAULT_TOKEN`, `GAIA_CHAIN_*`, `ZAP_*`, `SLACK_*`, etc.

2. **Levantar servicios:**
   ```bash
   docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d vault zap
   ```

3. **Inicializar Vault** (desde la raíz del repo, con [Vault CLI](https://developer.hashicorp.com/vault/docs/install) instalado):
   ```bash
   export VAULT_ADDR=http://127.0.0.1:8200
   ./scripts/staging/init_staging.sh
   ```
   El script genera `vault_init.json` en la raíz. Guardar en lugar seguro y configurar `VAULT_TOKEN` en `.env.staging` con el `root_token` (o un token con políticas de backend).

4. **Arrancar backend y auto-rotate:**
   ```bash
   docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d backend auto-rotate
   ```

Plan completo: [docs/deployment/PLAN_DESPLIEGUE_STAGING_ISO27001.md](../../docs/deployment/PLAN_DESPLIEGUE_STAGING_ISO27001.md).
