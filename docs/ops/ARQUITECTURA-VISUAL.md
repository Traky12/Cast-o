# Arquitectura Visual CASTUO-SYSTEM

```mermaid
flowchart LR
  subgraph Campo[Campo IoT]
    sensors[Sensores IoT]
    mqtt[MQTT Mosquitto]
  end

  subgraph Orq[Orquestacion y Backend]
    n8n[n8n Workflows]
    api[FastAPI]
    sabionda[Sabionda IA]
    mistral[Mistral AI]
  end

  subgraph Datos[Persistencia y Trazabilidad]
    tsdb[TimescaleDB/PostgreSQL]
    ipfs[IPFS]
    gaia[GaiaChain]
  end

  subgraph Front[Canales de salida]
    wp[WordPress]
    grafana[Grafana]
  end

  sensors --> mqtt --> n8n --> api
  api <--> sabionda
  sabionda <--> mistral
  api --> tsdb
  api --> ipfs
  api --> gaia
  n8n --> wp
  tsdb --> grafana
```

## Capas
- Campo IoT: captura y transporte de telemetria.
- Orquestacion: automatizacion (n8n) y servicios API/IA.
- Datos: almacenamiento operativo y trazabilidad inmutable.
- Frontales: publicacion (WordPress) y observabilidad (Grafana).

## Archivos Relacionados
- Terraform Hetzner: `hetzner_infra/main.tf`
- Variables Terraform: `hetzner_infra/variables.tf`
- Workflow n8n Mistral->WordPress: `n8n/workflows/mistral-wordpress-report.json`
- Runbook conectividad: `docs/ops/HUB-CONNECTIVIDAD.md`
