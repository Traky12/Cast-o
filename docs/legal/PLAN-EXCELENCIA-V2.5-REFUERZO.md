# 📜 Plan de excelencia (v2.5) — refuerzo operativo

**Ámbito:** Castúo-System — priorización técnica y contractual. **No** sustituye asesoramiento legal ni agrotécnico.

**Honestidad del repositorio:** no incluir en código URLs MAPA/SIGPAC inventadas. Cualquier `base_url` de API oficial solo tras contrato y documentación emitida por MAPA/FEGA. Ver [ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md](./ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md).

**Relación:** [PLAN-EXCELENCIA-INTEGRAL-CASTUO-SYSTEM.md](./PLAN-EXCELENCIA-INTEGRAL-CASTUO-SYSTEM.md) (síntesis operativa + empresarial + legal-social) · [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](./PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) (matriz A/B/C secrets + Vault; prontuario maestro refuerzo) · [CHECKLIST-TRL6-HETZNER-STAGING.md](../deploy/CHECKLIST-TRL6-HETZNER-STAGING.md) (edge + pytest + DPO §6) · [ROADMAP-TRL6-TRL7-CODE.md](../deploy/ROADMAP-TRL6-TRL7-CODE.md) · [ROADMAP-MEJORAS-P1-P5-2026.md](../deploy/ROADMAP-MEJORAS-P1-P5-2026.md) · [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](../deploy/CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) · [DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md](./DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md) · [PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md](./PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md) (fases TRL campo + piloto; sin cifras contractuales en git) · [SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md](./SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md) (rol `admin_general` + playbook seguridad en código) · [PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md](./PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md) (matriz normativa + robotics lab, orientativo) · [PRONTUARIO-MAESTRO-EXCELENCIA-SISTEMA-ANALISIS.md](../PRONTUARIO-MAESTRO-EXCELENCIA-SISTEMA-ANALISIS.md) · [PRONTUARIO-MAESTRO-MEJORA-CASTUO-SYSTEM.md](./PRONTUARIO-MAESTRO-MEJORA-CASTUO-SYSTEM.md) · [PRONTUARIO-MAESTRO-CONSULTA-CRITICA-CASTUO-SYSTEM.md](./PRONTUARIO-MAESTRO-CONSULTA-CRITICA-CASTUO-SYSTEM.md) · [RUTA-CONQUISTADORAS-CASTUO-LINK.md](./RUTA-CONQUISTADORAS-CASTUO-LINK.md) · [ANALISIS-CRITICO-EXCELENCIA-V2.5.md](./ANALISIS-CRITICO-EXCELENCIA-V2.5.md) · [PLAN-INTEGRACION-TECNICAS-AVANZADAS-V2.5.md](./PLAN-INTEGRACION-TECNICAS-AVANZADAS-V2.5.md) · [PLAN-INTEGRACION-REFORZADO-CASTUO-6.md](./PLAN-INTEGRACION-REFORZADO-CASTUO-6.md) · [DISENO-INTEGRAL-ECOSISTEMA-CASTUO-6.md](./DISENO-INTEGRAL-ECOSISTEMA-CASTUO-6.md) · [PRONTUARIO-MAESTRO-AUDITORIA-INTERNA.md](./PRONTUARIO-MAESTRO-AUDITORIA-INTERNA.md) · [PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md](./PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md)

---

## 1. Automatizar procesos críticos

### 1.1. SIGPAC (prioridad alta)

**Problemática actual**

- Descarga manual de GeoJSON desde SIGPAC Visor (`https://sigpac.mapa.gob.es/` — visor público, no API de integración en repo).
- Validación local con `sigpac_validator.py` (GDAL opcional).

**Solución propuesta (diseño; pseudocódigo)**

`base_url` y alcance del API **solo** con evidencia contractual — **prohibido** hardcodear patrones tipo `https://api.sigpac...` hasta exista fuente oficial.

```python
# backend/integrations/sigpac_api_client.py — diseño futuro (no copiar URL ficticia)
class SIGPACApiClient:
    def __init__(self, auth_token: str, base_url: str):
        self.auth_token = auth_token
        self.base_url = base_url.rstrip("/")  # p. ej. variable de entorno tras contrato

    def get_parcel_geometry(self, parcel_id: str) -> dict:
        raise NotImplementedError("Requiere contrato MAPA/FEGA y especificación de API")

    def validate_parcel(self, parcel_id: str) -> dict:
        raise NotImplementedError("Requiere contrato MAPA/FEGA y especificación de API")
```

