# Cursor + n8n — configuración segura reproducible (Castúo-System)

**Tiempo:** ~5–10 minutos.

Este documento alinea la intención (workspace trust, MCP, n8n) con **archivos versionados en el repo** y con **comandos reales**.

---

## 1. Archivos versionados en el repo

| Archivo | Rol |
|---------|-----|
| `.vscode/settings.json` | Trust del workspace, archivos no confiables, MCP sin auto-aprobación (si la versión lo aplica), autoSave off. |
| `.devcontainer/devcontainer.json` | **Opcional:** contenedor con `cap-drop` y `no-new-privileges` para aislamiento. |
| `.cursor/CURSOR-IMMEDIATE-SECURE.md` | Esta guía. |
| `docs/deploy/n8n-security-policy.example.json` | **Plantilla** de política (n8n no la lee sola; mapear a ENV + UI). |
| `scripts/n8n/validate_n8n_security.sh` | Comprueba CLI `n8n` si existe y la plantilla anterior. |
| `n8n/workflows/castuo-secure-http-placeholder.json` | Workflow mínimo de referencia (HTTP deshabilitado hasta URL real). |

### Importante: `.cursor/` en este monorepo

Se **versionan** `.cursor/rules/`, `.cursor/settings.json` (p. ej. GitLab) y `.cursor/security/`.  
**No** añadas una regla `.cursor/` en `.gitignore`: dejaría fuera reglas del kernel y Sabionda.

El ajuste global del **usuario** sigue en `%APPDATA%\Cursor\User\settings.json` (Windows) o `~/.config/Cursor/User/settings.json` (Linux).

### `.gitignore` y `.vscode/`

En el repo se usa **`.vscode/*`** + **`!.vscode/settings.json`** (no solo `.vscode/` + negación): así Git versiona solo `settings.json` y evita problemas al re-incluir un archivo dentro de un directorio ignorado en algunas versiones.

### `.cursor/settings.json` (forma JSON)

El archivo real usa el objeto anidado estándar de Cursor/VS Code: `"plugins": { "gitlab": { "enabled": true } }`. No uses la forma plana `plugins.gitlab` en JSON (no es válida).

---

## 2. Workspace Trust (Windows)

1. Abre la raíz del repo en Cursor.
2. **File → Preferences → Settings** (`Ctrl+,`) o **Preferences: Open User Settings (JSON)**.
3. Alinea **usuario** y **repo** con las mismas claves que `.vscode/settings.json`:
   - `security.workspace.trust.enabled`: `true`
   - `security.workspace.trust.untrustedFiles`: `prompt`
   - `cursor.mcp.autoApprove`: `false` (si tu build lo reconoce)
   - `files.autoSave`: `off`

### Linux / macOS

- Usuario: `~/.config/Cursor/User/settings.json` o `~/Library/Application Support/Cursor/User/settings.json`.

---

## 3. Comandos reales (no genéricos)

| Intención | Comando / acción |
|-----------|-------------------|
| Abrir el repo | **Open Folder** al clon; no uses URIs inventadas (`sandboxed-castuo-dev`) sin Dev Container definido. |
| Dev Container | **Command Palette → Dev Containers: Reopen in Container** si existe `.devcontainer/devcontainer.json`. |
| Activar workflow (CLI) | `n8n update:workflow --id=<ID> --active=true` (sintaxis exacta: `n8n --help` en tu versión). |
| Endurecer n8n | UI: **Settings → Workflow Security**; variables de entorno del contenedor; WAF/proxy delante. |

### Sobre `security.restrictUntrustedMode`

No forma parte del esquema estable documentado de VS Code como clave única con ese nombre; el comportamiento de **modo restringido** lo gobierna **Workspace Trust**. Por eso **no** está en `.vscode/settings.json` del repo.

---

## 4. Validación rápida (Cursor)

1. Abre un archivo desde una carpeta que Cursor trate como no confiable: debe **pedir confirmación** si `untrustedFiles` es `prompt`.
2. Confirma que `.vscode/settings.json` está presente y coincide con lo que quieres en equipo.
3. MCP: prueba una herramienta MCP; no debe ejecutarse sin confirmación si tienes desactivada la auto-aprobación.

---

## 5. Validación n8n (repo)

Desde la raíz del repo (Git Bash / WSL / Linux / macOS):

```bash
bash scripts/n8n/validate_n8n_security.sh
```

Si **no** tienes `n8n` en el PATH pero sí en Docker:

```bash
N8N_ALLOW_MISSING_CLI=1 bash scripts/n8n/validate_n8n_security.sh
```

En Windows sin bash, revisa manualmente:

```bash
n8n --version
```

y abre `docs/deploy/n8n-security-policy.example.json` como checklist frente a tu despliegue.

---

## 6. Git: qué incluir en el commit

Ejemplo:

```bash
git add .vscode/settings.json .gitignore .cursor/CURSOR-IMMEDIATE-SECURE.md \
  .devcontainer/devcontainer.json docs/deploy/n8n-security-policy.example.json \
  scripts/n8n/validate_n8n_security.sh n8n/workflows/castuo-secure-http-placeholder.json
git commit -m "docs(security): Cursor workspace trust, devcontainer opcional, n8n referencia"
```

---

## 7. Referencias

- Orquestación n8n en repo: `n8n/README-AGRI-BRAIN.md`
- Web avanzada / CORS: `docs/architecture/SABIONDA-N8N-WEB-FRONTEND.md`
