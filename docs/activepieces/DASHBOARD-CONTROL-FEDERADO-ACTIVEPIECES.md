# Dashboard de Control Federado (Activepieces/HTML) — V2.0

Este dashboard traduce a humanos la **salud federada + auditoria** del Castúo-System, con enfoque de soberania:

- Solo lectura: no emite ordenes fisicas ni cambios de estado.
- Local-first: consulta endpoints internos self-hosted dentro de la UE.
- Auditoria visible: cada registro se presenta con semaforo por severidad.

---

## 1) Pagina HTML (Custom Assets / Static Page)

Archivo en el repo:

- `frontend/public/panel-control-federado.html`

Este HTML consume:

- `GET http://localhost:8001/federated/dashboard` (métricas federadas + blockchain audit trail + lista agentes)
- `GET http://localhost:8000/api/agri-sense/audit?n=10` (últimos eventos de auditoria del kernel)
- `GET http://localhost:8000/api/agri-sense/state` (estado operacional para widgets de seguridad critica)

Si tu despliegue navega el frontend a través de un dominio distinto, puedes forzar los endpoints mediante variables globales en `window`:

- `window.FEDERATED_DASHBOARD_URL`
- `window.API_BASE_URL`

Ejemplo:

```html
<script>
  window.FEDERATED_DASHBOARD_URL = "http://castuo-bunker:8001/federated/dashboard";
  window.API_BASE_URL = "http://castuo-api:8000";
</script>
```

---

## 2) Acceso WebAuthn + Read-Only (nota de integración)

Activepieces (o el reverse-proxy del búnker) debe:

1. Exigir autenticacion con WebAuthn/FIDO2 (llave física).
2. Restringir permisos del rol de socio a solo lectura del panel.
3. Asegurar que cualquier “acción” (si se implementa en el futuro) pase por el kernel + consenso, nunca desde el panel.

El HTML entregado ya está diseñado sin botones de ejecución; solo renderiza estado y auditoria.

---

## 3) Checklist de despliegue (TRL9 compatible)

- Verifica que los contenedores del federated service están levantados:
  - `docker-compose -f docker-compose.federated.yml up -d`
- Abre el dashboard en navegador (por defecto, local):
  - `http://<TU_SERVIDOR>/panel-control-federado.html`
- Valida accesos a endpoints (sin credenciales en la lectura básica):
  - `http://localhost:8001/federated/dashboard`
  - `http://localhost:8000/api/agri-sense/audit?n=10`
  - `http://localhost:8000/api/agri-sense/state`

---

## 4) Evidencia de soberania visible

El dashboard muestra explícitamente:

- `consensus_pct` y `nodes_online`
- `audit_trail_blocks`, `last_block` e `ipfs_pins`
- lista de agentes federados
- último set de auditoria con semaforo por severidad

