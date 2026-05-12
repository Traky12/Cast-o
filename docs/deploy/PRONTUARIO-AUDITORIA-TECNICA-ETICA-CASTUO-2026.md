# Prontuario de auditoría técnica y ética — CASTÚO-System (2026)

*Análisis orientativo de **debilidades**, **puntos críticos**, **mejoras** y camino hacia la excelencia operativa. **No** sustituye una auditoría externa firmada ni presupuestos contractuales.*

**Relación:** [PRONTUARIO-MAESTRO-AUDITORIA-EVOLUCION-RESILIENTE-2026.md](./PRONTUARIO-MAESTRO-AUDITORIA-EVOLUCION-RESILIENTE-2026.md) *(síntesis resiliente / evidencia)* · [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) · [PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md](../legal/PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md) · [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md)

---

## 📋 1. Metodología de auditoría

*Enfoque técnico y ético; cada hallazgo debe poder **ligarse a evidencia** (código, log, captura, ticket).*

### 1.1 Áreas de auditoría

| Área | Enfoque | Herramientas *(ejemplos)* |
|------|---------|---------------------------|
| **Seguridad** | Vulnerabilidades, hardening, LLMNR/LAN | Nmap, OpenVAS, OWASP ZAP *(FOSS)*, tcpdump; Metasploit **solo** con mandato |
| **Rendimiento** | Latencia, caché, SLO | Prometheus, Grafana, Locust *(carga acordada)* |
| **Cumplimiento legal** | RGPD, AI Act, PAC cuando aplique | DPIA, checklists legales, registro de tratamientos *(fuera de git si es sensible)* |
| **Ética rural** | Confianza, inclusión, minimización | Matriz de impacto ético, entrevistas de campo *(proceso)* |
| **Código abierto** | Licencias, dependencias | `pip-licenses`, FOSSology, `licensecheck` |

---

## ⚠️ 2. Debilidades y puntos críticos

*Severidades orientativas; validar en **tu** entorno.*

### 2.1 Debilidades técnicas

| Debilidad | Impacto | Evidencia *(repo / ops)* | Severidad | Área |
|-----------|---------|---------------------------|-----------|------|
| **LLMNR poisoning** *(LAN mixta)* | Robo de sesión / relay hacia hosts con privilegios | Tráfico UDP 5355 en `tcpdump` si LLMNR activo | Crítica *(si LAN no confiable)* | Seguridad |
| **Validación de sensores SNN** | Decisiones subóptimas si inputs fuera de rango | `HydroSensorIn` en rutas documentadas; otros flujos pueden no validar igual | Alta | SNN |
| **Multilinker** *(capa operativa)* | Gobernanza fragmentada | Convención doc + playbook; sin agente único versionado | Media | Arquitectura |
| **Grafana** | Menos visibilidad operativa | Dashboards no versionados en el clon | Media | Observabilidad |
| **TTL caché SNN** | Regresión si se ignora `snn_cache_ttl_seconds()` | `neuromorphic_edge.hydro_infer_dict` usa `ttl` dinámico; riesgo = **código futuro** con literal fijo | Media | Rendimiento |

### 2.2 Puntos críticos éticos / de cumplimiento

| Punto crítico | Impacto ético / legal | Evidencia *(indicativa)* | Severidad | Área |
|---------------|------------------------|--------------------------|-----------|------|
| **Transparencia hacia operadores** | Desconfianza si no hay runbooks claros | Depende de despliegue; mejorar con informes acotados | Alta | Gobernanza |
| **`parcela_id` y trazas** | Re-identificación si se enlaza a persona | P. ej. logs stub PEI-002 con `parcela_id`; comentario DPIA en código | Alta | Privacidad / legal |
| **AI Act / GPAI** | Obligaciones según clasificación del sistema | **Proceso legal** y documentación; **no** un único “registro en BD UE” en el código | Alta | Legal |
| **Memristores / hardware** | Dependencia de cadena de suministro | Roadmap I+D vs simulación en repo | Media | Soberanía |
| **UX rural** | Exclusión si solo hay flujos “dev” | Modo agricultor no técnico **no** cerrado en UI | Media | Inclusión |

---

## 🔧 3. Mejoras recomendadas

*Priorización por **riesgo** y **esfuerzo**; **no** se afirma ROI numérico en este repositorio.*

### 3.1 Mejoras de seguridad

