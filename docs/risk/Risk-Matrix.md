# MATRIZ DE RIESGOS — CASTÚO / CTAEX

**Objetivo**: Identificación, mitigación y contingencia para riesgos críticos.  
**Revisión**: Semestral (junio y diciembre).

---

## Matriz de riesgos

| Riesgo | Impacto | Probabilidad | Mitigación | Responsable |
|--------|---------|--------------|------------|-------------|
| Incumplimiento de GDPR | Alto | Medio | Auditorías trimestrales + DPO dedicado | Legal Team |
| Fallo en GaiaChain | Alto | Bajo | Modo degradado con registro local + sincronización posterior | Blockchain Team |
| Retraso en certificaciones AEMPS | Medio | Alto | Automatizar validación de datos de LIMS + alertas tempranas | Backend Team |
| Pérdida de datos IoT | Medio | Medio | Backups cada 15 min en Backblaze B2 + redundancia en sensores | DevOps |
| Cambios en normativa UE | Alto | Bajo | Suscripción a alertas legales (LexisNexis) + revisión trimestral con asesor externo | Compliance Officer |
| Falta de liquidez | Alto | Medio | Fondo de contingencia (€100K) + línea de crédito con banco local | Finanzas |

---

## Póliza de seguro tecnológico

- **Cobertura**: Fallos en blockchain, pérdida de datos, ciberataques.
- **Proveedores recomendados**: Hiscox o Allianz (cobertura para agritech).
- **Costo estimado**: €2.000–€5.000/año.

---

## Referencias

- **Plan de Contingencia 2.0**: `docs/risk/Contingency-Plan-v2.0.md`
- **Reglamento Consejo Asesor**: `docs/governance/Advisory-Board-Regulations-v2.0.md`
