# Prontuario maestro — auditoría y evolución resiliente (2026)

*Análisis **realista** basado en **evidencia del repositorio**. No sustituye auditoría externa firmada.*

**Relación:** [PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md](./PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md) · [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md) · [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md)

---

## 📋 1. Principios rectores

*Fundamentos para auditoría honesta y evolución resiliente.*

1. Solo auditamos lo que existe en el repositorio.  
2. Priorizamos soluciones basadas en código real.  
3. Documentamos riesgos demostrables, no hipotéticos.  
4. Planificamos mejoras verificables mediante evidencia.  
5. Mantenemos transparencia sobre el estado real del sistema.

---

## 🔧 2. Herramientas de auditoría

*Recursos para evaluación técnica realista.*

| Herramienta | Uso concreto | Alternativa |
|-------------|--------------|-------------|
| **rg** (ripgrep) | Búsqueda de patrones: `rg "setex.*300"` para auditar **posibles regresiones TTL** (también revisar `neuromorphic_edge.py` — TTL vía `snn_cache_ttl_seconds()`) | `grep -r` |
| **tcpdump** | Verificación de tráfico LLMNR: `tcpdump -i any udp port 5355` | tshark |
| **Prometheus** | Monitorización de métricas reales: `castuo_neuro_hydro_infer_seconds` | — |
| **Locust** | Pruebas de carga: simulación de requests a `POST /api/robotics/lab/neuromorphic/hydroponics/infer` | k6, vegeta |
| **OWASP ZAP** | Análisis de seguridad web (alternativa ética a Burp Suite) | Nikto |

---

## 📊 3. Diagnóstico de componentes

*Análisis basado en evidencia real del repositorio.*

### 3.1 Tabla de componentes reales

| Componente | Estado real | Evidencia | Riesgos reales | Fortalezas |
|------------|-------------|-----------|----------------|------------|
| **SNN** (`neuromorphic_edge.py`) | TRL 4–5 | Código con tests en CI; uso de `snn_cache_ttl_seconds()` para TTL dinámico | Posible regresión si se introducen literales TTL (ej. `setex(..., 300)` en caché Redis); validación parcial de sensores | Arquitectura modular bien documentada; integración con ecosistema SIGPAC/PEI en despliegues que los acoplen |
| **TraceChain** | TRL 5 | Persistencia SQLite implementada; stub funcional | Sin nodo GaiaChain real en el clon; firma digital según despliegue | Implementación robusta de stub; integración con SNN en flujos lab/snapshot según configuración |
| **SIGPAC** | TRL 6 | Validación de usos del suelo; ecosistema PEI/SNN | `mapping.json` estático; validación de geometrías incompleta según alcance | Funcionalidad probada en flujo PEI; diseño extensible |
| **Señales (RF/IoT)** | TRL 3–4 | Stub GNU Radio; diseño para sensores | Sin integración real con hardware en repo; memristores no implementados | Arquitectura preparada para IoT; diseño modular |
| **Monitorización** | TRL 5 | Métricas básicas Prometheus en lab (`CASTUO_PROMETHEUS_METRICS=1`) | Sin dashboards en Grafana en repo; alertas no completas | Métricas clave disponibles en código; integrable con el stack de despliegue |

*El acoplamiento concreto entre PEI, SIGPAC y SNN depende del **despliegue**; el repositorio mantiene **módulos** y rutas documentadas.*

---

## ⚠️ 4. Puntos críticos demostrables

*Vulnerabilidades y riesgos con evidencia real.*

### 4.1 Vulnerabilidades técnicas

| Vulnerabilidad | Impacto | Evidencia | Severidad | Solución real |
|----------------|---------|-----------|-----------|---------------|
| **LLMNR poisoning** | Robo de tokens y escalada *(vía host comprometido en LAN)* | `tcpdump -i any udp port 5355` muestra tráfico en sistemas sin hardening | Crítica | Deshabilitar LLMNR/mDNS en `/etc/systemd/resolved.conf` — §5.1 y [evolución §2.2](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) |
| **Validación de sensores incompleta** | Decisiones incorrectas | Solo `/lab/neuromorphic/hydroponics/infer` usa `HydroSensorIn` | Alta | Extender validación a todas las rutas de sensores en alcance |
| **Riesgo de regresión TTL** | Ineficiencia en caché | Posibilidad de introducir literales TTL si se ignora `snn_cache_ttl_seconds()` | Media | Usar exclusivamente `snn_cache_ttl_seconds()` para TTL dinámico en Redis SNN |
| **Grafana no configurada** | Falta de visibilidad | Sin dashboards operativos versionados aquí | Media | Configurar dashboards básicos para métricas clave (**importar JSON versionado internamente**) |

