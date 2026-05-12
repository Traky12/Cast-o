# CASTUO-SYSTEM

### Despliegue producción Hetzner (D1)

Stack en la **raíz del repo**: `docker-compose.prod.yml`, `Dockerfile`, `castuo.conf`, `castuo-https.auto.conf`, `deploy.sh`, `hetzner-init.sh`, `init-db/`, `.env.production.example`. Guías: **[CHECKLIST D1](docs/deploy/CHECKLIST-CURSOR-HETZNER-D1.md)** · **[DNS + SSL](docs/deploy/DNS-SSL-HETZNER-CX22.md)** · [deploy/README.md](deploy/README.md). Verificación local: `scripts/windows/verify-dns-ssl.ps1`.

---

Plataforma de cultivos sostenibles: API de sensores, recomendaciones Sabionda, frontend HTML y flujo n8n (Webhook → API → MQTT), con integraciones a Mistral AI, WhatsApp, Notion, Gmail, LondBot y otros servicios.

**Sistemas España/UE**: facturación SII/Facturae, cumplimiento AEMPS y RD 903/2025 (cannabis), trazabilidad GaiaChain, mercados de carbono Verra/EU ETS, CASTUO Cloud 5.0 + Proyecto CASTUA (cáñamo industrial, agrovoltaica, economía circular). Ver [docs/ARQUITECTURA-CASTUO-CASTUA.md](docs/ARQUITECTURA-CASTUO-CASTUA.md).

**Integración maestra (n8n + OSS + gemelo digital):** orquestación multi-instancia, journal Trillizo con HMAC, stack recomendado (Postgres/Timescale, Appsmith, Grafana, SilverBullet), flujo captura → decisión → guardas OT → registro auditable, V&V con `scripts/tests/stress_test_313_cores.py` (firma local), inyección HTTP al gateway con `scripts/tests/stress_gateway_injection.py`, y marco de failover honesto. Documento único para README ejecutivo o whitepaper: **[docs/INTEGRACION-MAESTRA-N8N-GEMELO-DIGITAL.md](docs/INTEGRACION-MAESTRA-N8N-GEMELO-DIGITAL.md)**.

**IA en desarrollo:** Parte del código puede estar asistido por GitHub Copilot (Business, EU compliant). Todos los PRs requieren revisión humana. Ver [docs/legal/AI_POLICY.md](docs/legal/AI_POLICY.md) (EU AI Act).

### 🧠 Gestión por agentes de IA

Este repositorio está optimizado para ser gestionado por agentes autónomos (Sabionda, Cursor, etc.). Para inicializar un agente, asigne como **contexto primario**:

- **Master System Prompt:** [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md)
- **Protocolos de seguridad (VSA/PQC):** [docs/security/CASTUO-SECURITY-VSA-PQC-EXECUTIVE.md](docs/security/CASTUO-SECURITY-VSA-PQC-EXECUTIVE.md)
- **Kernel operativo (EASA-MIL-SPEC):** [docs/security/CASTUO-SYSTEM-KERNEL-V1.md](docs/security/CASTUO-SYSTEM-KERNEL-V1.md)

*El sistema opera bajo cifrado Cipher Level 5. No se autorizarán misiones sin validación cruzada del Gemelo Digital (&lt;300 s).*

