# Evaluación de impacto (EIPD / DPIA) — plantilla

## 1. Descripción del tratamiento

- **Nombre:** [p. ej. Soporte con modelo de lenguaje fine-tuned]
- **Responsable:** [organización]
- **Finalidad:** [responder consultas; mejora continua con datos pseudonimizados]
- **Flujo:** origen → almacenamiento → inferencia → logs → retención

## 2. Necesidad y proporcionalidad

- ¿Es necesario el tratamiento?
- ¿Alternativas menos intrusivas (solo humano, modelo más pequeño, reglas)?

## 3. Riesgos

| Riesgo | Prob. (1-5) | Impacto (1-5) | Mitigación |
|--------|-------------|---------------|------------|
| Filtración de datos | | | Cifrado, acceso mínimo, backups |
| Sesgo / respuestas incorrectas | | | Revisión humana selectiva, pruebas |
| Memorización en modelo | | | Minimización, evaluaciones, retención acotada |

## 4. Medidas

- Técnicas: TLS, cifrado en reposo, pseudonimización, RBAC.
- Organizativas: formación, DPO, runbook de incidentes.
- Legales: encargos, transferencias internacionales si aplica.

## 5. Consulta a interesados

- [ ] Encuesta / consulta cuando proceda

## 6. Conclusión

- ¿Procede el tratamiento con medidas propuestas?
- Próxima revisión: [fecha]
