# Runbook — respuesta a incidentes de seguridad (plantilla)

**Relación:** [PRONTUARIO-MAESTRO-REFUERZO-INTEGRAL-2026.md](./PRONTUARIO-MAESTRO-REFUERZO-INTEGRAL-2026.md) · [PRONTUARIO-MAESTRO-REFUERZO-SEGURIDAD-AVANZADA-2026.md](./PRONTUARIO-MAESTRO-REFUERZO-SEGURIDAD-AVANZADA-2026.md) · [CHECKLIST-SEGURIDAD-AVANZADA.md](./CHECKLIST-SEGURIDAD-AVANZADA.md) · [CHECKLIST-REFUERZO-SEGURIDAD.md](./CHECKLIST-REFUERZO-SEGURIDAD.md)

*Plantilla mínima: completar contactos, canales y SLAs internos. No incluye datos sensibles.*

## 1. Clasificación rápida

| Nivel | Ejemplos orientativos | Acción inicial |
|-------|----------------------|----------------|
| P1 | Compromiso de credenciales admin, exfiltración activa | Aislar afectado, preservar evidencia, escalar |
| P2 | Escaneo agresivo, intentos masivos de auth | Bloqueo temporal, revisar logs |
| P3 | Hallazgo de configuración débil | Ticket + remediación fechada |

## 2. Contención *(sin destruir evidencia)*

- Revocar tokens/rotar secretos según [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md)
- Reglas firewall temporales documentadas
- Capturas de `tcpdump`/logs con hash y hora

## 3. Erradicación y recuperación

- Parche o hardening aplicado con PR/commit referenciado
- Verificación post-cambio (tests `trl6`, health, métricas)

## 4. Post-incidente

- Acta breve: línea de tiempo, causa raíz (si conocida), lecciones
- Actualizar checklist y prontuarios si cambia el estándar

---

*Quien responde sin registrar el río de logs, pierde la brújula para la siguiente crecida.*
