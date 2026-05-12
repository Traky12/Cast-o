# CHECKLIST DE RECUPERACIÓN — PLAN DE CONTINGENCIA 2.0

**Uso**: Tras un incidente crítico (PostgreSQL, GaiaChain, IoT, ciberseguridad), comprobar que la recuperación está completa.

---

## PostgreSQL

- [ ] Servicio postgres operativo (`docker-compose ps` / healthcheck).
- [ ] Restauración desde backup (si aplica) completada.
- [ ] Backend puede conectar (probar `GET /health` y un endpoint que use BD).
- [ ] CTAEX notificado (email según plantilla).
- [ ] Status page actualizado.

---

## GaiaChain (modo degradado)

- [ ] Nodos GaiaChain accesibles (Prometheus / prueba manual).
- [ ] Cola Redis `pending_blockchain_tx` revisada (`GET /reports/blockchain/pending`).
- [ ] Sincronización de pendientes ejecutada (`POST /reports/blockchain/sync_pending`).
- [ ] CTAEX informado de retrasos <24h si aplica.

---

## Sensores IoT

- [ ] Sensores repuestos/operativos.
- [ ] Calibración aplicada (ver `backend/services/calibration.py`).
- [ ] Dashboard de monitoreo sin estado "degradado" (o actualizado con motivo).

---

## Seguridad / Ciberataque

- [ ] Sistemas aislados/restaurados según procedimiento.
- [ ] Backups verificados (Backblaze B2).
- [ ] Clientes afectados notificados en <24h.
- [ ] Análisis forense iniciado si procede (S21sec u otro).

---

## Cierre del incidente

- [ ] Acta de incidente documentada (fecha, duración, causa, acciones).
- [ ] Plan de Contingencia y contactos revisados para próximos 3 meses.
