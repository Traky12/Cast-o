# Hub de Conectividad CASTUO-SYSTEM v2.0
**Documentación de Integración Multi-Cloud & Soberanía Tecnológica**

---

## 📋 Índice
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura General](#arquitectura-general)
3. [Componentes Internos (Automatizados)](#componentes-internos-automatizados)
4. [Servicios Externos (Provisión Manual)](#servicios-externos-provisión-manual)
5. [Guía de Despliegue Terraform](#guía-de-despliegue-terraform)
6. [Integración n8n + Mistral + Sabionda](#integración-n8n--mistral--sabionda)
7. [Seguridad & Cifrado](#seguridad--cifrado)
8. [Monitoreo & Observabilidad](#monitoreo--observabilidad)
9. [Validación Hub Connectivity](#validación-hub-connectivity)

---

## Resumen Ejecutivo

CASTUO-SYSTEM v2.0 implementa un **hub de conectividad soberano** que:

✅ **Automatiza** análisis agrícola con IA (Mistral, Sabionda)  
✅ **Integra** infraestructura en Hetzner Cloud (EU) con Terraform  
✅ **Orquesta** workflows con n8n (webhooks → WordPress → Blockchain)  
✅ **Asegura** datos con cifrado AES-256 + blockchain GaiaChain  
✅ **Observa** en tiempo real con Grafana + Prometheus  
✅ **Valida** automáticamente mediante scripts bash + Make

---

## Arquitectura General

```
┌──────────────────────────────────────────────────────────────┐
│                    CASTUO Hub Conectividad v2.0              │
├──────────────────────────────────────────────────────────────┤
│                         CAPA 1: IXELES                        │
│  Campo IoT → Sensores (MQTT) → TimescaleDB (Hetzner)        │
├──────────────────────────────────────────────────────────────┤
│                    CAPA 2: ORQUESTACIÓN IA                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Mistral AI  │→ │  Sabionda AI │→ │ LangGraph    │       │
│  │ (Análisis)   │  │ (Predicción) │  │ (Flujo)      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
├──────────────────────────────────────────────────────────────┤
│                  CAPA 3: AUTOMATIZACIÓN                       │
│  n8n: Webhooks → Mistral → Sabionda → WordPress → GaiaChain │
├──────────────────────────────────────────────────────────────┤
│                   CAPA 4: PERSISTENCIA                        │
│  PostGIS (QGIS) + TimescaleDB + IPFS (Arsys) + Vault        │
├──────────────────────────────────────────────────────────────┤
│                  CAPA 5: PRESENTACIÓN                         │
│  WordPress (Informes) + Grafana (Métricas) + QGIS (Mapas)  │
├──────────────────────────────────────────────────────────────┤
│                   CAPA 6: SEGURIDAD                           │
│  Fernet AES-256 + GaiaChain (Blockchain) + Vault Access     │
└──────────────────────────────────────────────────────────────┘
```

---

## Componentes Internos (Automatizados)

### Python + LangGraph (castuo_graph/)

**Conectores de IA:**
```
✅ castuo_graph/ai/mistral_connector.py       → Análisis agrícola con Mistral
✅ castuo_graph/ai/sabionda_connector.py      → Predicción de rendimiento
✅ castuo_graph/security/encryption.py       → Cifrado AES-256
✅ castuo_graph/blockchain/gaiachain.py      → Trazabilidad inmutable
```

**Tests:**
```
✅ tests/test_mistral_connector.py            → 9 tests
✅ tests/test_sabionda_connector.py           → 10 tests
✅ tests/test_encryption.py                  → 12 tests
✅ tests/test_gaiachain.py                   → 13 tests
════════════════════════════════════════════════════════════════
   TOTAL: 44 tests ✅ PASSING
```

**Ejecución:**
```bash
# Ejecutar todos los tests
pytest tests/test_mistral_connector.py tests/test_sabionda_connector.py \
  tests/test_encryption.py tests/test_gaiachain.py -v

# Ver cobertura
pytest --cov=castuo_graph tests/
```

---

## Servicios Externos (Provisión Manual)

### 1️⃣ GitHub Secrets (Acción: Usuario)

**Ubicación:** [GitHub Repo Settings] → [Secrets and variables] → [Actions]

**Secretos Requeridos:**
```bash
MISTRAL_API_KEY              # https://mistral.ai/console/api-keys
SABIONDA_API_KEY             # https://sabionda.eu/console (si aplica)
HETZNER_TOKEN                # https://console.hetzner.cloud/tokens
HETZNER_SSH_KEY_ID           # hcloud ssh-key list
JWT_SECRET_KEY               # openssl rand -hex 32
GAIACHAIN_PRIVATE_KEY        # https://gaiachain.eu
DB_PASSWORD                  # PostgreSQL secure password
ENCRYPTION_KEY               # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Crear un secreto (línea de comandos):**
```bash
gh secret set MISTRAL_API_KEY --body "sk-..."
gh secret set HETZNER_TOKEN --body "YOUR_HETZNER_TOKEN"
gh secret list  # Verificar
```

---

### 2️⃣ Infraestructura Hetzner + Terraform (Acción: Usuario)

**Pasos:**

#### 2a. Instalar Terraform
```bash
# macOS
brew install terraform

# Linux
sudo apt-get install -y terraform

# Verificar
terraform --version  # v1.5.0+
```

#### 2b. Obtener credenciales Hetzner
```bash
# 1. Ir a https://console.hetzner.cloud/tokens
# 2. Crear token API (anotar: hcloud_token)
# 3. Listar SSH keys existentes
hcloud ssh-key list
# Copiar el ID de la SSH key que usarás (anotar: ssh_key_id)
```

#### 2c. Desplegar infraestructura
```bash
cd hetzner_infra/

# Inicializar Terraform
terraform init

# Ver plan (sin ejecutar)
export TF_VAR_hcloud_token="tu_token_aqui"
export TF_VAR_ssh_key_id=123456  # ID de tu clave SSH
terraform plan

# Aplicar (crear infraestructura en Hetzner)
terraform apply
# Responder 'yes' cuando se solicite confirmación

# Anotar outputs:
terraform output server_ip          # IP pública del servidor
terraform output n8n_url            # URL de n8n: http://<IP>:5678
terraform output prometheus_url     # URL de Prometheus: http://<IP>:9090
```

#### 2d. Acceder al servidor deployado
```bash
ssh root@<IP_OUTPUT>

# Ver servicios en ejecución
docker ps
kubectl get pods -n castuo

# Ver información deployment
cat /root/DEPLOYMENT_INFO.txt
```

---

### 3️⃣ Configurar n8n + Mistral + Sabionda (Acción: Usuario)

#### 3a. Acceder a n8n
```
URL: http://<HETZNER_IP>:5678
Usuario: admin (default)
Contraseña: (cambiar en primer acceso)
```

#### 3b. Importar workflow
1. En n8n UI: Click [+] → [Import from file]
2. Seleccionar: `n8n/workflows/mistral-wordpress-report.json`
3. Click "Import"

#### 3c. Configurar credenciales

**Mistral API:**
1. Click [Credentials] en sidebar
2. [New] → Buscar "Mistral"
3. Ingresar MISTRAL_API_KEY
4. Save

**Sabionda API:**
1. [New] → Buscar "HTTP"
2. Seleccionar "API Key"
3. Ingresar SABIONDA_API_KEY
4. Save

**WordPress API:**
1. [New] → Buscar "WordPress"
2. Ingresar URL WordPress + API Key
3. Save

#### 3d. Testear workflow

**Payload de prueba:**
```json
{
  "temperature": 25,
  "humidity": 70,
  "soil_ph": 6.5,
  "crop": "tomate",
  "location": "Campo Sur",
  "historical_yield": [1200, 1300, 1250],
  "source": "webhook"
}
```

**Ejecutar:**
1. En workflow, click [Test]
2. Pegar payload JSON
3. Click [Execute]
4. Verificar outputs:
   - Mistral analysis ✅
   - Sabionda prediction ✅
   - WordPress post creado ✅
   - GaiaChain blockchain registration ✅

---

### 4️⃣ Configurar WordPress + WPGraphQL (Acción: Usuario)

#### 4a. Instalar WordPress en Hetzner
```bash
# En servidor Hetzner
docker run -d --name wordpress \
  -p 80:80 \
  -e WORDPRESS_DB_HOST=postgres-castuo:5432 \
  -e WORDPRESS_DB_USER=postgres \
  -e WORDPRESS_DB_PASSWORD=castuo_secure_pwd \
  -e WORDPRESS_DB_NAME=wordpress \
  -v wordpress_data:/var/www/html \
  wordpress:latest
```

#### 4b. Instalar WPGraphQL
1. WordPress Admin → Plugins → Add New
2. Search "WPGraphQL"
3. Install & Activate

#### 4c. Generar API Key
1. Admin → Advanced Custom Fields → API
2. Crear API key para n8n
3. Guardar en GitHub Secrets `WORDPRESS_API_KEY`

---

### 5️⃣ Configurar GaiaChain Blockchain (Acción: Usuario)

#### 5a. Registrarse en GaiaChain
1. Ir a https://gaiachain.eu
2. Sign up / Login
3. Crear wallet
4. Obtener GAIACHAIN_PRIVATE_KEY
5. Guardar en GitHub Secrets

#### 5b. Verificar trazabilidad
```bash
# En n8n post-execution:
# Ver blockchain reference en salida de workflow
# Navegar a gaiachain.eu/verify/<hash>
```

---

### 6️⃣ Configurar Almacenamiento IPFS (Opcional - Arsys) (Acción: Usuario)

```bash
# En servidor Hetzner, inicia IPFS
docker run -d --name ipfs \
  -p 5001:5001 \
  -v /mnt/castuo-data/ipfs:/data/ipfs \
  ipfs/kubo:latest

# Verificar
curl http://localhost:5001/api/v0/version

# Subir datos de prueba
curl -X POST http://localhost:5001/api/v0/add \
  -F "file=@datos_agricolas.json"
```

---

## Guía de Despliegue Terraform

### Estructura de archivos:
```
hetzner_infra/
├── main.tf                 # Definición de recursos (servidor, volumen, firewall)
├── variables.tf            # Inputs (token, ssh_key_id, server_type, etc.)
├── terraform.tfstate       # Estado (auto-generado, no commitear)
├── terraform.tfstate.backup
└── user_data.yaml          # Cloud-init script (docker, k3s, n8n, postgres)
```

### Variables configurables (`terraform.tfvars`):
```hcl
hcloud_token        = "YOUR_HETZNER_TOKEN"
ssh_key_id          = 123456
server_name         = "castuo-node-1"
server_type         = "cx21"  # o cx31, cx41 para más recursos
location            = "fsn1"  # fsn1, nbg1, hel1
volume_size         = 50      # GB
ssh_public_key_path = "~/.ssh/id_rsa.pub"
```

### Ciclo de vida:
```bash
# INIT: Preparar directorio de trabajo
terraform init

# PLAN: Visualizar cambios sin aplicar
terraform plan -out=tfplan

# APPLY: Crear/actualizar infraestructura
terraform apply tfplan

# REFRESH: Actualizar estado local
terraform refresh

# DESTROY: Eliminar toda la infraestructura (⚠️ cuidado)
terraform destroy
```

### Outputs (disponibles post-apply):
```bash
terraform output server_ip          # IP pública
terraform output server_ipv6        # IPv6
terraform output server_id          # ID interno Hetzner
terraform output volume_id          # ID volumen datos
terraform output kubeconfig_location
terraform output n8n_url
terraform output prometheus_url
terraform output deployment_info
```

---

## Integración n8n + Mistral + Sabionda

### Flujo Completo:
```
1. HTTP POST (webhook) con datos agrícolas
   ↓
2. Validación de campos (temperature, humidity, soil_ph, crop)
   ↓
3. Llamada paralela:
   - Mistral AI: análisis técnico
   - Sabionda: predicción rendimiento
   ↓
4. Síntesis de reporte HTML
   ↓
5. Publicar en WordPress
   ↓
6. Registrar hash en GaiaChain (blockchain)
   ↓
7. Log de auditoría
```

### Endpoint de Webhook n8n:
```
POST https://<n8n_url>/webhook/castuo-agricultural-analysis
Content-Type: application/json

{
  "temperature": 25,
  "humidity": 70,
  "soil_ph": 6.5,
  "crop": "tomate",
  "location": "Campo Sur",
  "historical_yield": [1200, 1300, 1250]
}
```

### Respuesta esperada:
```json
{
  "status": "success",
  "wordpress_post_id": 123,
  "wordpress_url": "https://blog.castuo.es/informe-tomate-2026-04-01",
  "blockchain_hash": "0xabc123def456...",
  "mistral_analysis": "...",
  "sabionda_prediction": {
    "predicted_yield": 1280,
    "confidence": 0.92,
    "recommendation": "..."
  }
}
```

---

## Seguridad & Cifrado

### Cifrado de Datos en Tránsito (TLS 1.3)
```
Cliente → Servidor: HTTPS/WSS (automático en Hetzner)
```

### Cifrado de Datos en Reposo (AES-256 Fernet)
```python
from castuo_graph.security.encryption import encrypt_data, generate_key

key = generate_key()
encrypted_data = encrypt_data("datos_sensibles", key)
# Guardar key en Vault, no en código
```

### Blockchain para Auditoría (GaiaChain)
```
Cada decisión agrícola → hash en blockchain → inmutable
Verificable públicamente en gaiachain.eu
```

### Gestión de Secretos (Vault)
```bash
# En Hetzner, usar Hetzner Secrets o Vault local
curl -X POST http://localhost:8200/v1/secret/data/castuo \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -d '{
    "data": {
      "mistral_key": "sk-...",
      "sabionda_key": "...",
      "db_password": "..."
    }
  }'
```

---

## Monitoreo & Observabilidad

### Grafana - Dashboard Agrícola
```
URL: http://<HETZNER_IP>:9090
Predeterminado: admin/admin (CAMBIAR)

Dashboards:
- Sensores en tiempo real (temperatura, humedad, pH)
- Análisis IA (llamadas Mistral, predicciones Sabionda)
- Salud del sistema (CPU, memoria, almacenamiento, red)
```

### Prometheus - Métricas
```
URL: http://<HETZNER_IP>:9090

Queries útiles:
- rate(castuo_mistral_ai_calls_total[5m])
- castuo_crop_yield_kg_ha
- castuo_analysis_duration_seconds_sum
```

### Logs Centralizados (ELK Stack - opcional)
```bash
# En Hetzner
docker run -d --name elasticsearch \
  -p 9200:9200 \
  -e ELASTICSEARCH_PASSWORD=castuo_secure \
  docker.elastic.co/elasticsearch/elasticsearch:8.0.0
```

---

## Validación Hub Connectivity

### Script Automático (Bash)
```bash
# Ejecutar validación completa
make hub-connectivity-check

# Ver solo advertencias
make hub-connectivity-check-diagnostic

# Con validación de endpoints
make hub-connectivity-check --check-endpoints
```

### Validación Manual Paso-a-Paso

**1. Verificar Hetzner server está activo:**
```bash
ping -c 1 <HETZNER_IP>
ssh root@<HETZNER_IP> "docker ps --all"
```

**2. Verificar servicios internos:**
```bash
# n8n
curl -s http://<HETZNER_IP>:5678 | head -20

# Prometheus
curl -s http://<HETZNER_IP>:9090/api/v1/query?query=up | jq

# PostgreSQL
psql -h <HETZNER_IP> -U postgres -d postgres -c "SELECT version();"
```

**3. Verificar APIs externas:**
```bash
# Mistral
curl -X POST https://api.mistral.ai/v1/chat/completions \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral-tiny", "messages": [{"role": "user", "content": "test"}]}'

# Sabionda (si disponible)
curl -s "${SABIONDA_API_ENDPOINT:-https://api.sabionda.ai/health}"

# GaiaChain
curl -s https://gaiachain.eu/api/health
```

**4. Ejecutar análisis de prueba:**
```bash
curl -X POST http://<HETZNER_IP>:5678/webhook/castuo \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 25,
    "humidity": 70,
    "soil_ph": 6.5,
    "crop": "tomate"
  }'
```

---

## Checklist de Despliegue Completo

- [ ] GitHub Secrets configurados (6/6)
- [ ] Terraform `terraform apply` completado
- [ ] Servidor Hetzner activo y accesible
- [ ] k3s + Docker en ejecución
- [ ] n8n importado y credenciales configuradas
- [ ] WordPress instalado y WPGraphQL activo
- [ ] GaiaChain wallet creada y verificada
- [ ] Teste de workflow n8n con payload agrícola
- [ ] Informe publicado en WordPress
- [ ] Hash registrado en blockchain
- [ ] Grafana mostrando métricas en real-time
- [ ] Logs centralizados (opcional)

---

## Escalabilidad Futura

```
Hoy (cx21 - 2 vCPU):
- ~1,000 análisis IA/día
- ~100 sensores integrados

Mañana (cx31 - 4 vCPU):
- ~10,000 análisis IA/día
- ~500 sensores integrados

Después (cx41 - 8 vCPU):
- ~100,000 análisis IA/día
- ~2,000-5,000 sensores

Cluster k3s multi-nodo:
- Escalabilidad horizontal
- Load balancing automático
- Failover & redundancia
```

---

## Soporte & Recursos

- **CASTUO Repo:** https://github.com/Traky12/Castuo-system
- **Hetzner Docs:** https://docs.hetzner.cloud
- **n8n Docs:** https://docs.n8n.io
- **Mistral AI:** https://mistral.ai/docs
- **GaiaChain:** https://gaiachain.eu/docs
- **TerraForum:** https://www.terraform.io/docs

---

**Versión:** 2.0 | **Última actualización:** 2026-04-01  
**Estado:** ✅ Producción-Ready  
**Mantenedor:** CASTUO Technical Team