**Acciones**

| Acción | Equipo | Plazo orientativo |
|--------|--------|-------------------|
| Negociar contrato MAPA/FEGA | Legal | 4 semanas |
| Cliente OAuth2 | Backend | 3 semanas |
| Sustituir/ampliar `sigpac_remote_placeholder.py` | Backend | acoplado a contrato |

```python
# backend/integrations/sigpac_auth.py — esbozo
def get_sigpac_token(client_id: str, client_secret: str, token_url: str) -> str:
    """OAuth2: token_url y scopes según documentación oficial entregada con el contrato."""
    raise NotImplementedError
```

**Integración progresiva**

1. Validación básica de parcelas vía API acordada.  
2. Eventos / webhooks si el servicio oficial los ofrece (sin asumirlos en código hoy).

**Métricas objetivo (indicativas)**

- Reducción relevante del tiempo de ciclo de validación (medir antes/después).  
- Menos errores manuales en ingesta de geometría — **no** prometer «0 errores» como garantía del git.

### 1.2. Datos climáticos (prioridad media)

**Problemática actual:** umbrales en `extremadura_climate.yaml`; sin ingestión AEMET operativa en producción (mocks en tests).

**Solución propuesta (stub realista)**

La URL de OpenData AEMET es pública; la **clave API** y límites de uso son contractuales.

```python
# backend/ctaex/aemet_client.py — diseño
class AEMETClient:
    def __init__(self, api_key: str, base_url: str = "https://opendata.aemet.es/opendata/api"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def get_weather_data(self, station_id: str) -> dict:
        raise NotImplementedError("Requiere clave API AEMET y términos aceptados")

    def get_et0_data(self, lat: float, lon: float) -> dict:
        raise NotImplementedError("Requiere clave API AEMET y producto/endpoint acordado")
```

**Acciones:** solicitar clave API; implementar `ClimateService` que combine ingestión + `ExtremaduraClimateConfig` con fallback a YAML.

**Modelos predictivos:** evaluar Mistral-7B u otros bajo ADR, soberanía de datos y coste — **no** fijar proveedor en repo sin decisión explícita.

**Métricas objetivo (indicativas):** actualización periódica de umbrales; mejora de precisión de alertas — medir con conjunto de validación acordado (no fijar «>90 %» como certificación automática).

---

## 2. Mejorar seguridad y cumplimiento

### 2.1. Cifrado post-cuántico (prioridad alta)

**Estado repo:** `backend/security/pq_crypto.py` (Kyber-1024 / Dilithium-5 vía `pqcrypto` si instalado; fallback documentado en módulo).

**Objetivo operativo:** TLS 1.3 en perímetro, gestión de claves (HSM o secret store), rotación — ver [PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md](./PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md).

**Métricas:** ampliar % de datos sensibles protegidos según política interna; rotación con calendario acordado — **no** afirmar «100 % PQC en reposo en todo el sistema» sin auditoría de despliegue.

### 2.1 bis. Trazabilidad secretos — estado del despliegue (A / B / C)

| Opción | Significado | Dónde queda fijado en el clon |
|--------|-------------|-------------------------------|
| **A** | Docker Secrets + `CASTUO_*_FILE` | `docs/deploy/robotics-lab-hetzner.env.example`, `backend/auth_roles.read_secret` |
| **B** | Vault KV v2 + `VAULT_ADDR` + `VAULT_TOKEN_FILE` | `backend/security/VAULT_KV_PATHS.md`, `backend/security/vault.py` |
| **C** | Valores directos en `.env` | Solo dev local comentado; **no** producción ni repo |

Coherencia operativa: [SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md](./SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md) §5.1 · `backend/config/security.md`.

### 2.2. Auditorías automatizadas (prioridad media)

**Estado repo:** `scripts/audit/audit_repo_evidence_check.py` = inventario de rutas, no sustituto de auditoría externa.

**Diseño futuro:** orquestar comprobaciones + integración con herramientas de cumplimiento bajo DPA. Los ejemplos tipo `AutomatedAudit` con retorno fijo `OK` son **ilustrativos**, no evidencia de cumplimiento.

