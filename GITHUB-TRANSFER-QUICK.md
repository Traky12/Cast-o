# ⚡ Quick Start: Transferencia a goldfish

**Estado Actual:** Listo para transferencia (commit c7e2a4f)

---

## 🎯 En 5 Minutos

### 1️⃣ En GitHub: Crear repo "goldfish"
```
https://github.com/new
Name: goldfish
Visibility: Private
✅ Create repository
```

### 2️⃣ Ejecutar script de transferencia
```bash
bash scripts/github-transfer.sh

# O personalizado:
bash scripts/github-transfer.sh --user Traky12 --repo goldfish
```

**El script hará:**
- ✅ Verificar prerequisitos
- ✅ Conectar a GitHub
- ✅ Configurar remoto "goldfish"
- ✅ Hacer push de rama actual
- ✅ Confirmar transferencia

### 3️⃣ Ir a GitHub y verificar

```
https://github.com/Traky12/goldfish
```

Debe verse:
- 📁 castuo_graph/ (IA, Blockchain, Security)
- 📁 hetzner_infra/ (Terraform)
- 📁 tests/ (44 tests)
- 📄 docs/ (Documentación completa)
- 📄 Makefile (15 targets nuevos)

---

## 📋 Pre-Transferencia (Checklist)

- ✅ Repositorio git inicializado
- ✅ Todos los archivos commiteados (commit c7e2a4f)
- ✅ 44 tests passing
- ✅ +26 archivos nuevos
- ✅ Documentación completa
- ✅ Sin cambios pendientes

---

## 🚀 Opción A: Script Automático (Recomendado)

```bash
# Dry-run (ver qué haría sin ejecutar)
bash scripts/github-transfer.sh --dry-run

# Transferencia real
bash scripts/github-transfer.sh

# Con usuario personalizado
bash scripts/github-transfer.sh --user TuUsuario --repo TuRepo
```

**Ventajas:**
- Interactivo (pide confirmación en cada paso)
- Verifica prereq
- Colorea output
- Proporciona feedback detallado

---

## 🔄 Opción B: Manual (Si necesitas control total)

### Paso 1: Añadir remoto
```bash
git remote add goldfish https://github.com/Traky12/goldfish.git
git remote -v  # Verificar
```

### Paso 2: Hacer push de rama actual
```bash
BRANCH=$(git branch --show-current)
git push -u goldfish $BRANCH

# O explícitamente:
git push -u goldfish feat/excelencia-operativa
```

### Paso 3: Push de ramas adicionales (opcional)
```bash
git push goldfish main          # Si existe localmente
git push goldfish develop       # Si existe localmente
git push --all goldfish         # Todas las ramas
```

---

## ⚠️ Solución Rápida de Problemas

### "Authentication failed"
```bash
# Tu Personal Access Token es contraseña en prompts de git
# Generarlo en: GitHub Settings > Developer settings > Personal access tokens

# O usar SSH (más fácil si ya configuraste):
git remote set-url goldfish git@github.com:Traky12/goldfish.git
git push -u goldfish feat/excelencia-operativa
```

### "Repository not found"
```bash
# Verificar que creaste el repo en GitHub:
# https://github.com/new -> nombre exacto "goldfish"

# Verificar URL:
git remote -v
# Debe mostrar: goldfish  https://github.com/Traky12/goldfish.git
```

### "Branch already exists"
```bash
# El repo ya tiene la rama (probablemente fue un push anterior)
# Es normal, simplemente prosigue a verificación en GitHub
```

---

## ✨ Post-Transferencia

### 1. Configurar Secrets (CRÍTICO para CI/CD)
```bash
# En GitHub UI: Settings > Secrets and variables > Actions > New

MISTRAL_API_KEY           # sk-...
SABIONDA_API_KEY          # API key Sabionda
HETZNER_TOKEN             # Hetzner Cloud token
HETZNER_SSH_KEY_ID        # ID del SSH key en Hetzner
GAIACHAIN_PRIVATE_KEY     # GaiaChain key
ENCRYPTION_KEY            # AES-256 key (base64)
DB_PASSWORD               # PostgreSQL password
JWT_SECRET_KEY            # JWT secret
```

### 2. Verificar Workflows
```
GitHub > Actions > reconcile-ci.yml
Debe estar habilitado y listo
```

### 3. Cambiar Rama Default (Opcional)
```
Settings > Branches > Default branch
Seleccionar: feat/excelencia-operativa
```

---

## 📊 Resumen Transferencia

| Métrica | Valor |
|---------|-------|
| **Archivos nuevos** | 26 |
| **Tests** | 44/44 passing ✅ |
| **Tamaño repo** | ~3.8 MB |
| **Commits** | c7e2a4f (consolidado) |
| **Documentación** | 1,500+ líneas |
| **Tiempo estimado** | 2-5 min (script) |

---

## 🔗 Después de Transferencia

Ver archivo completo: [GITHUB-TRANSFER.md](GITHUB-TRANSFER.md)

Pasos avanzados:
1. Sincronizar cambios futuros
2. Configurar protección de rama
3. Habilitar automergencia en CI
4. Setup de despliegue en Hetzner
5. Configurar n8n workflow

---

## 📞 Soporte

Si algo falla:
1. Lee sección "⚠️ Solución Rápida de Problemas"
2. Revisa [GITHUB-TRANSFER.md](GITHUB-TRANSFER.md) (guía completa)
3. Verifica que GitHub repo esté creado: https://github.com/Traky12/goldfish

---

**Listo?** 🚀

```bash
bash scripts/github-transfer.sh
```
