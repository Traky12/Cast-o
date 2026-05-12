# Pruebas de carga (Locust) — lab stub

**Estado:** 🟡 `locustfile.py` presente; dependencia **no** en `backend/requirements.txt` (instalar aparte).

```bash
pip install locust
export CASTUO_ROBOTICS_LAB_BEARER_TOKEN=...   # mismo valor que el proceso uvicorn
locust -f tests/stress/locustfile.py --host http://127.0.0.1:8011
```

Compose scan3d suele usar puerto host **8012** → `--host http://127.0.0.1:8012`.

**Métricas:** registrar throughput y p95 en informe interno; **no** fijar “50 req/s” o “0 % errores” en git sin CSV/export Locust.

**Evidencia:** [INFORME-EVIDENCIA-TRL6-PLANTILLA.md](../../docs/legal/INFORME-EVIDENCIA-TRL6-PLANTILLA.md).
