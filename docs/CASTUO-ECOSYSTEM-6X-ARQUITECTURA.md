# Castúo Ecosystem 6X — SOIC distribuido (Industria 5.0)

Infraestructura crítica distribuida: FastAPI, IA/ML, consenso; no solo ERP.

## 1. Capas funcionales

| Capa | Rol |
|------|-----|
| **Edge / ingesta** | MQTT, nodos rurales (biodiversidad, radiación, H₂) |
| **Proceso (FastAPI)** | JWT, **AES-256-GCM**, orquestación ML |
| **Persistencia + consenso** | Federación multinodo; eventos críticos → **SHA-3-512** + quórum (ver [PROTOCOLO-CONSENSO-CASTUO.md](protocolos/PROTOCOLO-CONSENSO-CASTUO.md)) |

## 2. Autocuración (self-healing)

1. **Prometheus** — anomalías tráfico / sensores caídos.
2. **Diagnóstico IA** — fallo vs intrusión (zero-trust).
3. **Acción** — rotación claves si compromiso; **failover federado** si nodo rural cae.
4. **Reporting ESG** — resiliencia inmediata.

## 3. Matriz cumplimiento (referencia)

| Marco | Aplicación 6X | Entidad |
|-------|----------------|---------|
| CSN | Trazabilidad radiológica, residuos | Consejo Seguridad Nuclear |
| CSRD | PDF/CSV impacto ecológico | UE |
| MiCA / EBSI | Nodos blockchain interoperables | ESMA / EBSI |
| AI Act | Registro decisiones ML | Oficina IA UE |

## 4. Seguridad industrial

**AES-256-GCM** en BD y **WebSocket**; tráfico sensores rural no legible sin clave.

---

*Próximo refinamiento: protocolo de votos y split-brain en documento de consenso.*
