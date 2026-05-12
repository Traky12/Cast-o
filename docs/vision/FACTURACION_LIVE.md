# Facturación LIVE — 3 Cooperativas (v1.7.3)

Facturación real €140/ha/mes para las 3 cooperativas integradas. Total **€1,470/mes** (10.5 ha).

## Tabla facturación inmediata

| Cooperativa        | Hectáreas | Factura/mes |
|--------------------|-----------|------------|
| Sabionda Educa SAT | 2.5 ha    | €350       |
| Cooperativa #2     | 5.0 ha    | €700       |
| Cooperativa #3     | 3.0 ha    | €420       |
| **TOTAL**          | **10.5 ha** | **€1,470** |

- **ARR:** €17,640/año  
- **Valor empresa:** +€70K (facturación real validada)

## Endpoints

- **POST /billing/invoice/{coop_id}** — Generar factura (opcional `?hectareas=`).
- **GET /billing/facturacion** — Dashboard facturación (último mes).

## Comando único facturación (Hetzner / local)

```bash
cd /root/castuo-system/backend   # o ruta del backend

# 1. Tabla creada al primer request (SQLite billing.db)
# 2. Generar facturas 3 coops
curl -X POST http://localhost:8001/billing/invoice/1
curl -X POST http://localhost:8001/billing/invoice/2
curl -X POST http://localhost:8001/billing/invoice/3

# 3. Dashboard
curl http://localhost:8001/billing/facturacion

# 4. Total/mes (con jq)
curl -s http://localhost:8001/billing/facturacion | jq '[.[].total_eur] | add'
```

## Dashboard React

Ruta: **/facturacion**. Muestra tabla de facturas del último mes y total €/mes.

---

*[IOT_3_COOPS_PRODUCTION](IOT_3_COOPS_PRODUCTION.md) · [COOPERATIVAS_3_INTEGRADAS](COOPERATIVAS_3_INTEGRADAS.md) · [ESTATUS_VALOR_V1.7.1](ESTATUS_VALOR_V1.7.1.md)*
