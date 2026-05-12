# Roadmap código TRL6 → TRL7 (Castúo robotics lab)

**Versión:** 2026-03-22 · **Orientativo:** no certifica TRL; describe **evidencia en repo** y huecos típicos hacia demo comercial.

**Relación:** [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md) · [ROADMAP-MEJORAS-P1-P5-2026.md](./ROADMAP-MEJORAS-P1-P5-2026.md) · [INFORME-EVIDENCIA-TRL6-PLANTILLA.md](../legal/INFORME-EVIDENCIA-TRL6-PLANTILLA.md) · [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) · [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) §6

---

## TRL6 — “relevant environment” (estado actual del clon)

| Capacidad | Código / artefacto | Evidencia automática |
|-----------|-------------------|------------------------|
| Lab HTTP snapshot + digest | `lab_stub_app.py` | `pytest -m trl6` |
| Admin playbook soberano | `system_admin_playbook.py`, `/admin_general/playbook` | incluido en `trl6` |
| Vault KV opcional | `vault.py`, `VAULT_TOKEN_FILE` | `tests/security/test_vault_optional.py` |
| Cadena opt-in | `lab_gaiachain_optional.py` | `chain_status` / `chain_registration` |
| Neuromórfico + Scan3D sim | `neuromorphic_edge`, `scan3d_print` | tests integración |
| Edge container | `docker-compose.scan3d.yml` | `healthcheck` → `/health` |
| Secretos dev local | `secrets/README.md` + `.gitignore` | Opción A sin Opción C |
| Evidencia auditable | `Export-TRL6-Evidence.ps1`, `export_trl6_evidence.sh` | `reports/trl6/junit.xml` + `manifest.json` + [INFORME-EVIDENCIA-TRL6-PLANTILLA.md](../legal/INFORME-EVIDENCIA-TRL6-PLANTILLA.md) |
| Caché SNN + TTL | `CASTUO_SNN_CACHE_REDIS_URL` | Tests `test_snn_cache_hit_reproducible`, `test_snn_cache_ttl_expiry` |
| SNN sim vs hardware memristor | `neuromorphic_edge` (TRL-4 **sim** en JSON) | [NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md](../integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md); **sin** test de oblea física en CI |

**Comandos (repo):** `pytest -m trl6` · `.\scripts\windows\Invoke-TRL6-Validation.ps1` (stub en marcha para E2E) · `.\scripts\windows\Invoke-TRL6-Validation.ps1 -Evidence` (JUnit + manifiesto + E2E).

---

## TRL7 — demo comercial / entorno calificado (próximas extensiones típicas)

| Necesidad | Dirección técnica | Trazabilidad |
|-----------|-------------------|--------------|
| Contrato auditado + red acordada | Despliegue fuera de stub; política `tokenId` | Informe auditoría **externo** al git |
| Multi-cliente / rate limits | API gateway, cuotas por Bearer | ADR + OpenAPI |
| Observabilidad | Métricas Prometheus, trazas | `health` + `/metrics` futuro |
| Datos personales en cadena | Solo tras DPO explícito | `CASTUO_ROBOTICS_LAB_CHAIN_INCLUDE_PARCEL_ID=1` documentado |
| CI bloqueante | Workflow GitHub `pytest -m trl6` | `.github/workflows/trl6-robotics-gate.yml` |

Los tests marcados `trl7` hoy amplían el núcleo robotics (`test_robotics_lab.py`); el conjunto TRL7 completo en CI puede expresarse como `pytest -m "trl6 or trl7"` cuando se añadan más casos.

---

*TRL7 no es más código en git: es contrato, agua medida en campo y decisión DPO donde el dato lo exija.*
