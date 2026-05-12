# 📦 Guía de Transferencia a GitHub: CASTUO-SYSTEM → goldfish

**Fecha:** 1 Abril 2026  
**Estado:** ✅ Listo para transferencia (feat/excelencia-operativa)  
**Commit Actual:** c7e2a4f (Hub de Conectividad v2.0 completo)

---

## 📋 Checklist Pre-Transferencia

- ✅ Todos los archivos con seguimiento en Git
- ✅ 44 tests passing (100%)
- ✅ Commit principal: Hub v2.0 consolidado
- ✅ Documentación: completa y linkeada
- ✅ Infraestructura: Terraform validado
- ✅ Workflow n8n: JSON válido
- ✅ Sin archivos binarios grandes (no requiere Git LFS)

---

## 🚀 Procedimiento de Transferencia

### Paso 1: Preparar Token de Acceso Personal (GitHub)

**Ubicación en GitHub:**  
Settings → Developer settings → Personal access tokens → Tokens (classic)

**Permisos requeridos:**
- ✅ `repo` (acceso completo a repositorios privados y públicos)
- ✅ `workflow` (actualizar workflows de GitHub Actions)
- ✅ `admin:org_hook` (si aplica)

**Guardar el token** en lugar seguro (necesario para `git push`).

---

### Paso 2: Crear Repositorio "goldfish" en GitHub

**Opción A: Via GitHub UI**
1. Ir a https://github.com/new
2. Nombre: `goldfish`
3. Descripción: "CASTUO-SYSTEM™ Hub de Conectividad v2.0 - IA, Blockchain, IaC"
4. Visibilidad: **Privado** (recomendado para desarrollo)
5. ✅ No inicializar con README (ya tienes archivos locales)
6. Click "Create repository"

**Opción B: Via GitHub CLI**
```bash
gh repo create goldfish \
  --private \
  --source=. \
  --remote=origin \
  --push
```

---

### Paso 3: Transferencia de Archivos (Opción A: Manual)

#### 3a. Añadir Repositorio Remoto
```bash
cd /workspaces/Castuo-system

# Verificar remotos actuales
git remote -v

# Añadir nuevo remoto "goldfish" (reemplaza Traky12 si aplica)
git remote add goldfish https://github.com/Traky12/goldfish.git

# Verificar que se agregó
git remote -v
```

**Salida esperada:**
```
goldfish  https://github.com/Traky12/goldfish.git (fetch)
goldfish  https://github.com/Traky12/goldfish.git (push)
origin    https://github.com/Traky12/Castuo-system.git (fetch)
origin    https://github.com/Traky12/Castuo-system.git (push)
```

#### 3b. Hacer Push de la Rama Principal
```bash
# Push de rama actual (feat/excelencia-operativa) a goldfish
git push -u goldfish feat/excelencia-operativa

# También push de main (si quieres referencia)
git push goldfish main 2>/dev/null || echo "main no existe localmente"
```

**Autenticación:**  
Cuando Git pida contraseña, usa el **Personal Access Token** (no contraseña de GitHub).

#### 3c. Configurar Rama por Defecto (en goldfish)
```bash
# Ver ramas en remoto goldfish
git ls-remote goldfish | grep refs/heads

# En GitHub UI:
# Settings → Branches → Default branch → seleccionar feat/excelencia-operativa
```

---

### Paso 4: Transferencia (Opción B: Automática - Recomendado)

**Usar script one-liner:**

