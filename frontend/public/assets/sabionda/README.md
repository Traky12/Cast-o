# SABIONDA IA - Assets oficiales v3.1

## Imagen única (Básica + Administrador)
| Archivo | Uso |
|---------|-----|
| `sabionda-oficial.png` | **Única referencia sistema** (512×512) |
| `sabionda-oficial@2x.png` | Retina display (1024×1024) |
| `fallback-holo.svg` | Resiliencia 100% si PNG no disponible |

**USO:** Básica (farmers) + Administrador (CTO) → COHERENCIA TOTAL  
**VARIANTES:** profile/tech → Misma imagen + contexto dinámico

---

## Protocolo despliegue (ejecutar 1 vez)

```powershell
cd "C:\Users\traky\OneDrive - FCI\Castuo-System"
New-Item -ItemType Directory -Force -Path "frontend\public\assets\sabionda"

# Ajusta la ruta origen a tu PNG de Sabionda (ej. desde Cursor workspace):
Copy-Item "C:\Users\traky\.cursor\projects\c-Users-traky-OneDrive-FCI-Castuo-System\assets\...\sabionda-profile-*.png" "frontend\public\assets\sabionda\sabionda-oficial.png"
```

Referencia en código: **`/assets/sabionda/sabionda-oficial.png`**
