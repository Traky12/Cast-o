# Guia para Tecnicos de Campo - CASTUO-SYSTEM

## 1) Operativa diaria

### Estimacion THC

```powershell
curl -X POST "https://castuo.ctaex.es/thc/estimate" `
  -H "Content-Type: application/json" `
  -d '{
    "batch_id": "BATCH-001",
    "plant_id": "PLANT-001",
    "zone_id": "ZONE-A",
    "spectrum": [0.123, 0.456, 0.789]
  }'
```

Nota: `spectrum` debe tener exactamente 157 valores.

### Validacion LIMS

```powershell
curl -X POST "https://castuo.ctaex.es/thc/validate_lims" `
  -H "Content-Type: application/json" `
  -d '{
    "batch_id": "BATCH-001",
    "lab_certificate": "LIMS-ABC123",
    "thc_validated": 18.5,
    "validation_method": "HPLC"
  }'
```

## 2) Comandos rapidos (PowerShell)

```powershell
# Tests
.\scripts\thc.ps1 test-thc

# Validacion de flujo
.\scripts\thc.ps1 validate-thc

# Backup
.\scripts\thc.ps1 backup-thc
```

## 3) Problemas frecuentes

| Problema | Causa probable | Solucion |
|---|---|---|
| 400 en `/thc/estimate` | Espectro con longitud distinta de 157 | Corregir payload |
| `gaiachain_tx` vacio o null | Nodo no disponible o degradado | Revisar `backend/services/gaia_chain.py` y variables `GAIA_CHAIN_*` |
| 404 en `/thc/validate_lims` | `batch_id` inexistente | Verificar `batch_id` de la estimacion previa |

## 4) Resultado esperado

- Estimacion: `PENDING_VALIDATION`.
- Validacion LIMS: `VALIDATED_BY_LIMS`.
- Paso final regulatorio: `/cannabis/certify_aemps`.
