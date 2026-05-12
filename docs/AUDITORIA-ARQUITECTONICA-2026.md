# Auditoría arquitectónica completa — CASTÚO-SYSTEM (Marzo 2026)

**Proyecto:** CASTÚO-SYSTEM™ + Mistral Adapter  
**Cliente:** CASTÚO 360 S.L. (Gregorio J Jiménez Bodes)  
**Alcance:** Código, documentación, escalabilidad, cumplimiento, roadmap, riesgos y recomendaciones.

---

## 1. AUDITORÍA DE CÓDIGO (mistral_castuo_adapter.py)

**STATUS: 🟡**

### Fortalezas

- **API keys:** Validación de env en `_validate_env()`, soporte Fernet para clave cifrada, lectura desde `ENCRYPTED_MISTRAL_API_KEY` o `MISTRAL_API_KEY`; no se escriben en log (solo "en claro" en desarrollo).
- **Rate limiting:** `_wait_rate_limit()` con ventana 60 s y cola por minuto configurable (`DEFAULT_RATE_LIMIT_PER_MINUTE = 60`).
- **Región y compliance:** `DEFAULT_REGION_CONFIG` con ES/EU/GLOBAL, compliance por región (GDPR, AI_Act_2024, PAC_2040).
- **GaiaChain:** Hash SHA-256 de request+response+timestamp en `_log_to_gaiachain`; punto de extensión claro para backend real.
- **Tipado y docstrings:** Type hints en firmas, docstrings PEP 257 en clases y métodos principales.

### Problemas críticos

- **ERROR 1 — Inferencia de extensión CSV:** En `load_dataset()` línea 188, el mapa usa `"csv"` pero `ext` incluye el punto (ej. `".csv"`). Para `archivo.csv` → `ext == ".csv"` → `.get(".csv", "csv")` devuelve `"csv"` por defecto; si en el futuro se añade `".csv"` como clave explícita, fallaría. **Impacto:** Bajo hoy; riesgo de regresión si se refactoriza el dict.
- **ERROR 2 — API key en memoria en `MistralAPIClient`:** El constructor recibe `api_key: str` y lo guarda en `self.api_key` (línea 254). Si el cliente se serializa o se vierte en logs/cores, la key quedaría expuesta. **Impacto:** Medio; en producción usar solo `APIKeyManager.get_valid_key()` y no persistir el cliente con la key.
- **ERROR 3 — Sin manejo explícito 401/403/429:** `query()` hace `response.raise_for_status()` y captura `RequestException` genérico (línea 322–325). No se distingue 401 (no auth), 403 (forbidden), 429 (rate limit API). **Impacto:** El usuario no puede reintentar o degradar en 429; mensajes de error poco específicos.
- **ERROR 4 — Timeout fijo 30 s:** `timeout=30` en `session.post()` (línea 317). Para prompts grandes o respuestas largas puede ser insuficiente; no configurable. **Impacto:** Fallos en consultas pesadas sin opción de ajuste.

### Mejoras inmediatas

- **Fix 1 (30 min):** Corregir inferencia de tipo en `load_dataset`: usar claves con punto, p. ej. `{".csv": "csv", ".json": "json", ".parquet": "parquet"}` y `file_type = mapping.get(ext, "csv")` para coherencia.
- **Fix 2 (2 h):** En `query()`, capturar `requests.HTTPError`, leer `response.status_code` y relanzar excepciones tipadas o mensajes claros (401 → "API key inválida", 429 → "Rate limit; reintentar en X s" si viene `Retry-After`).
- **Feature (1 día):** Añadir parámetro opcional `timeout: Optional[int] = None` en `query()` y en `__init__` del cliente; usar `timeout or 30` en el `post`. Opcional: reintentos con backoff en 429.

### Testing

- **Cobertura actual:** No existen tests unitarios ni de integración específicos para `api/mistral_castuo_adapter.py`. Los tests del repo (`tests/test_all_endpoints.py`, `tests/test_webhooks.py`) no cubren el adapter.
- **Recomendación:** Añadir `tests/test_mistral_adapter.py`: (1) `APIKeyManager.get_valid_key()` con env mockeado; (2) `MistralDataManager.load_dataset` con CSV/JSON/Parquet de fixture y sin pandas; (3) `MistralAPIClient.query` con `responses` o `httpx` mock; (4) `_validate_gdpr_compliance` con DataFrame con columnas email/dni.

