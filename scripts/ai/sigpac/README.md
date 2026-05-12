# SIGPAC — utilidades de campo (CASTÚO)

## Qué hay en el repo (canónico)

| Ruta | Función |
|------|---------|
| `backend/integrations/sigpac_validator.py` | Validación estructural GeoJSON + área (OGR si disponible). |
| `pei-001-sigpac/` | Cruce parcelas Castúo vs capa SIGPAC manual (shapefile/GeoJSON), informes. |
| `scripts/ai/sigpac/geotiff_stats.py` | **Opcional:** estadísticas + hash de banda 1 en raster (rasterio). |
| `scripts/ai/sigpac/validator.py` | Misma lógica por `parcel_id` (`data_dir/{id}.tif`), logs JSON; campo `features` con NDVI/humedad `null` hasta integrar fuentes reales. |
| `scripts/ai/sigpac/sigpac_features.py` | Vector 8D desde resumen raster; slotes reservados para multispectral / sensores. |
| `scripts/ai/sigpac/federated_trainer.py` | Lab Flower (`server` / `client`) sobre el vector 8D, no sobre píxeles crudos. |

## GeoTIFF (opcional)

```bash
pip install -r scripts/ai/sigpac/requirements_sigpac.txt
python scripts/ai/sigpac/geotiff_stats.py ruta/parcela.tif --json-log logs/geotiff_audit.jsonl
# Por ID de parcela (ficheros en data/sigpac/<id>.tif):
python scripts/ai/sigpac/validator.py 12345 --data-dir data/sigpac --log logs/sigpac_validation.json
```

El hash es sobre la matriz de la banda 1; en rasters muy grandes puede ser costoso — valorar muestreo en producción.

## Lab federado (opcional, pesado)

```bash
pip install -r scripts/ai/sigpac/requirements_sigpac_federated.txt
python scripts/ai/sigpac/federated_trainer.py server --address 0.0.0.0:8080
# En otras terminales (≥2 parcelas .tif distintas):
python scripts/ai/sigpac/federated_trainer.py client --server 127.0.0.1:8080 --parcel-id parcela_a --data-dir data/sigpac
```

## PRONT A4

`docs/deploy/PRONT-CASTUO-SIGPAC-v1-2026.md`
