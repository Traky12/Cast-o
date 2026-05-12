# ⚡ EJECUTOR DE PASOS: 3 Acciones = Transferencia Completa

**Tiempo Total:** 8 minutos | **Dificultad:** ⭐ (muy fácil)

---

## 🚀 PASO 1: CREAR REPOSITORIO EN GITHUB (2 minutos)

### 👉 Abre browser:
```
https://github.com/new
```

### 📝 Rellena el formulario:
| Campo | Valor |
|-------|-------|
| **Repository name** | `goldfish` |
| **Description** | `CASTUO-SYSTEM Hub v2.0` |
| **Visibility** | Private ⚫ |
| **Initialize** | ❌ (NO seleccionar nada) |

### ✅ Botón:
`Create repository`

### 📍 Resultado:
- **URL:** `https://github.com/Traky12/goldfish` (vacío, es normal)

---

## 🔗 PASO 2: TRANSFERIR ARCHIVOS (1 minuto)

### 👉 En terminal, ejecuta:

```bash
cd /workspaces/Castuo-system && \
bash scripts/github-transfer-complete.sh
```

**El script:**
- ✓ Verifica repo en GitHub
- ✓ Configura remoto `origin`
- ✓ Hace push de 28 archivos
- ✓ Muestra confirmación

**Interacción:** Responde `y` a confirmaciones (2-3 veces)

**Duración:** ~1 minuto (depende conexión)

---

## ✨ PASO 3: VERIFICAR EN GITHUB (1 minuto)

### 👉 Abre URL:
```
https://github.com/Traky12/goldfish/commits/feat/excelencia-operativa
```

### ✅ Verifica:
- [ ] **28 archivos** nuevos listados
- [ ] **3 commits** en historial
- [ ] **3,837 insertiones** (+)
- [ ] Carpetas: castuo_graph/, hetzner_infra/, tests/, docs/, n8n/, scripts/

**✅ Si ves todo esto → ¡TRANSFERENCIA EXITOSA!**

---

## 🔐 BONUS: CONFIGURAR SECRETS (5-10 minutos)

### 👉 Opción A: RÁPIDA (GitHub CLI)

Ejecuta (reemplaza `xxxxx` con tus valores):

```bash
gh secret set MISTRAL_API_KEY --body "sk-xxxxx" -R Traky12/goldfish
gh secret set SABIONDA_API_KEY --body "xxxxx" -R Traky12/goldfish
gh secret set HETZNER_TOKEN --body "xxxxx" -R Traky12/goldfish
gh secret set HETZNER_SSH_KEY_ID --body "xxxxx" -R Traky12/goldfish
gh secret set JWT_SECRET_KEY --body "xxxxx" -R Traky12/goldfish
gh secret set GAIACHAIN_PRIVATE_KEY --body "xxxxx" -R Traky12/goldfish
gh secret set DB_PASSWORD --body "xxxxx" -R Traky12/goldfish
gh secret set ENCRYPTION_KEY --body "xxxxx" -R Traky12/goldfish
```

### 👉 Opción B: MANUAL (GitHub UI)

1. Ve a: `https://github.com/Traky12/goldfish/settings/secrets/actions`
2. Click `New repository secret`
3. Para cada secret:
   - Name: `MISTRAL_API_KEY`
   - Secret: Tu valor real
   - Click `Add secret`
4. Repite para los 8 secrets

---

## 📋 CHECKLIST RÁPIDO

```
PASO 1: ☐ Crear repo en GitHub (https://github.com/new)
        ☐ Nombre: goldfish, Privado, Sin inicializar
        ☐ Resultado: https://github.com/Traky12/goldfish

PASO 2: ☐ Ejecutar: bash scripts/github-transfer-complete.sh
        ☐ Responder "y" a confirmaciones
        ☐ Esperar ~1 minuto

PASO 3: ☐ Verificar: https://github.com/Traky12/goldfish/commits/feat/excelencia-operativa
        ☐ Ver: 28 archivos, 3 commits, 3,837 insertiones
        ☐ ✅ ÉXITO

BONUS:  ☐ Configurar 8 secrets (CLI o UI)
```

---

## 🆘 PROBLEMAS?

| Problema | Solución |
|----------|----------|
| **"Repository not found"** | Ve a https://github.com/new y crea el repo primero |
| **"Authentication failed"** | Genera PAT: https://github.com/settings/tokens (permisos: repo + workflow) |
| **"Branch already exists"** | Normal, continúa con paso 3 |
| **"Permission denied"** | Verifica PAT tiene permisos: repo + workflow |

---

## ⏱️ TIMELINE

```
T+0:00   Abes https://github.com/new
T+1:00   Creas repo goldfish
T+1:30   Ejecutas: bash scripts/github-transfer-complete.sh
T+2:30   Script hace push (ves progreso)
T+3:00   Push completa
T+3:30   Verificas en GitHub → ves 28 archivos ✅
T+5:00   Configuras secrets (8 rápidas)
T+8:00   ✅ TRANSFERENCIA COMPLETA
```

---

## 🎯 DESPUÉS

- ✅ 28 archivos en GitHub
- ✅ 44 tests documentados
- ✅ Rama: feat/excelencia-operativa
- ✅ Listo para CI/CD y deployment

---

**Estado:** ✅ LISTO PARA EJECUTAR  
**Duración:** 8 minutos  
**Dificultad:** ⭐ muy fácil  
**Automatización:** 95% automática

🚀 **¡COMIENZA AHORA!**
