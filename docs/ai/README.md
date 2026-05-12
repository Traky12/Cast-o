# Documentación IA — Sabionda / CASTÚO-SYSTEM

Documentos que definen la arquitectura cognitiva, valores y reglas de negocio para la IA y los sistemas CASTÚO.

---

## Documentos principales

| Documento | Descripción |
|-----------|-------------|
| [SABIONDA-v10.0-Global-Standard.md](SABIONDA-v10.0-Global-Standard.md) | **SABIONDA v10.0/v10.1** — Estándar global agrotech autónoma (escalable ∞): propósito 2026–2040, 25 módulos, integración legal (RPI/EUIPO), DAO + DynamicCompliance, contingencia global (USDA/SAHPRA/MHLW), roadmap 2026–2040, checklist ejecutivo |
| [CASTUO-Global-Architecture-v9.0.md](CASTUO-Global-Architecture-v9.0.md) | **Arquitectura global v9.0** — Estándar agrotech 5 continentes: propósito 2026–2031, 20 módulos (Europa/América/Asia/África/Oceanía, blockchain, anti-fraude Chainalysis, métricas FAO/ISO 14064, contratos por continente, adaptación cultural, roadmap y checklist) |
| [SABIONDA_MASTER-v7.1.md](SABIONDA_MASTER-v7.1.md) | **SABIONDA_MASTER v7.1** — Plataforma agrotech autónoma: propósito 2026–2031, 12 módulos (seguridad HSM, legal PAC 2027, trazabilidad, Sabionda Educa, Cursor), tono v7.1, barreras v7.1, roadmap técnico |
| [Prompt-Guide-v4.1.md](Prompt-Guide-v4.1.md) | **SABIONDA_MASTER v4.1** — Identidad, arquitectura cognitiva, valores, sistemas externos, procesamiento de código, métricas, protocolos, flujos, reglas de negocio, evolución e implementación (corto/medio/largo plazo) |
| [Sabionda-Persona-v7.0.md](Sabionda-Persona-v7.0.md) | **Sabionda v7.0** — Tono extremeño avanzado: estructura de respuestas, frases por contexto, extremeñismos, ejemplos completos (éxito, sensor, emergencia, educación), guía Mistral AI |
| [Sabionda-Mistral-Config-v7.json](Sabionda-Mistral-Config-v7.json) | Configuración JSON para Mistral AI (identidad, response_structure, extremeñisms, compliance, barriers_v61) |
| [tonos_extremeños.json](tonos_extremeños.json) | Plantillas de mensaje (greet / status / error) **sin KPIs fijos**; sustituyen `{yield}`, `{security}`, etc. con datos de `OmegaCore` + env `CASTUO_MEASURED_*` |
| [language-guide.md](language-guide.md) | Lenguaje inclusivo y tono (persona agricultora, socios CTAEX, respuestas con valores CASTÚO) |
| [Anomaly-Detection-Guide.md](Anomaly-Detection-Guide.md) | Detección de anomalías en inputs (Barreras v6.1): Isolation Forest, integración con API, registro en GaiaChain |

---

## Usabilidad y ética Sabionda

- **Usabilidad**: Persona v7.0 define el tono y la estructura de las respuestas para que Sabionda sea cercana, técnica y motivadora (NPS >70). Ver [Sabionda-Persona-v7.0.md](Sabionda-Persona-v7.0.md).
- **Ética y protección**: Las **Barreras de Protección Sabionda v7.1** (incl. Cursor Integration) son **NUNCA VIOLAR**. Ver [Sabionda-Barriers-v7.1.md](../security/Sabionda-Barriers-v7.1.md) y [Sabionda-Barriers-v6.1.md](../security/Sabionda-Barriers-v6.1.md).

---

## Código de referencia

- **Fachada Sabionda + Omega + Holobrain**: `scripts/sabionda/facade.py` — `SabiondaOmegaFacade`: tono desde `tonos_extremeños.json`, núcleo `scripts/omega/omega_core.py`, webhook vía `scripts/holo/holobrain_client.py`.
- **Análisis de código**: `backend/services/code_analysis.py` — Valida cumplimiento GDPR, AEMPS, GaiaChain, LIMS, AI Act sobre fragmentos de código.
- **API**: `POST /ue/code/analyze` — Body: `{"code_snippet": "...", "context": {"system": "cannabis"|"iot"|"microgreens"}}`.
- **Sostenibilidad**: `backend/services/sustainability.py` — Estima huella de carbono por acción (riego, energía).
- **v10.0**: `backend/services/usda_compliance.py` (USDA), `roi_subsidies.py` (ROI + subvenciones locales), `contingency_fallback.py` (USDA/SAHPRA/MHLW fallback); `scripts/chainalysis_monitor.py` (monitoreo Chainalysis 24/7); contratos `EUCore`, `DynamicCompliance`, `GlobalGovernance`, `CASTUO_System`; K8s `k8s/sabionda-core/`; legal `scripts/replace-placeholders.sh`, `docs/legal/verify-integrity-legal.sh`.

---

## Referencias cruzadas

- Reglas de negocio: Prompt-Guide v4.1 § Reglas de negocio para IA.
- Integraciones: [docs/integration/](../integration/) (CTAEX-LIMS, GlobalGAP, AEMPS, SAP, Moodle).
- Operaciones: [docs/operations/Kubernetes.md](../operations/Kubernetes.md).
