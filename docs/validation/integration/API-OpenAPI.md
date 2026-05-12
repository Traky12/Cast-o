# Documentación API — REST/gRPC, OpenAPI 3.0

**Estándar**: ETSI (interoperabilidad). OpenAPI 3.0, validación con Postman/Swagger.

---

## Uso

- **Swagger UI**: `https://[host]/docs` (FastAPI).
- **ReDoc**: `https://[host]/redoc`.
- **OpenAPI JSON**: `https://[host]/openapi.json`.

---

## Principales grupos de endpoints

| Prefijo | Descripción |
|---------|-------------|
| `/cannabis` | Certificación AEMPS, lotes cannabis |
| `/microgreens` | Certificación GlobalGAP, lotes microgreens |
| `/blockchain` | Registro en GaiaChain, sync pendientes |
| `/iot` | WebSocket sensores, ingesta datos |
| `/ue` | Calibración UE, cumplimiento, usabilidad |
| `/sync` | Sincronización LIMS CTAEX |
| `/reports` | KPIs, informes, blockchain pending |

---

## Autenticación (objetivo)

- **OAuth 2.0** para terceros (distribuidores UE): Authlib. Ver `OAuth-Guide.md`.
- **API Key** o JWT para integraciones internas (CTAEX).

---

## EDI (GlobalGAP)

- Soporte **EDI X12** o **UN/EDIFACT** con conector Python (python-edi). Ver `EDI-Guide.md`.
