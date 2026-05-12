# Marco de referencia: CAAE, PAC, mercados (honestidad del repositorio)

**Versión 1.0 · Revisión 2026-03-21**  
**Alcance:** delimita qué puede afirmarse del monorepo frente a **integraciones futuras** con organismos de certificación, ayudas PAC y datos de mercado.

**Impacto territorial:** certificación ecológica, PAC y precios se resuelven en **expediente, convocatorias y fuentes oficiales**; este documento **no implementa APIs ni métricas ficticias**.

---

## 1. Principios (no negociables en documentación)

- **No** APIs inventadas (`caae.es/api/v2`, `PAC 2027 REST`, `juntaex_trazabilidad.py`, etc.).
- **No** métricas Prometheus sin instrumentar (`ley3_*`, `caae_certifications_status`, `market_price_forecast`, …).
- **No** dashboards Grafana que pretendan datos que el backend no publica.
- **No** “texto completo” de reglamentos UE en markdown en repo **sustituyendo** EUR-Lex/BOE, salvo proceso explícito de mantenimiento.

---

## 2. CAAE (organismo de control)

| Referencia útil | Dónde obtener el texto |
|-----------------|-------------------------|
| Reglamento (UE) 2018/848 | EUR-Lex (versión consolidada) |

**En el repo hoy**

- Marco y límites: este documento y [REQUISITOS-FUTUROS-CAAE.md](./REQUISITOS-FUTUROS-CAAE.md).
- **No** hay `compliance_docs/generated/02.04.01_CAAE-Procedimiento.md`, `docs/legal/UE-2018-848-Agricultura-Ecológica.md`, `templates/legal/CAAE-Informe-Trazabilidad.docx`, `docs/quality/UNE-66800-Calidad-Ecológica.md` como evidencias versionadas actuales.
- Trazabilidad cannabis / AEMPS: `compliance/aemps_compliance.py` (estructura documental), **sin** API pública AEMPS inventada.

**Auditoría:** `python scripts/audit/audit_repo_evidence_check.py` — **no** existe el flag `--caae`; el inventario usa `REQUIRED_EVIDENCE` en el script.

---

## 3. PAC 2023–2027

| Referencia útil | Nota |
|------------------|------|
| Reglamento (UE) 2021/2115 | Marco PAC; ayudas concretas por convocatoria y CCAA |

**En el repo hoy**

- Narrativa de criterios: `docs/funding/PAC2040-Criterios.md` (**no** es resolución de ayuda).
- **No** hay `docs/legal/UE-2021-2115-PAC.md`, `docs/funding/ORDEN-AAA-XXX-2026-PAC.md`, `compliance_docs/generated/02.05.01_PAC-Criterios.md` en el árbol actual.
- **No** hay `backend/compliance/pac_client.py` ni endpoints `pac.juntaex.es` verificados.

**Auditoría:** **no** existe `--pac` en el script.

---

## 4. Mercados agrícolas

Referencias habituales (texto en fuentes oficiales): Reglamento (UE) 2016/1011 (índices de referencia), marco español de transparencia que aplique al producto.

**En el repo hoy**

- **No** hay `data/market/precios-historicos.csv`, `scripts/analytics/market_analysis.py`, `docs/legal/UE-2016-1011-Mercados.md`, `docs/legal/Ley-12-2013-Transparencia.md`, `docs/quality/UNE-66000-Innovacion.md` como rutas obligatorias.
- **No** hay `backend/market/price_forecast.py` (Prophet/XGBoost) ni predicciones auditadas.

**Auditoría:** **no** existe `--market` en el script.

---

## 5. Modelos predictivos y Grafana

- Un JSON de dashboard **no crea** series; hay que exponer métricas desde aplicación/exportadores.
- Cualquier ML con impacto en personas o precios exige datos, gobernanza y, si aplica, evaluación conforme a normativa de IA y DPIA.

---

## 6. Netafim / riego comercial

- Ver [REQUISITOS-NETAFIM-FUTURO.md](../iot/REQUISITOS-NETAFIM-FUTURO.md).

---

## 7. AEMPS, PDF masivos y GaiaChain

- `compliance/aemps_compliance.py` **no** expone `validate_license()` ni generación masiva tipo `aemps_reports.py` del briefing.
- Registro on-chain: `backend/api/services/gaiachain_service.py` + `POST /api/audit/register-event` (JWT). **No** mezclar con `GaiaChainAuditClient.register_event_in_chain` como si fuera el mismo canal que Web3 del cliente utilitario.

---

## 8. Criterio para futuras integraciones

1. Documentación **oficial** o contrato que describa el canal.
2. Módulo delgado y testeable.
3. Actualizar **este** marco y, si aplica, `REQUIRED_EVIDENCE` con rutas que **existen**.
4. Mantener el principio: **nunca** afirmar integración en README sin código y evidencia.

---

**Relación:** [SIGPAC-AEMPS-MARCO-REPOSITORIO.md](./SIGPAC-AEMPS-MARCO-REPOSITORIO.md) · [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md) · [IOT-MARCO-REPOSITORIO.md](../iot/IOT-MARCO-REPOSITORIO.md) · [REQUISITOS-FUTUROS-CAAE.md](./REQUISITOS-FUTUROS-CAAE.md)
