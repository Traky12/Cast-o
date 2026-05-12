# Prontuario maestro — infraestructura soberana CASTÚO-System (TRL6→TRL7)

*Estrategia **europea** de escalado **resiliente** y **soberana** (compute, datos, observabilidad). **No** es presupuesto contractual, **no** catálogo de precios vigente: cotizar siempre con proveedor y DPO/legal.*

**Relación:** [PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md](../legal/PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md) · [ROADMAP-TRL6-TRL7-CODE.md](./ROADMAP-TRL6-TRL7-CODE.md) · [PRONTUARIO-MAESTRO-REFUERZO-SEGURIDAD-AVANZADA-2026.md](./PRONTUARIO-MAESTRO-REFUERZO-SEGURIDAD-AVANZADA-2026.md) · [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md)

**Límite:** cifras € y % SLA son **órdenes de magnitud / objetivos** a validar con factura, contrato y medición. TRL7 en este doc = **criterios operativos orientativos**, no certificación NASA/ESA por git.

---

## 📋 1. Principios de soberanía tecnológica

1. **Prioridad europea** — Evaluar proveedores con presencia **UE/EEA** y **localización de datos** explícita en contrato.  
2. **Código abierto** — Preferir componentes **FOSS** con licencias compatibles con vuestro modelo *(AGPL implica obligaciones de redistribución; EUPL es opción UE)*.  
3. **Resiliencia operativa** — Arquitectura multi-AZ / backup / runbooks; el “99,9 %” solo tras **SLA medido**.  
4. **Coste controlado** — Cap inicial **orientativo** *(p. ej. ≤ €35K en 6 meses)* sujeto a alcance; **no** fijar en git sin aprobación financiera.  
5. **Cumplimiento** — RGPD, **AI Act** *(según clasificación del producto)*, PAC 2040 cuando aplique al caso de uso — con **DPO** y asesoría.

---

## 🔧 2. Arquitectura de infraestructura soberana

*Alternativas **ejemplificativas** a un único proveedor (p. ej. Hetzner); comparar con [CHECKLIST-TRL6](./CHECKLIST-TRL6-HETZNER-STAGING.md) actual.*

### 2.1 Proveedores y servicios *(ejemplos UE — cotizar)*

| Componente | Alternativa soberana *(ejemplo)* | Ventajas típicas | Coste *(indicativo)* |
|------------|----------------------------------|------------------|----------------------|
| **Cloud compute** | OVHcloud (FR) / Stackscale (ES) / otros IaaS UE | Catálogos UE, opciones SecNumCloud/HDS según producto | *Cotizar* |
| **Load balancer** | Scaleway (FR) / LB del propio IaaS | IP y tráfico en región acordada | *Cotizar* |
| **Redis gestionado** | Aiven (FI) / ElastiCache en región UE / self-host | TLS, backups, SLA | *Cotizar* |
| **PostgreSQL** | Crunchy Bridge / managed PG en región UE / self-host | HA, backups, extensiones | *Cotizar* |
| **Monitorización** | Netdata *(FOSS)* + Grafana *(self o Cloud con región UE elegida)* | Métricas host + dashboards | *Cotizar / €0 self-host* |

*Los importes del borrador (€8–€84/mes) son **ilustrativos**; no usar en contrato.*

*Integración OVH + Scaleway “nativa” **no** es automática: diseñar red (vRack/VPN) o usar un solo proveedor si simplifica.*

---

## 📊 3. Plan de escalado resiliente (TRL6→TRL7)

### 3.1 Infraestructura base *(plantilla)*

| Recurso | Especificación *(ajustar)* | TRL orientativo |
|---------|----------------------------|-----------------|
| Nodos de cómputo | 2–3 VMs/K8s workers según carga | TRL6 staging → TRL7 piloto |
| Balanceo | LB gestionado o ingress HA | TRL6+ |
| Base de datos | PostgreSQL HA + backup inmutable | TRL6+ |
| Caché | Redis cluster / single + persistencia según SNN | TRL6+ |
| Almacenamiento | Object + block según backups y artefactos | TRL6+ |
| Monitorización | Prometheus/Grafana/Netdata según política | TRL6+ |

### 3.2 Presupuesto total *(6 meses — ejemplo de estructura)*

| Concepto | Nota |
|----------|------|
| Infraestructura recurrente | Suma mensual **cotizada** (compute, DB, LB, obs). |
| Legal / DPO / asesoría AI Act | Partida única o recurrente según contrato. |
| Hardware IoT / campo | CAPEX separado; no mezclar con VPS sin acta. |
| **Total** | **Solo válido** tras hoja de cálculo interna firmada. |

*El total €25.140 del borrador es **ficción de planificación** hasta presupuesto real.*

---

## 🛡️ 4. Seguridad y cumplimiento soberano

### 4.1 Medidas avanzadas *(referencia)*