---

## 3. Optimizar infraestructura

### 3.1. CI/CD para GDAL (prioridad alta)

Ejemplo de flujo (ajustar versiones de acciones y método de instalación GDAL en Windows):

```yaml
# .github/workflows/gdal-ci.yml — borrador
name: GDAL CI
on: [push, pull_request]
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install GDAL
        run: choco install gdal -y
      - name: Run tests
        run: pytest tests/integrations/test_sigpac_validator.py -q
```

**Nota:** validar que el runner resuelve `osgeo` de forma estable; documentar en `requirements-sigpac-gdal.txt` y guía de desarrollo.

### 3.2. Pruebas de integración

**Estado orientativo:** suite `pytest tests/` con skips esperables (E2E Selenium, API viva — ver `CASTUO_FORCE_LIVE_API`, `tests/requirements.txt`).

**Objetivo:** más cobertura en informes y rutas audit; E2E opcionales — **no** «0 skipped» como exigencia global sin entorno dedicado.

---

## 4. Integrar tecnologías europeas

### 4.1. Gaia-X (roadmap)

Cliente y proveedor de identidad **solo** con marco contractual y APIs reales del ecosistema Gaia-X. No añadir paquete `backend/gaiax/` con implementación ficticia hasta especificación.

### 4.2. Copernicus (roadmap)

Claves, productos (CDS, etc.) y límites según portal oficial. Stub con `NotImplementedError` y `base_url` configurable aceptable; sin datos simulados como «producción».

---

## 5. Resumen de evidencias (84/84)

El inventario completo lo mantiene `scripts/audit/audit_repo_evidence_check.py` (`REQUIRED_EVIDENCE`). Ejemplos:

| ID | Evidencia | Verificada | Notas |
|----|-----------|------------|--------|
| 1.1 | Validación SIGPAC local | ✅ | `sigpac_validator.py` |
| 1.2 | Umbrales climáticos YAML | ✅ | `extremadura_climate.yaml` |
| … | … | … | … |
| (ejemplo legal) | Prontuario soberanía EU | ✅ | `PRONTUARIO-MAESTRO-DEBILIDADES-POTENCIAL-SOBERANIA-EU.md` |
| (ejemplo legal) | Plan integración reforzado Castuo 6 | ✅ | `PLAN-INTEGRACION-REFORZADO-CASTUO-6.md` |
| (ejemplo legal) | Diseño integral ecosistema Castuo 6 | ✅ | `DISENO-INTEGRAL-ECOSISTEMA-CASTUO-6.md` |
| (ejemplo legal) | Plan excelencia integral Castuo System | ✅ | `PLAN-EXCELENCIA-INTEGRAL-CASTUO-SYSTEM.md` |
| (ejemplo legal) | Prontuario cifrado y roles v2.5 | ✅ | `PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md` |
| (ejemplo legal) | Análisis crítico excelencia v2.5 | ✅ | `ANALISIS-CRITICO-EXCELENCIA-V2.5.md` |
| (ejemplo legal) | Prontuario consulta crítica | ✅ | `PRONTUARIO-MAESTRO-CONSULTA-CRITICA-CASTUO-SYSTEM.md` |

Ejecutar: `python scripts/audit/audit_repo_evidence_check.py`.

---

## 6. Conclusión

- Automatizar SIGPAC y clima con **contrato y fuentes oficiales**.  
- Reforzar seguridad (PQC módulo + despliegue) y auditoría asistida sin confundir script con auditor externo.  
- CI GDAL, pruebas ampliadas, Gaia-X y Copernicus como roadmap documentado.

**Enlaces:** [PRONTUARIO-MAESTRO-AUDITORIA-INTERNA.md](./PRONTUARIO-MAESTRO-AUDITORIA-INTERNA.md) · [ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md](./ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md)

**Notas para Cursor**

1. Leer [PRONTUARIO-MAESTRO-AUDITORIA-INTERNA.md](./PRONTUARIO-MAESTRO-AUDITORIA-INTERNA.md) (v2.5) antes de integraciones externas.  
2. **No inventar** endpoints MAPA/AEMPS/CAAE: usar marcos en `docs/legal/` y placeholders hasta contrato.

*Documento de refuerzo v2.5 — alineado a honestidad de repositorio.*
