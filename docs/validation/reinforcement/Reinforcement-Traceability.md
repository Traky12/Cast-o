# Refuerzo de Riesgos/Debilidades — Trazabilidad (AEMPS/GlobalGAP)

| Riesgo/Debilidad | Acción de Refuerzo | Responsable | Plazo | Métrica de Éxito | Documentación |
|------------------|--------------------|-------------|--------|------------------|---------------|
| Falta de integración con sistemas aduaneros UE | Conector EDI para DUNS. Validar con Aduanas UE. | Backend Team | 4 meses | 100% lotes exportables con documentación aduanera automática | [Guía EDI Aduanas](../integration/EDI-Customs-Guide.md) |
| Validación manual de datos LIMS | Automatizar con IA (regresión) para detectar anomalías (THC > 0.3%). | IA Team | 3 meses | Reducción 50% en tiempo de validación manual | Modelo IA LIMS |
| Falta de geolocalización precisa | Google Maps API o OpenStreetMap. Coordenadas GPS <5 m. | Backend Team | 2 meses | 100% lotes con geolocalización válida | [Guía Geolocalización](../traceability/Geolocation-Guide.md) |
| Checklists digitales no automatizados | App móvil para agricultores (checklists en campo, offline). | Mobile Team | 3 meses | 90% checklists completados digitalmente (vs. papel) | App Checklists |