**Score: 6/10**

---

## 2. CALIDAD DOCUMENTACIÓN (docs/mistral-adapter/)

**STATUS: 🟢**

### Fortalezas

- **MkDocs Material:** `mkdocs.yml` con nav completa (Introducción → Changelog), `docs_dir: docs/mistral-adapter`, theme material, idioma es, plugins search y git-revision-date-localized.
- **Cumplimiento:** `compliance.md` describe GDPR (validación columnas personales), GaiaChain (hash SHA-256), cifrado Fernet y adaptación por región (ES/EU/GLOBAL).
- **Onboarding:** `installation.md` en 5 pasos (clone, pip, .env, ejecutar ejemplo, MkDocs); `python api/mistral_castuo_adapter.py` y `ejemplo_completo()` permiten validar en &lt;5 min con API key.
- **Ejemplos:** `examples.md` con 3 ejemplos (sensores Parquet, informe cumplimiento UE, `ejemplo_completo()`); código ejecutable con imports correctos `from api.mistral_castuo_adapter import ...`.
- **API Reference:** Tabla de clases/métodos, configuración por región y variables de entorno en `api-reference.md`.
- **Deploy:** README con `mkdocs gh-deploy --clean`, CNAME/DNS por proveedor, checklist y test de enlaces (Introducción, Características, FAQ, Changelog).

### Problemas críticos

- **ERROR 1:** En `installation.md` se referencia `pip install -r requirements.txt` pero en la raíz del repo `requirements.txt` no incluye `pandas`, `pyarrow`, `cryptography`, `requests` necesarios para el adapter. **Impacto:** Usuario que solo sigue la doc puede tener `ModuleNotFoundError` si instala solo `requirements.txt` de raíz.
- **ERROR 2:** `api-reference.md` no documenta que `stream=True` está ignorado (solo warning en log). **Impacto:** Expectativa de streaming sin soporte real.

### Mejoras inmediatas

- **Fix 1 (30 min):** En `installation.md` sección "Instalar dependencias", indicar explícitamente: `pip install requests pandas pyarrow cryptography` o crear `api/requirements-mistral.txt` y referenciarlo.
- **Fix 2 (15 min):** En `api-reference.md` método `query()`, añadir nota: "`stream=True` no implementado en v1.0; se ignora y se registra un warning."
- **Feature (1 día):** Añadir en `examples.md` un ejemplo con dataset real Sabionda (ej. `data/agritech_samples.csv` con columnas cultivo, humedad, parcela) y enlace a archivo de ejemplo en el repo.

**Score: 8/10**

---

## 3. ARQUITECTURA ESCALABILIDAD

**STATUS: 🔴**

### Fortalezas

- **FastAPI principal (`api/main.py`):** Endpoints `/`, `/health`, `/events`, `/compliance`, `/audit`; health con chequeo PostgreSQL y compliance; CORS y HTTPS redirect configurables por env; token Bearer para /health y /audit.
- **Adapter como librería:** `mistral_castuo_adapter.py` es importable; no acoplado a un solo proceso; puede usarse desde workers o scripts.

### Problemas críticos

- **ERROR 1 — Mistral Adapter no expuesto en API:** `api/main.py` no importa ni expone endpoints para el Mistral Adapter (no hay `/mistral/query` ni `/mistral/health`). El backend en `backend/main.py` tiene `/mistral/ask` pero usa su propia llamada HTTP, no el adapter de `api/mistral_castuo_adapter.py`. **Impacto:** Para producción "client-facing" con FastAPI, el adapter no está disponible vía HTTP en el servicio `api/`.
- **ERROR 2 — Docker API sin Mistral:** `api/Dockerfile` copia solo `main.py` y usa `api/requirements.txt` (FastAPI, uvicorn, psycopg2, pydantic); no incluye `mistral_castuo_adapter.py` ni dependencias (requests, pandas, cryptography). **Impacto:** No se puede desplegar el adapter en el mismo contenedor que la API actual.
- **ERROR 3 — Sin .dockerignore en raíz:** No existe `.dockerignore` en el repo; builds de Docker pueden incluir `docs/`, `.git`, `site/`, etc. **Impacto:** Imágenes más grandes y mayor superficie de contexto.
- **ERROR 4 — Sin endpoint /metrics:** No hay Prometheus/OpenMetrics ni endpoint de métricas (p. ej. número de llamadas Mistral, latencia, errores). **Impacto:** Dificulta monitoring en Hetzner y alertas.