| Mejora | Beneficio | Esfuerzo | Plazo orientativo |
|--------|-----------|----------|-------------------|
| Mitigar LLMNR/mDNS en edge | Cierra vector clásico en LAN | Bajo | 1 semana |
| Formalizar Multilinker en ops | Checklist + playbook + evidencia | Medio | 2 semanas |
| Endurecer validación de entrada SNN | Menos decisiones con datos corruptos | Bajo | días |
| Firma PQC *(Dilithium)* en payloads donde aplique | Integridad criptográfica | Medio–alto | según roadmap |
| Grafana / SLO | Visibilidad y alertas acordadas | Medio | 2 semanas |

### 3.2 Mejoras éticas / de cumplimiento

| Mejora | Beneficio | Esfuerzo | Plazo orientativo |
|--------|-----------|----------|-------------------|
| Informe de transparencia operativa *(acotado)* | Confianza sin filtrar secretos | Medio | 1 mes |
| Política de minimización en logs | Menos `parcela_id` donde no sea necesario | Bajo–medio | 1–2 semanas |
| Modo / flujos “no técnico” | Inclusión | Alto | 2+ meses |
| Soberanía de proveedores *(hardware)* | Dependencias auditables | Alto | trimestres |
| Tramitación AI Act con asesoría | Cumplimiento normativo | Alto | según producto |

---

## 🌱 4. Implementaciones hacia excelencia

*Roadmaps **orientativos**; KPI “100%” solo tras definición contractual de medición.*

### 4.1 Roadmap ~6 meses

