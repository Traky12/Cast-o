# Integración OpEx (excelencia operativa) → Trillizo

Este documento enlaza el **Agente Análisis OpEx** (y flujos similares) con el **cerebro auditor** CASTÚO: webhook `audit-trigger` + diario Markdown en SilverBullet, con **HMAC opcional** alineado al resto del repo.

## Qué está versionado en el repositorio

| Artefacto | Rol |
|-----------|-----|
| `n8n/workflows/01-trillizo-auditoria-basica.json` | Recibe el POST y escribe `journal/diario-YYYY-MM-DD.md`. |
| `n8n/workflows/02-agente-diagnostico-ultra.json` | Patrón de firma y POST desde telemetría. |
| `n8n/workflows/03-castuo-opex-auditoria-trillizo.json` | **Puente OpEx → Trillizo** (webhook dedicado + mismo `stableStringify` / `X-Castuo-Signature`). |
| `scripts/n8n/sign_audit_webhook_body.py` | Firma offline del body exacto (laboratorio / CI). |
| `n8n/README-CEREBROS.md` | Contrato del body y cabeceras. |

## Por qué no “fusionar” todo en un solo JSON exportado

Un workflow monolítico con cientos de nodos (credenciales, Matrix, IPFS, etc.) es frágil para el repo: IDs de credencial, rutas cloud y placeholders (`<__PLACEHOLDER_VALUE__…>`) rompen la importación en otro entorno. La integración **audit-grade** aquí es: **contrato estable** + **workflow pequeño importable** + **un cable HTTP** desde tu orquestación.

## Patrón recomendado en tu orquestación grande

1. **Punto de enganche:** salida del **Agente Análisis OpEx** *después* del **Parser** estructurado (objeto `output` con campos numéricos fiables).
2. **Evitar:** enviar a Trillizo **solo** la salida de *Guardrails Militares* si ese nodo altera u homogeneiza tipos de forma que pierdas métricas (la auditoría humana necesita números coherentes).
3. **Opción A — Sub-workflow HTTP:** en la misma instancia n8n donde corre `03`, añade un nodo **HTTP Request**:
   - **Method:** POST  
   - **URL:** `http://localhost:5678/webhook/castuo/opex-audit` (ajusta host/puerto; en Docker, nombre del servicio n8n).  
   - **Body:** JSON = `{{ $json }}` (debe incluir `output: { … }` del agente).  
4. **Opción B — Duplicar el nodo Code:** copia el `jsCode` de `Preparar_Audit_Opex_Trillizo` en un nodo Code **en tu workflow**, seguido de IF + HTTP como en `02`/`03` (útil si no quieres cadena HTTP interna).

## Variables de entorno (misma instancia que emite o que recibe)

- `SECTOR_ID`, `CORE_ID` — inyectados en `auditBody` y en `#sector-…`.
- `CASTUO_TRILLIZO_AUDIT_URL` — por defecto `http://n8n-trillizo:5678/webhook/audit-trigger` en compose multi-n8n.
- `CASTUO_AUDIT_WEBHOOK_SECRET` — si está definido en **n8n-trillizo** y en el nodo que firma, debe ser **el mismo** valor; cabecera `X-Castuo-Signature`.

## Etiquetas y LQL / búsqueda

Los eventos OpEx llevan `#opex` además de `#ia-decision`. En SilverBullet, las consultas exactas dependen de la versión; parte de texto fijo (`OpEx`, `OPEX_ANALYSIS`) es estable para búsqueda en el diario.

## Límites (due diligence)

- El **Feedback Loop** que llama a `http://backend:8000/actuators/adjust` es **acción OT**: debe quedar gobernado por políticas de seguridad (guardianes, modo manual, etc.) del despliegue real; el Trillizo documenta la **intención** y el contexto OpEx, no sustituye el control de actuadores.
- Cifras de valoración o ROI en prompts de LLM son **escenarios**; no las mezcles con métricas auditadas sin etiquetar explícitamente el origen.

## Verificación rápida

1. Levantar Trillizo + workflow `01` activo.  
2. Importar y activar `03`.  
3. `curl` o n8n “Test workflow” con body mínimo:

```json
{
  "output": {
    "eficiencia_general_pct": 78,
    "oee_score": 0.82,
    "recomendaciones_opex": ["Revisar ciclo nocturno de HVAC"],
    "consumo_energia_kwh": 42
  }
}
```

