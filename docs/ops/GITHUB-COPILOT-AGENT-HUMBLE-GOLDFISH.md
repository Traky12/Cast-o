# GitHub Copilot Agent — entorno Codespace `humble-goldfish`

Guía para usar el agente de **GitHub Copilot** en la instancia Codespace asociada a **CASTÚO-SYSTEM™**, incluyendo delegación de tareas y cómo volcar resultados en el repo.

**Entorno web:** [https://humble-goldfish-q767gq4qqrqgh4jp.github.dev](https://humble-goldfish-q767gq4qqrqgh4jp.github.dev)

**Perfil GitHub:** [https://github.com/Traky12](https://github.com/Traky12)

**Repositorio destino (transferencia):** [https://github.com/Traky12/goldfish](https://github.com/Traky12/goldfish)

---

## Paso 1: Acceder al entorno

1. Abre [https://humble-goldfish-q767gq4qqrqgh4jp.github.dev](https://humble-goldfish-q767gq4qqrqgh4jp.github.dev).
2. Inicia sesión con la cuenta GitHub vinculada al Codespace.

---

## Paso 2: Habilitar Copilot y abrir Agents

1. Copilot: [https://github.com/settings/copilot](https://github.com/settings/copilot) (actívalo si aplica).
2. En el Codespace, abre el repositorio **`goldfish`** (o el que hayas clonado allí).
3. Icono de **GitHub Copilot** → menú **Agents**.

---

## Mapeo de rutas (plantilla genérica → este monorepo Castuo)

Los prompts siguientes mencionan carpetas de ejemplo (`hetzner_infra/`, `castuo_system/ai/`). En **Castuo-System / goldfish** suele aplicarse:

| Plantilla genérica        | Ubicación típica en Castuo                          |
|---------------------------|-----------------------------------------------------|
| `hetzner_infra/`          | `deploy/`, `scripts/deploy/`, `docs/deploy/`, `docker-compose*.yml` |
| `castuo_graph/`           | `backend/integrations/langgraph_castuo/`, routers asociados |
| `castuo_system/ai/`       | `backend/` (Mistral, servicios IA), `scripts/ai/`   |
| `n8n/`                    | `n8n/workflows/`, `scripts/n8n/`                    |
| WordPress                 | Proyecto web aparte; integración vía APIs/webhooks si aplica |

Al pegar prompts en Copilot, **sustituye** las rutas por las reales del árbol que veas en el Codespace.

---

## Paso 3: Tareas para delegar al agente

### Tarea 1 — Explicar el repositorio

**Objetivo:** resumen técnico de estructura, dependencias y flujos.

**Mensaje (ajusta rama y rutas):**

```text
@github-copilot Explica la estructura del repositorio en la rama actual (por ejemplo feat/excelencia-operativa o main). Incluye:

1. Resumen de arquitectura y cómo interactúan backend/, n8n/, deploy/ y docker-compose.
2. Un diagrama Mermaid de flujos principales (datos → API/backend → Mistral u otros servicios → integraciones externas).
3. Dependencias críticas y riesgos (versiones, paquetes sin pin).
4. Archivos clave para seguridad y secretos (.env.*.example, secrets/, certificados).
5. Recomendaciones de organización de carpetas.

Resultado: informe técnico con diagramas y lista de dependencias.
```

---

### Tarea 2 — Cobertura de tests

**Objetivo:** reforzar tests en conectores IA y automatización.

**Mensaje:**

```text
@github-copilot Analiza la cobertura de tests en backend/, scripts/ai/ y n8n/ (donde haya código Python o tests asociados). Luego:

1. Identifica módulos con baja o nula cobertura relacionados con Mistral, webhooks o n8n.
2. Propón tests unitarios/integración para manejo de errores, timeouts y respuestas malformadas en los conectores HTTP/IA que encuentres en el repo (no inventes rutas: primero lista archivos reales).
3. Sugiere integración en GitHub Actions (.github/workflows/).
4. Incluye un ejemplo de test pytest alineado con la estructura existente en tests/.

Entrega: archivos de test sugeridos y snippet de workflow CI.
```

---

### Tarea 3 — Plan Hetzner / Arsys

**Objetivo:** plan de despliegue alineado con lo que ya existe en el repo.

**Mensaje:**

```text
@github-copilot Crea un plan paso a paso para desplegar este proyecto en Hetzner usando lo que ya exista en deploy/, scripts/deploy/, docker-compose y documentación en docs/deploy/. Incluye:

1. Orden recomendado: variables de entorno, secretos, Docker/Compose o k8s si hay manifiestos.
2. Firewalls, SSH y TLS (sin inventar productos: basado en archivos del repo).
3. Backups y almacenamiento: solo propuestas compatibles con lo documentado (Arsys/IPFS si aparece en docs; si no, indica "no hallado en repo").
4. Seguridad: cifrado en tránsito (TLS), secretos fuera de git, rotación de claves.
5. Cumplimiento: GDPR / AI Act como checklist de buenas prácticas (alto nivel), sin afirmaciones legales categóricas sin revisión DPO.
6. Script de despliegue de ejemplo coherente con scripts/ existentes.

Nota técnica: AES-256-GCM es el estándar habitual en aplicaciones; no uses "AES-512" como requisito literal salvo que tu normativa interna lo defina explícitamente.
```

---

### Tarea 4 — Optimizar workflows n8n

**Objetivo:** latencia, errores, auditoría, trazas.

**Mensaje:**

```text
@github-copilot Revisa n8n/workflows/ y propone mejoras para:

1. Reducir latencia (reintentos, batch, nodos innecesarios).
2. Manejo de errores (timeouts, JSON inválido, códigos HTTP).
3. Logs y minimización de datos personales (GDPR).
4. Formato estable para informes o payloads hacia APIs externas.
5. Un workflow JSON de ejemplo listo para importar (basado en un workflow existente del repo).
6. Trazabilidad por hash de salida si el repo ya documenta blockchain/Gaia-X (solo si hay referencias en código o docs).

Entrega: JSON ejemplo + lista de cambios por workflow.
```

---

### Tarea 5 — Seguridad y cumplimiento

**Objetivo:** riesgos y checklist.

**Mensaje:**

```text
@github-copilot Analiza el repositorio en busca de:

1. Posibles secretos en archivos versionados (patrones tipo API keys, tokens).
2. Riesgos de dependencias (sugerir pip/npm audit o herramientas CI).
3. Checklist GDPR / AI Act / normativa sectorial solo como marco de buenas prácticas; señala dónde falta DPIA o registro de tratamientos si hay datos personales.
4. Recomendaciones de cifrado, logs y observabilidad alineadas con backend y docs/security si existen.
5. Checklist de mitigación priorizado (P0/P1/P2).

Entrega: informe + checklist; no aplicar cambios automáticos sin revisión humana.
```

---

## Paso 4 — Monitorear progreso

- Revisa respuestas en tiempo real en **Agents**.
- Valida cada sugerencia antes de mergear (especialmente seguridad y despliegue).

---

## Paso 5 — Aplicar cambios en git

```bash
git add <archivo>
git commit -m "Aplicando mejoras sugeridas por Copilot Agent: <descripción>"
git push origin <tu-rama>
```

Informes largos:

```bash
# Ejemplo
git add docs/AGENT_REVIEW_20260401.md
git commit -m "Añadiendo informe de revisión Copilot Agent"
git push origin <tu-rama>
```

Scripts:

```bash
git add scripts/<script>.sh
git commit -m "Añadir script de despliegue sugerido por revisión agente"
git push origin <tu-rama>
```

---

## Paso 6 — GitHub Actions (opcional)

```bash
git add .github/workflows/<workflow>.yml
git commit -m "CI: ajustes según revisión Copilot Agent"
git push origin <tu-rama>
```

Comprueba la pestaña **Actions** en GitHub.

---

## Mensaje combinado (todas las tareas en secuencia)

Pega en Copilot Agent si quieres un único encargo secuencial:

```text
@github-copilot Soy Gregorio Jiménez, director técnico de CASTÚO-SYSTEM™. Estoy en el Codespace humble-goldfish-q767gq4qqrqgh4jp.github.dev con el repositorio goldfish en la rama actual. Ejecuta de forma secuencial y entrega un informe final consolidado:

### Tarea 1: Análisis del repositorio
Estructura real del árbol, diagrama Mermaid, dependencias críticas.

### Tarea 2: Tests
Cobertura y tests propuestos para módulos IA/HTTP reales del repo (sin inventar rutas).

### Tarea 3: Plan de despliegue
Plan basado en deploy/, docker-compose y docs/deploy/ existentes.

### Tarea 4: Workflows n8n
Optimización y un JSON de ejemplo importable.

### Tarea 5: Seguridad y cumplimiento
Riesgos, secretos, dependencias, checklist GDPR/AI Act a nivel de buenas prácticas.

### Entrega final
Un documento único con: diagrama, tests sugeridos, plan de despliegue, workflow JSON, checklist de seguridad.
```

---

## Limitaciones

- El agente no conoce Sabionda, Gaia-X o terceros si no están en el código o en `docs/`.
- Repos privados: confirma que tu plan Copilot permita el uso en privados.
- Infraestructura sensible: siempre revisión humana antes de producción.

---

## Próximos pasos recomendados

1. Ejecutar Tarea 1 en el Codespace.
2. Priorizar Tarea 5 y Tarea 2.
3. Guardar el informe consolidado en `docs/` (por ejemplo `docs/AGENT_REVIEW.md`).
4. Opcional: ampliar `.github/workflows/` para tests automáticos.
