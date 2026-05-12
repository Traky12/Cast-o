# Plan de Pruebas de Usabilidad (ISO 9241-11:2018)

**Referencia**: NIST / TÜV Rheinland (certificación usabilidad).  
**Objetivo**: 90% de las tareas completadas sin errores.

---

## Criterios ISO 9241-11

| Criterio | Requisito | Acción | Herramienta |
|----------|-----------|--------|--------------|
| **Eficacia** | 90% tareas completadas sin errores | Pruebas con 20 usuarios reales (agricultores, técnicos CTAEX) | Plan de Pruebas |
| **Eficiencia** | Tiempo medio < 5 min por tarea | Optimizar flujos (ej: certificación de 6 a 3 pasos), heatmaps | Hotjar |
| **Satisfacción** | NPS > 70 | Encuestas post-uso Typeform | Encuesta NPS |
| **Accesibilidad** | WCAG 2.1 AA | Auditoría axe DevTools, corregir CSS/JS | Informe WCAG |
| **Multilingüe** | ES, EN, FR, DE (mínimo) | i18next, validar con nativos | Plan de Localización |

---

## Perfil de usuarios (20)

- **Agricultores / técnicos CTAEX**: 10 (España).
- **Técnicos de calidad / certificación**: 5.
- **Usuarios piloto Francia/Alemania**: 5 (para ES/EN/FR/DE).

---

## Tareas a medir

1. Completar registro de un lote (cannabis o microgreens).
2. Solicitar certificación AEMPS (flujo completo).
3. Consultar trazabilidad por QR / batch_id.
4. Interpretar dashboard de sensores IoT (temperatura, pH, EC).
5. Generar informe de cumplimiento (checklist UE).

**Métrica por tarea**: % completada sin error, tiempo en segundos.

---

## Documentos relacionados

- **Informe de Eficiencia**: `docs/validation/usability/Efficiency-Report-Template.md`
- **Encuesta NPS**: Typeform (pregunta "¿Recomendarías este sistema? 1-10").
- **Informe WCAG**: auditoría con axe DevTools.
- **Guía de Estilo UI/UX**: `docs/validation/usability/UI-UX-Style-Guide.md`
- **Auditoría externa TÜV Rheinland**: ~€10.000, plazo 3 meses.
