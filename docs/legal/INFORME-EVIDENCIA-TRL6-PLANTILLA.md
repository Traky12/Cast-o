# Plantilla — informe de evidencia TRL6 (trazabilidad verificable)

**Versión:** 2026-03-22 · **Ámbito:** laboratorio robotics / edge Castúo-System.

**Límite legal:** este informe documenta **resultados de pruebas automatizadas y despliegue** en un instante. **No** constituye certificación TRL oficial, **no** sustituye [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) ni decisión del DPO sobre §6.

---

## 1. Identificación del ejercicio

| Campo | Valor |
|--------|--------|
| Fecha / hora (UTC) | |
| Responsable técnico | |
| Entorno | `local` / `CI` / `Hetzner staging` / otro |
| Commit git (o etiqueta) | *copiar de `reports/trl6/manifest.json` → `git_commit`* |
| Versión Python | |

---

## 2. Evidencia de pruebas (gate `trl6`)

| Artefacto | Ruta / adjunto |
|-----------|----------------|
| Manifiesto máquina-legible | `reports/trl6/manifest.json` (generado por `Export-TRL6-Evidence.ps1`) |
| JUnit XML | `reports/trl6/junit.xml` |
| Salida consola pytest | `reports/trl6/pytest-console.txt` |

**Comando reproducible:**

```text
python -m pytest -m trl6 -q
```

**Resultado declarado (rellenar tras ejecución):** passed: \_\_\_ / skipped: \_\_\_ / failed: \_\_\_

---

## 3. E2E scripts (opcional)

| Script | Ejecutado (sí/no) | URL lab | Incidencias |
|--------|-------------------|---------|-------------|
| `scripts/windows/Invoke-TRL6-Validation.ps1` | | | |
| `scripts/windows/Test-Complete-RoboticsLab.ps1` | | | |

---

## 4. Despliegue edge (post-DPO)

| Paso | Evidencia (sí/no) |
|------|-------------------|
| Secretos Opción A/B (sin Opción C en prod) | |
| `scp` solo compose + `robotics-lab-hetzner.env.example` | |
| `GET /health` → `chain_status` coherente | |
| DPIA §6 revisado si cadena activa | |

Referencias: [CHECKLIST-TRL6-HETZNER-STAGING.md](../deploy/CHECKLIST-TRL6-HETZNER-STAGING.md) · [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](./PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md)

---

## 5. Coherencia y usabilidad

- **Usabilidad:** un solo gate documentado (`pytest -m trl6`) + script de evidencia para no discutir recuentos a mano.
- **Trazabilidad:** manifiesto con timestamp y commit.
- **Legalidad:** vínculo explícito con DPIA §6 y DPO antes de datos identificativos on-chain.
- **Coherencia:** mismos nombres que `pytest.ini`, `Invoke-TRL6-Validation.ps1` y compose scan3d.

---

## 6. Firma / cierre

| Rol | Nombre | Fecha |
|-----|--------|--------|
| Técnico | | |
| DPO (si aplica) | | |

---

*Los datos del informe deben ser los del manifiesto y del JUnit adjuntos, no una captura retocada.*
