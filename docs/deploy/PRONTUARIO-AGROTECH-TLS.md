# PRONTUARIO AGROTECH + TLS + IA (puerta TRL-6 integración)

`docs/deploy/PRONTUARIO-AGROTECH-TLS.md`

**Prontuario completo TRL-6: integración honesta con SNN TRL-4** — cierre de etapas **documentables en monorepo** (puerta de integración + sim lab explícita); industrialización en **§9** y `deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md`.

**TRL (honesto):** TRL-6 = **puerta de integración** (`model_tier` / `tier_disclosure.integration_gate` cuando `TRL_LEVEL` contiene `TRL-6`). La **SNN** sigue siendo **TRL-4 lab sim** (`tier_disclosure.neuromorphic_simulation`). `model_implementation_note`: `SNN TRL-4 (NeuromorphicEdge v2.0)`.

Guía operativa para combinar perfilado terpénico (laboratorio), despliegue TLS y automatización n8n en CASTUO-SYSTEM.

## 0) Etapas TRL en Castúo-System: qué alcanza este prontuario

| Declaración / etapa | Ámbito | Evidencia que aporta **este monorepo** | Para avanzar de etapa (fuera del solo repo) |
|---------------------|--------|----------------------------------------|---------------------------------------------|
| **TRL-6-staging** (puerta integración) | Repo + CI + despliegue documentado | Pruebas `trl6`, `docker-compose.prod.yml`, TLS y workflows descritos, playbook + ética enlazados | Checklist `deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md` (A–E) con **artefactos** en entorno real |
| **TRL-4-lab-sim** (SNN hidroponía) | Código y documentación | `tier_disclosure.neuromorphic_simulation` en API, `model_implementation_note`, perfiles terpénicos `TERPENE_PROFILES_VERSION` v2.1.0 (`agrotech/terpene_profiles.py`), tests neuromórficos | Fase **D** del checklist: validación con datos reales y evidencia de TRL |
| **Operación industrial** (TRL 7–9) | Sistema en producción | Documento checklist `deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md` (fases A–E) como marco verificable | Ejecución y documentación de fases A–E con **métricas reales** (no solo texto en git) |

**¿Mejora la estructura y “garantiza” alcanzar el TRL hablado?** Mejora la **trazabilidad y coherencia** entre documentación, código y pruebas: eso **sí** permite afirmar con rigor la **puerta TRL-6 del repositorio** y la **etiqueta TRL-4** de la SNN en laboratorio. **No** sustituye la ejecución del checklist industrial ni la evidencia en producción; por tanto **no garantiza** por sí solo un TRL industrial más alto — define **cómo** alcanzarlo de forma honesta.

## 1) Estructura objetivo del repo

```text
Castuo-System/
├── agrotech/
│   ├── ETHICS_TRACEABILITY.md
│   ├── mirceno.md
│   └── terpene_profiles.py
├── backend/
│   ├── integrations/
│   │   └── robotics/
│   │       └── neuromorphic_edge.py
│   └── models/
│       └── system_admin_playbook.py
├── castuo.conf
├── castuo-https.auto.conf
├── deploy/
│   ├── setup-ssl.sh
│   └── CHECKLIST-TRL7-INDUSTRIAL-LIVE.md
├── Dockerfile
├── docker-compose.prod.yml
├── hetzner-init.sh
├── n8n/
│   └── workflows/
│       ├── castuo_sentinel_terpene_tracking_alerts.json
│       └── castuo_system_monitor.json
└── tests/
    └── system/
        └── test_trl6.py
```

## 2) Agrotech: perfiles terpénicos

- Módulo: `agrotech/terpene_profiles.py`
- Documento operativo: `agrotech/mirceno.md`
- Uso: orientar setpoints de cultivo y trazabilidad en laboratorio.

## 3) TLS producción (Hetzner)

Plantilla mínima de variables de aplicación (copiar y rellenar): `.env.production.example` → `.env.production`.

Variables base:

```bash
export CASTUO_DOMAIN=castuo.tudominio.eu
export CERTBOT_EMAIL=admin@tudominio.eu
export CASTUO_REPO_ROOT=/opt/castuo-system
```

Ejecución:

```bash
cd "$CASTUO_REPO_ROOT"
./deploy/setup-ssl.sh
```

## 4) Verificación rápida

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production ps
curl -fsS http://localhost/health
docker compose -f docker-compose.prod.yml --env-file .env.production logs --tail 200
curl -X POST "http://localhost:5678/webhook/castuo-terpene-track" -H "Content-Type: application/json" -d "{\"ndvi\":0.72,\"ph\":5.9,\"ec\":1.3,\"humedad\":64,\"uvb_ratio\":0.05}"
```

Redis opcional (caché SNN): `docker compose -f docker-compose.prod.yml --env-file .env.production --profile redis up -d` y `CASTUO_SNN_CACHE_REDIS_URL=redis://redis:6379/0` en `.env.production`.