**Estado de consolidación — Castúo-System 1.0:** El ecosistema es íntegro. Si un agente intentara desplegar [PROJECT-VULCAN] (Falcon X) sin que [BIO-HUB-DIGITAL] haya confirmado stock de bioetanol, el SYSTEM_PROMPT bloquearía la acción. Brechas críticas cerradas: seguridad física (calima PTM), lógica (PQC en cada comando), ética (validación de impacto rural y biodiversidad). Contratos endurecidos: [contracts/HARDENED-LOGIC/](contracts/HARDENED-LOGIC/) (BioPayV2 Pull, EnergyCredit Multisig). Recuperación ante blackout: [docs/security/BLACKOUT-RECOVERY-SOP.md](docs/security/BLACKOUT-RECOVERY-SOP.md). **Validación final (estrés):** [FINAL_VALIDATION_REPORT.md](FINAL_VALIDATION_REPORT.md) · [informe completo](docs/security/FINAL_VALIDATION_REPORT.md). **Manifiesto 1.0:** [docs/MANIFESTO-CASTUO-SYSTEM-1-0.md](docs/MANIFESTO-CASTUO-SYSTEM-1-0.md) · código [`castuo_manifest/`](castuo_manifest/). **Certificado Sabionda GOLD:** [SABIONDA-AUTH-V1.cert](SABIONDA-AUTH-V1.cert) · [SABIONDA_FINAL_RELEASE.log](SABIONDA_FINAL_RELEASE.log) · [entrega CASTUO_GOLD_V1](docs/CASTUO-GOLD-V1-DELIVERY-MANIFEST.md). **Análisis extremeño + cuántico:** [docs/SABIONDA-CUANTICO-EXTREMENO-CASTUO-GOLD.md](docs/SABIONDA-CUANTICO-EXTREMENO-CASTUO-GOLD.md).

**Sello y verificación:** `python scripts/sabionda_final_release_seal.py` · `python scripts/seal.py --verify`

**Certificación blockchain (NFT — tras despliegue):** completar TX/IPFS en [CASTUO-GOLD-V1-DELIVERY-MANIFEST.md](docs/CASTUO-GOLD-V1-DELIVERY-MANIFEST.md) y en `.cert`; plantillas en `scripts/castuo_nft_metadata.example.json`. *Explorer: sustituir por URL real de la red elegida.*

### Documentación técnica y operativa