---

## 🛡️ 5. Mitigaciones reales

*Soluciones basadas en código y ops existentes.*

### 5.1 Mitigación de LLMNR poisoning

```bash
# 1. Verificar estado actual
grep -E '^LLMNR=|^MulticastDNS=' /etc/systemd/resolved.conf

# 2. Configurar hardening (sin romper DNS — ver advertencias sed en doc evolución)
sudo sed -i '/\[Resolve\]/a LLMNR=no\nMulticastDNS=no' /etc/systemd/resolved.conf

# 3. Reiniciar servicio
sudo systemctl restart systemd-resolved

# 4. Verificar
sudo resolvectl status
sudo tcpdump -i any udp port 5355 -c 10   # Objetivo: 0 paquetes LLMNR salvo excepción documentada
```

### 5.2 Configuración básica de Grafana

```bash
# 1. Instalación (Ubuntu/Debian)
sudo apt install grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# 2. Configuración inicial (ajustar ruta homepath según paquete)
grafana-cli admin reset-admin-password --homepath /usr/share/grafana

# 3. Importar dashboards básicos (desde versionado interno)
cp /path/to/internal/dashboards/castuo-basic.json .
grafana-cli admin import-dashboards -f castuo-basic.json
```

*La sintaxis exacta de `grafana-cli` depende de la versión de Grafana; alternativa: **API HTTP** o **UI** de importación.*

---

## 📈 6. Métricas y evolución

*Indicadores basados en evidencia: **medir** en Prometheus/staging.*

### 6.1 Métricas actuales (medir en Prometheus/staging)

| Métrica | Fuente |
|---------|--------|
| `castuo_neuro_hydro_infer_seconds` | Prometheus |
| `system_uptime` / SLI de disponibilidad | Prometheus / probes |

### 6.2 Roadmap de evolución resiliente

| Acción | Plazo | Criterio de éxito | Prioridad |
|--------|-------|-------------------|-----------|
| Mitigar LLMNR en producción | 1 semana | 0 paquetes UDP 5355 *(ventana acordada)* | 🔥🔥🔥 |
| Configurar Grafana básica | 2 semanas | Dashboards operativos | 🔥🔥 |
| Auditoría de TTL | 1 día | Confirmar uso de `snn_cache_ttl_seconds()` | 🔥 |
| Documentar política de TTL | 1 día | Tabla en [README robotics](../../backend/integrations/robotics/README.md#política-de-ttl-para-caché-snn) | 🔥 |
| Extender validación de sensores | 2 semanas | 100 % rutas validadas **según alcance definido** | 🔥🔥 |

---

## 📜 7. Documentación y gobernanza

*Recursos para implementación realista.*

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md | Síntesis de componentes y hoja de ruta 6 meses | [Enlace](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) |
| PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md | Auditoría técnica y ética detallada | [Enlace](./PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md) |
| CHECKLIST-TRL6-HETZNER-STAGING.md | Validación en entorno staging | [Enlace](./CHECKLIST-TRL6-HETZNER-STAGING.md) |
| DPIA-Robotics-2026.md | Análisis de impacto legal y ético | [Enlace](../legal/DPIA-Robotics-2026.md) |

---

## 🎯 8. Conclusión y recomendaciones

*Resumen basado en realidad técnica.*

### 8.1 Top 3 acciones inmediatas

1. Mitigar LLMNR en producción (1 semana).  
2. Configurar Grafana básica (2 semanas).  
3. Auditoría y limpieza de TTL (1 día).

### 8.2 Recomendaciones estratégicas

**Enfoque en seguridad demostrable**

- Priorizar mitigación de vulnerabilidades reales.  
- Implementar soluciones basadas en código existente.

**Evolución resiliente**

- Planificar mejoras basadas en métricas reales.  
- Evitar promesas de rendimiento sin evidencia.

**Documentación honesta**

- Mantener transparencia sobre el estado real del sistema.  
- Documentar solo lo implementado y verificable.

---

🚜 *Pa'lante, campeón.* 🌱

*Prontuario realista: debilidades y fortalezas con evidencia, soluciones ancladas al código, roadmap verificable y documentación transparente para implementación.*