```bash
#!/usr/bin/env bash
set -euo pipefail

GITHUB_USER="Traky12"  # Reemplaza si aplica
REMOTE_NAME="goldfish"
REMOTE_URL="https://github.com/${GITHUB_USER}/${REMOTE_NAME}.git"

cd /workspaces/Castuo-system

# 1. Agregar remoto
git remote add "$REMOTE_NAME" "$REMOTE_URL" || git remote set-url "$REMOTE_NAME" "$REMOTE_URL"

# 2. Verificar conexión
echo "[INFO] Verificando conexión con $REMOTE_URL..."
git ls-remote "$REMOTE_NAME" > /dev/null 2>&1 && echo "✓ Conectado a $REMOTE_URL"

# 3. Push de rama actual
CURRENT_BRANCH=$(git branch --show-current)
echo "[INFO] Haciendo push de rama: $CURRENT_BRANCH"
git push -u "$REMOTE_NAME" "$CURRENT_BRANCH"

# 4. Push de ramas adicionales
git push "$REMOTE_NAME" main 2>/dev/null || true
git push "$REMOTE_NAME" develop 2>/dev/null || true

# 5. Información de resultado
echo ""
echo "✅ Transferencia completada!"
echo "📍 Repositorio: $REMOTE_URL"
echo "🔗 Vista en GitHub: https://github.com/${GITHUB_USER}/${REMOTE_NAME}"
echo ""
echo "Próximos pasos:"
echo "  1. Ve a GitHub y verifica que los archivos estén presentes"
echo "  2. Configura rama default: Settings > Branches"
echo "  3. Habilita GitHub Actions: Actions > [Habilitar]"
echo "  4. Configura secrets: Settings > Secrets and variables > Actions"
```

**Ejecutar:**
```bash
bash /ruta/al/script.sh
```

---

### Paso 5: Verificación en GitHub

#### 5a. Verificar Archivos en GitHub UI
```
https://github.com/Traky12/goldfish
```

**Debe contener:**
- ✅ castuo_graph/ (ai, blockchain, security)
- ✅ hetzner_infra/ (main.tf, variables.tf, user_data.yaml)
- ✅ n8n/workflows/ (mistral-wordpress-report.json)
- ✅ docs/ops/ (HUB-CONECTIVIDAD.md, HERRAMIENTAS-INTEGRACION.md, ARQUITECTURA-VISUAL.md)
- ✅ .github/workflows/reconcile-ci.yml
- ✅ tests/ (test_*.py con 44 tests)
- ✅ Makefile (extendido con targets nuevos)
- ✅ README.md (con sección Hub v2.0)

#### 5b. Verificar Historial de Commits
```bash
# En GitHub UI: Code → Commits
# Debe mostrar:
#   c7e2a4f feat: Hub de Conectividad v2.0...
#   1724283 feat: infraestructura de seguridad...
#   [etc.]
```

#### 5c. Verificar Tamaño del Repositorio
```bash
# En GitHub UI: Settings → General
# Mostrar: ~5-10 MB (archivos de código, no binarios)
```

---

### Paso 6: Configurar Secrets en GitHub

**Ubicación:** Settings → Secrets and variables → Actions

**Secrets requeridos para CI/CD:**

```bash
# Comando para cada secret (reemplaza <valor>):
gh secret set MISTRAL_API_KEY --body "<valor>" -R Traky12/goldfish
gh secret set SABIONDA_API_KEY --body "<valor>" -R Traky12/goldfish
gh secret set HETZNER_TOKEN --body "<valor>" -R Traky12/goldfish
gh secret set HETZNER_SSH_KEY_ID --body "<valor>" -R Traky12/goldfish
gh secret set JWT_SECRET_KEY --body "<valor>" -R Traky12/goldfish
gh secret set GAIACHAIN_PRIVATE_KEY --body "<valor>" -R Traky12/goldfish
gh secret set DB_PASSWORD --body "<valor>" -R Traky12/goldfish
gh secret set ENCRYPTION_KEY --body "<valor>" -R Traky12/goldfish
```

**O manualmente en GitHub UI:**
1. Settings → Secrets and variables → Actions → New repository secret
2. Name: `MISTRAL_API_KEY`
3. Secret: `sk-...`
4. Add secret
5. Repetir para cada secret

---

### Paso 7: Configurar GitHub Actions

**Ubicación:** Settings → Actions → General

**Configuración:**
- ✅ Allow all actions and reusable workflows → **Habilitado**
- ✅ Fork pull request workflows from outside collaborators → **Requiere aprobación**

**Verificar Workflows:**
1. Ve a Actions tab
2. Debe mostrar `reconcile-ci.yml` como workflow disponible
3. Habilitar si es necesario

---

### Paso 8: Actualizaciones Post-Transferencia

#### 8a. Sincronizar Cambios Locales
```bash
# Si trabajas en local y necesitas actualizar origen
git fetch goldfish
git pull goldfish feat/excelencia-operativa
```