| **Documento** | **Descripción** | **Enlace** |
|---------------|-----------------|------------|
| **Integración maestra (whitepaper técnico)** | n8n + stack soberano + gemelo digital, V&V, flujo E2E, Error Trigger, enlaces verificables al repo. | [INTEGRACION-MAESTRA-N8N-GEMELO-DIGITAL.md](docs/INTEGRACION-MAESTRA-N8N-GEMELO-DIGITAL.md) |
| **Arquitectura y Roadmap** | Arquitectura modular, flujos de trabajo, roadmap de 6 meses y KPIs. | [SABIONDA-PRO-ARCHITECTURE-ROADMAP.md](docs/SABIONDA-PRO-ARCHITECTURE-ROADMAP.md) |
| **Guía de Cuentas Pro** | Modelos, permisos, endpoints y ejemplos de uso. | [PRO-ACCOUNTS-GUIDE.md](docs/PRO-ACCOUNTS-GUIDE.md) |
| **Manual de Operaciones CTAEX** | Procedimientos operativos para cannabis y microgreens. | [OPERATIONS-MANUAL-CTAEX.md](docs/OPERATIONS-MANUAL-CTAEX.md) |
| **Informe Técnico** | Detalles técnicos, diagramas y métricas de rendimiento. | [TECHNICAL-REPORT-CTAEX.md](docs/TECHNICAL-REPORT-CTAEX.md) |
| **Integración con Legacy Systems** | Conectores para SAP, LIMS y bases de datos antiguas. | LEGACY-INTEGRATION.md (en desarrollo) |
| **Guía de Sensores IoT** | Configuración de sensores, alertas y ajustes automáticos. | IOT-SENSORS-GUIDE.md |
| **Cumplimiento Normativo** | Validación de GDPR, AI Act, ISO 27001 y normativas por país. | COMPLIANCE-MANUAL.md |
| **AI Policy (EU AI Act)** | Uso de GitHub Copilot Business, human review y RACI. | [docs/legal/AI_POLICY.md](docs/legal/AI_POLICY.md) |
| **Plan de migración PostgreSQL** | Esquemas y pasos para cannabis y microgreens. | [POSTGRESQL-MIGRATION-PLAN.md](docs/POSTGRESQL-MIGRATION-PLAN.md) |
| **Acuerdo CTAEX–CASTÚO** | Resumen del acuerdo estratégico, beneficios y fondo de I+D. | [CTAEX-CASTUO-AGREEMENT-SUMMARY.md](docs/CTAEX-CASTUO-AGREEMENT-SUMMARY.md) |
| **CASTUO 5.PRO — Nexo bioeconomía circular** | Aleaciones Jara/Cáñamo/Chlorella, ZIP Soberanía Total, README maestro. | [README_MAESTRO.md](docs/README_MAESTRO.md) · [CATALOGO-ALEACIONES-ECOLOGICAS-v5PRO.md](docs/CATALOGO-ALEACIONES-ECOLOGICAS-v5PRO.md) |
| **BioCoin Castuo (físico-digital)** | BOM, BioCoinVault.sol, EvidenceHash, dashboard Evidence. | [README_BIOCOIN_CASTUO.md](docs/biocoin/README_BIOCOIN_CASTUO.md) |
| **Setup Composer (ZIP + Git)** | Manifiesto SHA-256, `rebuild_system.py`, arranque medido. | [SETUP-COMPOSER.md](docs/SETUP-COMPOSER.md) |
| **Compliance BIOJARA 5.PRO** | MiCA, multisig DAO, KPIs, soberanía despliegue. | [COMPLIANCE-BIOJARA-5PRO.md](docs/COMPLIANCE-BIOJARA-5PRO.md) |
| **AgroVision 360** | Dictamen CDTI/IDAE/Junta (edge, sensores, financiación). | [AGROVISION-360-DICTAMEN-ESTRATEGICO.md](docs/AGROVISION-360-DICTAMEN-ESTRATEGICO.md) |
| **CASTO LÁSER v2.1** | TiAlC, tether fibra, CASTO-QC, EvidenceHash patrimonio. | [CASTUO-LASER-v2.1-ARQUITECTURA.md](docs/CASTUO-LASER-v2.1-ARQUITECTURA.md) |
| **Hidrante urbano / extinción** | PEM+Li, LiDAR humo, RD 517/2024, Castuo 360. | [CASTUO-360-HIDRANTE-URBANO-EXTINCION.md](docs/CASTUO-360-HIDRANTE-URBANO-EXTINCION.md) |
| **Circular FAB + biocomposite** | Cáñamo FDM, camilla rescate, QC blockchain. | [CASTUO-CIRCULAR-FAB-BIOCOMPOSITE-MANUAL.md](docs/CASTUO-CIRCULAR-FAB-BIOCOMPOSITE-MANUAL.md) |
| **CASTUO LITE V2** | Autonomía η, térmica láser, RFI, paracaídas. | [CASTUO-LITE-V2-PREPRODUCCION.md](docs/CASTUO-LITE-V2-PREPRODUCCION.md) |
| **Ecosystem 6X + consenso** | FastAPI federado, self-healing, quórum nodos. | [CASTUO-ECOSYSTEM-6X-ARQUITECTURA.md](docs/CASTUO-ECOSYSTEM-6X-ARQUITECTURA.md) · [PROTOCOLO-CONSENSO-CASTUO.md](docs/protocolos/PROTOCOLO-CONSENSO-CASTUO.md) |
| **CASTUO Nano + Lab** | SLAM confinado, Faraday, MS portátil, brazo háptico, XAI + ledger. | [CASTUO-NANO-LAB-ARQUITECTURA.md](docs/CASTUO-NANO-LAB-ARQUITECTURA.md) · [roadmap A/B/C](docs/CASTUO-ROADMAP-NANO-LAB-ENTREGABLES.md) |
| **Cripta del Silencio (C)** | Caso patrimonio + API logs XAI firmados. | [CASTUO-SIMULACION-OPERACION-CRIPTA-SILENCIO.md](docs/CASTUO-SIMULACION-OPERACION-CRIPTA-SILENCIO.md) · [API-XAI-LEDGER-LOGS.md](docs/API-XAI-LEDGER-LOGS.md) |
| **CASTUO Cloud 5.X** | Soberanía territorial: Zero-Water, NIR-Core, GaiaChain, CIS, Edge. | [CASTUO-CLOUD-5X-SOBERANIA-TERRITORIAL.md](docs/CASTUO-CLOUD-5X-SOBERANIA-TERRITORIAL.md) |
| **Segureja LÁSER** | Descorche femtosegundo, enjambre, GaiaChain corcho, Fase 0 Extremadura. | [SEGUREJA-LASER-DESCORCHE-5.md](docs/SEGUREJA-LASER-DESCORCHE-5.md) |
| **API corcho + CIS** | `POST /traceability/cork-extraction-events`, `/cis/calculate`. | [API-TRACEABILITY-CORK-CIS.md](docs/API-TRACEABILITY-CORK-CIS.md) |
| **Ladanum 5.PRO+** | CastuoRegistry, HSM scripts, CI release, Xtranet Edge. | [CASTUO-LADANUM-5PRO-INTEGRACION-FINAL.md](docs/CASTUO-LADANUM-5PRO-INTEGRACION-FINAL.md) |
| **Libro blanco / Chlorella / Gobernanza** | Pilares, KPIs, MiCA-AI Act-DORA. | [CASTUO-LIBRO-BLANCO-5PRO-INTEGRAL.md](docs/CASTUO-LIBRO-BLANCO-5PRO-INTEGRAL.md) · [CHLORELLA](docs/PROYECTO-CHLORELLA-5PRO.md) · [Compliance](docs/CASTUO-GOBERNANZA-COMPLIANCE-5PRO.md) |
| **Trazabilidad corcho + SQL** | Propiedad digital árbol, PG/QuestDB. | [ESTADO-CAPA-TRAZABILIDAD-CORCHO.md](docs/ESTADO-CAPA-TRAZABILIDAD-CORCHO.md) |
| **Legal-as-code + TABACASTUO / Roméa** | Cláusulas 4/5/7, auditoría V/A/R. | [CASTUO-GOBERNANZA-LEGAL-AS-CODE-5PRO.md](docs/CASTUO-GOBERNANZA-LEGAL-AS-CODE-5PRO.md) · [6.X tabaco/romero](docs/TABACASTUO-ROMEA-PRO-ECOSYSTEM-6X.md) |
| **CASTUO360 expediente** | Hash ZIP, GaiaChain, Smart-NDA. | [CASTUO360-EXPEDIENTE-SOBERANIA-DIGITAL.md](docs/CASTUO360-EXPEDIENTE-SOBERANIA-DIGITAL.md) |
| **CASTUO360 blindaje ejecución** | Ancla, PI por componente, Smart-NDA, checklists OEPM/PCT. | [CASTUO360-BLINDAJE-EJECUCION-6X.md](docs/CASTUO360-BLINDAJE-EJECUCION-6X.md) |
| **Dronda 120 + Remolque XXL** | Micro-grid, aprendizaje federado, KPIs, U-Space. | [DRONDA-120-REMOLQUE-XXL-EXCELENCIA.md](docs/DRONDA-120-REMOLQUE-XXL-EXCELENCIA.md) |
| **CASTO 1.0 → ECO-STEALTH 5.0** | Optimización prototipo, ruta bio-metaestructura, failsafe láser. | [CASTO-1-0-ECO-STEALTH-5-0-RUTA.md](docs/CASTO-1-0-ECO-STEALTH-5-0-RUTA.md) |
| **Falcon X Hydro-Renhace 6.1** | AIP bioetanol/H₂, SLR-Ω+, PQC, NextGen EU. | [FALCON-X-CASTUO-HYDRO-RENHACE-6-1-ECO-QUANTUM.md](docs/FALCON-X-CASTUO-HYDRO-RENHACE-6-1-ECO-QUANTUM.md) |
| **Planta Bioetanol 6.0** | Digital-Bio-Hub, gemelo biorreactor, grado aeronáutico, RED III. | [PLANTA-BIOETANOL-6-0-EXTREMADURA-DIGITAL-BIO-HUB.md](docs/PLANTA-BIOETANOL-6-0-EXTREMADURA-DIGITAL-BIO-HUB.md) |
| **Aetheris (nodo)** | Trifecta 3.0, PTM, Hydro-Renhace, gemelo + SOAR. | [AETHERIS-NODO-TRIFECTA-ENERGIA-3.md](docs/AETHERIS-NODO-TRIFECTA-ENERGIA-3.md) · [Ultra-Link](docs/protocolos/AETHERIS-ULTRA-LINK-PROTOCOL.md) · [PTM settlement](docs/AETHERIS-PTM-SETTLEMENT.md) |
| **BioPay / EnergyCredit** | Pago por calidad NIR; créditos energía PTM. | [BIOPAY-QUALITY-SMART-CONTRACT.md](docs/BIOPAY-QUALITY-SMART-CONTRACT.md) · `contracts/BioPayQualityV1.sol` · `EnergyCredit.sol` |
| **Nexus 5.0 + AR** | Nodo terrestre; dashboard AR operador. | [NEXUS-5-0-TRACTOR-AUTONOMO.md](docs/NEXUS-5-0-TRACTOR-AUTONOMO.md) · [INTERFACE-AR-NEXUS-CONTROL.md](docs/INTERFACE-AR-NEXUS-CONTROL.md) |
| **SAFE-EXIT 6.1** | Emergencia H₂, SOAR, EASA/MITECO, Nexus primera intervención. | [SAFE-EXIT-6-1-EMERGENCY.md](docs/protocolos/SAFE-EXIT-6-1-EMERGENCY.md) |
| **Blackout Recovery (OMEGA-SHIELD)** | Ghost-Mesh, cold recovery, navegación post-GPS, SOP. | [BLACKOUT-RECOVERY-SOP.md](docs/security/BLACKOUT-RECOVERY-SOP.md) |
| **Contratos endurecidos (CIPHER-LEVEL-5)** | BioPayV2 Pull, EnergyCredit Multisig, oráculo/PTM/PQC. | [contracts/HARDENED-LOGIC/](contracts/HARDENED-LOGIC/) |
| **Cuento Castúo y Sabionda** | Historias, mapa del tesoro, cómic 2040, scripts educativos; guía de instalación y manual transmedia. | [docs/cuento-castuo-sabionda/](docs/cuento-castuo-sabionda/README.md) · [Guía instalación](docs/cuento-castuo-sabionda/GUIA-INSTALACION-RAPIDA.md) · [Manual transmedia](docs/castuo-educacion-2040/README.md) · [scripts/educacion/](scripts/educacion/README.md) |
| **Manifiesto Castúo-System 1.0** | Visión, pilares soberanía, pitch, DESIGN FREEZE. | [MANIFESTO-CASTUO-SYSTEM-1-0.md](docs/MANIFESTO-CASTUO-SYSTEM-1-0.md) · [castuo_manifest/](castuo_manifest/) |

