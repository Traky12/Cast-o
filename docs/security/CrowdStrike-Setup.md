# Configuración CrowdStrike Falcon — Protección Día Cero

**Objetivo**: Detección de malware y amenazas avanzadas (Barreras Sabionda v6.1). Aislar sistemas afectados en <1 min; notificar CTAEX y AEMPS en <10 min; registrar incidencia en GaiaChain.

---

## Componentes

- **CrowdStrike Falcon**: EDR/EPP en endpoints y servidores (Windows/Linux).
- **Integración**: Alertas vía webhook o API a Slack #alertas-criticas y a sistema de ticketing; script que registra en GaiaChain (tipo de evento, host, timestamp, sin datos sensibles).

---

## Protocolos

1. Alerta de Falcon → clasificar severidad.
2. Si crítica: aislar host (red o CrowdStrike containment) en <1 min.
3. Notificar CTAEX y AEMPS en <10 min (plantilla preaprobada).
4. Registrar en GaiaChain: `action: "zero_day_incident"`, `timestamp`, `host_id` (opaco), `severity`, `signature_hash` (opcional).

---

## Referencias

- [Sabionda-Barriers-v6.1.md](Sabionda-Barriers-v6.1.md) § 9.1
