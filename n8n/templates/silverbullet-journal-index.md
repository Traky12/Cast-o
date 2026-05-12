# Journal AGRI-BRAIN (Trillizo)

Espacio **auditable** generado por n8n (`01-trillizo-auditoria-basica.json`): archivos `diario-YYYY-MM-DD.md` en esta carpeta.

- Cada **POST** a `/webhook/audit-trigger` **añade** un bloque Markdown al diario del día.
- Opcional: firma **HMAC-SHA256** del **body JSON completo** (canonical) con cabecera `X-Castuo-Signature` (ver `n8n/README-CEREBROS.md`).

## Enlaces útiles

- [[README]] — vuelve al índice del space si existe.
- Revisa el grafo en SilverBullet para correlacionar notas con operaciones.

---

*Plantillas en repo: `n8n/templates/silverbullet-journal-index.md` (esta página) y `n8n/templates/journal/plantilla.md` (estructura diaria con frontmatter).*