### Mejoras inmediatas

- **Fix 1 (2 h):** En `api/main.py` añadir router o endpoints que usen el adapter: p. ej. `POST /mistral/query` (body: model, prompt, temperature, max_tokens) llamando a `MistralAPIClient` con API key desde `APIKeyManager(region).get_valid_key()`, y `GET /mistral/health` que compruebe env (key presente) sin llamar a la API.
- **Fix 2 (1 h):** Incluir en `api/Dockerfile` la copia de `mistral_castuo_adapter.py` y en `api/requirements.txt` las dependencias: `requests`, `pandas`, `pyarrow`, `cryptography`. Mantener usuario no-root.
- **Fix 3 (30 min):** Crear `.dockerignore` en raíz con: `docs/`, `site/`, `.git/`, `*.md`, `tests/`, `.env`, `__pycache__/`, `*.pyc`.
- **Feature (1 día):** Añadir endpoint `GET /metrics` en formato Prometheus (contador de requests Mistral, histograma de latencia) o integrar `prometheus-fastapi-instrumentator` en `api/main.py`.

**Score: 4/10**

---

## 4. CUMPLIMIENTO LEGAL (compliance.md)

**STATUS: 🟡**

### Fortalezas

- **GDPR:** Validación de columnas tipo email/DNI/teléfono y aviso si no tienen prefijo `ANON_`; documentado en compliance.md.
- **AI Act / PAC 2040:** Mencionados en configuración EU (compliance list) y en doc; trazabilidad vía hash en GaiaChain.
- **Cifrado:** API key con Fernet; doc menciona AES-256-GCM y YubiKey en el ecosistema CASTÚO.
- **Regiones:** Tabla normativas por región (UE, USA, LATAM, Asia) en compliance.md.

### Problemas críticos

- **ERROR 1 — Data minimization no aplicada en código:** El adapter no limita qué columnas o filas se envían a Mistral; `ejemplo_completo()` puede enviar `df.head().to_markdown()` con datos sensibles. **Impacto:** Riesgo de enviar PII a terceros (Mistral) sin minimización documentada en flujo.
- **ERROR 2 — Consentimiento explícito:** No hay flujo ni documentación de consentimiento del usuario para envío de datos a LLM; compliance.md no lo menciona. **Impacto:** Para uso con datos de agricultores UE, puede ser requisito legal.
- **ERROR 3 — eIDAS:** Se menciona "firma digital para trazabilidad GaiaChain" en doc pero el adapter solo registra un hash; no hay firma con certificado eIDAS en el código. **Impacto:** Trazabilidad sí; no cumplimiento eIDAS de firma en el adapter.
- **ERROR 4 — ISO 27001:** No hay documento que mapee controles ISO 27001 con implementación (por ejemplo, control de acceso, cifrado, auditoría). **Impacto:** Certificación futura requerirá trabajo adicional de documentación.

### Mejoras inmediatas

- **Fix 1 (30 min):** En compliance.md añadir sección "Minimización de datos": recomendar enviar solo columnas no personales o agregados; no incluir email/DNI en el prompt.
- **Fix 2 (2 h):** En `MistralDataManager` o en doc, añadir advertencia: "Antes de enviar datos a Mistral, asegurar consentimiento para procesamiento por terceros (DPA/contractual)."
- **Feature (1 día):** Añadir en roadmap/compliance: (1) clasificación de riesgo AI Act (Limited/High) según uso; (2) plantilla de cláusula de consentimiento para Sabionda Educa; (3) opción de no enviar contenido crudo (solo resúmenes o hashes) para modo "high privacy".

**Score: 5/10**

---

## 5. ROADMAP TÉCNICO (roadmap.md)

**STATUS: 🟢**

### Fortalezas

- **Corto/medio/largo plazo:** Tabla clara: GaiaChain 2.0 real, streaming, más regiones; OAuth2, esquemas, Sabionda Educa; GaiaChain nativo, PQC, PAC 2040.
- **Compatibilidad:** Mistral API v1 (chat/completions), CASTÚO-SYSTEM, GaiaChain 2.0 como backend futuro.
- **Priorización visible:** Integración GaiaChain y streaming en corto plazo; OAuth2 y validación de esquemas en medio.

