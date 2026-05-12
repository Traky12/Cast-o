# Automatización de Validación LIMS

**Objetivo**: Reducir tiempo de validación manual (objetivo -50 %). Validar THC/CBD y datos de laboratorio antes de certificar. Plazo: 2 meses (corto plazo 2026).

---

## Componentes

- **Entrada**: Datos de LIMS CTAEX (vía `POST /sync/lims` o EDI/API).
- **Validación automática**: Reglas (THC ≤ 0,3 %, rangos CBD, metales pesados, pesticidas). Opcional: modelo de IA para detección de anomalías.
- **Salida**: Aprobación/rechazo; registro en GaiaChain; notificación a CTAEX (webhook).

---

## Integración

- Usar `backend/routers/lims_sync.py` como punto de entrada.
- Opcional: tarea Celery para colas y reintentos.
- Documentar reglas de negocio en este documento o en código (comentarios / tests).

---

## Referencias

- [CTAEX LIMS](CTAEX-LIMS.md) (si existe)
- [Plan de Contingencia 2.0](../risk/Contingency-Plan-v2.0.md) para fallos LIMS