Puerta TRL-6 en CI (ejemplo):

```bash
python -m pytest tests/models/test_system_admin_playbook.py tests/integrations/test_neuromorphic.py tests/system/test_trl6.py -q
```

Salida esperada en CI sano: **13 passed** (incluye `test_trl6_traceability_without_trl6_env`).

## 5) Integración n8n sugerida

Cadena recomendada:

- Sentinel NDVI -> normalización -> `hydroponics/infer` -> decisión de riego -> registro de auditoría.
- Workflow listo para importar: `n8n/workflows/castuo_sentinel_terpene_tracking_alerts.json`.
- El nodo HTTP del infer debe leer sensores bajo `current` (p. ej. `$node['Code'].json.current.humedad` o, saliendo del Code, `$json.current.humedad`); no uses `Code.json.humedad` en la raíz.
- Endpoint webhook sugerido en n8n: `/webhook/castuo-terpene-track`.
- Soporta `target_terpene` (por defecto `mirceno`) y calcula bandera de desvío de perfil.
- Envío de alerta Telegram cuando `deviation_any=true` (requiere credencial Telegram en n8n y variables de entorno).

Recomendación de gobernanza:

- No introducir sidecars con `docker.sock` para renovación automática TLS sin evaluación de riesgo explícita.
- Mantener vía principal: cron de host + `certbot renew` + `nginx -s reload`.

## 6) Marco regulatorio mínimo (UE)

Referencias orientativas para revisión legal:

- Reglamento (UE) 2015/2283 (nuevos alimentos).
- Directiva 2002/46/CE (complementos alimenticios).
- España: Real Decreto 130/2018 (productos de base natural; revisar alcance sectorial concreto).
- Alemania: marco PflSchG (Ley de Productos Fitosanitarios; validar aplicabilidad por producto/uso).
- ISO 22000:2018 (seguridad alimentaria), cuando aplique al caso de uso.
- Certificación UE de producción ecológica, cuando proceda.

## 7) Límites y responsabilidad

- Este prontuario es técnico y de operaciones.
- No constituye asesoría médica ni legal.
- Las alegaciones terapéuticas deben pasar por validación regulatoria y equipos competentes.

## 8) Ética, trazabilidad y RGPD (operación)

- Documento canónico: `agrotech/ETHICS_TRACEABILITY.md`.
- El API de laboratorio adjunta `inference.traceability` en `hydroponics/infer` (marca temporal, `processing_purpose` con sufijo `_TRL6` si `TRL_LEVEL` incluye `TRL-6`, `profiles_version`, `validation_checks`, `tier_disclosure`, sin claim de conformidad legal).
- Opcional: `CASTUO_GOVERNANCE_DOCS_BASE_URL` en `.env.production` rellena `governance_doc_urls` en la respuesta (rutas públicas del mismo repo, sin URL inventada en código).
- Listas normativas en `agrotech/terpene_profiles.py` son **referencias para asesoría jurídica**, no certificación del sistema.
- Alertas Telegram: usar `CASTUO_ALERT_LEGAL_PREFIX` y **no** incluir datos personales ni ubicación precisa sin evaluación de base legal y DPIA.
- Marco legal del repo: `docs/legal/MARCO-LEGAL-SOBERANIA-UE-2026.md`.

### 8.1) TRL global, cifrado confidencial y roles (operación)

- **TRL de todo el sistema:** no se **garantiza** con cambios solo de documentación o IAM; el TRL **operativo** sigue exigiendo checklist industrial y evidencia (§0 y §9). El endurecimiento de roles **reduce riesgo** pero no sustituye piloto ni métricas reales.
- **Cifrado de lo confidencial:** capas y claves orientativas en `backend/models/system_admin_playbook.py` (`ENCRYPTION_STACK`); profundidad en `docs/legal/PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md` y `docs/deploy/PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md`. En producción: secretos fuera del git (`*_FILE`, Vault, volúmenes cifrados).
- **Roles (`backend/auth_roles.py`):** solo **`admin_general`** tiene prefijo `*` (acceso HTTP IAM completo en este esquema). El rol **`admin`** queda **acotado** a rutas CTAEX/ecommerce (`/trazabilidad`, `/certificacion`, `/ecommerce`, sensor microgreens legacy). Usuario de campo / técnico: `FARMER_API_KEY` → `agricultor`, `MQTT_TECHNICIAN_PASSWORD` / `IOT_API_KEY` → `tecnico`; laboratorio: `CASTUO_ROBOTICS_LAB_BEARER_TOKEN` → `robotics_lab`.
- **Pendrive / USB:** la API no monta ni detecta USB; el host desbloquea LUKS y expone rutas. Procedimiento y checklist de ficheros: **§8.2** y `deploy/PENDRIVE-CONTENIDO.md`.

