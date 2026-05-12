# Checklist — integración biológica-digital (CASTÚO-System)

**Relación:** [PRONTUARIO-MAESTRO-INTEGRACION-BIOLOGICA-DIGITAL-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-BIOLOGICA-DIGITAL-2026.md) · [PRONTUARIO-MAESTRO-ECOLOGIA-DIGITAL-AGRICOLA-2026.md](./PRONTUARIO-MAESTRO-ECOLOGIA-DIGITAL-AGRICOLA-2026.md) · [NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md](../integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md)

Marca con **evidencia** (fecha, responsable, enlace a informe o commit). Separar **parcela física** de **laboratorio software**.

## A. Calidad del “nutriente” (datos)

- [ ] Inventario de variables agronómicas usadas en decisión (pH, EC, humedad, luz, etc.)
- [ ] Cobertura Pydantic / validación acordada por ruta que ingiere sensores
- [ ] Calibración de sensores de campo documentada *(o plan de calibración)*
- [ ] Política de retención y minimización alineada a [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md)

## B. Ciclo biológico-digital en software

- [ ] Baseline de `castuo_neuro_hydro_infer_seconds` (u otra métrica de inferencia) **medida y archivada**
- [ ] Comportamiento del caché SNN (Redis) entendido: TTL, clave canónica — ver orientación neuromórfica
- [ ] Tests de regresión del lab SNN ejecutados en CI o antes de release

## C. Trazabilidad y cadena *(opt-in)*

- [ ] Si se usa cadena / TraceChain: coherencia con [TraceChain-Compliance-2026.md](../legal/TraceChain-Compliance-2026.md)
- [ ] Sin afirmar “blockchain en cada gota” sin diseño y coste acordados

## D. Seguridad del territorio digital

- [ ] Hardening LAN/edge donde haya operadores: [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md)
- [ ] Secretos prod A/B según [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md)

## E. Visualización y red simbiótica *(metáfora operativa)*

- [ ] Dashboards Grafana (u otro) con propietario de alerta — si aplica despliegue
- [ ] [MAPA-REDES-SIMBIOTICAS.md](./MAPA-REDES-SIMBIOTICAS.md) revisado en versión mayor de arquitectura

---

*Checklist sin evidencia es abono sin análisis de suelo: bonito en el papel, arriesgado en el terruño.*
