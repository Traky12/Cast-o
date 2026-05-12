# Marco de cumplimiento SIGPAC local (PEI-001) — 2026

**Ámbito:** trazabilidad del **informe generado por** `pei-001-sigpac/scripts/validate_sigpac.py` frente a capas SIGPAC **descargadas manualmente** (visor oficial). **No** es certificación MAPA ni veredicto agronómico.

**Relación:** [TraceChain-Compliance-2026.md](./TraceChain-Compliance-2026.md) · [SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md](./SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md) · [ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md](./ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md) · [pei-001-sigpac/README.md](../../pei-001-sigpac/README.md)

---

## 1. Cómo se genera la evidencia

1. Colocar parcelas Castúo en `pei-001-sigpac/data/input/` (GeoJSON o SHP).
2. Colocar recintos SIGPAC exportados en `pei-001-sigpac/data/sigpac/`.
3. Ejecutar (ajustar nombres de columnas si tu capa usa otros campos que `id` / `uso_declarado` / `uso_sigpac`):

```bash
pip install -r pei-001-sigpac/scripts/requirements.txt
python pei-001-sigpac/scripts/validate_sigpac.py \
  --parcelas pei-001-sigpac/data/input/parcelas_castuo.geojson \
  --sigpac pei-001-sigpac/data/sigpac/<capa_local>.shp \
  --sigpac-code-field <columna_codigo_si_existe> \
  --mapping-path pei-001-sigpac/data/mapping.json \
  --out-json pei-001-sigpac/reports/sigpac_informe.json \
  --out-pdf pei-001-sigpac/reports/sigpac_informe.pdf
```

El JSON incluye `summary` (`total_parcelas`, `cumple`, `no_cumple`, `porcentaje_cumplimiento`, `usos_problematicos`), `mapping_path` si aplica, y `results` con `cumple_via` (`literal` / `mapping` / `no`), `codigo_sigpac` si usas `--sigpac-code-field`. Mapping recomendado: `pei-001-sigpac/data/mapping.json` (`usos_*` + `codigos_sigpac`).

---

## 2. Plantilla de registro (rellenar tras cada ejecución real)

> **No** versionar porcentajes ni listas de incumplimiento sin ejecutar el script sobre datos reales del piloto.

### Informe SIGPAC — fecha de ejecución: _YYYY-MM-DD_

| Campo | Valor |
|--------|--------|
| **Rutas de entrada** | `data/input/…`, `data/sigpac/…` |
| **Resumen** | Copiar `summary` del JSON generado |
| **Incumplimientos** | IDs de `results` con `cumple: false` |
| **Evidencia JSON** | Ruta relativa al repo, p. ej. `pei-001-sigpac/reports/sigpac_informe.json` |
| **Evidencia PDF** | Opcional: `pei-001-sigpac/reports/sigpac_informe.pdf` |

**Enlace simbólico en documentación:** tras generar el informe, enlazar aquí la ruta del fichero (o subir artefacto de CI con nombre de run).

---

## 3. CI

El workflow `.github/workflows/sigpac-validation-pei001.yml` valida **fixtures sintéticos** y sube artefactos desde `pei-001-sigpac/reports/`. Eso demuestra que el pipeline funciona; **no** sustituye datos SIGPAC reales.

---

## 4. Notas para Cursor

1. Alinear nombres de columnas con la **capa exportada** (códigos de cultivo / usos reales del shapefile).
2. No inventar URLs de API SIGPAC.
3. El validador estructural del backend sigue siendo `backend/integrations/sigpac_validator.py`.

*Documento orientativo; integración crítica sujeta a contrato y datos del territorio.*
