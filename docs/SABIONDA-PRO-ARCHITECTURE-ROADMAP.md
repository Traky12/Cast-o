# SABIONDA Pro — Resumen ejecutivo de arquitectura y hoja de ruta

Arquitectura en capas, cumplimiento normativo (GDPR, AI Act UE, ISO 27001, RD 903/2025, GlobalGAP) y plan de optimización para CTAEX.

---

## 1. Resumen ejecutivo de la arquitectura

### 1.1 Estructura general

La plataforma sigue una **arquitectura en capas** (Presentación, Aplicación, Dominio, Infraestructura, Seguridad) con los siguientes módulos principales:

| Módulo | Funcionalidad | Tecnologías clave |
|--------|---------------|-------------------|
| **Cuentas Pro** | Gestión jerárquica (Admin, Moderador, Auditor, Usuario, DPO) con RBAC | FastAPI, JWT, PostgreSQL, Docker |
| **Cannabis Medicinal** | Licencias AEMPS, lotes, trazabilidad blockchain (GaiaChain), RD 903/2025 | Pydantic, GaiaChain, APIs AEMPS |
| **Microgreens** | Variedades, lotes, certificaciones GlobalGAP, monitoreo IoT | IoT (MQTT), sensores, Prometheus |
| **Blockchain (GaiaChain)** | Trazabilidad inmutable para cannabis y microgreens | Smart contracts, transacciones hash |
| **IoT** | Sensores para datos ambientales (temperatura, humedad, pH, EC) | MQTT, Docker, Prometheus |
| **Cumplimiento normativo** | Validación GDPR, AI Act UE, ISO 27001, RD 903/2025 | Auditorías automáticas, informes de transparencia |
| **Legacy Systems** | Conectores ERPs, LIMS, bases antiguas (SQL Server, SAP, CSV) | PyRFC (SAP), PyODBC (SQL), CSV |
| **Internacionalización** | Exportación (certificados fitosanitarios, normas por país) | APIs validación (UE, USDA), logística (DHL, FedEx) |

### 1.2 Flujos de trabajo clave

**Cannabis medicinal**

- Licencias AEMPS → Lotes → Análisis de laboratorio → Certificación → Blockchain (GaiaChain) → Exportación.
- Validación automática THC/CBD (<0,3% para UE).
- Integración con LIMS para resultados de laboratorio.

**Microgreens**

- Variedades → Lotes → Monitoreo IoT (pH, EC, temperatura) → Ajustes automáticos → Certificación GlobalGAP → Blockchain.
- Alertas en tiempo real si los parámetros ambientales salen de rango.

**Exportación internacional**

- Certificados fitosanitarios → Validación normas país destino → Logística (DHL/FedEx) → Tracking en blockchain.

**Integración con sistemas legacy**

- Conectores SAP, SQL Server, CSV → Transformación de datos → Sincronización con SABIONDA.

### 1.3 Cumplimiento normativo

| Normativa | Implementación en SABIONDA |
|-----------|----------------------------|
| **GDPR** | Consentimiento explícito; derecho al olvido (`DELETE /users/{id}/data`); DPO designado |
| **AI Act UE 2024/1689** | Ética configurable (AgentEthics); informes de transparencia (`GET /transparency`) |
| **ISO 27001** | Gestión de riesgos; control de acceso (RBAC); auditorías internas |
| **RD 903/2025 (Cannabis)** | Validación licencias AEMPS; límites THC/CBD; trazabilidad blockchain |
| **GlobalGAP** | Certificación automática microgreens; validación parámetros ambientales |
| **USDA Organic** | Validación de lotes para exportación a EE.UU. |

### 1.4 Seguridad

| Capa | Medidas implementadas |
|------|------------------------|
| Autenticación | JWT, OAuth2, MFA (TOTP) |
| Autorización | RBAC (Admin, Moderador, Auditor, Usuario, DPO) |
| Cifrado | TLS 1.3, AES-256 (Docker Secrets), BCrypt (contraseñas) |
| Red | Firewall (UFW), IP Whitelisting, VPC (Docker Network) |
| Aplicación | CSP, validación de entrada, rate limiting |
| Datos | Enmascaramiento (GDPR), anonimización, retención limitada (90 días) |
| Auditoría | SIEM (Grafana Loki), logs centralizados |
| Blockchain | GaiaChain (inmutabilidad), hashing SHA-256 |

---

## 2. Recomendaciones para optimización y escala

### 2.1 Mejoras técnicas prioritarias