---

## 1. Requisitos de infraestructura y servicios externos

**Servicios externos**

| Servicio | Uso |
|---------|-----|
| **Mistral AI** | Cuenta y clave API para modelos de lenguaje. |
| **WhatsApp Business API** | Cuenta y acceso a la API para notificaciones. |
| **Notion** | Cuenta y clave API para bases de datos y trazabilidad. |
| **Gmail / SMTP** | Cuenta Gmail o servidor SMTP para envío de correos. |
| **LondBot** | Acceso a la API del bot especializado. |
| **Arsys** | Acceso a la API si se utiliza. |
| **Money** | Acceso a la API si se utiliza. |
| **Hetzner** | Servidor para desplegar la aplicación en producción. |

**Dominio y SSL**

- Un dominio registrado apuntando al servidor.
- Certificados SSL de Let's Encrypt (Certbot) para HTTPS.

---

## 2. Estructura de archivos y directorios

```
CASTUO-SYSTEM/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── dronica/
│   │   ├── missions.py
│   │   ├── connection.py
│   │   └── lora.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   ├── assets/
│   │   └── *.html
│   └── src/
│       └── components/
├── n8n/
│   ├── workflows/
│   │   ├── sabionda.json
│   │   ├── whatsapp_notifications.json
│   │   ├── email_notifications.json
│   │   ├── notion_integration.json
│   │   └── dronica_missions.json
│   └── Dockerfile
├── integrations/
│   ├── mistral/
│   ├── londbot/
│   ├── arsys/
│   ├── money/
│   └── dronica/
├── docker-compose.yml
├── docker-compose.prod.yml
├── nginx/
│   └── conf.d/
│       └── default.conf
├── .env
├── .env.example
└── README.md
```

