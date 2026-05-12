# CASTÚO-SYSTEM — Technical pitch (versión auditada)

Este documento presenta la **capacidad arquitectónica** de CASTÚO-SYSTEM para la gestión de infraestructura agraria crítica. Las **cifras de impacto económico** se presentan exclusivamente como **escenarios parametrizables**, sujetas a validación en **entorno operacional** (objetivo de evidencia tipo **TRL 7** en campo: piloto industrial con métricas, no el estado del solo repositorio).

---

## 1. Arquitectura de resiliencia (The Core)

### Mensaje

Topología de **gobernadores federados** (varias instancias n8n y servicios asociados) para reducir acoplamiento operativo y favorecer soberanía de despliegue. La **integridad** del registro hacia auditoría es verificable por diseño cuando se activa HMAC compartido.

| Componente | Implementación técnica (referencia) | Artefacto de verificación (repo) |
|------------|-------------------------------------|----------------------------------|
| Orquestación | Multi-instancia n8n (Docker) | `docker-compose.multi-n8n.yml`, `n8n/README-MULTI-N8N.md` |
| Integridad | HMAC-SHA256 del body JSON canónico | `n8n/workflows/01-trillizo-auditoria-basica.json`, `scripts/n8n/sign_audit_webhook_body.py` |
| Persistencia operativa | Postgres (stack cerebros / credencial n8n) | `docker-compose.cerebros.yml`, `n8n/README-CEREBROS.md` |
| Esquema telemetría (plantilla) | Tabla `telemetria` por sector (laboratorio / adaptación) | `n8n/sql/telemetria_sector_template.sql` |
| Libro de actas (SQL, opcional) | `trillizo_audit_log` + vista `vista_eficiencia_operativa` (paralelo al Markdown) | `n8n/sql/schema_auditoria_trillizo.sql` |
| UI / Grafana / CMS (opcional) | No fijado en compose base; guía de integración | `docs/ops/frontend-and-observability-stack.md` |
| Registro auditable | Journal Markdown en volumen compartido | `01-trillizo…` + `cerebros/auditoria/journal/` (montaje en compose) |
| Borde | Inferencia en n8n (nodos Code); LLM/Ollama **integrable** en flujos adicionales | `n8n/workflows/02-agente-diagnostico-ultra.json` (diagnóstico sector → audit) |

### Evidence backlog

| Ítem | Estado | Nota |
|------|--------|------|
| Lógica HMAC en webhook Trillizo (validación de cabecera vs body canónico) | Implementado en repo | Reimportar workflow activo en instancia real |
| Aislamiento **de red estricto por sector** (VLAN/servicio dedicado por núcleo) | No incluido por defecto | `castuo_multi_n8n` comparte red entre servicios; el aislamiento es **lógico** (instancias/volúmenes), no segregación automática por sector |
| Failover / HA automático (hot-standby, RTO fijo) | Diseño documentado; no implementado en compose | `docs/ops/failover-strategy.md` (separación honesta objetivo vs repo) |
| Test de carga sintético (p. ej. 100 req/s al `audit-trigger`) | Pendiente | Definir SLO y entorno (staging) |
| PoC local: firmas HMAC concurrentes (misma canonicalización que n8n) | Script en repo | `scripts/tests/stress_test_313_cores.py` + `castuo_audit_stress_common.py` |
| PoC HTTP: ráfaga POST a `audit-trigger` con firma | Script en repo | `scripts/tests/castuo_trillizo_audit_http_stress.py` (requiere Trillizo activo; no es failover) |
| Backup Postgres + Markdown | Implementado en repo | `scripts/backup_castuo_cerebros.sh`, `deploy/RUNBOOK-BACKUP-CEREBROS-POSTGRES.md` |
| Poblado de `trillizo_audit_log` desde n8n (INSERT tras webhook o vía servicio) | Pendiente | El esquema SQL existe; el flujo `01` hoy persiste en disco, no inserta filas automáticamente |

---

## 2. Determinismo vs. inferencia

### Mensaje

CASTÚO separa, a nivel de **diseño recomendado**, la **lógica de seguridad / límites físicos** (determinista) de la **optimización o sugerencia analítica** (IA agéntica). En repositorio actual el patrón parcialmente materializado es: **umbrales en flujo de diagnóstico** + **registro de decisión y confianza** en Trillizo.

| Capa | Rol | Estado en repo |
|------|-----|----------------|
| **Determinista (objetivo)** | Bloqueo de actuación si pH/EC/etc. violan rangos críticos, independientemente de la IA | **Backlog**: no existe aún un workflow nominal `02-actuator-safety`; implementar o enlazar capa OT existente (`backend/security/ot_actuator_guard.py`, etc.) |
| **Agéntica / analítica** | Tendencias, set-points, recomendaciones | Ejemplo: `02-agente-diagnostico-ultra.json` (umbrales demo + payload `kind: ia`) |
| **Contrato de salida** | `confidence` / `confianza` + contexto en auditoría | Payload hacia `01-trillizo-auditoria-basica.json` → `journal/diario-YYYY-MM-DD.md` |

