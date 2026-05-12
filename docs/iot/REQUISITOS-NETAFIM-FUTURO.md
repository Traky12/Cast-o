# Netafim / riego por goteo — requisitos futuros

**Estado:** no hay en el monorepo `backend/irrigation/netafim_integration.py` ni credenciales Cloud.

Para una integración aceptable:

1. Contrato o acuerdo con el proveedor y **documentación técnica oficial** (API, VPN, MQTT, etc.).
2. Módulo delgado aislado; secretos fuera del repo (vault / env en despliegue).
3. Registro de órdenes de riego alineado con política de auditoría y, si aplica, `gaiachain_service` (no stubs de briefing).
4. Cumplimiento **UNE 50510** / eficiencia hídrica (**RD 169/2021** y normativa autonómica) según proyecto real.

---

**Relación:** [CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md](../legal/CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md)