---

## 3. Configuración de Docker y Nginx

**docker-compose.yml** (desarrollo)

- **api**: Construye el backend y expone el puerto 8000.
- **mqtt**: Eclipse Mosquitto para mensajería MQTT.
- **n8n**: Imagen oficial de n8n con volumen de workflows.
- **frontend**: Nginx sirviendo archivos estáticos (puerto 3000).
- **db**: PostgreSQL para datos persistentes.
- **qdrant**: Almacenamiento vectorial.

**docker-compose.prod.yml** (producción)

- **nginx**: Sirve el frontend, HTTP/HTTPS y proxy inverso a la API.
- **api**: Backend en modo producción (`ENVIRONMENT=production`).
- **certbot**: Obtención y renovación de certificados SSL (perfil `certbot`).

**nginx/conf.d/default.conf**

- Servidores HTTP (80) y HTTPS (443).
- Proxy inverso de `/api/` al backend (`http://api:8000/`).
- Ruta `/.well-known/acme-challenge/` para Certbot.

---

## 4. Backend

- **GET /** — mensaje de bienvenida.
- **POST /sensors/** — recibe datos de sensores (`sensor_id`, `temperature`, `humidity`, `light`).
- **GET /sabionda/recommendations** — recomendaciones Sabionda.
- **POST /sabionda/decide** — decisión agronómica (bandeja, pH, EC, O3).
- **POST /mistral/ask** — consulta a Mistral AI (`prompt`, `model` opcional).
- **POST /londbot/ask** — consulta a LondBot (`query`, `context` opcional).
- **POST /dronica/missions** — crea una misión de drone (`mission_id`, `drone_id`, `waypoints`).
- **GET /dronica/missions/{mission_id}** — estado de una misión.
- **GET /dronica/connection** — estado de la conexión (drones, gateway).
- **POST /lora/message** — recibe mensajes LoRaWAN (`device_eui`, `payload`, `gateway_id`).

CORS habilitado. Variables de entorno: ver `.env.example`.

---

## 5. Frontend

- Páginas HTML en `frontend/public/` (Tailwind + Font Awesome).
- `index.html` llama a `http://localhost:8000/sabionda/recommendations` al cargar.
- Componente React `frontend/src/components/GridIoT.jsx` (bandejas B001–B048).
- **sabionda-ia.html**: Interfaz para Sabionda IA (Mistral) y LondBot; en producción llama a `/api/mistral/ask` y `/api/londbot/ask`.
- **dronica.html**: Interfaz para misiones de drones y estado de conexión; llama a `/api/dronica/missions` y `/api/dronica/connection` en producción.

---

## 6. n8n (workflows)

Workflows en `n8n/workflows/`:

- **sabionda.json**: Webhook → API `/sensors/` → MQTT `sabionda/recommendations`; opcional Notion (crear página con `lot_id`/`action`).
- **whatsapp_notifications.json**: Webhook `whatsapp-webhook` → envío por WhatsApp Business API.
- **email_notifications.json**: Webhook `email-webhook` → envío por SMTP (Gmail).
- **notion_integration.json**: Webhook `notion-webhook` → crear página en Notion (`title`, `description`).

Importa los JSON en n8n (http://localhost:5678) y configura credenciales (Notion OAuth2, Gmail, WhatsApp, MQTT). Sustituye `YOUR_NOTION_DATABASE_ID` por el ID real de la base de datos en los workflows que usan Notion.

---

## 7. Variables de entorno

Copia `.env.example` a `.env` y rellena las credenciales:

```bash
cp .env.example .env
```

**.env**: Conexiones a servicios externos (Gmail, WhatsApp, Notion, Mistral, LondBot, Arsys, Money), credenciales de base de datos y APIs.  
**.env.example**: Plantilla para copiar a `.env` y rellenar con valores reales.

---

## 8. Comandos para ejecutar el proyecto

### Desarrollo local

Iniciar servicios localmente:

```bash
docker-compose up -d
```

- API: http://localhost:8000  
- Frontend (nginx): http://localhost:3000  
- n8n: http://localhost:5678  
- MQTT: 1883, 9001  
- PostgreSQL y Qdrant (volúmenes persistentes)

Ver solo el frontend (sin Docker):

```bash
cd frontend/public/
npx serve -p 3000
```

Abrir: http://localhost:3000/

### Comandos útiles

Ver logs de un servicio:

```bash
docker-compose logs -f api
```

Detener servicios:

```bash
docker-compose down
```

### Producción en Hetzner

Subir archivos al servidor (incluye `backend/` para poder construir la API):

```bash
scp -r frontend/public/ root@89.167.5.233:/frontend/
scp -r nginx/ root@89.167.5.233:/frontend/
scp -r backend/ root@89.167.5.233:/frontend/
scp docker-compose.yml docker-compose.prod.yml root@89.167.5.233:/frontend/
scp .env root@89.167.5.233:/frontend/
```

En el servidor:

```bash
ssh root@89.167.5.233
cd /frontend
mkdir -p certbot/www certbot/conf
docker-compose -f docker-compose.prod.yml up -d nginx api
```

Obtener certificados SSL (cuando el dominio apunte al servidor):

```bash
docker-compose -f docker-compose.prod.yml --profile certbot run --rm certbot
docker-compose -f docker-compose.prod.yml restart nginx
```

Renovar certificados:

```bash
docker-compose -f docker-compose.prod.yml --profile certbot run --rm certbot renew
```

Abrir: http://89.167.5.233/ (o https tras sustituir `tu-dominio.com` en `nginx/conf.d/default.conf`).

Para una guía paso a paso en Hetzner (CAX21, Dronica, Nginx /api, pruebas y troubleshooting), ver **[DEPLOY.md](DEPLOY.md)**. Monitorización (Prometheus + Grafana): **[MONITORING.md](MONITORING.md)**. Arquitectura v5.2 (stack, seguridad, Sabionda 3.0): **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**. Git avanzado con Cursor (hooks, trazabilidad GS1 EPCIS): **[docs/GIT-CURSOR.md](docs/GIT-CURSOR.md)**. Workflow enterprise Git + BioCoin Castúo (hooks TX, Grafana, GitHub Actions, smart contract): **[docs/CASTUO_GIT_BIOCOIN.md](docs/CASTUO_GIT_BIOCOIN.md)**. Cumplimiento legal (España BOE, SII Facturae, Europa GS1 EPCIS, AI Act): **[docs/COMPLIANCE-LEGAL.md](docs/COMPLIANCE-LEGAL.md)**. Arquitectura integrada CRM+ERP+LEGAL (Odoo + Nextcloud + EPCIS + BioCoin): **[docs/ODOO-CRM-ERP-LEGAL.md](docs/ODOO-CRM-ERP-LEGAL.md)**. Drones, IoT, riego, energía, chatbot y voz: **[docs/ARQUITECTURA-DRONES-IOT-VOZ.md](docs/ARQUITECTURA-DRONES-IOT-VOZ.md)**. Robótica agrícola, tokenización de activos, materiales compuestos y modo offline 72h: **[docs/INTEGRACION-AVANZADA.md](docs/INTEGRACION-AVANZADA.md)**. Extrusora de bio-compuestos (Arduino + MQTT) y módulo Odoo Materials: **[docs/EXTRUSORA-MATERIALES.md](docs/EXTRUSORA-MATERIALES.md)**. Estrategias de escalado: **[ESCALADO.md](ESCALADO.md)**.

---

## 9. Interacción con Sabionda

- **Frontend**: En desarrollo obtiene recomendaciones con `fetch('http://localhost:8000/sabionda/recommendations')`. En producción usa `/api/sabionda/recommendations` y Nginx hace proxy a `http://api:8000/sabionda/recommendations`.
- **n8n**: Envía datos de sensores a `POST /sensors/` y reenvía resultados por MQTT.

En producción, el frontend llama a `/api/mistral/ask` y `/api/londbot/ask`; Nginx reenvía a `http://api:8000/mistral/ask` y `http://api:8000/londbot/ask`.

---

## 10. Notas importantes

- **Variables de entorno**: Configura `.env` en el servidor con las credenciales reales. No subas `.env` al repositorio (está en `.gitignore`).
- **Certificados SSL**: Sustituye `tu-dominio.com` por tu dominio real en `nginx/conf.d/default.conf`.
- **Notion**: En los workflows de n8n que usan Notion, sustituye `YOUR_NOTION_DATABASE_ID` por el ID real de la base de datos.

---

## 11. Resumen de integraciones

| Integración | Uso |
|-------------|-----|
| **Mistral AI** | Recomendaciones avanzadas y consultas de lenguaje. |
| **WhatsApp Business** | Notificaciones y alertas a usuarios. |
| **Notion** | Registro y gestión de datos de trazabilidad. |
| **Gmail / SMTP** | Envío de correos electrónicos. |
| **LondBot** | Respuestas de un bot especializado (cultivos, fertilizantes, etc.). |
| **Arsys** | Integraciones adicionales según necesidades. |
| **Money** | Integraciones adicionales según necesidades. |
| **Dronica / LoRaWAN** | Misiones de drones, CASTUO-Gate y mensajes LoRaWAN. |

Con esta arquitectura, CASTUO-SYSTEM queda integrado con los servicios y plataformas indicados.

---

## 12. Dronica

Módulo para la gestión de misiones de drones, conexión LoRaWAN y CASTUO-Link.

**Endpoints**

- **POST /dronica/missions**: Crea una nueva misión para un drone.
- **GET /dronica/missions/{mission_id}**: Obtiene el estado de una misión.
- **POST /lora/message**: Recibe mensajes LoRaWAN.
- **GET /dronica/connection**: Obtiene el estado de la conexión (drones, gateway).

**Workflows n8n**

- **dronica_missions.json**: Webhook `dronica-mission-webhook` → API → MQTT `dronica/missions` → opcional Notion (log de misiones). Sustituye `YOUR_NOTION_DATABASE_ID` en el nodo Notion.

**Frontend**

- **dronica.html**: Interfaz para crear misiones, ver estado de la conexión y consultar el estado de una misión.

**Ejemplo de uso**

```bash
# Crear una misión
curl -X POST "http://localhost:8000/dronica/missions" \
  -H "Content-Type: application/json" \
  -d '{"mission_id": "mission_001", "drone_id": "drone_001", "waypoints": [{"lat": 40.416775, "lng": -3.703790}]}'

# Ver el estado de una misión
curl -X GET "http://localhost:8000/dronica/missions/mission_001"
```

---

## 13. LoRaWAN y CASTUO-Link

Integración con LoRaWAN para comunicación con sensores remotos y CASTUO-Link para la conexión de drones.

**Configuración**

- **Broker MQTT**: `mqtt://mqtt:1883` (variable `DRONICA_MQTT_BROKER`).
- **Topics**: `dronica/missions` para misiones; `lora/messages` para mensajes LoRaWAN (variable `DRONICA_MQTT_TOPIC`).

**Ejemplo de uso**

```bash
# Enviar un mensaje LoRaWAN
curl -X POST "http://localhost:8000/lora/message" \
  -H "Content-Type: application/json" \
  -d '{"device_eui": "1234567890", "payload": "{\"temperature\": 25, \"humidity\": 60}", "gateway_id": "CASTUO-Gate-001"}'
```

---

## 14. CASTUO-Gate

Gateway para la conexión de dispositivos LoRaWAN y drones.

**Configuración**

- **Conexión MQTT**: `mqtt://mqtt:1883`
- **Topics**: `dronica/missions` (misiones de drones) y `lora/messages` (mensajes LoRaWAN).

---

## Windows/PowerShell Quickstart (THC)

### Requisitos previos

- PowerShell 5.1+ (Windows 10/11).
- `pytest` disponible en entorno Python activo.
- `bash` disponible (Git Bash o WSL) para scripts `.sh`.

### Comandos rapidos

```powershell
# Tests THC
.\scripts\thc.ps1 test-thc

# Validacion de flujo THC (backend en localhost:8000)
.\scripts\thc.ps1 validate-thc

# Backup THC
.\scripts\thc.ps1 backup-thc

# Ayuda
.\scripts\thc.ps1 help
```

### Solucion de problemas

| Problema | Solucion |
|---|---|
| `pytest` no encontrado | `pip install pytest` |
| `bash` no reconocido | Instalar Git Bash o WSL |
| Error de conexion a DB | Verificar stack con `docker-compose ps` |
| Bloqueo de scripts PowerShell | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
