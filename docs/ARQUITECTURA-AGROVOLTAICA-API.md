# Arquitectura API Agrivoltaica (CTAEX / Castúo)

Documento técnico de referencia: núcleo modular, estrategias de cálculo, contratos y auditoría.

## Capas

| Capa | Módulo | Rol |
|------|--------|-----|
| **Núcleo** | `backend.agrivoltaic` | `SensorNormalized`, Adapter de payload, Strategy demo / UNE 216701 |
| **Métricas demo** | `backend.agrivoltaic.strategies.DemoAgrivoltaicStrategy` | Métricas orientativas hasta certificación normativa |
| **Métricas UNE** | `backend.agrivoltaic.strategies.UNE216701AgrivoltaicStrategy` | Anclaje para fórmulas oficiales CTAEX (`_une216701_official`) |
| **Storefront** | `backend.shopware_adapter` | Facade Shopware; `LegacyAgrivoltaicRequest` + `build_agrivoltaic_analysis` |
| **Federated** | `backend.federated.routes` | 202 Accepted + auditoría; `AnalysisRequest` ampliado |
| **Reexport** | `backend.agrivoltaic_metrics` | Compatibilidad: `compute_demo_metrics` |

## Puntos de entrada HTTP

| Ruta | Método | Éxito | Validación |
|------|--------|-------|------------|
| `POST /api/analyze` | JSON | 200 + cuerpo análisis | Normalización en núcleo; errores → **400** `AUD-AGRO-PAYLOAD` |
| `POST /storefront/agrivoltaic/analyze` | JSON | 200 | Pydantic opcional + Adapter; mismo comportamiento legacy |
| `POST /federated/agrivoltaic/analyze` | JSON | **202** + `AnalysisResponse` | `AnalysisRequest`; payload corrupto → **400** + audit |

## Payload unificado (Adapter)

El adaptador (`normalize_agrivoltaic_payload`) fusiona sin intervención del cliente:

- **Legacy**: `sensores.{ solar, humedad, temperatura, … }`
- **Federated**: `solar_exposure` + `sensors_data` (dict o lista)
- **Claves alternativas**: `humidity`, `temperature`, `temp`, `wind_speed`, `irradiancia_wm2`, `soil_moisture`, `panel_tilt_deg`, `albedo`
- **Lista posicional**: `[GHI, humedad, temp]` o `[humedad, temp]` si GHI viene en `solar_exposure`

## UNE 216701

- **Activación**: `CASTUO_UNE216701_IMPLEMENTED=true` **o** `UNE_216701_IMPLEMENTED = True` en `backend/federated/routes.py`.
- **Implementación**: sustituir el cuerpo de `UNE216701AgrivoltaicStrategy._une216701_official` por las fórmulas del anexo CTAEX; los campos de entrada ya incluyen viento, irradiancia, suelo e inclinación para ecuaciones normativas.
- **Salida certificable**: `FederatedMetricsEnvelope` con `source=une216701`, `certifiable=True`, `normative_ref` acorde al anexo.

## Códigos de auditoría (errores agrivoltaicos)

| Código | HTTP | Cuándo |
|--------|------|--------|
| `AUD-AGRO-PAYLOAD` | 400 | Datos incoherentes (Adapter / núcleo) |
| `AUD-AGRO-VAL` | 400 | Validación Pydantic en rutas agrivoltaicas (`/federated/agrivoltaic`, etc.) |
| `AUD-{hash}` | 500 | Resto (handler global existente) |

Las respuestas **202** del flujo federado **no** indican error: confirman aceptación del proceso asíncrono.

## Schemas OpenAPI

- `backend.federated.schemas.AnalysisRequest` / `AnalysisResponse`
- `backend.shopware_adapter.LegacyAgrivoltaicRequest` (uso interno + documentación implícita en storefront)

## Geotermia (sinergia híbrida)

- `AnalysisRequest`: `ground_temperature_10m`, `heat_pump_status`, `delta_t_fluid` (opcionales).
- Métricas extendidas: `cop_geothermal`, `solar_surplus_kw_est`, `prioritize_geothermal_exchanger`, `osmosis_inlet_advisory`, `lue_land_use_efficiency`.
- Triángulo Solar + Agua + Geotermia: `docs/ARQUITECTURA-SISTEMA.md`.

## Referencia

- `docs/ACUERDO-COOPERACION-CTAEX-CASTUO.md`
- `docs/ARQUITECTURA-SISTEMA.md`

## Relacion con el prototipo piloto Extremadura
- `docs/ops/pilotos/extremadura-agrovoltaica-terracota-2026.md`
- `docs/ops/pilotos/ctaex-acuerdo-prototipo-agrovoltaica-terracota.md`