| Medida | Implementación típica | Estándar / marco |
|--------|-------------------------|------------------|
| Firewall perimetral | FW proveedor + `nftables`/host | ISO 27001 *(si se certifica)*; CIS |
| Cifrado en tránsito | **TLS 1.3** (ACME/Let’s Encrypt u PKI interna) | Buenas prácticas; no confundir con eIDAS |
| Autenticación | MFA, Keycloak/IdP en región acordada; PQC en aplicación según [pq_crypto](../../backend/security/pq_crypto.py) | Política interna |
| Segmentación | vRack, VLANs, políticas K8s NetworkPolicy | CIS v8 |
| Backup | PGBackRest / snapshots + object lock si aplica | RGPD art. 32 *(medidas técnicas)* |

### 4.2 Cumplimiento legal

| Regulación | Medida | Responsable |
|------------|--------|-------------|
| **RGPD** | Minimización, `parcela_id` según DPIA, retención | DPO |
| **AI Act** | Clasificación del sistema, documentación, **proceso** con asesoría *(no “un registro mágico en BD UE”)* | Legal + producto |
| **PAC 2040** | Coherencia con SIGPAC/datos de explotación cuando aplique | Agronomía / administración |

---

## 📈 5. Métricas de escalado

*Objetivos **diseño**; medir baseline en TRL6 antes de fijar SLAs.*

### 5.1 Métricas técnicas

| Métrica | Objetivo TRL6 *(ejemplo)* | Objetivo TRL7 *(ejemplo)* | Herramienta |
|---------|---------------------------|---------------------------|-------------|
| `castuo_neuro_hydro_infer_seconds` | Mejorar vs baseline medido | Mejorar vs TRL6 | Prometheus / Netdata |
| Disponibilidad servicio | SLA interno acordado | SLA más estricto **si** medido 30+ días | Probe + SLO |
| Tiempo respuesta incidente | Definir TTR interno | Reducir con evidencia | Runbook |
| Éxito de despliegue | % pipelines verdes | Subir vs baseline | CI *(p. ej. GitHub Actions u otro)* |

### 5.2 Métricas de negocio

*No fijar en git **coste por inferencia**, **ROI** o **% adopción** sin modelo económico y datos reales.*

| Métrica | Uso |
|---------|-----|
| Coste por inferencia | KPI interno tras contabilidad de cómputo |
| ROI | **Fuera** del alcance del repositorio salvo informe financiero |
| Adopción agricultores | Encuestas / uso con base RGPD |

---

## 🔄 6. Plan de migración (Hetzner → soberano UE)

*Ejemplo de fases; ajustar ventanas y proveedor.*

### 6.1 Cronograma *(3 meses orientativos)*

| Fase | Acción | Responsable típico |
|------|--------|---------------------|
| Meses 1–2 | Aprovisionamiento UE, migración datos, pruebas de carga acotadas | DevOps |
| Mes 3 | Validación operativa, documentación, formación | SRE |

### 6.2 Checklist validación TRL7 *(orientativa)*

Ver checklist versionada: [CHECKLIST-MIGRACION-TRL7.md](./CHECKLIST-MIGRACION-TRL7.md).

*Ejemplos de criterio (definir umbral interno):*

- [ ] Uptime medido ≥ objetivo **acordado** en ventana (p. ej. 30 días).  
- [ ] Latencia SNN mejorada vs baseline **archivado**.  
- [ ] 0 incidentes **críticos abiertos** sin plan/fecha *(según definición de crítico)*.  
- [ ] RGPD / AI Act: actas y DPIA **actualizada** si cambia tratamiento o ubicación.  
- [ ] Inventario de componentes y **regiones** de datos documentado.

---

## 📜 7. Documentación y recursos

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| **Este prontuario** | Maestro TRL6→TRL7 infra | *(este archivo)* |
| Puntero corto | Mismo contenido | [PRONTUARIO-INFRAESTRUCTURA-SOBERANA.md](./PRONTUARIO-INFRAESTRUCTURA-SOBERANA.md) |
| Checklist migración TRL7 | Cierre de fase | [CHECKLIST-MIGRACION-TRL7.md](./CHECKLIST-MIGRACION-TRL7.md) |
| DPIA robotics | Tratamiento datos lab/robotics | [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |

*No existe `DPIA-SOBERANIA-2026.md` en el repo: actualizar DPIA vigente o crear anexo con **DPO** si el cambio de infraestructura altera transferencias o subencargados.*

---

## 🎯 8. Conclusión y recomendaciones

### 8.1 Top 5 acciones *(orden sujeto a riesgo)*

1. Elegir **IaaS/PaaS UE** y región de datos por contrato.  
2. Definir **PostgreSQL + Redis** gestionados o self-host con mismo nivel de backup.  
3. **Observabilidad** (Prometheus/Grafana/Netdata) con alertas mínimas.  
4. **Migración por fases** con rollback documentado.  
5. **Cierre legal** (DPIA, encargados del tratamiento, AI Act si aplica).

### 8.2 Estrategia

- **Soberanía:** región + jurisdicción + licencias FOSS entendidas.  
- **Resiliencia:** medir antes de prometer “99,95 %”.  
- **Honestidad:** costes y SLAs en hoja interna, no solo en markdown público.

---

*El agua del regadío y el dato del edge no negocian con catálogos desactualizados: cotizar y medir.*
