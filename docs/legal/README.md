# ÍNDICE LEGAL — CASTÚO-SYSTEM 2040

Punto de entrada para documentación **legal + técnica** (plantillas) con enlaces internos y `PLACEHOLDER:` rastreables.

---

## Documentos clave

| Documento | Propósito | Estado | Placeholders |
|----------|-----------|--------|--------------|
| `PRONT-MAESTRO-LEGAL-TECNICO-CASTUO-SYSTEM-2040.md` | guía maestra legal+técnica | ✅ | — |
| `CUMPLIMIENTO-POR-PAIS.md` | checklist por jurisdicción | ✅ plantilla | DPO, servidores, procesos |
| `POLITICA-PRIVACIDAD.md` | privacidad (GDPR/DSA) | ✅ plantilla | emails, retención, responsable |
| `TERMINOS-Y-CONDICIONES.md` | términos de uso | ✅ plantilla | jurisdicción, contactos |
| `INCIDENTES.md` | respuesta a incidentes | ✅ plantilla | contacto seguridad |
| `REGISTRO-DE-ACTIVIDADES.json` | GDPR Art. 30 (registro) | ✅ plantilla | completar primera actividad real |
| `DPIA-CASTUO-SYSTEM.md` | DPIA (GDPR Art. 35) | ✅ placeholder | completar + firmar y exportar |

Licencias (repositorio):

- Código (MIT): `../../LICENSE`
- Documentación (CC BY-SA): `../LICENSE-CC-BY-SA.md`
- Datos (ODC-By): `../../data/LICENSE-ODC-BY.md`

---

## Checklist para despliegue real (mínimo viable)

### Legal

- [ ] Definir responsable y contactos en `POLITICA-PRIVACIDAD.md` (rellenar `PLACEHOLDER:`).
- [ ] Completar al menos **una** actividad real en `REGISTRO-DE-ACTIVIDADES.json`.
- [ ] Definir jurisdicción y contactos en `TERMINOS-Y-CONDICIONES.md`.

### Técnico (offline-first)

- [ ] Generar manifiesto de integridad:

```bash
python scripts/seguridad/generar_manifiesto.py
```

- [ ] Ejecutar auditoría:

```bash
python scripts/revision/revisar_docs.py > revision_docs.log
python scripts/revision/revisar_scripts.py > revision_scripts.log
python scripts/revision/generar_informe.py --output informe_revision.md
```

---

## Nota sobre DPIA

El DPIA formal suele ser un PDF firmado por el DPO. En este repo se mantiene como plantilla documental:

- `DPIA-CASTUO-SYSTEM.md` (placeholder)
- `PLACEHOLDER: DPIA-CASTUO-SYSTEM.pdf (exportado y firmado)`

