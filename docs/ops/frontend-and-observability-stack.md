# Frontend y observabilidad sobre n8n (stack OSS recomendado)

n8n actúa como **orquestación y lógica**; las interfaces para técnicos, ejecutivos y auditores pueden vivir en capas **separadas** que consumen las mismas fuentes de verdad (Postgres, webhooks, journal Markdown). Este documento resume opciones **open source** habituales y cómo encajan con CASTÚO; **no** incluye compose de producción en el repo hasta que elijas imágenes y redes definitivas.

---

## 1. Contexto en el repositorio actual

| Capa | En repo hoy |
|------|-------------|
| Orquestación | `docker-compose.multi-n8n.yml`, workflows bajo `n8n/workflows/` |
| Postgres (operativo / cerebros) | `docker-compose.cerebros.yml`, puerto host típico **5433** |
| Auditoría texto (journal) | Trillizo = n8n + volumen `cerebros/auditoria` + workflow `01-trillizo-auditoria-basica.json` |
| Integridad POST auditoría | HMAC opcional: `CASTUO_AUDIT_WEBHOOK_SECRET`, `scripts/n8n/sign_audit_webhook_body.py` |
| SQL de actas (opcional) | `n8n/sql/schema_auditoria_trillizo.sql` (no insertado automáticamente por el workflow 01) |

**Aclaración:** “Trillizo” en este proyecto **no** es sinónimo de “solo Postgres”; el journal principal hoy es **Markdown**. Postgres agrega telemetría, tablas de negocio y, si lo cableas, `trillizo_audit_log`.

---

## 2. Panel de control y formularios (Appsmith, ToolJet, Budibase…)

**Rol:** CRUD, botones, tablas y flujos internos (técnicos, sala de control).

**Integración típica:**

- **REST** contra webhooks n8n (p. ej. rutas del gateway `castuo_main_orchestrator_gateway.json` o webhooks dedicados a “manual override”).
- **Postgres** en solo lectura o con cuidado en escritura (evitar saltarse reglas OT; preferir *siempre* pasar acciones críticas por n8n o por `backend/security/ot_actuator_guard.py` según tu política).

**Manual override:** un botón puede hacer `POST` a un webhook con payload JSON; si el flujo exige HMAC, el firmador debe ejecutarse **en el mismo proceso** que construye el cuerpo (Appsmith puede llamar a un **backend intermedio** que firme, o usar n8n como único emisor firmado). No afirmes latencias fijas sin medir en tu red.

---

## 3. Telemetría y dashboards ejecutivos (Grafana)

**Rol:** Series temporales, alertas, vistas tipo “centro de control”.

**Integración típica:**

- n8n escribe en **Postgres**, **InfluxDB** o **Prometheus** (métricas push/gateway); Grafana consume esas fuentes.
- Las **alertas** deben basarse en umbrales definidos por negocio y probados; los números de “ROI en pantalla” deben salir de **consultas** sobre datos reales o de escenarios etiquetados como tales, no de valores estáticos de demo.

**En repo:** referencia Prometheus en `docker/prometheus.yml` si usas ese stack; Grafana no está fijado como servicio único en este documento.

---

## 4. Portal headless / CMS (Directus, Strapi)

**Rol:** API y administración de entidades (sectores, usuarios, documentos públicos) para clientes o administraciones.

**Directus** puede apoyarse en un esquema Postgres existente con convenciones claras; requiere diseño de **permisos** y separación de datos sensibles.

**En repo:** ejemplo de despliegue local `docker-compose.directus.example.yml` + `.env.directus.example`; integración con n8n y antipatrones (no `fetch` al puerto 5432) en [docs/architecture/SABIONDA-N8N-WEB-FRONTEND.md](../architecture/SABIONDA-N8N-WEB-FRONTEND.md).

---

## 5. Arquitectura lógica “full stack” (referencia)

| Capa | Tecnología OSS (ejemplo) | Función |
|------|-------------------------|---------|
| Lógica / automatización | n8n | Orquestación, webhooks, firma en flujo |
| Datos relacionales | Postgres | Telemetría, config, opcional `trillizo_audit_log` |
| UI operativa | Appsmith / ToolJet / similar | Tableros y acciones hacia webhooks o API |
| Visualización / alertas | Grafana | Series y salud del sistema |
| Journal / conocimiento | SilverBullet | Decisiones `#ia-decision`, humano-in-the-loop |
| Portal / contenido | Directus / Strapi | Headless CMS si aplica |

SilverBullet sigue siendo el **journal legible**; Grafana complementa con **gráficos**; Appsmith con **acciones**; no son sustitutos obligatorios entre sí.

---

## 6. Wireframe de “dashboard de valor” (sin datos ficticios)

Pantalla tipo (métricas = **consultas reales** o “N/D” hasta piloto):

- **Estado de núcleos:** conectividad última vez / healthcheck (fuente: tu monitor o tabla propia).
- **Integridad:** ratio de webhooks `audit-trigger` 200 vs 401/500 (logs o tabla).
- **Ahorro hídrico / energético:** solo si hay **sensores + método** acordado; si no, mostrar “pendiente de línea base”.
- **Botones:** deben invocar endpoints documentados (n8n) con auth y, si aplica, HMAC generado correctamente.

Evita textos tipo “313/313”, “62 ms”, “100 % HMAC” o importes en € **como hechos** sin origen de datos en la query.

---

## 7. Próximos pasos de ingeniería (opcionales)

1. Elegir **una** herramienta de UI interna y **una** de series (o solo Postgres + Grafana).
2. Definir **contrato** del webhook “manual override” (`tipo_accion`, sector, auditor, notas).
3. Añadir **compose override** o chart con red común (`castuo_multi_n8n` / `castuo_cerebros`) y TLS terminado en proxy.
4. Documentar **quién firma** el HMAC cuando la acción nace en el navegador (patrón BFF recomendado).

---

*Documento orientativo; no sustituye DPIA, SLAs ni diseño OT.*
