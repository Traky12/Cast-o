# PRONT MAESTRO LEGAL + TÉCNICO — CASTÚO-SYSTEM 2040 (seguro, abierto y global)

Documento operativo para mantener el ecosistema **legalmente coherente**, **técnicamente consistente** y **seguro por diseño**, sin depender de servicios externos para operar el bloque educativo.

> Nota: este documento **no sustituye** asesoría legal. Funciona como “legal-as-documentation”: decisiones, plantillas y rutas dentro del repo.

---

## 1) Marco legal y licencias (mapa de compatibilidad)

### Licencias por componente (repo)

| Componente | Licencia | Archivo |
|-----------|----------|---------|
| Código (scripts Python) | MIT | `LICENSE` |
| Documentación (MD/PDF) | CC BY-SA 4.0 | `docs/LICENSE-CC-BY-SA.md` |
| Datasets (si se publican) | ODC-By 1.0 | `data/LICENSE-ODC-BY.md` |
| Imágenes / cómic (si aplica) | CC BY-NC-SA 4.0 | `docs/lengua-comun/LICENSE-IMAGES.md` |
| Badges | CC0 1.0 | `docs/lengua-comun/BADGES/LICENSE-CC0.md` |
| Traducciones | CC BY-SA 4.0 | `docs/lengua-comun/TRANSLATIONS/LICENSE.md` |

**Regla de coherencia**: todo activo nuevo debe declararse en el mapa anterior o heredar explícitamente la licencia correspondiente.

---

## 2) Cumplimiento por país / región (plantilla operativa)

Archivo: `docs/legal/CUMPLIMIENTO-POR-PAIS.md`

Objetivo: mantener un checklist mínimo por jurisdicción (UE/España/México/otros) para:

- consentimiento informado en talleres
- minimización de datos personales
- seguridad del tratamiento
- derechos de las personas (acceso/rectificación/supresión)

---

## 3) Privacidad y términos (plantillas)

Archivos:

- `docs/legal/POLITICA-PRIVACIDAD.md`
- `docs/legal/TERMINOS-Y-CONDICIONES.md`
- `docs/legal/INCIDENTES.md`
- `docs/legal/DPIA-CASTUO-SYSTEM.md` (placeholder hasta PDF firmado)

Principios:

- recoger **solo lo mínimo**
- preferir **modo local/offline**
- si hay blockchain: almacenar **hashes**, no datos personales

---

## 4) Seguridad y cifrado (práctico, sin “red por defecto”)

Carpeta: `scripts/seguridad/`

Incluye:

- `encriptar_aes_gcm.py` (AES-GCM; usa `cryptography` si está disponible)
- `validar_integridad.py` (SHA-256 de archivos críticos)

Regla: el cifrado se usa para **datos sensibles** (formularios, listados de contacto, etc.). Los materiales educativos se mantienen abiertos salvo necesidad real.

---

## 5) Auditorías automáticas (mínimas)

Carpeta: `scripts/revision/`

Ejecutar:

```bash
python scripts/revision/revisar_docs.py > revision_docs.log
python scripts/revision/revisar_scripts.py > revision_scripts.log
python scripts/revision/generar_informe.py --output informe_revision.md
```

Cobertura:

- `docs/cuento-castuo-sabionda/`
- `docs/lengua-comun/`
- `docs/castuo-educacion-2040/`
- `docs/legal/` (plantillas legales)
- `scripts/educacion/` + `scripts/dashboard/` + `scripts/seguridad/` (sin tocar `scripts/security/`)

---

## 6) Referencias internas ya existentes

- Marco legal CASTÚO: `docs/legal/CASTUO-Legal-Framework.md`
- AI Policy (EU): `docs/legal/AI_POLICY.md`
- Protocolos y anexos: `docs/legal/ANEXO-*.md`
- Índice legal: `docs/legal/README.md`