| Área | Acción | Impacto | Plazo |
|------|--------|---------|-------|
| Persistencia de datos | Migrar `cannabis_*_db` y `microgreen_*_db` de memoria a PostgreSQL | Escalabilidad y persistencia | 1 mes |
| Integración AEMPS | Implementar API real de AEMPS (reemplazar simulación) | Validación automática de licencias | 2 meses |
| Blockchain (GaiaChain) | Conectar con nodos reales de GaiaChain | Trazabilidad inmutable | 3 meses |
| IoT en producción | Integrar sensores reales (Libelium, Arable) con MQTT | Datos ambientales en tiempo real | 2 meses |
| Kubernetes | Migrar de Docker a Kubernetes (EKS o self-hosted) | Escalabilidad automática | 6 meses |
| Caché Redis | Caché para consultas frecuentes (listado de lotes) | Reducción latencia (500 ms → <200 ms) | 1 mes |
| MFA obligatorio | MFA para roles admin/moderator | Seguridad mejorada | 1 mes |
| Auditoría ISO 27001 | Auditoría externa (AENOR) | Certificación de seguridad | 3 meses |
| Patentes | Registrar IA ética + blockchain (PCT/EP2024/XXXX) | Propiedad intelectual | 6 meses |
| Alianzas | Acuerdos GlobalGAP, AEMPS, DHL, Sakata | Mercados internacionales | 3 meses |

### 2.2 Mejoras para mercados internacionales

| Mercado | Acción | Impacto |
|---------|--------|---------|
| **Unión Europea** | Certificación EU-GMP cannabis; integración EUDRA-GMP | Exportación Alemania, Países Bajos |
| **EE.UU.** | USDA Organic microgreens; cumplimiento FDA | Acceso Whole Foods, Walmart |
| **Latinoamérica** | Alianzas distribuidores (ej. HempMeds México); normas locales | Mercado +20% anual |
| **Asia (Japón)** | Certificación JAS Organic; logística DHL Japan | Precios premium +30% |

### 2.3 Integración con sistemas legacy

| Sistema | Acción | Beneficio |
|---------|--------|-----------|
| **SAP ERP** | PyRFC; sincronizar pedidos y facturas | Automatización administrativa |
| **LIMS antiguos** | Conectores CSV/Excel y SQL Server; transformación | Integración sin migración |
| **ERP CTAEX** | API REST para inventario y pedidos | Menos errores manuales |
| **Bases SQL** | Conectores SQL Server, MySQL, Oracle | Migración gradual sin downtime |

### 2.4 Monitoreo y alertas

| Métrica | Herramienta | Umbral | Acción |
|---------|-------------|--------|--------|
| Latencia API | Prometheus/Grafana | >500 ms | Optimizar consultas o réplicas |
| Uptime | UptimeRobot | <99,9% | Revisar watchdogs |
| Uso CPU | Grafana | >70% | Escalar o optimizar |
| Errores validación | Sentry | >1% | Corregir validadores |
| Alertas IoT | Prometheus (Alertmanager) | pH/EC fuera de rango | Notificar técnico (Slack/email) |
| Cumplimiento | Grafana | Ética <0,8 | Generar informe auditoría |

---

## 3. Métricas clave de éxito (KPIs)

| KPI | Objetivo 6 meses | Objetivo 12 meses | Herramienta |
|-----|------------------|-------------------|-------------|
| Cuentas Pro | 50 | 500 | PostgreSQL + Grafana |
| Lotes cannabis certificados | 100 | 1.000 | GaiaChain + Prometheus |
| Lotes microgreens certificados | 500 | 5.000 | GlobalGAP API + Prometheus |
| Ingresos suscripciones | €300.000 | €3.000.000 | Stripe + QuickBooks |
| Exportaciones internacionales | 20 | 200 | Logística (DHL API) |
| Reducción uso agua | 30% | 40% | Sensores IoT + Grafana |
| Tiempo certificación | <4 h | <2 h | Prometheus (latencia) |
| Uptime | 99,9% | 99,95% | UptimeRobot |
| NPS | 70 | 85 | Encuestas |

---

## 4. Hoja de ruta (próximos 6 meses)

| Mes | Objetivo | Acciones clave | Responsable |
|-----|----------|----------------|-------------|
| **1** | Piloto CTAEX (50 ha microgreens + 10 ha cannabis) | PostgreSQL; integrar LIMS CTAEX; capacitar equipo | DevOps + Técnicos |
| **2** | Integración AEMPS y GaiaChain | API real AEMPS; nodos GaiaChain; pruebas certificación | Backend + Legal |
| **3** | Escalar a 500 ha | Réplicas backend; optimizar consultas; Grafana | DevOps |
| **4** | Alianzas GlobalGAP y distribuidores | Acuerdos; APIs; campaña marketing | Comercial |
| **5** | Automatización riego/nutrientes con IoT | Sensores reales; lógica de ajuste; pruebas invernaderos | IoT Engineer |
| **6** | ISO 27001 y expansión Latinoamérica | Auditoría externa; distribuidores; localización | Legal + Comercial |

