# Índice de Validación — Usabilidad, Seguridad, Trazabilidad, Economía, Integración, Cooperación, Evolución

Documentos para cumplir requisitos de validación rigurosa (AEMPS, ISO 27001, Fraunhofer, TÜV, GS1, etc.).

---

## 0. Resumen y acciones

| Documento | Descripción |
|-----------|-------------|
| [Resumen de lo implementado](Validation-Summary.md) | Estado por área (usabilidad, seguridad, trazabilidad, etc.) |
| [Métricas 2026](Metrics-2026.md) | Objetivos por área (2026 y 2031) |
| [Conclusión y recomendaciones](Conclusion-Recommendations.md) | Fortalezas, prioridades, valoración final (1–10) |
| [Acciones inmediatas](Immediate-Actions.md) | Tabla priorizada (presupuesto ~€168K) |
| **Refuerzo por área** | |
| [Refuerzo Usabilidad](reinforcement/Reinforcement-Usability.md) | Riesgos y acciones (UX, TÜV, WCAG, i18n) |
| [Refuerzo Seguridad](reinforcement/Reinforcement-Security.md) | HSM, Pentesting, DPO, ELK |
| [Refuerzo Trazabilidad](reinforcement/Reinforcement-Traceability.md) | EDI aduanas, IA LIMS, geolocalización, checklists |
| [Refuerzo Economía](reinforcement/Reinforcement-Economy.md) | Premium, diversificación, Stripe, optimización costes |
| [Refuerzo Integración](reinforcement/Reinforcement-Integration.md) | SAP, API docs, caching, OAuth 2.0 |
| [Refuerzo Cooperación](reinforcement/Reinforcement-Cooperation.md) | Ferias, legal UE, case studies, portal verificación |
| [Refuerzo Evolución](reinforcement/Reinforcement-Evolution.md) | Patentes, infraestructura, k6, Fraunhofer |
| [Refuerzo Sabionda](reinforcement/Reinforcement-Sabionda.md) | ANECA, app móvil, gamificación, Open Badges |

---

## 1. Usabilidad (ISO 9241-11)

| Documento | Descripción |
|-----------|-------------|
| [Plan de Pruebas de Usabilidad](usability/Usability-Test-Plan.md) | Eficacia 90 %, eficiencia <5 min, NPS >70, WCAG 2.1 AA, multilingüe ES/EN/FR/DE |
| [Guía de Estilo UI/UX](usability/UI-UX-Style-Guide.md) | Colores, tipografía, componentes, accesibilidad |

**Pendiente**: Informe TÜV Rheinland (~€10.000, 3 meses).

---

## 2. Seguridad (ISO 27001 + ENS Alto)

| Documento | Descripción |
|-----------|-------------|
| [PSI — Política de Seguridad de la Información](security/PSI-ISO27001.md) | Cifrado AES-256/TLS 1.3, MFA, RBAC, logs 5 años, pentesting semestral |
| [Registro de Activos](security/Asset-Register.md) | Activos, ubicación, responsable, criticidad |

**Pendiente**: Guía MFA, configuración ELK, informe pentesting (junio 2026).

---

## 3. Trazabilidad (EPCIS 2.0 + GS1)

| Documento | Descripción |
|-----------|-------------|
| [Dossier AEMPS](traceability/AEMPS-Dossier-Template.md) | 5 lotes piloto, cumplimiento RD 903/2025 |
| [Checklist AEMPS](traceability/AEMPS-Checklist.md) | THC <0,3 %, trazabilidad, LIMS, blockchain |
| [Checklist GlobalGAP](traceability/GlobalGAP-Checklist.md) | Certificación exportación, checklists digitales |

**Pendiente**: Guía EPCIS 2.0, integración IPFS, certificación GS1 (~€15.000, 4 meses).

---

## 4. Economía

| Documento | Descripción |
|-----------|-------------|
| [Estrategia de Precios](economy/Pricing-Strategy.md) | Basic/Pro/Enterprise, ROI >20 % en 3 años, subvenciones, escalabilidad |

**Pendiente**: Modelo financiero (Excel/Deloitte), auditoría financiera (~€20.000).

---

## 5. Integración

| Documento | Descripción |
|-----------|-------------|
| [API OpenAPI 3.0](integration/API-OpenAPI.md) | REST/gRPC, Swagger, OAuth 2.0 |
| [Guía EDI](integration/EDI-Guide.md) | EDI X12/UN/EDIFACT para GlobalGAP, python-edi |

**Pendiente**: Guía Webhooks, Guía OAuth, Guía SAP (PyRFC).

---

## 6. Cooperación

| Documento | Descripción |
|-----------|-------------|
| [Acuerdo Marco CTAEX](cooperation/Acuerdo-Marco-CTAEX.md) | 5 años, cláusulas salida, PI 50/50, Fondo I+D €50K/año |

**Pendiente**: NDA distribuidores, Plan de Expansión UE (FR, DE, PT).

---

## 7. Evolución

| Documento | Descripción |
|-----------|-------------|
| [Roadmap 2026–2031](evolution/Roadmap-2026-2031.md) | Hitos por año, I+D+i, patentes, certificaciones ISO, escalabilidad |

**Pendiente**: Plan de Patentes, Plan de Certificaciones (ISO 9001, 14001).

---

## 8. Auditorías externas (RFPs)

| Documento | Descripción |
|-----------|-------------|
| [RFP AEMPS](audits/RFP-AEMPS.md) | Pasos y plazos para auditoría AEMPS (€18K–22K, 3–4 meses) |
| [RFP ISO 27001](audits/RFP-ISO27001.md) | Pasos para certificación ISO 27001 (€25K–30K, 4–5 meses) |
| [RFP Fraunhofer](audits/RFP-Fraunhofer.md) | Validación tecnológica IA/blockchain (€35K–45K, 4–5 meses) |

---

## 9. Sistema educativo Sabionda

| Documento | Descripción |
|-----------|-------------|
| [Sistema Educativo Sabionda](../sabionda/Sabionda-Educational-System.md) | Objetivos, programas, cooperación, métricas, plan implementación |
| [Guía Certificados Blockchain](../sabionda/Blockchain-Certificates-Guide.md) | Emisión y verificación en GaiaChain |
| **Contrato Solidity** | `contracts/SabiondaCertificates.sol` (raíz del repo) — emisión y revocación de certificados |

---

## Acciones inmediatas (resumen)

| Acción | Responsable | Plazo | Documento resultante |
|--------|-------------|--------|------------------------|
| Contratar auditoría AEMPS | Legal Team | 4 meses | Informe AEMPS |
| Certificación GlobalGAP | Calidad | 4 meses | Certificado GlobalGAP |
| Implementar ISO 27001 | Seguridad | 6 meses | Certificado ISO 27001 |
| Desarrollar conector EDI | Backend Team | 2 meses | Conector EDI |
| Patentar algoritmo IA | I+D | 3 meses | Patente OEPM |
| Simulacro de Contingencia | DevOps | 1 mes | Informe Simulacro |
| Pruebas de usabilidad | UX Team | 2 meses | Informe Usabilidad |
| Auditoría Fraunhofer | Innovación | 5 meses | Informe Fraunhofer |
| Contratar DPO | Legal Team | 1 mes | Contrato DPO |