| Fase | Acción | Plazo | Criterio de éxito *(ejemplo)* |
|------|--------|-------|--------------------------------|
| Mes 1 | Mitigar LLMNR (Hetzner/staging) | 1 semana | Política en `resolved.conf` + evidencia `tcpdump` |
| Mes 1 | Multilinker ops (playbook + checklist) | 2 semanas | Checks ejecutados y archivados |
| Mes 1 | Validar resolución DNS post-cambio | 1 día | `resolvectl` + prueba de servicio |
| Mes 2–3 | Grafana + paneles mínimos | 2 semanas | Métricas clave visibles sin PII |
| Mes 2–3 | Auditoría seguridad | 1 mes | Informe con remediación fechada |
| Mes 2–3 | TTL documentado y revisado | 1 día | [README robotics](../../backend/integrations/robotics/README.md#política-de-ttl-para-caché-snn) |
| Mes 4–6 | Campo / feedback *(si aplica)* | continuo | Actas o encuestas con alcance RGPD |
| Mes 4–6 | AI Act / DPIA | según legal | Cierre con DPO donde proceda |

### 4.2 Roadmap ~12 meses *(hipótesis)*

| Ventana | Acción | Nota |
|---------|--------|------|
| Mes 7–9 | Cadena suministro / pilots hardware | Evidencia contractual, no solo git |
| Mes 7–9 | Optimización latencia SNN | Medir baseline antes de fijar % |
| Mes 10–12 | Nuevos cultivos / dominios | Validación agronómica + legal |
| Mes 10–12 | Certificación / sello *(si programa)* | Externo al repositorio |
| Mes 10–12 | CI/CD endurecido | Gates de seguridad en pipeline |

---

## 📊 5. Métricas de excelencia

*Los valores **actuales** deben **medirse** en tu entorno; lo siguiente son **metas de diseño**, no lecturas del clon.*

### 5.1 Métricas técnicas

| Métrica | Objetivo | Actual *(obligatorio medir)* | Meta orientativa | Herramienta |
|---------|----------|------------------------------|------------------|---------------|
| `castuo_neuro_hydro_infer_seconds` | Latencia SNN | Baseline TBD | Mejorar vs baseline | Prometheus |
| `system_uptime` / SLI | Disponibilidad | Baseline TBD | Según SLA interno | Probe / exporter |
| Tráfico LLMNR (5355) | Seguridad LAN | 0 en ventana de prueba acordada | 0 | tcpdump |
| Custodia secretos | A/B, no .env prod | Revisar despliegue | 100% A o B | Checklist Vault |
| Minimización logs | Menos identificadores | Auditar muestras | Política escrita | Revisión manual |

### 5.2 Métricas éticas / sociales

| Métrica | Objetivo | Actual | Meta | Herramienta |
|---------|----------|--------|------|---------------|
| Satisfacción usuarios campo | Confianza | Encuesta TBD | Definir escala | Encuestas + RGPD |
| Transparencia publicable | Runbooks e informes | TBD | Publicar lo acordado | Comunicación |
| Soberanía tecnológica | % componentes auditables / UE | Matriz TBD | Según política | Inventario |
| Huella / eficiencia | Recursos por inferencia | TBD | Mejorar vs baseline | Medición infra |
| Inclusión | Uso modo simplificado | TBD | Definir KPI | Producto |

---

## 🔧 6. Implementaciones técnicas detalladas

### 6.1 Mitigación LLMNR *(Ubuntu / Hetzner)*

Canónico y advertencias de `sed`: [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) §2.2 y [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md).

```bash
grep -E '^LLMNR=|^MulticastDNS=' /etc/systemd/resolved.conf
# … editar [Resolve] o sed una sola vez verificado — ver doc enlazada
sudo systemctl restart systemd-resolved
sudo resolvectl status
sudo tcpdump -i any udp port 5355 -c 10
```

### 6.2 Multilinker y playbook

**En el código** existe `llmnr_multicast_off` en `backend/models/system_admin_playbook.py`. **No** existen en el repo los comandos `multilinker status` ni `multilinker integrate`; son **ilustrativos** hasta que el equipo estandarice un agente.

```python
# Implementado hoy (resumen)
CRITICAL_HARDENING_CHECKS["llmnr_multicast_off"]  # cmd, expected list, remediation → doc §2.2
```

### 6.3 Grafana *(orientativo)*

El despliegue puede ser **paquete del SO**, **Docker** o **managed**; ajustar a tu política.

```bash
# Ejemplo Debian/Ubuntu — verificar versión y hardening
sudo apt install grafana
sudo systemctl enable --now grafana-server
```

*No usar en documentación comandos inexistentes tipo `multilinker configure-grafana` hasta existan en el repositorio.*

---

## 📜 7. Documentación y gobernanza ética

### 7.1 Documentos clave

| Documento | Propósito | Estado | Enlace |
|-----------|-----------|--------|--------|
| Evolución TRL superior | TRL y evidencia | ✅ | [PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md) |
| Evolución segura y ética | Componentes y principios | ✅ | [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) |
| Integraciones P1–P3 | Mejoras | ✅ | [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) |
| DPIA Robotics | Impacto tratamiento | 🟡 | [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |
| Matriz TRL aceleradora | Plan campo | 📋 | [PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md](../legal/PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md) |

### 7.2 Gobernanza ética *(roles orientativos)*

| Proceso | Descripción | Frecuencia | Responsable *(típico)* |
|---------|-------------|------------|-------------------------|
| Revisión ética / riesgos | Alineación con valores y DPIA | Trimestral | DPO + técnico |
| Transparencia publicable | Qué se publica y qué no | Semestral | Legal + producto |
| Soberanía y dependencias | Inventario y alternativas UE/FOSS | Anual | Arquitectura |
| Feedback campo | Encuestas / entrevistas con consentimiento | Según programa | Operaciones |

---

## 🎯 8. Conclusión y recomendaciones finales

### 8.1 Prioridades *(top 5)*

| Acción | Plazo | Impacto | Prioridad |
|--------|-------|---------|-----------|
| Mitigar LLMNR en edge/LAN relevante | 1 semana | Reduce vector crítico en entornos mixtos | Máxima |
| Formalizar Multilinker (ops + tests) | 2 semanas | Coherencia gobernanza | Máxima |
| Grafana / observabilidad mínima | 2 semanas | Detección temprana | Alta |
| Auditoría seguridad externa o interna rigurosa | 1 mes | Hallazgos fechados | Alta |
| Política TTL + revisión logs `parcela_id` | días–semanas | Reduce regresión y riesgo privacy | Media–alta |

### 8.2 Líneas estratégicas

1. **Seguridad con mínima exposición:** LLMNR, secretos A/B, TLS, firma PQC donde aplique.  
2. **Multilinker como disciplina:** un solo hilo entre checklist, playbook y staging.  
3. **Legal y ética:** DPIA, AI Act y minimización — con asesoramiento externo si el producto lo exige.  
4. **Soberanía:** preferir FOSS auditables y proveedores alineados con política europea cuando haya paridad técnica.  
5. **Sostenibilidad:** medir antes de optimizar (agua, energía, cómputo).

---

*Una auditoría que no deja huella verificable en el territorio es solo papel; una que humilla al pequeño agricultor deja de ser ética.*
