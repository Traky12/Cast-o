# Soberanía Tecnológica — Castuo-System y Brújula Digital UE 2030

Este documento detalla cómo Castuo-System se alinea con las directrices de la **Brújula Digital de la UE 2030** y con un **stack europeo y abierto**, apto para fondos de innovación (Horizon Europe) y certificaciones UNE 216701.

---

## 1. Stack europeo y abierto adoptado

| Función | Componente | Origen / ventaja |
|--------|------------|-------------------|
| **Series temporales / telemetría** | QuestDB | Alemania. Alta velocidad para sensores NPK y geotermia. |
| **Orquestación de datos / IoT** | FIWARE (NGSI-LD) | España/UE. Estándar Smart Cities y Smart Agrifood. |
| **Visualización** | Grafana (Open Source) / Streamlit+Plotly | Suecia / stack Python. Referencia en telemetría técnica. |
| **Comunicación sensores** | Eclipse Mosquitto (MQTT) | Fundación Eclipse (Europa). Ligero y auditable. |
| **Predicción / ML** | Scikit-Learn / PyTorch | Inria (Francia). Frameworks abiertos. |
| **Clima** | Open-Meteo | Alemania. Datos meteorológicos abiertos sin API key comercial. |
| **Autenticación** | Keycloak (Open Source) | Red Hat / comunidad. Control de acceso al dashboard en servidores propios. |

---

## 2. Estandarización FIWARE (NGSI-LD)

El **system_orchestrator** y los sensores (pH, NPK, geotermia, solar) están preparados para modelarse como **Entidades NGSI-LD** compatibles con el Context Broker de FIWARE:

- Cada sensor es una entidad con `type`, `id`, atributos con `value` y `observedAt`.
- Las actuaciones (válvula NPK, bomba de calor, inyección O₃) pueden publicarse como entidades de tipo `Actuator` con estado y causa raíz en metadatos.

Esto permite:

- **Interoperabilidad** con otros sistemas (tractores inteligentes, Copernicus/ESA, estaciones meteorológicas locales).
- **Transparencia** en auditorías UNE 216701: no hay “cajas negras” en el procesamiento.

---

## 3. Base de datos QuestDB

La telemetría de alta frecuencia (ósmosis, riego, NPK, geotermia) puede almacenarse en **QuestDB** en lugar de logs en archivo plano:

- Inserción por lotes y consultas SQL sobre series temporales.
- Conexión desde `system_orchestrator` o un módulo `backend/telemetry/questdb_client.py` que persista ciclos de control y eventos de auditoría.

---

## 4. Seguridad soberana (Keycloak)

El **Dashboard de telemetría** (`dashboard/telemetry_app.py`) y las APIs de control pueden protegerse con **Keycloak**:

- Los datos de la finca permanecen en servidores controlados por el operador o CTAEX.
- Sin dependencia de identidad comercial de terceros para el control operativo.

---

## 5. Open-Meteo para clima

Sustitución de APIs de clima propietarias por **Open-Meteo** (Alemania):

- Datos meteorológicos precisos y abiertos.
- Integración en el orquestador para evapotranspiración y predicción solar/sombras (UNE 216701).

---

## 6. Independencia y portabilidad

- **Docker Compose**: todo el sistema (API, orquestador, dashboard, QuestDB, Mosquitto, Keycloak opcional) puede desplegarse en cualquier proveedor de hosting europeo (OVHcloud, Hetzner, etc.).
- **Sin vendor lock-in**: componentes open source sustituibles y auditables.

---

## 7. Resumen de cumplimiento

| Directriz UE / Objetivo | Cumplimiento en Castuo-System |
|-------------------------|-------------------------------|
| Infraestructura de datos europea | FIWARE NGSI-LD, QuestDB, Open-Meteo |
| Control y soberanía de datos | Keycloak, despliegue en servidores propios/UE |
| Transparencia y auditoría | Logs de auditoría con causa raíz, trazabilidad UNE 216701 |
| Interoperabilidad | Entidades estándar, APIs documentadas, MQTT |
| Innovación y I+D | Candidato a Horizon Europe; stack abierto y documentado |

---

## Referencias

- Brújula Digital 2030 (UE).
- FIWARE: https://www.fiware.org/
- QuestDB: https://questdb.io/
- Open-Meteo: https://open-meteo.com/
- Keycloak: https://www.keycloak.org/
