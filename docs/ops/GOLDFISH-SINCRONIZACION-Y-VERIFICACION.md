# Goldfish + Castuo-system: estado, verificación y siguientes pasos

Documento operativo tras alinear **GitHub `goldfish`** con **`feat/excelencia-operativa`** de **Castuo-system** (commit canónico de referencia: `51bf03a` o posterior en esa línea).

---

## 1. Diagnóstico (resumen)

| Problema | Causa |
|----------|--------|
| Rama local `goldfihs-transfer` (worktree antiguo) con ~4 commits | Historial **no conectado** al de GitHub (raíz distinta); `merge` fallaba con *unrelated histories*. |
| Fuente de verdad del progreso | Rama **`feat/excelencia-operativa`** en `Traky12/Castuo-system` (historial completo: TRL9, CI, docs, k8s, etc.). |

## 2. Solución aplicada

- **`goldfish/main`** y **`goldfish/goldfihs-transfer`** actualizados con el contenido de **`origin/feat/excelencia-operativa`** (`git push goldfish origin/feat/excelencia-operativa:<rama>` con `--force-with-lease`).
- Worktree local **`cpb`**: `git reset --hard origin/feat/excelencia-operativa` y seguimiento de **`goldfish/main`** (ajustar si prefieres `origin`).

---

## 3. A. Verificar en Codespace `humble-goldfish`

En la terminal del Codespace (repo **goldfish** clonado desde `https://github.com/Traky12/goldfish`):

```bash
git remote -v
git fetch origin
git checkout main
git pull origin main
git log -1 --oneline
```

**Esperado:** último commit alineado con la rama de excelencia (p. ej. `51bf03a` o más nuevo si ya hubo pushes).

---

## 3. B. Historial

```bash
git log --oneline --graph -25
```

---

## 3. C. Archivos y carpetas clave (rutas reales en este monorepo)

En la raíz del repositorio:

```bash
ls -la
ls -la k8s/ docs/ .github/workflows/ 2>/dev/null || true
ls -la wp-content/ 2>/dev/null || true
ls -la monitoring/prometheus/rules/ 2>/dev/null || true
```

| Área | Ruta en repo |
|------|----------------|
| Kubernetes (manifiestos ejemplo) | `k8s/` (`deployment.yaml`, `ingress.yaml`, `secrets.example.yaml`, …) |
| Documentación | `docs/` (incl. `docs/deploy/`, `docs/ops/`) |
| CI/CD | `.github/workflows/` (incl. `deploy-to-hetzner.yml`, `ci.yml`, e2e, seguridad) |
| WordPress (tema B2B agritech) | `wp-content/themes/castuo-agritech/` |
| Prometheus (alertas) | `monitoring/prometheus/rules/castuo_alerts.yml` |

**Nota:** No hay en el árbol actual una ruta documentada como `wp-content/plugins/castuo-validar-lote/`. Si el plugin vive en otra rama o repo, documentar aquí la ruta real al añadirlo.

---

## 4. Continuar el desarrollo

### Rama `main` sincronizada

Trabajar directamente en `main` solo si el equipo lo permite; lo habitual es rama de feature.

### Nueva rama (recomendado)

```bash
git checkout main
git pull origin main
git checkout -b feat/mi-cambio
# … editar …
git add -A
git commit -m "feat: descripción breve"
git push -u origin HEAD
```

En **goldfish**, `origin` es `https://github.com/Traky12/goldfish.git`.

### Mantener alineado Castuo-system (opcional)

Si el trabajo canónico sigue en **Castuo-system**, tras merge en `feat/excelencia-operativa` allí:

```bash
git fetch https://github.com/Traky12/Castuo-system.git feat/excelencia-operativa
git push origin FETCH_HEAD:main   # solo si quieres volver a espejar goldfish desde Castuo
```

(Ajustar remoto y nombres de rama según tu flujo.)

---

## 5. Integración con sistemas

### 5.1 Kubernetes / Hetzner

```bash
ls -la k8s/
```

Aplicar en un cluster **solo** con contexto correcto y tras revisar `secrets` (no aplicar `secrets.example.yaml` como secretos reales sin sustituir valores):

```bash
kubectl apply -f k8s/namespace.yaml
# … revisar orden y dependencias (configmap, deployment, service, ingress, etc.)
```

Seguir runbooks en `docs/deploy/` si existen para tu entorno.

### 5.2 GitHub Actions

```bash
ls -la .github/workflows/
```

Ejemplo de disparo manual (requiere `gh` autenticado y permisos):

```bash
gh workflow list --repo Traky12/goldfish
gh workflow run deploy-to-hetzner.yml --ref main --repo Traky12/goldfish
```

Si `gh` no está instalado, usa la pestaña **Actions** en GitHub → **Run workflow**.

### 5.3 WordPress

- Tema: `wp-content/themes/castuo-agritech/`
- Probar en instancia WP copiando el tema o usando el pipeline de despliegue que defináis.

### 5.4 Prometheus / Grafana

```bash
ls -la monitoring/prometheus/rules/
```

Aplicación con `kubectl` **solo** si esas reglas forman parte de un manifiesto/Helm usado en vuestro cluster; ejemplo genérico:

```bash
kubectl apply -f monitoring/prometheus/rules/castuo_alerts.yml
```

Validar antes el namespace y las labels que espera vuestro stack de monitoring.

---

## 6. Tabla rápida de comandos

| Acción | Comando |
|--------|---------|
| Sincronizar Codespace | `git fetch && git checkout main && git pull` |
| Ver historial | `git log --oneline --graph -25` |
| Listar k8s / CI / docs | `ls -la k8s/ docs/ .github/workflows/` |
| Workflow Hetzner (ejemplo) | `gh workflow run deploy-to-hetzner.yml --ref main --repo Traky12/goldfish` |
| Reglas Prometheus | `ls -la monitoring/prometheus/rules/` |

---

## 7. Próximos pasos recomendados

1. En Codespace: verificar `git log -1` y existencia de `k8s/`, `.github/workflows/`, `wp-content/themes/castuo-agritech/`, `monitoring/prometheus/rules/`.
2. Ejecutar CI en GitHub (push o workflow manual) y corregir fallos.
3. Documentar en `docs/` cualquier decisión de despliegue (Hetzner, DNS, secretos).
4. Definir si **goldfish** es espejo solo de lectura o también recibe PRs; si es espejo, automatizar sync desde Castuo-system con workflow o documentar procedimiento manual.

---

*Última actualización alineada con la sincronización goldfish ↔ feat/excelencia-operativa.*