### 8.2) Integración con pendrive seguro (LUKS, frase de paso, Docker)

**Requisitos del host**

1. `sudo apt-get update && sudo apt-get install -y cryptsetup`.
2. Identificar el bloque real del USB en Linux (`lsblk`, `/dev/disk/by-id/...`). La letra **D:** en Windows no es el nodo de dispositivo en el servidor Linux.
3. Estructura `tokens/` con ficheros de **una sola línea** y `chmod 600`. Listado completo: **`deploy/PENDRIVE-CONTENIDO.md`**.
4. **Windows (opcional):** `scripts/windows/Prepare-CastuoPendrive.ps1` genera árbol + tokens de ejemplo **sin BOM** y copia scripts/docs al USB; **NTFS no sustituye LUKS** — para volumen cifrado usar `deploy/prepare_pendrive_luks.example.sh` en Linux y volcar allí los secretos.

**Preparación inicial del pendrive (una vez)**

Plantilla interactiva (pide confirmación `YES`):

```bash
export CASTUO_LUKS_DEVICE=/dev/disk/by-id/usb-...-part1
./deploy/prepare_pendrive_luks.example.sh
```

Tras el script, el volumen queda montado en `CASTUO_LUKS_PREP_MOUNT` (por defecto `/mnt/castuo_prep`): crea los ficheros en `tokens/` según la checklist, `chmod 600`, luego `sudo umount …` y `sudo cryptsetup close castuo_usb` como indica el script.

**Acceso con usuario/contraseña (frase de paso LUKS)**

No hay “usuario LUKS” separado por defecto: la **frase de paso** es el factor de desbloqueo del volumen.

```bash
./deploy/mount_secure.example.sh /dev/disk/by-id/usb-...-part1
ls /mnt/castuo_secure/tokens
```

Desmontaje:

```bash
./deploy/umount_secure.example.sh
```

Variables útiles: `CASTUO_LUKS_MAPPER`, `CASTUO_CASTUO_SECURE_MOUNT` (por defecto `/mnt/castuo_secure`). El script usa `cryptsetup open … --key-file -` (compatible con frase introducida de forma oculta).

**Alternativa:** montaje interactivo estándar (sin script de contraseña por stdin): `export LUKS_PARTITION=…` y `./deploy/montar_pendrive.example.sh` con `CASTUO_USB_MOUNT` (p. ej. `/mnt/usb`); entonces `CASTUO_TOKENS_PATH=/mnt/usb/tokens` para `verify_castuo_tokens.py`.

**Verificación de tokens**

```bash
export CASTUO_TOKENS_PATH=/mnt/castuo_secure/tokens
python3 scripts/verify_castuo_tokens.py
```

**Docker y despliegue**

```bash
cp docker-compose.override.tokens.example.yml docker-compose.override.yml
export CASTUO_VERIFY_TOKENS_BEFORE_UP=1
./deploy.sh --local
```

El ejemplo de compose monta **`/mnt/castuo_secure/tokens:/app/tokens:ro`** y define rutas `*_FILE` bajo `/app/tokens/…` (solo rutas, sin secretos en el YAML). Si prefieres no duplicar en compose, omite esas claves del override y decláralas solo en `.env.production`.

**Política:** LUKS obligatorio para soporte extraíble en este flujo; montaje manual; verificación opcional antes de `compose` con `CASTUO_VERIFY_TOKENS_BEFORE_UP=1`. Playbook: `ENCRYPTION_STACK` → `iam_bearer_archivo`, `pendrive_path` `/mnt/castuo_secure/tokens/`. Backup: `docs/deploy/PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md`.

## 9. De TRL-6 integración a sistema vivo industrial (cliente)

Resumen de alcance TRL: ver **§0** (tabla etapa → evidencia → límite).

El repo cumple una **puerta TRL-6 de integración** honesta; un sistema **industrial activo** para usuarios finales exige fases adicionales (observabilidad, backup, piloto en entorno real, sustitución/evidencia del modelo sim TRL-4, SLAs).

Guía operativa:

- `deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md`

### Características alineadas con TRL-6 (integración)

