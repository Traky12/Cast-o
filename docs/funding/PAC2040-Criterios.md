# PAC 2040 — Criterios de elegibilidad (agrovoltaica)

Referencia para submedidas y ayuda máxima. **Plazo:** 31/12/2026.

---

## Submedidas aplicables

| Código | Descripción |
|--------|-------------|
| **14.2.1** | Agrovoltaica — instalaciones que combinan producción agrícola y generación fotovoltaica |
| **6.1** | Jóvenes agricultores — incorporación y establecimiento |

---

## Ayuda máxima

- **Agrovoltaica:** hasta **€120.000/hectárea** (según convocatoria y ratio kWp/ha).
- **Criterios técnicos:** superficie mínima, cultivo compatible con sombreado, ratio máxima kWp/hectárea definida por normativa.

---

## Criterios técnicos (resumen)

1. **Superficie mínima** según tipo de explotación y región.
2. **Cultivo compatible** con instalación de paneles (vid, olivo, hortícolas, etc.).
3. **Ratio kWp/hectárea** dentro del límite que establezca la convocatoria.
4. **Titular:** joven agricultor (submedida 6.1) o explotación que cumpla 14.2.1.

---

## Endpoint API

La API expone un resumen de criterios y plazo:

```bash
curl http://localhost:8001/pac2040/eligibilidad
```

Respuesta (ejemplo):

```json
{
  "submedidas": ["14.2.1 Agrovoltaica", "6.1 Jóvenes agricultores"],
  "ayuda_max": "€120.000/hectárea",
  "plazo": "31/12/2026",
  "elegibilidad": "Superficie mínima, cultivo compatible, kWp/ha dentro de ratio."
}
```

---

## Enlace con cooperativas

Cada **parcela** en el modelo de cooperativa tiene el campo `pac2040_eligible`. El **ROI anual** estimado incluye €25k por parcela elegible (ver `backend/models/cooperativa.py`).
