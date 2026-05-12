# CASTÚO — módulo generativo / invertible (RGI, hoja de ruta)

Este directorio recoge **utilidades y contratos** para flujos **biyectivos** (encode ↔ decode) sobre vectores de sensores u otras señales, alineados con trazabilidad y almacenamiento en edge (pendrive LUKS, RPi).

## Límites honestos (operación)

- **Normalizing flows** en `nflows` requieren que la dimensión del espacio sea coherente con el transform (típicamente misma dimensión entrada/salida salvo diseños con padding/splits). Un flujo “20 → 10” estricto **no es** un difeomorfismo en ℝ²⁰ sin acotar el diseño.
- **`log_prob`** devuelve log-densidad, no un par `(z, log_det)` genérico como en pseudocódigo; la compresión “10×” en MB/día depende de **codificación, cuantización y dominio** — no se asume aquí.
- **TRL / AEMPS / RD**: la carpeta es **técnica**; certificación y TRL efectivo exigen evidencia, piloto y revisión regulatoria fuera del repo.
- **Export ONNX** de grafos `nflows` completos suele ser **no trivial**; validar en el destino (RPi) antes de prometer latencias.

## Contenido

| Fichero | Rol |
|---------|-----|
| `reversible_affine.py` | Stub **100% reversible** en NumPy (auditoría de pipeline sin PyTorch). |
| `requirements_rgi.txt` | Dependencias **opcionales** (torch, nflows, onnxruntime). |
| `train_sensor_flow.py` | Esqueleto de entrenamiento NF (solo si `nflows` + `torch` instalados). |

Integración pendrive: `Prepare-CastuoPendrive.ps1` copia esta carpeta y, si existen, artefactos bajo `models/rg/`.

PRONT imprimible (A4, campo/lab): `docs/deploy/PRONT-CASTUO-RGI-v2-2026.md`.  
Patrón y nuevos PRONT: `docs/deploy/PRONT-PATRON-SISTEMAS-INTEGRADOS.md` · `python scripts/generate_pront.py --help`
