# Modulo aleaciones vegetales (enlace tecnico)

- **API montada** en `backend/main.py` con prefijo `/vegetal-alloys`.
- **Paquete** `backend/vegetal_alloys/` (SQLAlchemy 2, SQLite por defecto).
- **ChemAxon**: mock sin credenciales; contrato HTTP real vía `CHEMAXON_*`.
- **Carga**: `tests/load/locustfile.py` y `k8s/locust-staging.yaml`.
- **Operaciones**: `docs/ops/vegetal-alloys/README.md`.
- **Formulas ASCII**: `docs/ops/vegetal-alloys/BIOPLA-STEVIA-2026*.txt`.

Limites de escala no documentados aqui como garantizados: medir en cluster y base de datos reales.
