# AI Policy — CASTÚO-SYSTEM v1.7.4

Cumplimiento EU AI Act (plazo principal agosto 2026). Uso de sistemas de IA en desarrollo documentado, clasificación de riesgo y supervisión humana.

---

## Estado: Agosto 2026 READY (Main deadline)

| Requisito | Estado | Nota |
|-----------|--------|------|
| Inventario AI | ✅ | GitHub Copilot documentado |
| Risk classification | ✅ | Low-risk (herramienta de desarrollo) |
| Policies | ✅ | Human review de PRs obligatorio |
| Logging | ✅ | Commits GitHub públicos audibles |
| RACI | ✅ | Gregorio Jiménez = AI Responsible Person |

---

## Prohibiciones (desde feb 2025) — NO APLICA

- **Social scoring:** CASTÚO no utiliza.
- **Biometría para identificación remota en tiempo real (uso prohibido):** CASTÚO no utiliza.

Ningún uso de IA del proyecto cae en las categorías prohibidas del Reglamento UE.

---

## CASTÚO-SYSTEM → GitHub Copilot Business (€19/usuario/mes)

### 1. Licencia

- **Producto:** GitHub Copilot (plan Business).
- **Conformidad:** EU compliant; uso como asistente de código en desarrollo.
- **Coste:** €19/usuario/mes (según tarifa GitHub).

### 2. Política

- **Todos los PRs con código sugerido por Copilot requieren revisión humana** antes de merge.
- No se hace merge a `main` sin al menos una aprobación humana (branch protection).

### 3. Documentación

- **Política de IA:** Este documento (`docs/legal/AI_POLICY.md`).
- **Inventario:** Herramienta registrada = GitHub Copilot Coding Agent (Business).

### 4. RACI

- **AI Responsible Person (RACI):** Gregorio Jiménez — CTO CASTÚO 360 S.L.  
- Contacto: gregorio@castuo.es  
- Responsable de cumplimiento, políticas de uso y supervisión humana.

### 5. Logs

- **Trazabilidad:** Commits en GitHub (públicos o visibles para la organización) audibles.
- Todo cambio que pase por Copilot queda en historial de commits tras revisión humana.

**Tiempo de implementación documental:** ~15 minutos → 100% EU AI Act ready (para uso low-risk documentado).

---

## Uso autorizado

- ✅ Corrección de bugs, implementación de features, tests y documentación con asistencia de Copilot.
- ✅ Código generado o sugerido por Copilot como punto de partida, siempre con revisión y aprobación humana.

## Uso no autorizado

- ❌ Llevar a producción código generado por IA sin revisión humana.
- ❌ Merge a rama protegida sin aprobación de al menos un revisor humano.

---

## Branch protection (recomendado)

```bash
# Ejemplo con GitHub CLI (ajustar según repo)
gh repo edit --enable-merge-commit false
gh api repos/:owner/:repo/branches/main/protection -X PUT -f required_pull_request_reviews=1 -f enforce_admins=true
```

O en GitHub: Settings → Branches → Branch protection rules para `main`: *Require a pull request before merging*, *Require approvals* ≥ 1.

---

## Comandos rápidos (dejar listo en ~15 min)

```bash
# 1. Licencia: GitHub Settings → Copilot Business → €19/mes

# 2. Branch protection (revisión humana obligatoria)
gh repo edit --enable-merge-commit false
# Luego en GitHub: Settings → Branches → Add rule for main → Require pull request, Require 1 approval

# 3. Política documentada (este archivo)
# docs/legal/AI_POLICY.md ya creado

# 4. Commit y push
git add docs/legal/AI_POLICY.md README.md
git commit -m "EU AI Act: Copilot Business policy, human review, RACI"
git push origin main
```

---

*Referencia: Reglamento (UE) 2026 (EU AI Act); clasificación low-risk para herramientas de asistencia al desarrollo. Última actualización: v1.7.4.*
