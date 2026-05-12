# PEI-001 — Validación SIGPAC local (parcelas Castúo)

**Objetivo:** cruzar geometrías de parcelas Castúo (GeoJSON/SHP) con una **capa SIGPAC descargada manualmente** (visor oficial), emitir JSON (+ PDF opcional) bajo `reports/`.

**No sustituye** al validador estructural del repo (`backend/integrations/sigpac_validator.py`: topología, área GDAL). Aquí el foco es **superposición + coherencia de usos** según columnas configurables.

**Territorio:** sin API MAPA inventada; la capa SIGPAC es responsabilidad operativa (export/manual).

## Uso

```bash
pip install -r pei-001-sigpac/scripts/requirements.txt
python pei-001-sigpac/scripts/validate_sigpac.py \
  --parcelas pei-001-sigpac/data/input/parcelas_castuo.geojson \
  --sigpac pei-001-sigpac/data/sigpac/recinto.shp \
  --out-json pei-001-sigpac/reports/sigpac_informe.json \
  --out-pdf pei-001-sigpac/reports/sigpac_informe.pdf
```

### Mapping de usos (`--mapping-path`)

Cuando el código SIGPAC no coincide literalmente con el uso declarado Castúo (p. ej. registro interno vs capa oficial), usa un JSON con equivalencias bidireccionales:

- `usos_declarados`: clave = uso en parcelas → lista de usos/códigos de capa aceptados.
- `usos_sigpac`: clave = uso en capa → lista de usos declarados aceptados.
- `codigos_sigpac`: mapa **código oficial → uso canónico** (texto). Si informas `--sigpac-code-field` y el mapping incluye esta sección, se exige que el **texto de uso en la capa** coincida con el uso del catálogo para ese código (coherencia interna del shapefile).

Plantilla canónica: `pei-001-sigpac/data/mapping.json` (ajustar a tu provincia/año). Copia de referencia: `mapping.example.json`.

```bash
python pei-001-sigpac/scripts/validate_sigpac.py \
  --parcelas pei-001-sigpac/data/input/parcelas_castuo.geojson \
  --sigpac pei-001-sigpac/data/sigpac/recinto.shp \
  --sigpac-code-field codigo_sigpac \
  --mapping-path pei-001-sigpac/data/mapping.json \
  --out-json pei-001-sigpac/reports/sigpac_informe.json
```

El informe añade `porcentaje_cumplimiento`, `usos_problematicos` (por uso declarado → clave de agrupación: código SIGPAC si existe, si no texto de uso), `codigo_sigpac` por fila si definiste campo, y `cumple_via` (`literal` | `mapping` | `no`). Usa `--verbose` para logs INFO.

Shapefile requiere **GDAL** del sistema + `geopandas`. Solo GeoJSON: puede usarse entorno mínimo (ver `requirements.txt`).

## Pruebas

```bash
pytest pei-001-sigpac/tests/test_validate_sigpac.py -v
```

## CI

`.github/workflows/sigpac-validation-pei001.yml` ejecuta validación con **fixtures sintéticos** y sube artefactos desde `pei-001-sigpac/reports/`.
