# GitHub Copilot Agent — Entorno humble-goldfish-q767gq4qqrqgh4jp.github.dev

Guía operativa para delegar tareas de análisis, tests, despliegue y seguridad de **CASTÚO-SYSTEM™** a GitHub Copilot Agent en el entorno Codespace goldfish.

---

## Datos del entorno

| Campo | Valor |
|---|---|
| Codespace URL | `https://humble-goldfish-q767gq4qqrqgh4jp.github.dev` |
| Cuenta GitHub | `https://github.com/Traky12` |
| Repositorio goldfish | `https://github.com/Traky12/goldfish` |
| Rama activa | `feat/excelencia-operativa` |
| Rama Cursor local | `goldfihs-transfer` |

---

## Mapa de rutas: plantilla → monorepo real

Las tareas al agente usan rutas de ejemplo. Usa esta tabla para traducirlas al árbol **real** del repo:

| Ruta del prompt (plantilla) | Ruta real en este repo |
|---|---|
| `castuo_system/ai/mistral_connector.py` | `castuo_graph/ai/mistral_connector.py` |
| `castuo_system/ai/sabionda_connector.py` | `castuo_graph/ai/sabionda_connector.py` |
| `hetzner_infra/main.tf` | `hetzner_infra/main.tf` |
| `n8n/workflow_mistral_wordpress.json` | `n8n/workflows/mistral-wordpress-report.json` |
| `backend/` | `api/` + `services/` |
| `castuo_system/blockchain/` | `castuo_graph/blockchain/gaiachain.py` |
| `castuo_system/security/` | `castuo_graph/security/` + `infrastructure/fastapi/` |
| `deploy/` | `hetzner_infra/` + `k8s/` + `infrastructure/` |
| `tests/test_mistral_connector.py` | `tests/test_mistral_connector.py` (ya existe) |
| `tests/test_sabionda_connector.py` | `tests/test_sabionda_connector.py` (ya existe) |

> **Nota sobre cifrado:** Los prompts mencionan "AES-512". AES sólo existe en 128/192/256 bits.
> El estándar en uso en este repo es **AES-256-GCM** (ver `castuo_graph/security/encryption.py`).
> Pide al agente "AES-256-GCM con HKDF-SHA256" — no "AES-512".

---

## Paso 1 — Acceder al Codespace goldfish

```
https://humble-goldfish-q767gq4qqrqgh4jp.github.dev
```

Inicia sesión con la cuenta `Traky12`. El entorno ya tiene el repo con la rama `feat/excelencia-operativa`.

---

## Paso 2 — Habilitar GitHub Copilot

- Verificar/activar en: `https://github.com/settings/copilot`
- Requiere plan **Copilot Business** o **Enterprise** para analizar repos privados.
- Haz clic en el ícono de Copilot → **Agents** en la barra lateral izquierda.

---

## Paso 3 — Tareas individuales para el agente

### Tarea 1: Análisis del repositorio

```
@github-copilot Explica la estructura del repositorio `goldfish` en la rama
`feat/excelencia-operativa`. Incluye:
1. Resumen de arquitectura: cómo interactúan api/, castuo_graph/, services/,
   hetzner_infra/, n8n/workflows/, k8s/.
2. Diagrama Mermaid de flujo principal: IoT → MQTT → FastAPI → Mistral AI
   → GaiaChain → WordPress.
3. Dependencias críticas y versiones (requirements/production.txt).
4. Archivos de mayor riesgo: hetzner_infra/variables.tf, k8s/secrets.example.yaml,
   config/global_config.py.
5. Recomendaciones de reorganización de carpetas.
```

**Resultado esperado:** informe técnico + diagrama Mermaid + lista de archivos críticos.

---

### Tarea 2: Cobertura de tests

