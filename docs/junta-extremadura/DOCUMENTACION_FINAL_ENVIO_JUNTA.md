# Documentación Final para Envío a la Junta de Extremadura

Todo listo para copiar/pegar, enviar por email o exportar a PDF. Incluye plantilla de email, lista de adjuntos e instrucciones de exportación.

---

## 1. Email para envío a la Junta

**Asunto:** Propuesta de Colaboración para Implementación del Sistema ForestOwnershipToken en la Junta de Extremadura

**De:** Gregorio Jiménez Bodes \<gregorio.jimenez@castuo-system.com\>

**Para:** Dirección General de Medio Ambiente \<medioambiente@juntaex.es\>

**CC:**

- Dirección General de Economía Rural \<economiarural@juntaex.es\>
- Dirección General de Política Forestal \<politicaforestal@juntaex.es\>
- Asesoría Jurídica de la Junta \<asesoria.juridica@juntaex.es\>

**Fecha:** [15/04/2026] *(sustituir por fecha real)*

---

### Cuerpo del email

Estimados/as miembros de la Junta de Extremadura,

Adjunto a este correo envío la propuesta técnico-legal completa para la implementación del sistema **ForestOwnershipToken**, diseñado para tokenizar propiedades forestales con certificaciones PEFC/FSC/Red Natura 2000, calcular subvenciones automáticas (hasta €800–1.350/ha/año) y vincularse a mercados de carbono.

Este sistema cumple con todas las normativas aplicables (Ley 3/2023 de Montes, Decreto 45/2020, GDPR) y ofrece trazabilidad inmutable, seguridad (cifrado post-cuántico) y automatización de procesos administrativos.

**Documentos adjuntos:**

1. Propuesta Técnico-Legal Completa (PROPUESTA_TECNICO_LEGAL_FORESTOWNERSHIPTOKEN.pdf)
2. Anexo VII: Procedimiento de Derecho al Olvido — GDPR Art. 17 (ANEXO_VII_DERECHO_AL_OLVIDO.pdf)
3. Guía de Despliegue del Dashboard (guia_despliegue_dashboard.pdf)
4. Borrador de Acuerdo con SIGPAC (borrador_acuerdo_sigpac.pdf)
5. Plan de Formación para Técnicos (plan_formacion_tecnicos.pdf)
6. Lista de Propietarios Piloto (propietarios_piloto.csv)
7. *Opcional:* Guión y protocolo para demo en vivo y vídeo tutorial (DEMO_VIDEO_TUTORIAL.pdf)

**Resumen del plan propuesto:**

- Firma de acuerdos (SIGPAC + licencia con CASTÚO).
- Despliegue técnico del dashboard en servidores de la Junta.
- Formación de 50 técnicos en 4 semanas.
- Piloto con 10 propietarios (100 ha; €100K–135K/año en ingresos estimados).

**Próximos pasos propuestos:**

- Revisión y aprobación de la propuesta por la Asesoría Jurídica.
- Firma del acuerdo con SIGPAC (borrador adjunto).
- Reunión de coordinación para iniciar el despliegue (propuesta: 22/04/2026).

Quedo a su disposición para cualquier aclaración o ajuste en la propuesta. Pueden contactarme directamente en este correo o en el teléfono 600 000 000.

Atentamente,

**Gregorio Jiménez Bodes**  
CEO, CASTÚO-SYSTEM™  
gregorio.jimenez@castuo-system.com  
[Firma digital]

---

## 2. Adjuntos para el email

