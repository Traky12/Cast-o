# Demo gemelo digital — ICEX HLTH Europe (TRL de feria)

## Que es esto

Pipeline **demostrable** en el repo: ingest JSON → witness opcional (GaiaChain minimal) → certificado HTML/PDF → factura XML/PDF de **demo**.

No sustituye:

- certificación **TRL** emitida por tercero,
- **FacturaE** validada AEAT,
- **eIDAS** alto ni **99,99%** SLO sin informes de explotación.

## Arquitectura (flujo)

```mermaid
graph LR
  S[Fuentes / curl] -->|POST JSON| I[/agents/gemelo/ingest]
  I --> W[witness_minimal]
  I --> C[cert PDF/HTML]
  I --> F[factura demo PDF/XML]
  I --> R[respuesta JSON URLs]
```

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/agents/gemelo/ingest` | Cuerpo: `agent_type`, `sensor_data`, opc. `customer`, `generate_invoice` |
| GET | `/agents/gemelo/dashboard` | Página HTML con instrucciones |
| GET | `/agents/gemelo/artifacts/certificate/{id}.html` | Certificado HTML |
| GET | `/agents/gemelo/artifacts/certificate/{id}.pdf` | PDF si ReportLab disponible |
| GET | `/agents/gemelo/artifacts/invoice/{archivo}` | `.pdf` o `.xml` demo |

## Variables

| Variable | Efecto |
|----------|--------|
| `DEMO_TRL101_DATA_DIR` | Directorio base (por defecto `data/demo_trl101/` en la raíz del repo) |
| `GAIA_CHAIN_API_KEY` | Si existe, witness POST; si no, hash calculado y log local |
| `GAIA_CHAIN_API_URL` | URL witness (ver `witness_minimal.py`) |

`coop_id` demo: **CASTUO-DEMO-01**.

## Ejecución local

```bash
cd /ruta/al/Castuo-System
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Dashboard: `http://127.0.0.1:8000/agents/gemelo/dashboard`

## Evidencias para auditor

1. Exportar logs de API y métricas Prometheus del entorno **real** de la feria.
2. Conservar ZIP de `DEMO_TRL101_DATA_DIR` tras la demo.
3. No afirmar cumplimiento normativo en marketing sin informe jurídico/fiscal.

## Código

- `backend/demo_trl101/` — router, generadores, rutas de artefactos
- `backend/routers/agents.py` — montaje bajo `/agents/gemelo`
- `tests/test_demo_trl101_ingest.py` — pruebas básicas

## Scripts

- `scripts/demo/icex_hlth_demo.ps1` (Windows)
- `scripts/demo/icex_hlth_demo.sh` (Unix)
