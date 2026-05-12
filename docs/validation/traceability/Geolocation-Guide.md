# Guía de Geolocalización — Lotes (GPS < 5 m)

**Objetivo**: **100%** de lotes con geolocalización válida. Precisión **< 5 m**.

---

## Opciones técnicas

- **Google Maps API**: Geocoding, reverso, y opcionalmente registro de polígonos de parcela.
- **OpenStreetMap**: Alternativa open source (Nominatim, etc.) para reducir dependencia y coste.

---

## Modelo de datos

- En tabla de lotes (cannabis/microgreens): campos `latitude`, `longitude`, opcionalmente `accuracy_m` y `source` (ej. "gps_device", "manual_map").
- Validación: coordenadas dentro de rangos válidos y, si aplica, dentro de parcela/centro autorizado.

---

## UX

- En app/web: selector de mapa (pin o polígono) o integración con dispositivo GPS en app móvil en campo.

---

## Métrica de éxito

- **100%** de lotes nuevos con al menos lat/lon válidos; objetivo precisión **< 5 m** cuando el dato provenga de GPS.