```
@github-copilot Analiza la cobertura de tests en `castuo_graph/ai/` y `n8n/workflows/`:
1. Identifica baja cobertura en:
   - castuo_graph/ai/sabionda_connector.py (actualmente ~53% según pytest-cov)
   - castuo_graph/blockchain/gaiachain.py (actualmente ~49%)
   - services/ (0% — sin tests unitarios aún)
2. Genera tests para:
   - castuo_graph/ai/mistral_connector.py: manejo de TimeoutError, HTTP 429 y
     respuestas malformadas.
   - castuo_graph/ai/sabionda_connector.py: validar respuestas sin campo "content",
     autenticación fallida.
   - n8n/workflows/mistral-wordpress-report.json: simula fallo en API Mistral
     (usa mocks en pytest).
3. Sugiere cómo incorporar los tests en .github/workflows/validate-all.yml.
4. Genera un ejemplo completo: tests/test_sabionda_extended.py.
```

**Resultado esperado:** tests nuevos listos para `pytest`, instrucciones para CI.

---

### Tarea 3: Plan de despliegue Hetzner

```
@github-copilot Crea un plan paso a paso para desplegar CASTÚO-SYSTEM™ en Hetzner
usando hetzner_infra/main.tf. El plan debe incluir:
1. Comandos exactos:
   cd hetzner_infra
   terraform init
   terraform plan -var="hcloud_token=$HETZNER_TOKEN" \
     -var="ssh_key_id=$HETZNER_SSH_KEY_ID"
   terraform apply -auto-approve ...
2. Post-deploy: k3s, Kubernetes (k8s/), despliegue de n8n, WordPress headless,
   Prometheus, Grafana.
3. Integración con Arsys para backups S3-compatible e IPFS via services/ipfs/.
4. Hardening: restringir puerto 22 a IP fija, desactivar puerto 5678 público,
   rotar claves SSH cada 90 días.
5. Validación AI Act: transparencia en castuo_graph/ethical_guard.py.
6. Un script ejecutable: scripts/deploy_hetzner.sh.
```

**Resultado esperado:** plan completo + `scripts/deploy_hetzner.sh`.

---

### Tarea 4: Optimización workflows n8n

```
@github-copilot Revisa y optimiza n8n/workflows/mistral-wordpress-report.json:
1. Reducir latencia: añade timeout de 30 s en nodo HTTP Mistral.
2. Manejo de errores: retry x3 con backoff exponencial, fallback a nodo Slack
   si falla la API.
3. GDPR: antes de enviar datos a Mistral, añade un nodo "Anonymize" que elimine
   campos PII (nombre, email, DNI) del payload.
4. Hash GaiaChain: al finalizar el informe, llama a services/blockchain/
   gaiachain_client.py para registrar el SHA-256 del reporte generado.
5. Exporta el workflow mejorado como JSON listo para importar.
```

**Resultado esperado:** JSON optimizado + descripción de nodos añadidos.

---

### Tarea 5: Seguridad y cumplimiento

```
@github-copilot Analiza el repositorio en busca de riesgos de seguridad. Revisa:
1. Secrets hardcodeados en config/global_config.py, docker-compose*.yml y
   agents/sabionda/config.json.
2. Dependencias con CVE usando Pip-audit sobre requirements/production.txt.
3. Cumplimiento:
   - GDPR: rastrea dónde se almacenan datos personales (api/routers/).
   - AI Act: verifica que castuo_graph/ethical_guard.py registra las decisiones.
   - AEMPS: confirma que api/routers/trazabilidad_qr.py cumple trazabilidad.
4. Cifrado: verifica que castuo_graph/security/encryption.py usa AES-256-GCM
   (no AES-ECB) y que las claves no son fijas en código.
5. Genera un checklist de acciones prioritarias con severidad (CRÍTICA/ALTA/MEDIA).
```

**Resultado esperado:** informe de vulnerabilidades + checklist priorizado.

---

## Paso 4 — Mensaje combinado (análisis integral)

Copia este bloque completo en Copilot → Agents para ejecutar las 5 tareas de una vez:

```
@github-copilot Soy Gregorio Jiménez, director técnico de CASTÚO-SYSTEM™.
Entorno: humble-goldfish-q767gq4qqrqgh4jp.github.dev
Rama: feat/excelencia-operativa

Ejecuta las siguientes tareas en orden y entrega un informe consolidado al final.

---

### Tarea 1: Análisis del repositorio
Explica la arquitectura general (api/, castuo_graph/, services/, hetzner_infra/,
n8n/workflows/, k8s/). Genera un diagrama Mermaid del flujo IoT → Mistral AI →
GaiaChain → WordPress. Lista las dependencias críticas (requirements/production.txt)
y los archivos de mayor riesgo.

---

### Tarea 2: Tests
Analiza la cobertura de tests. Los módulos con menor cobertura son:
- castuo_graph/ai/sabionda_connector.py (~53%)
- castuo_graph/blockchain/gaiachain.py (~49%)
- services/ (0%)
Genera tests para mistral_connector.py (timeouts, HTTP 429) y sabionda_connector.py
(respuestas malformadas, auth fallida). Ejemplo: tests/test_sabionda_extended.py.

---

### Tarea 3: Plan de despliegue Hetzner
Comandos Terraform para hetzner_infra/main.tf. Post-deploy k3s + k8s/. Integración
Arsys/IPFS. Hardening de firewall. Script: scripts/deploy_hetzner.sh.

---

### Tarea 4: Optimización n8n
Mejora n8n/workflows/mistral-wordpress-report.json: timeout 30 s, retry x3, nodo
Anonymize para GDPR, hash GaiaChain al finalizar. Exporta JSON listo para importar.

---

### Tarea 5: Seguridad y cumplimiento
Revisa secrets en config/global_config.py y docker-compose*.yml. Pip-audit sobre
requirements/production.txt. Checklist CRÍTICA/ALTA/MEDIA con GDPR, AI Act, AEMPS.

---

### Entrega final
Consolida en un informe técnico:
1. Diagrama Mermaid de arquitectura.
2. Tests generados (código Python completo).
3. Plan de despliegue + script deploy_hetzner.sh.
4. Workflow n8n optimizado (JSON).
5. Checklist de seguridad y cumplimiento priorizado.
```

---

## Paso 5 — Aplicar cambios sugeridos

```bash
# Código/configuraciones
git add <archivo>
git commit -m "fix: mejoras sugeridas por Copilot Agent — <descripción>"
git push origin feat/excelencia-operativa

# Documentación generada
mv informe_copilot.md docs/AGENT_REVIEW_$(date +%Y%m%d).md
git add docs/AGENT_REVIEW_*.md
git commit -m "docs: informe de revisión de Copilot Agent"

# Scripts de despliegue
mv deploy_hetzner.sh scripts/
chmod +x scripts/deploy_hetzner.sh
git add scripts/deploy_hetzner.sh
git commit -m "feat: script de despliegue Hetzner generado por Copilot Agent"
```

---

## Estado del push a goldfish

El repo `https://github.com/Traky12/goldfish` debe crearse **vacío** en `github.com/new`
antes de poder hacer push. El remoto ya está configurado en ambos entornos.

**Desde Cursor (Windows PowerShell):**
```powershell
cd "C:\Users\traky\.cursor\worktrees\Castuo-System\cpb"
$env:GIT_TERMINAL_PROMPT = "0"
git push -u goldfish goldfihs-transfer
git push goldfish goldfihs-transfer:main
```

**Desde este Codespace:**
```bash
cd /workspaces/Castuo-system
git push -u goldfish feat/excelencia-operativa
```

---

## Precauciones antes de aplicar sugerencias del agente

| Área | Precaución |
|---|---|
| Smart contracts / GaiaChain | Revisar con experto antes de aplicar |
| Cifrado | Verificar que usa AES-256-GCM, nunca AES-ECB ni "AES-512" |
| Secrets | Nunca aceptar código que hardcodee claves — usar `os.environ` |
| GDPR | Validar que anonymize elimina PII reales, no sólo campos de prueba |
| Terraform apply | Revisar `terraform plan` completo antes de `apply -auto-approve` |
| Repos privados | Requiere Copilot Business/Enterprise activo en la cuenta Traky12 |