4. Comprobar aparición en `cerebros/auditoria/journal/diario-YYYY-MM-DD.md` con bloque IA y `#opex`.

---

## Blueprint export masivo (sensores, OpEx, gateway, inversores)

Si tienes un **único JSON** exportado desde n8n Cloud/self-hosted con cientos de nodos (sensores por sector, agentes, Matrix, IPFS, inversores, holobrain, stress test, etc.), úsalo como **referencia de producto** y cablea la **excelencia operativa auditada** contra lo que ya está versionado aquí.

### Mapa rápido: tu export → repo

| Bloque del blueprint | En CASTÚO-SYSTEM (preferido) |
|----------------------|------------------------------|
| Gateway + router + forward | `n8n/workflows/castuo_main_orchestrator_gateway.json` + `n8n/README-AGRI-BRAIN.md` + `n8n/README-MULTI-N8N.md` |
| OpEx → diario firmado | `n8n/workflows/03-castuo-opex-auditoria-trillizo.json` + este documento |
| Trillizo / `audit-trigger` | `n8n/workflows/01-trillizo-auditoria-basica.json` + `n8n/README-CEREBROS.md` |
| Diagnóstico / firma telemetría | `n8n/workflows/02-agente-diagnostico-ultra.json` |
| Stress / métricas / informe | `scripts/tests/stress_gateway_injection.py`, `scripts/chaos/castuo_chaos_lab.py`, `docs/ops/CHAOS-ENGINEERING-LAB.md` |
| Holobrain (demo) | `n8n/workflows/castuo-holobrain-webhook-stub.json`, `docs/architecture/HOLOGRAPHIC-CASTUO-ARCHITECTURE.md` |
| Actuadores OT | Backend: `backend/security/ot_actuator_guard.py`, `docs/deploy/OT-SEGURIDAD-ACTUADORES-CASTUO.md` |

### Por qué no commiteamos el megaworkflow tal cual

- **Credenciales:** los `credentials.id` del export son de **tu** instancia; en otro n8n fallan.
- **Placeholders:** `<__PLACEHOLDER_VALUE__…>` deben sustituirse por IDs reales de Data Tables, canales Slack, endpoints Power BI, etc.
- **Duplicidad del gateway:** si el export incluye otro `castuo-orchestrate` con lógica distinta a `castuo_main_orchestrator_gateway.json`, tendrás **dos fuentes de verdad**; alinea rutas y env con el workflow versionado o documenta la divergencia.
- **Rutas webhook dinámicas:** expresiones tipo `path: "=sensor-data/{{ $env.SECTOR_ID }}"` dependen de la versión de n8n; a menudo es más robusto **un path fijo** (`sensor-data`) + `SECTOR_ID` en el cuerpo, o enrutar todo por el gateway con `request_type`.

### Correcciones habituales al pegar/importar

1. **Nodo `Filtrar Datos Válidos`:** el IF que comprueba `{{ $json.validation.is_valid }}` no coincide con la salida típica del Code `Validación de Esquema y Bio-límites` (suele exponer `is_valid` en la raíz del JSON). Ajusta la expresión o el Code para que el contrato sea único.
2. **`Preparar Análisis para BD`:** referencias a `$json.output.*` requieren que el item anterior sea **salida del Parser** del agente; si el flujo pasa por un Set intermedio, las expresiones fallan.
3. **`Enviar a Auditoría (Trillizo)`:** el body debe respetar el **stable stringify** y la cabecera `X-Castuo-Signature` como en `02`/`03`; no mezclar con campos stringificados incorrectamente.
4. **Prompts con cifras legales/financieras** (valoración €500M, 80.000 ha, RTO declarado): trátalos como **borrador narrativo**; en due diligence separa **modelo** vs **medición** (véase también `docs/ops/failover-strategy.md`).

### Checklist mínima tras importar en staging

1. Definir `.env.n8n-multi` (o variables de instancia) según `.env.n8n-multi.example` — incluidas claves opcionales de cifrado/HMAC si activas esos nodos.
2. Sustituir **todos** los `<__PLACEHOLDER_VALUE__…>` por recursos creados en tu n8n.
3. Probar **solo** el camino OpEx → Trillizo con `03` o HTTP interno documentado arriba.
4. Probar **gateway** con `curl` de `n8n/README-AGRI-BRAIN.md`.
5. Registrar resultados de stress/chaos en artefactos locales antes de claims ante inversores.
