# Registro en EU AI Database — Modelos de IA (AI Act)

**Objetivo**: Cada modelo de IA de alto riesgo registrado en EU AI Database con propósito, datos de entrenamiento y métricas de sesgo. Cumplimiento 100 %.

---

## Campos a registrar (referencia)

- **Propósito**: Ej. "Predicción de plagas en cultivos".
- **Datos de entrenamiento**: Fuente (ej. CTAEX 2020–2023), tamaño, procedencia.
- **Métricas de sesgo**: Ej. demographic parity 0,92; igualdad de oportunidades (documentar con fairlearn o equivalente).
- **Nivel de riesgo**: Alto (según Art. 8 AI Act) para sistemas que afecten salud o seguridad.

---

## Proceso

1. Clasificar modelo (alto riesgo según anexos AI Act).
2. Preparar documentación (propósito, datos, métricas, medidas de mitigación de sesgo).
3. Registrar en el portal EU AI Database cuando esté operativo (o en registro nacional si aplica).
4. Actualizar ante cambios sustanciales del modelo.

---

## Referencias

- [Sabionda-Barriers-v6.1.md](../security/Sabionda-Barriers-v6.1.md) § 4
- [AI compliance](backend/services/ai_compliance.py), [AI transparency](backend/services/ai_transparency.py)