### Problemas críticos

- **ERROR 1 — Priorización no cuantificada:** No se indica orden claro GaiaChain 2.0 vs OAuth2 vs PQC para Sabionda Educa ni fechas objetivo. **Impacto:** Dificulta planificación de sprints y funding.
- **ERROR 2 — MVP vs Enterprise no delimitado:** No hay lista "MVP (Sabionda piloto)" vs "Enterprise (multi-tenant, SSO, PQC)". **Impacto:** Riesgo de sobre-inversión en features no necesarias para piloto.
- **ERROR 3 — Dependencies Mistral:** No se documenta límites de tasa/cuota de Mistral ni estrategia de fallback (ej. otro modelo o proveedor) si la API no está disponible. **Impacto:** Sin plan B, caídas de Mistral = caída del servicio.
- **ERROR 4 — PAC 2040:** Roadmap menciona "reglas de cumplimiento agrovoltaico" pero no submedidas concretas (superficies, elegibilidad, reportes). **Impacto:** Implementación futura sin especificación clara.

### Mejoras inmediatas

- **Fix 1 (30 min):** En roadmap.md añadir subsección "Prioridad para Sabionda Educa": 1) GaiaChain 2.0 (trazabilidad demostrable); 2) Ejemplos y datos de ejemplo; 3) OAuth2 si hay integración con plataforma educativa.
- **Fix 2 (1 h):** Añadir tabla "MVP vs Enterprise": MVP = API Key + ES/EU + ejemplo_completo + doc; Enterprise = OAuth2 + multi-región + PQC + GaiaChain nativo + esquemas validados.
- **Feature (1 día):** Documentar en roadmap o en faq.md: (1) Límites conocidos Mistral (tokens/min, modelos); (2) Fallback: desactivar consultas o mostrar mensaje "Servicio temporalmente no disponible" y reintentar más tarde; (3) Opción futura multi-LLM (OpenAI/Anthropic) para reducir vendor lock-in.

**Score: 7/10**

---

## 6. RIESGOS CRÍTICOS

**STATUS: 🟡**

### Vendor lock-in (Mistral)

- **Riesgo:** Toda la capa de IA depende de Mistral API; cambio de precios o de términos podría impactar el producto.
- **Mitigación actual:** Solo uso de Mistral; backend tiene llamadas directas a `api.mistral.ai` en varios módulos (`backend/services/mistral.py`, `backend/routers/orchestrator.py`, etc.) sin abstracción común.
- **Recomendación:** Introducir una capa de abstracción "LLMProvider" (interface: `query(model, prompt, **kwargs)`) con implementación Mistral y, a medio plazo, OpenAI/Anthropic; configurar proveedor por env. El adapter en `api/mistral_castuo_adapter.py` puede ser una de las implementaciones.

### Costos (tokens)

- **Riesgo:** Uso descontrolado de tokens (p. ej. datasets grandes en prompt) dispara coste.
- **Mitigación actual:** Rate limiting por minuto en el adapter; no hay límite por usuario ni por día; no hay métricas de tokens consumidos.
- **Recomendación:** (1) Añadir en `query()` lectura de `usage` en la respuesta Mistral y log o métrica (tokens prompt + completion); (2) opcional: tope por cliente o por día con variable de entorno; (3) alertas (ej. Prometheus) si se supera umbral.

### Datos (anonimización)

- **Riesgo:** Datos de agricultores UE enviados a Mistral sin anonimización efectiva; GDPR y posible veto del interesado.
- **Mitigación actual:** Solo aviso si columnas email/dni/phone no tienen prefijo `ANON_`; no se filtra ni se anonimiza en código.
- **Recomendación:** (1) En modo producción, por defecto no incluir columnas marcadas como personales en el prompt; (2) ofrecer función `anonimize_for_llm(df, columns_to_drop)` que elimine o generalice columnas; (3) documentar en compliance y en Sabionda que los datos de ejemplo deben ser sintéticos o anonimizados.

### Competencia (AgriTech)

