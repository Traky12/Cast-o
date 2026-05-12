# castuo_manifest — Castúo-System 1.0

Estructura modular:

| Módulo | Contenido |
|--------|-----------|
| `admin.py` | `AdminProfile` (env `CASTUO_ADMIN_*`) |
| `vision.py` | `StrategicVision` |
| `pillars.py` | `SovereigntyPillars` |
| `impact.py` | `SocioeconomicImpact` |
| `pitch_deck.py` | `StrategicPitchDeck` |
| `sovereignty.py` | `eu_sovereignty_framework()` (EU-first, frameworks, agentes, bloques `trazabilidad`, `resilencia`, `crecimiento`, `expansion`) |
| `bundle.py` | `manifest_bundle()` (incluye siempre `eu_sovereignty`) |

`manifest_bundle()` devuelve unidad atómica **`V1.0-SOVEREIGNTY`**: valida `eu_sovereignty` antes de sellar. `export_strategic_pitch_deck_only()` lanza `SovereigntyViolationError`.

Documentación: [docs/MANIFESTO-CASTUO-SYSTEM-1-0.md](../docs/MANIFESTO-CASTUO-SYSTEM-1-0.md).

```python
from castuo_manifest import manifest_bundle, AdminProfile, eu_sovereignty_framework
b = manifest_bundle()  # incluye eu_sovereignty por defecto
```
