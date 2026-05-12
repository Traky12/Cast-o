# Checklist — refuerzo integral (seguridad + soberanía + evolución)

**Relación:** [PRONTUARIO-MAESTRO-REFUERZO-INTEGRAL-2026.md](./PRONTUARIO-MAESTRO-REFUERZO-INTEGRAL-2026.md)

Marca cada ítem con **evidencia** (ticket, commit, captura, informe). Este checklist **extiende** el de seguridad avanzada; no lo sustituye.

---

## A. Base — seguridad avanzada *(obligatorio)*

Completar primero: [CHECKLIST-SEGURIDAD-AVANZADA.md](./CHECKLIST-SEGURIDAD-AVANZADA.md)

- [ ] Checklist seguridad avanzada cerrada o con brechas documentadas y fechadas

---

## B. Soberanía y cadena de datos

- [ ] Inventario de proveedores cloud/SaaS con **ubicación** del tratamiento (UE/EEE u otras) y encargado
- [ ] DPA / anexos firmados o en curso para nuevos subencargados
- [ ] Revisión DPIA si cambia ubicación o nuevas medidas invasivas ([DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md))
- [ ] Objetivos de disponibilidad (SLO) **definidos y medidos** — no solo objetivo en papel
- [ ] Si aplica migración TRL7: progreso en [CHECKLIST-MIGRACION-TRL7.md](./CHECKLIST-MIGRACION-TRL7.md)

---

## C. Evolución verificable

- [ ] Roadmap técnico alineado con [PRONTUARIO-MAESTRO-AUDITORIA-EVOLUCION-RESILIENTE-2026.md](./PRONTUARIO-MAESTRO-AUDITORIA-EVOLUCION-RESILIENTE-2026.md) *(evidencia git / releases)*
- [ ] Baseline de KPIs de seguridad y resiliencia **registrada** (primera medición archivada)
- [ ] Runbook de incidentes revisado en el último trimestre ([RUNBOOK-RESPUESTA-INCIDENTES.md](./RUNBOOK-RESPUESTA-INCIDENTES.md))

---

## D. Stack de observabilidad / SIEM

- [ ] Decisión documentada: ELK vs OpenSearch u otro *(licencia, coste, operación)*
- [ ] Retención y minimización de logs acordes con DPIA
- [ ] Alertas críticas con responsable y canal (no solo dashboard)

---

*Quien marca casillas sin evidencia en el territorio deja la puerta abierta a la próxima crecida sin brújula.*
