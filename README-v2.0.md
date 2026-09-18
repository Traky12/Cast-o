# CASTÚO-SYSTEM™ v2.0 — Agente SABIONDA

## Descripción del Proyecto

CASTÚO-SYSTEM™ es la **plataforma autónoma de gestión rural** de **CASTÚO 360 S.L.**, impulsada por **SABIONDA**, un agente de IA basado en OpenClaw RAG que gestiona:

- **Ganadería y cultivos** con inteligencia artificial
- **Automatización de trámites** con administraciones públicas
- **Cumplimiento normativo automático** (UE, España)
- **100% legal y auditado** con trazabilidad blockchain

## Arquitectura del Sistema

```mermaid
graph TD
    A[CASTÚO-SYSTEM] --> B[SABIONDA AI Core]
    A --> C[OpenClaw RAG]
    A --> D[n8n Workflows]
    A --> E[PostgreSQL 16]
    A --> F[FastAPI]
    A --> G[LoRaWAN]
    B --> H[Holographic UI]
    C --> I[Document Engine]



Componentes principales:

SABIONDA AI Core: Motor de inteligencia artificial con modelos Mistral
OpenClaw RAG: Sistema de recuperación y generación de documentos
n8n: Automatización de flujos de trabajo
PostgreSQL 16: Base de datos con soporte para grandes volúmenes de datos agrícolas
FastAPI: Backend para integración con sistemas gubernamentales
LoRaWAN: Conexión con sensores IoT en el campo
Características Principales
 Gestión Ganadera Avanzada

50+ razas soportadas (Retinta, Avileña, Duroc, Ibérico, etc.)
Monitoreo animal con sensores IoT
Cumplimiento normativo automático (GRASP, ISO 14001)
 Gestión de Cultivos Inteligente

Control de riego y fertilización con algoritmos predictivos
Integración GlobalGAP 5.4 para cultivos premium
Optimización de invernaderos (CO₂, VPD, pH)
 Sistema de Riego Autónomo

Sensores de humedad en tiempo real
Fertigación automatizada con control de nutrientes
Protocolos de ahorro hídrico
 Generación de Documentos Gubernamentales
python
Copiar

# Documentos generados automáticamente:
- SIEX Cuaderno de Campo Digital
- Certificados TRACES para exportación
- Declaraciones PAC 2026
- Registros SIGPAC y REGEPA
- Certificados GlobalGAP/GRASP



Inicio Rápido
Requisitos Previos

Docker y Docker Compose
Git
16GB RAM recomendados
Configuración
bash
Copiar

# Clonar repositorio
git clone https://github.com/Traky12/Castuo-system.git
cd Castuo-system

# Configurar entorno
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar sistema
docker compose up -d



Verificación
bash
Copiar

# Verificar estado
curl http://localhost:8000/health
# Respuesta esperada: {"status":"ok","agent":"SABIONDA","version":"2.0"}



Estructura del Proyecto
text
Copiar

.
├── agents/sabionda/       # Configuración del agente
│   ├── system-prompt.md   # Prompt del sistema
│   └── config.json        # Configuración
├── api/                   # Backend FastAPI
│   ├── main.py            # Endpoints
│   └── schemas/           # Esquemas JSON
├── workflows/            # Automatizaciones n8n
├── config/               # Configuraciones
├── docker-compose.yml     # Despliegue
└── README.md              # Documentación



Endpoints de API


  
    
      Método
      Ruta
      Descripción
    
  
  
    
      GET
      /health
      Estado del sistema
    
    
      POST
      /api/v1/siex/cuaderno-campo
      Generar cuaderno de campo SIEX
    
    
      POST
      /api/v1/traces/certificado
      Generar certificado TRACES
    
    
      POST
      /api/v1/pac/eco-esquema
      Generar eco-esquemas PAC
    
    
      GET
      /api/v1/schemas/{name}
      Obtener esquema JSON
    
  


Legal y Cumplimiento
Todos los documentos siguen este proceso:

Generación por el agente (JSON estructurado)
Revisión por el agricultor
Firma digital del productor
Envío a sistemas oficiales
 Cada documento incluye:

"Documento generado para REVISIÓN y FIRMA del productor"

Licencia

Código: AGPL-3.0
Documentación: CC-BY-SA-4.0
Datos: No compartibles (protegidos)


"Cultivamos tecnología para alimentar el futuro"

## Integración con Claude Code

Para conectar Claude Code con todo el sistema, usa la nueva capa unificada en FastAPI:

- `GET /api/v1/claude/tools`: catálogo de herramientas disponibles (documentales, RAG e IoT declaradas).
- `GET /api/v1/claude/context`: contexto del agente SABIONDA (capacidades, cumplimiento y prompt de sistema).
- `POST /api/v1/claude/execute/{tool_name}`: ejecución unificada de funciones documentales.

### Ejemplo: descubrir herramientas

```bash
curl http://localhost:8000/api/v1/claude/tools
```

### Ejemplo: ejecutar SIEX desde Claude Code

```bash
curl -X POST http://localhost:8000/api/v1/claude/execute/generate_siex_cuaderno \
    -H "Content-Type: application/json" \
    -d '{
        "payload": {
            "explotacion": {"rea": "EX123456", "titular": "Finca Demo", "nif": "12345678A"},
            "parcelas": [{"sigpac_ref": "10:20:0:0:1:1:1", "superficie_ha": 12.5, "cultivo": "trigo"}],
            "tratamientos": []
        }
    }'
```

### Variables de entorno relevantes (docker compose)

El servicio `fastapi` ya queda preparado para Claude con:

- `AGENT_CONFIG_PATH=/app/agents/sabionda/config.json`
- `AGENT_PROMPT_PATH=/app/agents/sabionda/system-prompt.md`

Y con montaje de volumen:

- `./agents:/app/agents:ro`

## Promotion closure / Cierre de promoción

The current CASTÚO posture remains **`PROMOTION = BLOCK` / `LOCAL_RESULT_NO_CLAIM`** until the bounded S-001A slice has an executable contract, portable evidence envelope, independent replay, human review and rollback evidence.

La ruta priorizada, los gaps, los riesgos P0 y los gates de salida están documentados en [`docs/CASTUO_PROMOTION_CLOSURE_PLAN.md`](docs/CASTUO_PROMOTION_CLOSURE_PLAN.md). Este repositorio debe conservar estados evidence-scoped y no elevar `LOCAL`, `PENDING` o `EVIDENCE_REQUIRED` a claims de producción, independencia de proveedor o validación independiente.