### Evidence backlog

- [ ] Workflow o servicio explícito **actuador + guardas** con trazas vinculadas al mismo `SECTOR_ID` / `CORE_ID`.
- [ ] Política documentada: umbral mínimo de confianza para **ejecutar** vs solo **registrar**.
- [ ] Convención de tag **`#manual-override`** (u homónimo) cuando un humano anule a la IA; hoy el repo usa `#ia-decision` / `#evento-sistema` y `tags[]` en payload — extensible en plantillas LQL.

---

## 3. Soberanía y jurisdicción de datos

### Mensaje

Frente a un SaaS cerrado, el stack puede ejecutarse en **infraestructura del operador** (on-premise o nube bajo contrato soberano). Los pesos de modelos y datos sensibles pueden mantenerse en el perímetro **si** el despliegue y la red lo garantizan (no es automático).

| Capacidad | Notas |
|-----------|--------|
| Despliegue local / soberano | Compose + env documentados; sin dependencia obligatoria de un vendor de notas |
| Air-gapped | **Objetivo de despliegue**: requiere imágenes, modelos y actualizaciones gestionadas offline; no certificado por este documento |
| Auditoría forense | Integridad del **payload** firmado (HMAC) respecto al secreto compartido; registro en texto en SilverBullet. Ejemplos tipo “`V-102_activation`” son **ilustrativos** hasta existan eventos reales con ese contrato |

### Evidence backlog

- [ ] DPIA / registro de tratamientos y localización (fuera de este MD, referenciado en dossier).
- [ ] Diagrama de flujos de datos para due diligence (qué sale del perímetro).

---

## 4. La caja negra explicable (SilverBullet)

### Mensaje

La supervisión no es solo un dashboard cerrado: es un **journal de ingeniería** en Markdown, de baja carga cognitiva para revisión humana.

| Elemento | Repo |
|----------|------|
| Plantilla diaria | `n8n/templates/journal/plantilla.md` |
| Índice journal | `n8n/templates/silverbullet-journal-index.md` |
| Consultas ejemplo (LQL / sintaxis según versión SB) | `n8n/templates/silverbullet-control-panel-lql.example.md` |
| Tags en cuerpo | `#ia-decision`, `#sector-…` vía payload + línea **Etiquetas:** en `01-trillizo-auditoria-basica.json` |

**LQL:** la sintaxis “en lenguaje natural” depende del producto; las consultas del repo son **plantillas** a validar en la build instalada. Separación de responsabilidades legales: usar **`#ia-decision`** vs **`#manual-override`** (convención recomendada; implementar emisión del segundo donde proceda).

### Evidence backlog

- [ ] Grabación: webhook → entrada visible en `cerebros/auditoria/journal/`.
- [ ] Consulta validada en la versión concreta de SilverBullet.

---

## 5. Anexo — Escenarios de impacto (ROI parametrizado)

Las cifras siguientes son **proyecciones de capacidad** basadas en variables de mercado; **no** son métricas auditadas de este repositorio hasta piloto TRL 7.

\[
ROI = \frac{(V_{\text{mitigación}} + E_{\text{insumos}}) - \text{Costo}_{\text{infra}}}{\text{Costo}_{\text{infra}}}
\]

### Variables de sensibilidad (editables)

| Símbolo | Significado | Ejemplo de uso |
|---------|-------------|----------------|
| \(C_w\) | Coste de agua | €/m³, sectorizado por región |
| \(L\) | Latencia / conectividad | Impacto de cortes en cultivos de ciclo rápido (escenario) |
| \(V_a\) | Valor del activo biológico | €/ha (cultivo de alto valor vs. extensivo) |
| \(A\) | Superficie bajo gobierno | ha |
| \(s\) | Fracción de ahorro atribuible | requiere línea base medida en piloto |

### Regla de uso

Ningún ROI presentado con esta fórmula es **garantía** sin: método, periodo, muestra, responsable y datos primarios (facturas, sensores, inventarios).

---

## 6. Due diligence técnica

### Lo que el repositorio sustenta (diseño + código)

- Flujo de datos **documentado** entre instancias n8n, Postgres (según despliegue) y Trillizo → journal.
- **Integridad criptográfica opcional** del mensaje al webhook de auditoría (HMAC del JSON canónico).
- Estructura de despliegue **replicable** vía contenedores y variables de entorno de ejemplo.

### Lo que requiere piloto operacional (evidencia TRL 7)

- Tasa real de ahorro de agua / insumos ligada a precisión de sensores y protocolo de campo.
- Durabilidad de hardware en condiciones ambientales reales.
- Curva de aprendizaje del personal con SilverBullet y procedimientos de auditoría.
- Escalado **N** núcleos (p. ej. despliegue federado): factible como patrón; el número concreto y el rendimiento son **medición**, no promesa del repo.

---

*Rutas relativas a la raíz del repositorio Castuo-System.*
