# DPIA — Análisis de Impacto de Protección de Datos (GDPR Art. 35)

**ESTADO**: `PLACEHOLDER:` Reemplazar por PDF firmado cuando esté completo.

Este documento existe en Markdown para iteración y auditoría. La versión final para despliegue real debe exportarse y firmarse (p.ej. como PDF) por el DPO/Responsable.

---

## 1) Descripción del tratamiento

| Campo | Detalle |
|------|---------|
| Nombre del tratamiento | `PLACEHOLDER:` |
| Responsable | `PLACEHOLDER:` |
| Finalidad | `PLACEHOLDER:` |
| Categorías de datos | `PLACEHOLDER:` (minimizar) |
| Categorías de interesados | `PLACEHOLDER:` |
| Sistemas | talleres / foro / certificados (según aplique) |

---

## 2) Necesidad y proporcionalidad

- Minimización: recoger solo lo imprescindible.
- Offline-first: preferir talleres sin cuentas ni emails salvo necesidad.
- Transparencia: explicar en lenguaje claro.

---

## 3) Riesgos

| Riesgo | Probabilidad (1–5) | Impacto (1–5) | Mitigación | Riesgo residual |
|-------|---------------------|---------------|------------|-----------------|
| Filtración de emails | `PLACEHOLDER:` | `PLACEHOLDER:` | AES-256-GCM + acceso limitado | `PLACEHOLDER:` |
| Acceso no autorizado | `PLACEHOLDER:` | `PLACEHOLDER:` | 2FA + rate limit (si hay foro) | `PLACEHOLDER:` |
| Pérdida de datos | `PLACEHOLDER:` | `PLACEHOLDER:` | backups cifrados + integridad | `PLACEHOLDER:` |

---

## 4) Medidas (GDPR Art. 32)

- Cifrado (si aplica): `scripts/seguridad/encriptar_aes_gcm.py`
- Integridad: `scripts/seguridad/generar_manifiesto.py` → `docs/lengua-comun/DASHBOARD/integridad.sha256.json`
- Registro Art. 30: `docs/legal/REGISTRO-DE-ACTIVIDADES.json`
- Incidentes: `docs/legal/INCIDENTES.md`

### 4.1) Encargados: NTN / 5G / plataforma IoT

Si la telemetría (o metadatos) sale del perímetro CASTÚO hacia **NTN (p. ej. 5G-IoT satelital)**, **núcleo 5G** u **hosting/IoT cloud** (p. ej. Arsys), cada proveedor activo debe constar como encargado/subencargado en el **Registro Art. 30** y contar con **DPA** y ubicación de datos acordes. Revisar transferencias fuera del EEE; TLS en tránsito; minimizar payload. Si el **gemelo digital** actúa como punto único de verdad antes de CASTÚO, documentar tratamiento, retención y subprocessors del servicio GEMelo. Borrador de arquitectura: `docs/architecture/TRL10-CONEC-EU-SATELIOT-NEXTEPC-ARSYS.md`.

---

## 5) Conclusión

- Riesgo residual global: `PLACEHOLDER: Bajo/Medio/Alto`
- Revisión: `PLACEHOLDER: periodicidad`

### Firma (DPO / responsable)

- Nombre: `PLACEHOLDER:`
- Fecha: `PLACEHOLDER:`
- Firma: `PLACEHOLDER:`

---

## Documentos relacionados

- [PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md](./PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md) — marco 90 días, scripts verificables y límites (no certificación automática).