- **Riesgo:** Diferenciación frente a otras soluciones AgriTech/agrovoltaica.
- **Fortalezas actuales:** Integración trazabilidad (GaiaChain), cumplimiento multi-región, enfoque Sabionda Educa (educación), marca CASTÚO + Extremadura.
- **Recomendación:** Reforzar en documentación y pitch: (1) trazabilidad end-to-end (campo → GaiaChain → informe); (2) cumplimiento GDPR/AI Act listo para UE; (3) piloto educativo como caso de uso claro; (4) roadmap PQC y PAC 2040 como diferenciador normativo.

---

## 7. RECOMENDACIONES INMEDIATAS (Prioridad Alta)

### Quick Wins (&lt;1 día)

1. **Corregir inferencia CSV en `load_dataset`:** Dict con claves `".csv"`, `".json"`, `".parquet"` (30 min).
2. **Documentar dependencias adapter en installation.md:** Lista explícita `requests pandas pyarrow cryptography` o `api/requirements-mistral.txt` (30 min).
3. **Añadir `.dockerignore`** en raíz (30 min).
4. **Documentar en api-reference que `stream=True` no está implementado** (15 min).
5. **En `query()`, manejo de 401/403/429** con mensajes claros y opcionalmente retry en 429 (2 h).

### Must-Have (&lt;1 semana para Sabionda Educa)

1. **Exponer Mistral Adapter en API:** Endpoints `POST /mistral/query` y `GET /mistral/health` en `api/main.py` usando `mistral_castuo_adapter.py` (medio día).
2. **Docker API con adapter:** Incluir `mistral_castuo_adapter.py` y deps en `api/Dockerfile` y `api/requirements.txt` (1 h).
3. **Tests unitarios adapter:** `tests/test_mistral_adapter.py` con mocks de env y HTTP (1 día).
4. **Dataset de ejemplo Sabionda:** Archivo `data/agritech_samples.csv` con columnas realistas (cultivo, humedad, parcela_id, fecha) y referenciado en examples.md (1 h).
5. **Compliance: sección "Minimización de datos" y advertencia consentimiento** en compliance.md (1 h).

### Funding-ready (Deck + demo CTAEX/Fundecyt)

1. **One-pager técnico:** 1 página con arquitectura (Usuario → FastAPI → Mistral Adapter → Mistral API; GaiaChain para trazabilidad), cumplimiento (GDPR, AI Act), TRL actual y siguiente hito (Sabionda Educa piloto).
2. **Demo script:** (1) `python api/mistral_castuo_adapter.py` con `data/agritech_samples.csv`; (2) mostrar doc en https://castuo-system.github.io/mistral-adapter/; (3) opcional: llamada a `GET /health` y `POST /mistral/query` si se implementan.
3. **Métricas de impacto:** Nº de parcelas/usuarios objetivo, ahorro estimado (agua, insumos), alineación con ODS y PAC 2040.
4. **Riesgos y mitigación:** Vendor lock-in (abstracción multi-LLM en roadmap), costes (monitoreo de tokens), datos (anonimización y consentimiento documentados).

---

## CONCLUSIÓN EJECUTIVA

| Criterio | Valor |
|----------|--------|
| **Funding Ready** | Parcial |
| **TRL** | 4–5 (componentes validados en entorno relevante; integración con usuario piloto pendiente de cerrar) |
| **Clientes Ready** | Parcial (Sabionda Educa puede usar el adapter vía script y doc; falta API HTTP estable y dataset de ejemplo) |
| **Prioridad #1** | Exponer el Mistral Adapter en la API FastAPI (`api/main.py`) con `POST /mistral/query` y `GET /mistral/health`, e incluir el adapter en el Dockerfile de la API para un despliegue único production-ready. |

### Resumen por área

| Área | Score | Estado |
|------|-------|--------|
| 1. Código (adapter) | 6/10 | 🟡 |
| 2. Documentación | 8/10 | 🟢 |
| 3. Escalabilidad/Arquitectura | 4/10 | 🔴 |
| 4. Cumplimiento legal | 5/10 | 🟡 |
| 5. Roadmap | 7/10 | 🟢 |
| 6. Riesgos | — | 🟡 |
| 7. Recomendaciones | — | Accionables |

**Siguiente acción recomendada:** Implementar los Quick Wins 1–4 y el Must-Have 1–2 (API + Docker) para tener un flujo "cliente llama a FastAPI → Mistral Adapter → Mistral API" desplegable en Hetzner y demostrable en menos de una semana.
