# Evaluación de impacto relativo a la protección de datos (EIPD / DPIA) — plantilla

## 1. Descripción del tratamiento

- **Nombre del tratamiento:** [p. ej. Asistente FAQ con modelo de lenguaje]
- **Responsable:** [organización]
- **Encargados:** [proveedores, hosting, modelo base]
- **Finalidad:** [responder consultas, formación, etc.]
- **Flujo de datos:** origen → almacenamiento → inferencia → logs → retención

## 2. Necesidad y proporcionalidad

- ¿Es necesario el tratamiento para la finalidad?
- ¿Existen alternativas menos intrusivas (humano, reglas, modelo más pequeño)?

## 3. Riesgos para interesados

| Riesgo | Probabilidad (1-5) | Impacto (1-5) | Mitigación |
|--------|---------------------|---------------|------------|
| Fuga de datos personales | | | Cifrado, acceso RBAC, pentest |
| Memorización en modelo | | | Minimización datos, evaluaciones, fine-tune controlado |
| Sesgo / respuestas incorrectas | | | Revisión humana en casos sensibles, monitorización |

## 4. Medidas técnicas y organizativas

- Segregación de entornos, secretos fuera del repo, backups cifrados.
- Formación y procedimientos de incidentes.

## 5. Consulta a interesados o representantes

- [ ] ¿Se ha consultado a AAPP o grupos afectados cuando proceda?

## 6. Conclusión y revisión

- ¿Procede el tratamiento con las medidas propuestas?
- Fecha próxima revisión: [ ]
