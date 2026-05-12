# CASTUO-SYSTEM™ — Git avanzado en Cursor

Integración nativa con IA, seguridad enterprise y workflows optimizados (Git 2.53+, Cursor AI, GitHub Enterprise).

---

## 1. Configuración base

### Requisitos

- **Git 2.53.0(2)** en todos los entornos (Windows/Linux).
- **Cursor AI** 2.0+ con Git AI 2.3.5 activado.
- **GitHub Enterprise**: repositorio privado con PAT (Personal Access Token), sin NTLM.

```bash
git --version   # Debe mostrar v2.53.0(2)

# Actualizar (Windows)
winget upgrade git.git

# Actualizar (Linux / Hetzner)
sudo apt update && sudo apt upgrade git
```

### Seguridad (post-CVE-2025-66413)

```bash
# Desactivar NTLM (mitigación CVE-2025-66413)
git config --global http.ntlm false

# HTTPS + PAT (GitHub)
git config --global credential.helper store
git config --global http.version HTTP/2

# Verificar
git config --list | grep -E "http|credential"
```

---

## 2. Workflow con Cursor Git AI 2.3.5

### Commits inteligentes (recomendado)

En lugar de mensajes genéricos, usar convención tipo Conventional Commits + trazabilidad:

```bash
# Ejemplo generado/ sugerido por Cursor AI
git commit -m "feat(monitoring): prometheus + grafana stack
- FastAPI instrumentator + 5 targets
- Alertas LER <1.2 + API P95 >500ms
- Puerto 3001 solución conflicto
- GS1 EPCIS TX:[a1b2c3...]"
```

### Composer → Git en un prompt

**Prompt en Cursor:** *"Deploy monitoring a producción + push GitHub"*

Cursor puede ejecutar (o guiarte):

```bash
docker-compose up -d --build api
git add .
git commit -m "[AI] feat(monitoring): deploy producción v5.2 + prometheus/grafana"
git push origin main
```

### Resolución de conflictos con IA

**Prompt:** *"Resuelve merge: prioriza métricas prometheus + alertas LER"*

Tras revisar los cambios, Cursor puede proponer la resolución y:

```bash
git add .
git commit -m "[AI] fix(merge): resuelto conflicto prometheus metrics"
git push
```

---

## 3. Workflow optimizado CASTUO-SYSTEM™

| Tarea                 | Git manual   | Cursor Git AI   | Ahorro            |
|-----------------------|-------------|------------------|-------------------|
| Commit monitoring     | ~2 min      | ~5 s (AI)        | Muy rápido        |
| Push a GitHub         | 3 comandos  | 1 prompt         | Automatizado      |
| Resolver merge        | ~5 min      | IA asiste        | Menos fricción    |
| Trazabilidad          | Manual      | TX hash (EPCIS)  | Compliance        |

---

## 4. Seguridad y trazabilidad enterprise

### Hooks de Git (AI Act + GDPR)

El repo incluye un **pre-commit** opcional que exige trazabilidad blockchain (TX hash GS1 EPCIS) en el mensaje de commit.

**Instalación (una vez):**

```bash
# Desde la raíz del repo
./scripts/setup-git-hooks.sh

# O manual (Linux/macOS/Git Bash)
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Si el hook está instalado, cada commit debe incluir en el mensaje un hash de tipo GS1 EPCIS, por ejemplo:

```text
TX:[a1b2c3d4e5f6789012345678abcdef12]
```

**Ejemplo de commit con trazabilidad:**

```bash
git commit -m "feat(drones): ruta optimizada sector 4
- 25 antenas Castuo Link activas
- ROI 62x (broccoli)
- TX:[a1b2c3d4e5f6...]"
```

Para commits que no requieran trazabilidad blockchain (por ejemplo docs o scripts locales), puedes hacer commit con `--no-verify` (usa con criterio y solo cuando sea adecuado).

### Trazabilidad con blockchain (GS1 EPCIS)

Los hashes en el mensaje de commit permiten vincular cambios de código con eventos en la cadena (GS1 EPCIS / Hyperledger) para auditoría y cumplimiento.

---

## 5. Métricas y alertas (Prometheus / Grafana)

Si se integra un exporter o script que exponga métricas de Git:

- **Métrica sugerida:** `git_commits_total{tx_hash="..."}` (o `tx_hash=""` cuando falte).
- **Alerta sugerida:** commits sin TX hash durante X tiempo → notificación (p. ej. en Alertmanager).

Ejemplo conceptual de regla (requiere un job de scraping real):

```yaml
# Ejemplo: solo si existe exporter que exponga git_commits_total
# - alert: GitCommitWithoutTX
#   expr: git_commits_total{tx_hash=""} > 0
#   for: 1m
#   labels: { severity: critical }
#   annotations:
#     summary: "Commit sin trazabilidad blockchain (GS1 EPCIS)"
```

Hasta tener ese exporter, la trazabilidad se garantiza con el **pre-commit** (sección 4).

---

## 6. Integración Cursor + GitHub Enterprise

### Comandos rápidos

- **Abrir proyecto:** ruta local del repo (p. ej. `Castuo-System`).
- **Desarrollar con IA:** `Ctrl+K` → describir feature (ej. *"Implementa módulo de smart contracts para BioCoin"*).
- **Commit + push:** pedir en el chat *"Push a GitHub castuo-system/main"* (Cursor puede ejecutar `git add`, `commit`, `push`).

### Flujo típico

1. Implementar feature con Cursor (Composer / Chat).
2. Revisar diff en la pestaña Source Control.
3. Commit con mensaje que incluya TX hash si aplica.
4. Push a `main` (o rama indicada).
5. Deploy en Hetzner: `docker-compose up -d` (o script de deploy del repo).

---

## 7. ROI y beneficios

| Aspecto      | Valor aproximado                          |
|-------------|--------------------------------------------|
| Coste       | Cursor + infra (p. ej. Hetzner)           |
| Ahorro      | Menos tiempo en workflows Git repetitivos  |
| Seguridad   | CVE-2025-66413 mitigado + HTTPS/PAT       |
| Trazabilidad| GS1 EPCIS + blockchain en commits         |

---

**Resumen:** Configura Git con HTTPS y PAT, desactiva NTLM, instala el pre-commit opcional para TX hash, y usa Cursor para commits, merges y push siguiendo esta guía.