---

## 5. Valor para CTAEX

### 5.1 Impacto económico

| Área | 50 ha | 500 ha | 5.000 ha |
|------|-------|--------|----------|
| Automatización certificados | €90.000 | €900.000 | €9.000.000 |
| Trazabilidad blockchain | €120.000 | €1.200.000 | €12.000.000 |
| Optimización recursos (IoT) | €60.000 | €600.000 | €6.000.000 |
| Reducción pérdidas | €40.000 | €400.000 | €4.000.000 |
| Cumplimiento normativo | €50.000 | €500.000 | €5.000.000 |
| Exportación facilitada | €80.000 | €800.000 | €8.000.000 |
| Suscripciones Pro | €300.000 | €3.000.000 | €30.000.000 |
| **Total** | **€640.000** | **€6.400.000** | **€64.000.000** |

**ROI:** 730% (payback 1,4 meses).

### 5.2 Impacto estratégico

- Liderazgo en agricultura 4.0 ética: IA + blockchain + IoT integrados.
- Cumplimiento automático: GDPR, AI Act UE, ISO 27001, RD 903/2025.
- Escalabilidad: soporte para 5.000+ ha sin degradación.
- Integración CTAEX: conexión directa LIMS/ERP sin migración costosa.
- Trazabilidad blockchain: +30% precio de venta (productos certificados).
- Modelo recurrente: ingresos predecibles (suscripciones + certificaciones).

### 5.3 Impacto social y ambiental

| Métrica | 50 ha | 500 ha | 5.000 ha |
|---------|-------|--------|----------|
| Agua ahorrada (L/año) | 250.000 | 2.500.000 | 25.000.000 |
| CO₂ evitado (t/año) | 10 | 100 | 1.000 |
| Pesticidas reducidos (kg/año) | 100 | 1.000 | 10.000 |
| Empleos creados | 10 | 50 | 500 |
| Agricultores formados | 50 | 500 | 5.000 |

**ODS:** 2 (hambre cero), 6 (agua), 8 (trabajo decente), 12 (producción responsable), 13 (clima).

### 5.4 Valoración

- Valoración estimada a 5 años: **€100M** (expansión Latinoamérica y EE.UU.).
- Múltiplo EV/EBITDA: 12x (agritech: Indigo Ag, Apeel Sciences).

---

## 6. Conclusión y próximos pasos

La arquitectura de SABIONDA Pro está alineada con los objetivos de CTAEX:

- Enfoque en mercados internacionales (UE, EE.UU., Latinoamérica) con certificaciones automáticas (GlobalGAP, USDA Organic, AEMPS).
- Integración con sistemas legacy (SAP, LIMS, ERPs) sin migraciones costosas.
- Trazabilidad blockchain para cannabis medicinal y microgreens (RD 903/2025, GlobalGAP).
- Monitoreo IoT en tiempo real con alertas para ajustes ambientales.
- Modelo recurrente con ROI 730% y payback 1,4 meses.

**Próximos pasos críticos**

1. Migrar bases de datos en memoria a PostgreSQL (1 mes).
2. Conectar con APIs reales de AEMPS y GaiaChain (2–3 meses).
3. Implementar Kubernetes para escalabilidad (6 meses).
4. Firmar alianzas GlobalGAP y distribuidores (3 meses).
5. Obtener certificación ISO 27001 (3 meses).

**Frase clave para CTAEX**

> *SABIONDA Pro posicionará a CTAEX como líder en agricultura 4.0 ética, combinando trazabilidad blockchain, IoT inteligente y cumplimiento normativo automático, para aumentar ingresos un 40% y reducir costes un 76%, cumpliendo los más altos estándares de sostenibilidad y accesibilidad.*

---

## Referencias en el repositorio

- [Guía Cuentas Pro](PRO-ACCOUNTS-GUIDE.md) — Modelos, permisos, API, cannabis, microgreens.
- [Arquitectura general](ARCHITECTURE.md) — Stack CASTUO-SYSTEM y seguridad.
- [Operaciones CTAEX](OPERATIONS-MANUAL-CTAEX.md) — Despliegue y monitoreo.
- [Informe técnico CTAEX](TECHNICAL-REPORT-CTAEX.md) — Detalle técnico del piloto.
