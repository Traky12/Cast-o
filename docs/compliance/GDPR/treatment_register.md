# Registro de actividades de tratamiento (plantilla Art. 30 RGPD)

Sustituir corchetes por datos reales. Mantener versión fechada y responsable interno.

| ID | Actividad | Finalidad | Base legal | Categorías de datos | Destinatarios | Plazo conservación | Medidas seguridad |
|----|-----------|-----------|------------|---------------------|---------------|-------------------|-------------------|
| 1 | Soporte estudiantes (FAQ / chat) | Responder consultas | Consentimiento / ejecución contrato | Identificadores de contacto, contenido consulta | Personal autorizado, encargados con contrato | [p. ej. 12 meses inactividad] | Cifrado en tránsito, control acceso |
| 2 | Mejora modelo IA (LoRA) | Ajuste asistente | Interés legítimo / consentimiento explícito si aplica | Texto pseudonimizado, métricas agregadas | Proveedor nube si existe (DPA) | Hasta revocación o fin proyecto | Entornos segregados, sin secretos en repos |
| 3 | Métricas operativas | Observabilidad | Interés legítimo | Logs técnicos, IDs pseudónimos | Equipo interno | [p. ej. 90 días] | Minimización, rotación logs |

**Nota:** el entrenamiento con datos personales directos suele exigir base legal sólida, DPIA y transparencia; preferir datos ya pseudonimizados o sintéticos cuando sea posible.