#### 8b. Cambiar Repositorio por Defecto (Opcional)
```bash
# Si quieres que "origin" apunte a goldfish
git remote rename origin castuo-original
git remote rename goldfish origin

# Verificar
git remote -v
```

#### 8c. Actualizar Configuración de CI/CD
Edita `.github/workflows/reconcile-ci.yml` si necesitas paths específicos o cambios:
```yaml
on:
  push:
    branches: [ feat/excelencia-operativa, main ]  # Adds rama target
  pull_request:
    branches: [ feat/excelencia-operativa, main ]
```

---

## 📌 Solución de Problemas Comunes

### Problema: "fatal: Authentication failed"
**Solución:**
```bash
# Generar nuevo Personal Access Token en GitHub
# Luego usar como contraseña en git push

# O usar SSH (más seguro):
git remote set-url goldfish git@github.com:Traky12/goldfish.git
git push -u goldfish feat/excelencia-operativa
```

### Problema: "Repository already exists"
**Solución:**
```bash
# El repositorio ya existe en GitHub
# Opción 1: Usar otro nombre
git remote set-url goldfish https://github.com/Traky12/goldfish-v2.git

# Opción 2: Limpiar el repo en GitHub (Settings > Danger Zone > Delete)
```

### Problema: "Branch 'feat/excelencia-operativa' not found"
**Solución:**
```bash
# Verificar ramas locales
git branch -a

# Push explícitamente
git push -u goldfish feat/excelencia-operativa:feat/excelencia-operativa
```

---

## ✨ Después de Transferencia

### 1. Actualizar URLs en Documentación
```bash
# Reemplazar todas las referencias a Castuo-system con goldfish
sed -i 's|github\.com/Traky12/Castuo-system|github.com/Traky12/goldfish|g' README.md docs/**/*.md
git add .
git commit -m "docs: actualizar URLs a nuevo repo goldfish"
git push goldfish feat/excelencia-operativa
```

### 2. Crear README.md Específico para goldfish
```markdown
# goldfish - CASTUO-SYSTEM Hub de Conectividad v2.0

Repositorio espejo de desarrollo/staging para CASTUO-SYSTEM™.

**Rama principal:** feat/excelencia-operativa

## 🔗 Enlaces Importantes
- [Documentación Hub](docs/ops/HUB-CONECTIVIDAD.md)
- [Herramientas OSS](docs/ops/HERRAMIENTAS-INTEGRACION.md)
- [CI/CD Policies](docs/ci-policies.md)
- [Arquitectura](docs/ops/ARQUITECTURA-VISUAL.md)

## 🧪 Tests
```bash
make test-all  # 44 tests (100% passing)
```

## 🚀 Despliegue
```bash
cd hetzner_infra
terraform plan && terraform apply
```

> Repositorio original: [Traky12/Castuo-system](https://github.com/Traky12/Castuo-system)
```

### 3. Habilitar Protección de Rama (Recomendado)
```
Settings → Branches → Add rule
Branch name pattern: feat/excelencia-operativa
✅ Require a pull request before merging
✅ Dismiss stale pull request approvals
✅ Require status checks to pass
```

---

## 📊 Resumen de Transferencia

| Item | Estado | Detalles |
|------|--------|----------|
| Archivos transferidos | ✅ | 26 archivos nuevos + 7 modificados |
| Tamaño | ✅ | ~3.8 MB (código, sin binarios grandes) |
| Tests | ✅ | 44/44 passing (100%) |
| Documentación | ✅ | Completa (1,500+ líneas) |
| Secrets | ⏳ | Requiere configuración manual |
| Workflows | ✅ | reconcile-ci.yml listo |
| IaC | ✅ | Terraform validado, sin secretos embebidos |

---

## 🎯 Siguiente: Despliegue en Producción

**Ver:** [docs/ops/HUB-CONECTIVIDAD.md](docs/ops/HUB-CONECTIVIDAD.md) (secciones 5-9)

**Pasos:**
1. Configurar GitHub Secrets (6 mínimo)
2. Ejecutar `terraform plan` en hetzner_infra/
3. Ejecutar `terraform apply`
4. Configurar n8n y credenciales
5. Desplegar workflow n8n
6. Validar con `make hub-connectivity-check`

---

**Versión:** 1.0  
**Actualizado:** 1 April 2026  
**Responsable:** CASTUO Technical Team
