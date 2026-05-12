# CASTÚO-SYSTEM™ v2.0 — Agente SABIONDA

## Project Description

CASTÚO-SYSTEM™ is the autonomous rural management platform by **CASTÚO 360 S.L.**
It is powered by **SABIONDA**, an AI agent built on OpenClaw RAG that manages livestock, crops, irrigation, and government document generation for Spanish agricultural holdings — 100% legal and compliant.

## Architecture

```
docker-compose:
├── openclaw-agente   (SABIONDA AI agent — OpenClaw RAG)
├── n8n               (workflow automation, webhooks, LoRaWAN)
├── postgres           (PostgreSQL 16 — farm data, 150ha+)
├── fastapi            (APIs: SIEX, TRACES, SIGPAC, REGEPA, PAC)
└── lorawan-gateway    (TTN — IoT sensors)
```

## Features

- **Livestock management**: Retinta, Avileña (vacuno); Duroc, Ibérico (porcino); Manchega, Churra (ovino/caprino); GRASP welfare for poultry/apiculture.
- **Crop management**: Dryland (wheat/olive/vineyard), irrigated (tomato/pepper), greenhouse (CO₂, VPD, pH control), fruit (GlobalGAP 5.4).
- **Irrigation**: Tensiometers, flow meters, fertigation, deficit drip.
- **Government document generation** (JSON → PDF, firmable):
  - SIEX Cuaderno de Campo Digital
  - SIGPAC parcelas
  - TRACES certificados sanitarios
  - REGEPA explotaciones
  - PAC 2026 eco-esquemas
  - GlobalGAP / GRASP / ISO 14001
  - Libro fitosanitario (RD 1311/2012)
- **Real-time alerts**: Fever detection (>39.4 °C), humidity-based auto-irrigation, sensor anomaly reporting.
- **Compliance**: PAC 2023-2027, AI Act EU, RGPD, RD 285/2023, SIEX digital 2027.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Setup

```bash
git clone https://github.com/Traky12/Castuo-system.git
cd Castuo-system
cp .env.example .env
# Edit .env with your passwords and API URLs
docker compose up -d
```

### Verify

```bash
# Check the API health
curl http://localhost:8000/health
# Expected: {"status":"ok","agent":"SABIONDA","version":"2.0"}
```

## Project Structure

```
.
├── agents/sabionda/       # SABIONDA agent configuration
│   ├── system-prompt.md   # Full system prompt
│   └── config.json        # Agent capabilities & compliance config
├── api/                   # FastAPI backend
│   ├── main.py            # API endpoints (SIEX, TRACES, PAC)
│   ├── Dockerfile
│   └── requirements.txt
├── config/schemas/        # JSON Schemas for gov documents
│   ├── siex.schema.json
│   ├── traces.schema.json
│   ├── pac.schema.json
│   ├── sigpac.schema.json
│   └── regepa.schema.json
├── docker-compose.yml     # Full stack deployment
├── .env.example           # Environment variable template
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/siex/cuaderno-campo` | Generate SIEX field notebook |
| `POST` | `/api/v1/traces/certificado` | Generate TRACES health certificate |
| `POST` | `/api/v1/pac/eco-esquema` | Generate PAC eco-scheme submission |
| `GET` | `/api/v1/schemas/{name}` | Retrieve JSON schema |

## Legal & Compliance

All generated documents follow the legal process:

1. **Agent generates** → structured JSON payload
2. **Farmer reviews** → validates content
3. **Farmer signs** → digital signature
4. **Upload** → via official API (SIEX, TRACES, SIGPAC)

> ⚠️ Every document includes: _"Documento generado para REVISIÓN y FIRMA del productor"_

## License

For detailed documentation, refer to the [Wiki](https://github.com/Traky12/castuo-system/wiki).