- Trazabilidad ética en documentación, playbook de administración y respuestas del API de laboratorio
- Checklist industrial explícito para operación en condiciones reales (no se confunde con la puerta TRL-6 del repo)
- Documentación técnica y legal enlazada desde gobernanza y workflows
- Validación continua de todos los componentes (pytest puerta `trl6`)
- Configuración TLS operativa (`deploy/setup-ssl.sh`, nginx)

### Fragmento compose mínimo (solo api+n8n+nginx+redis)

```yaml
version: '3.9'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./castuo.conf:/etc/nginx/conf.d/default.conf:ro
      - ./castuo-https.auto.conf:/etc/nginx/conf.d/castuo-https.auto.conf:ro
      - castuo_certbot_www:/var/www/certbot:ro
      - castuo_letsencrypt:/etc/letsencrypt
    networks:
      - castuo_internal
    depends_on:
      - api

  api:
    build: .
    environment:
      - TERPENE_PROFILE=${TERPENE_PROFILE:-mirceno}
      - TRL_LEVEL=${TRL_LEVEL:-TRL-6-staging}
    networks:
      - castuo_internal

  n8n:
    image: n8nio/n8n
    environment:
      - TRL_LEVEL=${TRL_LEVEL:-TRL-6-staging}
    ports:
      - "5678:5678"
    networks:
      - castuo_internal

  redis:
    image: redis:7-alpine
    profiles: [redis]
    networks:
      - castuo_internal

volumes:
  castuo_certbot_www:
  castuo_letsencrypt:

networks:
  castuo_internal:
```

**Nota:** el `docker-compose.prod.yml` del repositorio añade Postgres y más servicios; sin `DATABASE_URL` / Postgres la API completa no equivale a producción.

### Sistema operativo (TRL-6)

```bash
# Prefijo legal en alertas
CASTUO_ALERT_LEGAL_PREFIX="Lab agrotech | no asesoría médica"

# Configuración de entorno
DATABASE_URL=postgresql+psycopg2://castuo:CAMBIA_openssl_rand_hex_16@postgres:5432/castuo
# Opcional (industrial / alto tráfico)
# CASTUO_DB_POOL_SIZE=20
```

### Objetivo TRL del monorepo Castúo-System (alcance honesto)

**Puerta TRL-6 cumplida en este repositorio**

- **Integración honesta:** Compose, TLS, pruebas `trl6`, workflows documentados.
- **SNN hidroponía:** Declarada como TRL-4 lab sim en código y documentación (`tier_disclosure.neuromorphic_simulation` en el API de laboratorio).
- **Checklist industrial:** Guía explícita para operación en condiciones reales (`deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md`); no confunde la puerta TRL-6 del repo con TRL industrial en cliente.

**Lo que NO implica este prontuario**

- **Certificación TRL-7/9:** Requiere checklist operativo completado y evidencia en producción (piloto, SLO/SLA, backups probados, modelo frente a datos reales).
- **Validación de campo:** El modelo SNN sigue siendo simulación de laboratorio; no declara silicio neuromórfico desplegado ni producto certificado en finca.
- **Declaración de conformidad:** No sustituye DPIA, figura del DPO ni asesoría legal o regulatoria específica del despliegue.

Las **etapas completadas en repo** para el objetivo de **transparencia TRL** son: gobernanza y ética enlazadas, trazabilidad API, pruebas de integración `trl6`, y ruta documentada hacia industrialización.

### Sistema completamente operativo con TRL-6 en integración y caminos claros a TRL-7/9

**Características implementadas**

- Trazabilidad ética completa en todos los componentes
- Checklist industrial honesto para TRL 7–9
- Documentación técnica y legal alineada
- Validación continua de todos los componentes
- Configuración TLS operativa (`deploy/setup-ssl.sh`, nginx)

**Documentación**

- Documento ético — `agrotech/ETHICS_TRACEABILITY.md`
- Checklist industrial — `deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md`
- Configuración técnica — `docker-compose.prod.yml`, `.env.production.example`, `deploy/setup-ssl.sh`
- Workflow de monitoreo — `n8n/workflows/castuo_sentinel_terpene_tracking_alerts.json`

**Nota:** validado con `python -m pytest tests/models/test_system_admin_playbook.py tests/integrations/test_neuromorphic.py tests/system/test_trl6.py -q` → **13 passed** (ver también **§4**).

### Prefijo legal en alertas

```bash
CASTUO_ALERT_LEGAL_PREFIX="Lab agrotech | no asesoría médica"
```

### Configuración de entorno

```bash
DATABASE_URL=postgresql+psycopg2://castuo:CAMBIA_openssl_rand_hex_16@postgres:5432/castuo
# Opcional (industrial / alto tráfico)
# CASTUO_DB_POOL_SIZE=20
```

