# Auditoría Energética con Satélites

*(Sistema integrado con Castúo-System | 2026 | Autor: Gregorio Julian Jimenez Bodes)*

## Estructura del proyecto

```text
docs/ops/energy-audit/
├── AUDITORIA-ENERGETICA-SATELITE-CASTUO-2026.md
├── examples/
│   └── energy_audit_report.example.json
├── requirements-extra.txt
└── README.md
```

## Requisitos

Desde esta carpeta:

```bash
pip install -r requirements-extra.txt
```

*(Apunta a `backend/energy_audit/requirements-extra.txt`.)*

Desde la raíz del repositorio:

```bash
pip install -r backend/energy_audit/requirements-extra.txt
```

Variables opcionales Copernicus:

```bash
export COPERNICUS_USER="tu_usuario"
export COPERNICUS_PASSWORD="tu_contraseña"
```

Witness (opcional): `GAIA_CHAIN_API_KEY`, `GAIA_COOP_ID`.

## Backend

| Módulo | Descripción | Uso |
|---|---|---|
| `satellite_preprocess.py` | Sentinel-2/3 (NDVI, albedo). | `python -m backend.energy_audit.satellite_preprocess --zip archivo.zip --product_id ...` |
| `digital_twin_energy.py` | Gemelo 4D / eficiencia energética. | `from backend.energy_audit.digital_twin_energy import EnergyAuditTwin` |
| `osint_energy.py` | Precios y políticas (mock). | `from backend.energy_audit.osint_energy import EnergyOSINT` |
| `witness_minimal.py` | GaiaChain opcional (`GAIA_CHAIN_API_KEY`). | `from backend.energy_audit.witness_minimal import witness_event` |

## Frontend

| Archivo | Descripción |
|---|---|
| `digital_twin_viewer.html` | Visualizador 3D con Three.js r128. |
| `mock_twin_data.json` | Datos de ejemplo para pruebas locales. |

## Scripts

| Script | Descripción | Uso |
|---|---|---|
| `Register-EnergyAudit.sh` | Notariza informes en GaiaChain. | `bash scripts/energy_audit/Register-EnergyAudit.sh docs/ops/energy-audit/examples/energy_audit_report.example.json` |

*(Con CWD en `docs/ops/energy-audit/`: `bash ../../../../scripts/energy_audit/Register-EnergyAudit.sh examples/energy_audit_report.example.json`.)*

## Documentación principal

[`AUDITORIA-ENERGETICA-SATELITE-CASTUO-2026.md`](AUDITORIA-ENERGETICA-SATELITE-CASTUO-2026.md)
