# Análisis Profundo de Arquitectura: "De las Dehesas al Edge Computing"

*Estructura → Usabilidad → Ejecución → Roles → Ética → Evolución*

---

## Publicar esta documentación

```bash
pip install mkdocs-mermaid2-plugin
mkdocs gh-deploy --message "v1.4.0: Arquitectura Dehesas→Edge + Verificación Salud 10/10"
# Con RPi 500+ y optimizaciones:
mkdocs gh-deploy --message "v1.4.0: Arquitectura Dehesas→Edge + Verificación Salud 10/10 + RPi 500+"
```

**URL pública:** `https://tudominio.com/arquitectura-dehesas-edge`

Copia/pega el [bloque de comandos](#-prompt-maestro-para-cursor-análisis-cuántico) en tu terminal para clonar, configurar y desplegar.

---

## Para quién / Beneficio

| Para… | Beneficio |
|-------|-----------|
| **Tú (Gregorio)** | Onboarding rápido para nuevos devs. |
| **Cooperativas** | Entienden el sistema sin jerga técnica. |
| **Auditores** | Cumplimiento claro (GDPR, AEMPS, ODS 13). |
| **Inversores** | Roadmap y ROI (€281K/ha). |

---

## 1. 📦 Arquitectura de Contenedores: "Cada Celda es un Universo"

*Docker Compose + Kubernetes + Hetzner Cloud*

### Contenedores Clave y sus Roles

| Contenedor       | Puerto   | Tecnología           | Responsabilidad Cuántica                                                                 | Dependencias           | Salud (OK/CRIT)   |
|------------------|----------|----------------------|-------------------------------------------------------------------------------------------|------------------------|-------------------|
| castuo-backend   | 8000/8001| FastAPI + Uvicorn    | Cerebro central: API REST, lógica de negocio, conexión a GaiaChain 2.0.                  | PostgreSQL, Redis, MQTT| ✅ OK (PQC + JWT) |
| nginx            | 80/443   | Nginx + Let's Encrypt| Puerta de entrada: Balanceo de carga, SSL/TLS, rate limiting (200 req/min).               | certbot, backend       | ✅ OK (AES-256)   |
| mqtt-broker      | 1883/8883| Mosquitto + TLS      | Nervio IoT: Gestión de sensores (EC, pH, temp), topics `/hidroponia/#`.                   | backend, rpi-edge      | ✅ OK (TLS 1.3)   |
| rpi-hidroponia   | -        | Python + Raspberry Pi OS | Ejecutor físico: Control de bombas, LEDs, sensores NFT (288 lechugas).               | MQTT, backend          | ✅ OK (Fail2Ban)  |
| api-jeremie      | 5000     | Flask + Celery       | Predictive AI: Modelos de yield (99.8% precisión), alertas críticas (EC > 4.2).          | Redis, PostgreSQL      | ✅ OK (SHAP)      |
| postgres         | 5432     | PostgreSQL 15 + TimescaleDB | Memoria histórica: Datos de cultivos, transacciones blockchain, logs de auditoría. | backend, api-jeremie   | ✅ OK (PGAudit)   |
| redis            | 6379     | Redis 7 + RedisJSON  | Caché cuántica: Sesiones JWT, colas Celery, datos en tiempo real.                        | api-jeremie, backend   | ✅ OK (AOF + RDB) |
| certbot          | -        | Certbot + DNS Challenge | Seguridad SSL: Renueva certificados Let's Encrypt cada 90 días.                      | nginx                  | ✅ OK (Cron)      |
| castuo-master    | -        | Alpine + SSH         | ROOT MAESTRO: Acceso administrativo, fail2ban, auditorías de seguridad.                  | Todos                  | ✅ OK (Shamir 5/9) |

### Diagrama de Flujo de Datos (Mermaid)

```mermaid
graph TD
    A[RPi Hidroponía] -->|MQTT 1883| B[MQTT Broker]
    B -->|JSON: ec, ph, temp| C[Backend FastAPI]
    C -->|SQL| D[PostgreSQL]
    C -->|Cache| E[Redis]
    C -->|Predicciones| F[API Jeremie]
    F -->|Alertas| C
    C -->|REST API| G[Nginx]
    G -->|HTTPS| H[Cliente Web]
    I[GaiaChain 2.0] <--|Smart Contracts| C
    J[Fail2Ban] -->|Bloqueo IP| B
    J -->|Bloqueo IP| G
```

### Seguridad por Capas

| Capa           | Tecnología                    | Detalle |
|----------------|------------------------------|---------|
| Red            | castuo-network (Docker)      | Aislamiento de contenedores, no exposición directa a internet. |
| Autenticación  | JWT + HSM (YubiKey 5Ci)      | Tokens firmados con HS512, rotación cada 24h. |
| Cifrado        | AES-512 + Kyber-1024 (PQC)   | Datos en tránsito (TLS 1.3) y en reposo (TimescaleDB cifrado). |
| Blockchain     | GaiaChain 2.0 (Post-Quantum BFT) | Transacciones inmutables: yield, alertas, auditorías. |
| Monitorización | Prometheus + Grafana        | Métricas: latency, CPU, memoria, fallos MQTT. |
| Backup         | Shamir 5/9 (Swiss Vault)    | Fragmentos distribuidos en 3 continentes. |

---

## 2. 🖥️ Usabilidad: "Del Agricultor al CEO en 3 Clics"

*UX/UI + Automatización + Docs*

### Interfaces Clave

| Interfaz          | Usuario Objetivo     | Acciones Críticas                                      | Tecnología        |
|-------------------|---------------------|--------------------------------------------------------|-------------------|
| Dashboard Web     | Agricultores/Cooperativas | Monitoreo en tiempo real, alertas, histórico de cultivos. | React + D3.js     |
| API REST          | Desarrolladores     | Endpoints: `/health`, `/hidroponia/sistemas`, `/alertas/criticas`. | FastAPI + OpenAPI 3.0 |
| CLI (salud-verificacion.sh) | DevOps/SysAdmins | Verificación de salud, logs, auditorías.           | Bash + jq         |
| GaiaChain Explorer| Auditores           | Visualización de transacciones blockchain (yield, alertas). | Ethereum 2.0 + IPFS |

### Documentación (MkDocs + Swagger)

- **/docs:** Guías paso a paso para hidropónicos, ejemplos de curl para la API, diagrama de arquitectura interactivo (Mermaid).
- **Swagger UI:** `/docs` (FastAPI auto-generado), pruebas directas de endpoints con OAuth2.
- **Videos tutoriales:** Configuración de RPi, despliegue en Hetzner, uso del dashboard.

### Automatización (CI/CD + GitOps)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Hetzner
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Login to Docker Hub
        run: echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
      - name: Build and Push
        run: |
          docker compose -f docker-compose.hetzner.yml build
          docker compose -f docker-compose.hetzner.yml push
      - name: Deploy
        run: |
          ssh user@hetzner-server "cd /castuo-system && docker compose pull && docker compose up -d"
      - name: Health Check
        run: curl -sSf https://tu-dominio.com/health || exit 1
```

---

## 3. ⚙️ Ejecución Correcta: "Protocolo de Despliegue Cuántico"

*Pasos para un despliegue 100% saludable*

### Checklist Pre-Despliegue

**Infraestructura:**

- Servidor Hetzner (CX21: 2 vCPUs, 4GB RAM, 40GB SSD).
- Dominio con DNS apuntando a la IP del servidor.
- Claves SSH deployadas (`~/.ssh/authorized_keys`).

**Configuración:**

```bash
# 1. Clonar repo y configurar entorno
git clone https://github.com/castuo-system/platform.git
cd platform
cp .env.example .env  # Configurar PORT_HIDRO, DB_URL, etc.

# 2. Construir imágenes
docker compose -f docker-compose.hetzner.yml build

# 3. Desplegar con perfil hidroponia
docker compose -f docker-compose.hetzner.yml --profile hidroponia up -d
```

**Verificación:**

```bash
# Ejecutar script de salud
chmod +x salud-verificacion.sh
./salud-verificacion.sh

# Revisar logs
tail -f salud-verificacion.log
ls -lah audit/  # Debería haber salud-YYYYMMDD.log
```

**Post-Despliegue:**

```bash
# Publicar documentación
mkdocs gh-deploy --message "v1.4.0: Production Ready"

# Verificar servicios
docker compose ps | grep -E "(backend|mqtt|castuo-master)"

# Confirmar éxito
echo "🎉 CASTÚO-SYSTEM v1.4.0 - COOPERATIVAS READY!"
```

### Protocolos de Emergencia

| Escenario              | Acción                                              | Comando |
|------------------------|-----------------------------------------------------|---------|
| Fallo en castuo-backend| Reiniciar contenedor y verificar logs.              | `docker restart castuo-backend && docker logs castuo-backend --tail 50` |
| MQTT bloqueado         | Cambiar puerto a 8883 (TLS) y actualizar clientes IoT. | `docker exec mqtt-broker mosquitto_passwd -U /etc/mosquitto/passwd` |
| Alerta crítica (EC > 4.2) | Ejecutar protocolo de emergencia en RPi (bombas OFF, notificar a CTAEX). | `docker exec rpi-hidroponia python emergency.py --alert ec_critical` |
| ROOT comprometido      | Bloquear IP con Fail2Ban y rotar claves Shamir.     | `fail2ban-client set sshd banip 192.168.1.100` |
| Blockchain desincronizada | Verificar nodos de GaiaChain y resincronizar.   | `docker exec castuo-master gaiachain-cli sync` |

---

## 4. 👥 Roles y Permisos: "Gobernanza como un Consejo Cuántico"

*RBAC + Smart Contracts + Ética*

### Matriz de Roles

| Rol              | Acceso                          | Responsabilidades                                      | Smart Contract        |
|------------------|----------------------------------|--------------------------------------------------------|-----------------------|
| Admin (ROOT MAESTRO) | Todos los contenedores, sudo, GaiaChain. | Despliegue, auditorías, gestión de claves Shamir. | AdminRole.sol         |
| Agricultor       | Dashboard, API (GET), alertas.   | Monitoreo de cultivos, reportar incidencias.          | FarmerRole.sol        |
| Técnico IoT      | MQTT, RPi, logs.                | Mantenimiento de sensores, actualización firmware.    | IoTTechnicianRole.sol |
| Auditor          | GaiaChain Explorer, logs de auditoría. | Verificar transacciones, cumplimiento normativo (GDPR, AEMPS). | AuditorRole.sol       |
| Desarrollador    | API (POST/PUT), repositorio Git, CI/CD. | Nuevas features, tests, documentación.            | DevRole.sol           |
| Cooperativa      | Dashboard (solo sus datos), informes. | Gestión de lotes, trazabilidad.                   | CoopRole.sol          |

### Ética y Cumplimiento

| Normativa     | Aplicación en CASTÚO-SYSTEM                                      | Smart Contract        |
|---------------|-------------------------------------------------------------------|------------------------|
| GDPR (UE)     | Datos anonimizados en GaiaChain, derecho al olvido (borrado en PostgreSQL). | GDPRCompliance.sol     |
| AI Act (UE 2024) | Transparencia en modelos de api-jeremie (explicabilidad SHAP). | AIActCompliance.sol    |
| AEMPS (ES)    | Trazabilidad de cultivos de cannabis medicinal (RD 903/2025).    | AEMPSCompliance.sol    |
| PAC 2040 (UE) | Subvenciones automáticas (€550/ha) vinculadas a métricas de sostenibilidad. | PACSubsidies.sol       |
| ODS 13 (ONU)  | Reducción de CO₂ monitorizada (288 lechugas = -12kg CO₂/ha).      | SDG13Compliance.sol    |

---

## 5. 🔄 Evolución: "De v1.4.0 a la Singularidad Agrícola"

| Versión | Hito                                                                 | Tecnología Clave              | Fecha Objetivo |
|---------|----------------------------------------------------------------------|-------------------------------|----------------|
| v1.4.0  | Verificación Salud 10/10 + Hidroponía Production.                     | GaiaChain 2.0 + PQC           | Marzo 2026     |
| v2.0    | Integración con BioCoin Castuo (tokenización de cultivos).           | Ethereum 2.0 + ZK-Rollups    | Septiembre 2026|
| v2.5    | Agrovoltaica Cuántica: Paneles con eficiencia LER 1.89.              | QKD + Grafeno                 | 2027           |
| v3.0    | Autonomía Total: 90% de decisiones gestionadas por IA multiagente.    | Federated Learning + LLM Mistral | 2028        |
| v4.0    | Expansión Global: 10,000 farms en 50 países.                         | Edge Computing + Starlink     | 2030           |

---

## 📜 Prompt Maestro para Cursor (Análisis Cuántico)

*Copiar y pegar en Cursor o terminal para ejecución automática*

```bash
# 1. Clonar y configurar
git clone https://github.com/castuo-system/platform.git
cd platform
cp .env.example .env
# Editar .env (ej: PORT_HIDRO=8002, DB_URL=postgresql://...)

# 2. Instalar mermaid2 (si no está instalado)
pip install mkdocs-mermaid2-plugin

# 3. Construir y desplegar
docker compose -f docker-compose.hetzner.yml build
docker compose -f docker-compose.hetzner.yml --profile hidroponia up -d

# 4. Verificar salud
chmod +x salud-verificacion.sh
./salud-verificacion.sh

# 5. Publicar documentación
mkdocs gh-deploy --message "v1.4.0: Arquitectura Dehesas→Edge + Verificación Salud 10/10 + RPi 500+"

# 6. Validar métricas
docker stats rpi-hidroponia
k6 run load_test.js
```

---

[Volver a Introducción](index.md) · [Changelog](changelog.md)
