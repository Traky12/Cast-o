# Detección de Anomalías en Inputs — Barreras Sabionda v6.1

**Objetivo**: Identificar patrones sospechosos en requests con modelo de anomalías (ej. Isolation Forest). False positives <1 %; tasa de bloqueo inputs maliciosos >99,9 %.

---

## Enfoque

- **Entrenamiento**: Datos históricos de requests válidos (body, headers, path, tamaño).
- **Inferencia**: Para cada request nuevo, extraer features (ej. longitud, caracteres especiales, ratio de palabras bloqueadas) y pasar al modelo.
- **Decisión**: Si `model.predict([features]) == -1` (anomalía) → rechazar, registrar en GaiaChain y opcionalmente alertar.

---

## Ejemplo (Isolation Forest)

```python
from sklearn.ensemble import IsolationForest
model = IsolationForest(contamination=0.01)
model.fit(training_data)  # Datos históricos de requests válidos
if model.predict([new_request_features]) == -1:
    return {"status": "blocked", "reason": "Anomalía detectada por IA"}
```

---

## Integración

- **Punto de enlace**: Middleware o dependencia FastAPI antes de rutas sensibles (ej. `/sync/lims`, `/cannabis/certify_aemps`, `/iot/ingest`).
- **Features sugeridos**: Longitud del body, número de campos, presencia de patrones regex peligrosos, ratio de caracteres no imprimibles, IP/país.
- **Registro**: Incluir hash del request (sin PII) y resultado (blocked/ok) en GaiaChain para auditoría.