| Documento | Origen en el repo | Exportar a PDF |
|-----------|-------------------|----------------|
| Propuesta técnico-legal | [PROPUESTA_TECNICO_LEGAL_FORESTOWNERSHIPTOKEN.md](PROPUESTA_TECNICO_LEGAL_FORESTOWNERSHIPTOKEN.md) | PROPUESTA_TECNICO_LEGAL_FORESTOWNERSHIPTOKEN.pdf |
| Anexo VII (Derecho al olvido) | [ANEXO_VII_DERECHO_AL_OLVIDO.md](ANEXO_VII_DERECHO_AL_OLVIDO.md) | ANEXO_VII_DERECHO_AL_OLVIDO.pdf |
| Guía de despliegue | [../guias/guia_despliegue_dashboard.md](../guias/guia_despliegue_dashboard.md) | guia_despliegue_dashboard.pdf |
| Borrador acuerdo SIGPAC | [../acuerdos/borrador_acuerdo_sigpac.md](../acuerdos/borrador_acuerdo_sigpac.md) | borrador_acuerdo_sigpac.pdf |
| Plan de formación | [PLAN_FORMACION_TECNICOS.md](PLAN_FORMACION_TECNICOS.md) | plan_formacion_tecnicos.pdf |
| Propietarios piloto | [propietarios_piloto.csv](propietarios_piloto.csv) | Adjuntar CSV directamente |
| Demo y vídeo tutorial (guión, storyboard, legal) | [DEMO_VIDEO_TUTORIAL.md](DEMO_VIDEO_TUTORIAL.md) | DEMO_VIDEO_TUTORIAL.pdf *(opcional)* |

---

## 3. Instrucciones para exportar a PDF

### 3.1. Requisitos

- **Pandoc:** `sudo apt install pandoc` (Linux) o [pandoc.org](https://pandoc.org) (Windows/Mac).
- Opcional, para PDF con mejor tipografía: motor LaTeX (`texlive`) o `pandoc --pdf-engine=wkhtmltopdf`.

### 3.2. Comandos (ejecutar desde la raíz del repositorio)

```bash
# Propuesta técnico-legal
pandoc docs/junta-extremadura/PROPUESTA_TECNICO_LEGAL_FORESTOWNERSHIPTOKEN.md -o PROPUESTA_TECNICO_LEGAL_FORESTOWNERSHIPTOKEN.pdf

# Anexo VII — Derecho al olvido
pandoc docs/junta-extremadura/ANEXO_VII_DERECHO_AL_OLVIDO.md -o ANEXO_VII_DERECHO_AL_OLVIDO.pdf

# Guía de despliegue
pandoc docs/guias/guia_despliegue_dashboard.md -o guia_despliegue_dashboard.pdf

# Borrador acuerdo SIGPAC
pandoc docs/acuerdos/borrador_acuerdo_sigpac.md -o borrador_acuerdo_sigpac.pdf

# Plan de formación
pandoc docs/junta-extremadura/PLAN_FORMACION_TECNICOS.md -o plan_formacion_tecnicos.pdf

# Demo y vídeo tutorial (opcional)
pandoc docs/junta-extremadura/DEMO_VIDEO_TUTORIAL.md -o DEMO_VIDEO_TUTORIAL.pdf
```

### 3.3. Adjuntar al email

- PROPUESTA_TECNICO_LEGAL_FORESTOWNERSHIPTOKEN.pdf  
- ANEXO_VII_DERECHO_AL_OLVIDO.pdf  
- guia_despliegue_dashboard.pdf  
- borrador_acuerdo_sigpac.pdf  
- plan_formacion_tecnicos.pdf  
- propietarios_piloto.csv *(copiar desde docs/junta-extremadura/propietarios_piloto.csv)*
- DEMO_VIDEO_TUTORIAL.pdf *(opcional; desde docs/junta-extremadura/DEMO_VIDEO_TUTORIAL.md)*

---

[← Email detallado](EMAIL_PROPUESTA_COLABORACION.md) · [Propuesta técnico-legal](PROPUESTA_TECNICO_LEGAL_FORESTOWNERSHIPTOKEN.md) · [Anexo VI (derecho al olvido, versión técnica)](ANEXO_VI_DERECHO_AL_OLVIDO.md)
