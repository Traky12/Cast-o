# Guía de implementación — Acuerdo CTAEX–CASTÚO-SYSTEM

Documento interno para el seguimiento del marco jurídico, técnico y operativo de la colaboración.  
**Objetivo:** Trazabilidad, innovación y protección mutua.

---

## 1. Estado de los documentos

### 1.1. Anexos legales (docs/legal/)

| Anexo | Archivo | Contenido principal | Validación |
|-------|---------|---------------------|------------|
| **I** | [ANEXO-FONDO-I+D-CTAEX-CASTUO.md](legal/ANEXO-FONDO-I+D-CTAEX-CASTUO.md) | Fondo I+D 10% (máx. €50K/año), Comité Mixto (1+1, unanimidad), destino exclusivo, Ley 38/2003, UE 2021/695, GDPR, informes trimestrales, auditoría externa anual. | ✅ Revisado. Pendiente: Firma. |
| **II** | [ANEXO-II-PROTOCOLO-INTEGRACION-TECNICA.md](legal/ANEXO-II-PROTOCOLO-INTEGRACION-TECNICA.md) | LIMS, ERP, IoT, GaiaChain, AEMPS; flujos Mermaid; APIs; JWT + IP whitelist; pruebas; penalizaciones (LIMS 5%, certificación 10%, IoT 3%). | ✅ Revisado. Pendiente: Validar con equipo técnico CTAEX. |
| **III** | [ANEXO-III-CONFIDENCIALIDAD-Y-PROTECCION-DATOS.md](legal/ANEXO-III-CONFIDENCIALIDAD-Y-PROTECCION-DATOS.md) | Información confidencial, no divulgación, TLS 1.3, AES-256, PI 50/50 Fondo I+D; penalizaciones (€50K/€20K/€10K). | ✅ Revisado. Pendiente: Firma. |
| **IV** | [ANEXO-IV-LISTA-PERSONAL-AUTORIZADO.md](legal/ANEXO-IV-LISTA-PERSONAL-AUTORIZADO.md) | Tablas CTAEX y CASTÚO (placeholders), solicitud/aprobación 15 días, NDA individual, revocación. | ⚠️ Pendiente: Sustituir placeholders (ver sección 3). |
| **V** | [ANEXO-V-PROTOCOLO-SEGURIDAD-Y-CUMPLIMIENTO.md](legal/ANEXO-V-PROTOCOLO-SEGURIDAD-Y-CUMPLIMIENTO.md) | GDPR, ISO 27001, RD 903/2025, Ley 38/2003, AI Act; MFA, cifrado, auditorías; brecha 72h, incumplimiento normativo. | ✅ Revisado. Pendiente: Validar con seguridad CTAEX. |
| **VI** | [ANEXO-VI-PLAN-CONTINGENCIA-Y-RECUPERACION.md](legal/ANEXO-VI-PLAN-CONTINGENCIA-Y-RECUPERACION.md) | RTO/RPO &lt;4 h / &lt;1 h; PostgreSQL, GaiaChain, DDoS, brecha, IoT; rollback_to_memory.sh; backups; pruebas. | ✅ Revisado. Pendiente: Pruebas con DevOps. |
| **VII** | [ANEXO-VII-METRICAS-EXITO-Y-KPIS.md](legal/ANEXO-VII-METRICAS-EXITO-Y-KPIS.md) | KPIs financieros/operativos/I+D/cumplimiento; informes trimestrales; penalizaciones (uptime, certificación, I+D, GDPR). | ✅ Revisado. Pendiente: Ajustar métricas con operaciones CTAEX. |

### 1.2. Documentos actualizados

| Documento | Cambios | Estado |
|-----------|---------|--------|
| [CTAEX-CASTUO-AGREEMENT-SUMMARY.md](CTAEX-CASTUO-AGREEMENT-SUMMARY.md) | Sección 6: enlaces a Anexos I–VII; Sección 7: anexos parte integrante y vinculantes. | ✅ Actualizado. |
| [POSTGRESQL-MIGRATION-PLAN.md](POSTGRESQL-MIGRATION-PLAN.md) | Referencias a Anexo II (integración) y Anexo VI (contingencia). | ✅ Actualizado. |

---

## 2. Pendientes críticos

### 2.0. Tabla consolidada de pendientes

| Área | Tarea | Responsable | Plazo | Estado |
|------|-------|-------------|-------|--------|
| Anexo IV | Sustituir placeholders con nombres reales (3 CTAEX + 3 CASTÚO). | CTAEX (RRHH) + Gregorio | 3 días | ❌ Pendiente |
| Revisión legal | Abogado revisa Acuerdo Principal + Anexos I–VII. | Legal (ambas partes) | 5 días | ❌ Pendiente |
| Firma | Firma física/digital de todos los documentos. | Ambos | 1 día | ❌ Pendiente |
| Notarización | Opcional: notarizar en Cáceres. | Ambos | 3 días | ❌ Opcional |
| Integración LIMS/ERP | Pruebas con equipo técnico de CTAEX. | Técnico CTAEX | 5 días | ❌ Pendiente |
| Pruebas de contingencia | Ejecutar rollback_to_memory.sh y simular fallos. | DevOps | 10 días | ❌ Pendiente |
| Auditoría de seguridad | Contratar auditor externo (ej.: AENOR). | Seguridad | 7 días | ❌ Pendiente |
| Comité Mixto | Primera reunión para aprobar proyectos I+D. | Comité Mixto | 1 semana | ❌ Pendiente |

### 2.1. Ajustes en anexos

| Anexo | Acción | Responsable | Plazo |
|-------|--------|-------------|-------|
| **IV** | Sustituir placeholders (CTAEX: 3 nombres; CASTÚO: 3 nombres). | Gregorio (CASTÚO) + RRHH CTAEX | 3 días |
| **II** | Validar endpoints de API con equipo técnico CTAEX (ej.: /api/cannabis/batches). | Equipo Técnico CTAEX | 5 días |
| **V** | Revisar protocolos de brecha de seguridad con equipo de seguridad CTAEX. | Seguridad CTAEX | 7 días |
| **VI** | Ejecutar pruebas de contingencia (rollback a memoria, modo degradado GaiaChain). | DevOps | 10 días |

### 2.2. Revisión legal final

| Documento | Aspectos a revisar | Plazo |
|-----------|-------------------|-------|
| Acuerdo Principal | Cláusulas de equity (2%) y terminación. | 5 días |
| Anexo I (Fondo I+D) | Destino exclusivo del fondo y gobernanza del Comité Mixto. | 3 días |
| Anexo III (Confidencialidad) | Alcance de la información confidencial y penalizaciones. | 2 días |
| Anexo V (Seguridad) | Cumplimiento con ISO 27001 y GDPR. | 4 días |

**Recomendación:** Contratar a un abogado especializado en contratos tecnológicos (ej.: Garrigues, Cuatrecasas) para: equity y Ley de Sociedades de Capital; Fondo de I+D y Ley 38/2003; confidencialidad y propiedad intelectual.

### 2.3. Firmas y notarización

| Documento | Acción | Plazo |
|-----------|--------|-------|
| Acuerdo Principal + Anexos I–VII | Firma por ambas partes (digital o física). | 1 día |
| Notarización | Opcional: notarizar en Cáceres para mayor seguridad jurídica. | 3 días |

---

## 3. Checklist final para el lanzamiento

### 3.1. Documentación

| Tarea | Detalle | Responsable | Estado |
|-------|---------|-------------|--------|
| Revisión legal final | Abogado revisa Acuerdo Principal + Anexos I–VII. | Legal | ❌ Pendiente |
| Firma de documentos | Firma física/digital de Acuerdo + Anexos. | Ambos | ❌ Pendiente |
| Notarización (opcional) | Notarizar en Cáceres. | Ambos | ❌ Opcional |
| Sustituir placeholders Anexo IV | Rellenar nombres reales del personal autorizado. | RRHH CTAEX + Gregorio | ❌ Pendiente |

### 3.2. Implementación técnica

| Tarea | Detalle | Responsable | Estado |
|-------|---------|-------------|--------|
| Validar integración LIMS/ERP | Pruebas de sincronización con equipo técnico CTAEX. | Técnico CTAEX | ❌ Pendiente |
| Pruebas de contingencia | Ejecutar rollback_to_memory.sh y simular fallos GaiaChain. | DevOps | ❌ Pendiente |
| Configurar monitorización | Prometheus/Grafana (uptime, certificaciones, alertas IoT). | DevOps | ✅ Completado |
| Auditoría de seguridad inicial | Contratar auditor externo (ej.: AENOR) ISO 27001/GDPR. | Seguridad | ❌ Pendiente |

### 3.3. Operaciones

| Tarea | Detalle | Responsable | Estado |
|-------|---------|-------------|--------|
| Primera reunión Comité Mixto | Aprobar primeros proyectos del Fondo I+D. | Comité Mixto | ❌ Pendiente |
| Contratar auditor externo | Empresa para auditoría anual del Fondo I+D (ej.: Deloitte). | Finanzas | ❌ Pendiente |
| Primer informe trimestral | 15 días tras cierre del primer trimestre. | Finanzas | ❌ Pendiente |

---

## 4. Recomendaciones específicas

### 4.1. Placeholders en Anexo IV

**CTAEX** debe proporcionar 3 nombres (Laboratorio, Calidad, IoT) + cargos + emails. Ejemplo:

| Nombre | Cargo | Email | Acceso a |
|--------|-------|-------|----------|
| María López | Jefa de Laboratorio | maria.lopez@ctaex.es | LIMS, datos de cultivos. |
| Carlos García | Responsable Calidad | carlos.garcia@ctaex.es | Certificaciones AEMPS/GlobalGAP. |
| Ana Martínez | Jefa de IoT | ana.martinez@ctaex.es | Sensores, alertas ambientales. |

**CASTÚO** debe completar 3 nombres (CEO, Backend, IoT) + cargos + emails. Ejemplo:

| Nombre | Cargo | Email | Acceso a |
|--------|-------|-------|----------|
| Gregorio Jiménez Bodes | CEO | gregorio@castuo.system | Todos los módulos. |
| Luis Rodríguez | Backend Engineer | luis.rodriguez@castuo.system | APIs, integración LIMS/ERP. |
| Sofía Fernández | IoT Specialist | sofia.fernandez@castuo.system | Sensores, datos ambientales. |

### 4.2. Revisión legal — puntos críticos

- **Equity (2%):** Comprobar que no vulnere la Ley de Sociedades de Capital (límites a emisión de acciones). Opción de compra €500K en año 5: verificar con proyecciones de CTAEX.
- **Fondo de I+D:** Confirmar que el 10% (máx. €50K/año) cumple Ley 38/2003 (destino I+D+i). Auditoría externa: asegurar acceso del auditor a registros del Fondo.
- **Confidencialidad:** Revisar que las penalizaciones (€50K/€20K/€10K) sean proporcionales (Código Civil, Art. 1101).

### 4.3. Pruebas de contingencia — pasos concretos

**Simular fallo en PostgreSQL:**

```bash
# Detener PostgreSQL
docker-compose stop postgres

# Ejecutar rollback
chmod +x scripts/rollback_to_memory.sh
./scripts/rollback_to_memory.sh

# Verificar endpoints críticos
curl -X GET "http://localhost:8000/pro-accounts/test_account/cannabis/batches" -H "Authorization: Bearer <token>"
```

**Simular caída de GaiaChain:** Configurar respuestas 500; verificar que las transacciones se guardan en cola local (Redis) y se sincronizan al restaurar.

**Prueba de carga / DDoS (Locust):**

```bash
locust -f tests/load_test_locust.py --headless -u 1000 -r 100 -t 60s --host=http://localhost:8000
```

Comprobar mitigación (Cloudflare) y que el sistema sigue operativo.

---

## 5. Resumen de beneficios

### 5.1. Para CASTÚO-SYSTEM

| Aspecto | Beneficio |
|---------|-----------|
| Ingresos recurrentes | €53,7K–€1,84M/año (licencia + royalty + equity). |
| Equity | €100K iniciales → €1M en 5 años (sin inversión adicional). |
| Protección legal | Exclusividad, confidencialidad y propiedad intelectual. |
| Innovación | €50K/año para I+D (nuevos módulos, patentes). |
| Exclusividad | Protección frente a competidores en UE/Latinoamérica. |
| Casos de éxito | CTAEX como cliente referencia para otras cooperativas. |

### 5.2. Para CTAEX

| Aspecto | Beneficio |
|---------|-----------|
| Ahorro en certificaciones | ~90% de reducción (ej.: de €120K a €12K/año para 50 ha). |
| Trazabilidad blockchain | +30% en precio de venta (productos premium certificados). |
| Cumplimiento normativo | Reducción de riesgo de multas (GDPR, AI Act UE, RD 903/2025). |
| Innovación | €50K/año para nuevos módulos (ej.: IA predictiva). |
| Equity sin coste | 2% de participación sin desembolso inicial. |
| Exclusividad | Ventaja competitiva en UE/Latinoamérica. |

### 5.3. Frase clave para cerrar el acuerdo

*"Este acuerdo win-win permite a CTAEX obtener €740K/año de beneficio neto con 50 ha (ROI del 730%) y exclusividad competitiva en UE/Latinoamérica, mientras CASTÚO-SYSTEM recibe ingresos escalables (€50K–€1,84M/año) y participación en el crecimiento de CTAEX (2% equity, valorado en €1M en 5 años). El modelo combina:*

- *Licencia base (€50K–€100K/año) para cubrir costes de mantenimiento.*
- *Royalty escalonado (0,5%–1%) que crece con el éxito de CTAEX.*
- *Equity estratégico (2%) para alinear intereses a largo plazo.*
- *Fondo de I+D (€50K/año) para innovación continua sin coste para CTAEX.*
- *Exclusividad territorial que protege a ambas partes de la competencia.*
- *Trazabilidad y auditoría para garantizar el uso correcto de los fondos."*

---

## 6. Plantilla de email para solicitar datos del Anexo IV

**Asunto:** Acuerdo CTAEX–CASTÚO-SYSTEM — Lista de personal autorizado (Anexo IV)

---

Estimado/a [Nombre del Responsable de RRHH o Legal de CTAEX],

Espero que este mensaje le encuentre bien.

En el marco del **Acuerdo de Colaboración Estratégica entre CTAEX y CASTÚO-SYSTEM**, y conforme a lo establecido en el **Anexo IV – Lista de Personal Autorizado**, necesitamos completar la lista de **personal de CTAEX que tendrá acceso al sistema CASTÚO-SYSTEM** para garantizar la **seguridad, confidencialidad y trazabilidad** de los datos.

**Solicitamos que nos facilitéis los siguientes datos** para **3 miembros de vuestro equipo** (uno por cada área crítica):

1. **Responsable de Laboratorio (LIMS)**
   - Nombre completo:
   - Cargo:
   - Email corporativo:
   - Ámbito de acceso: Datos de LIMS (resultados de análisis de THC/CBD, pesticidas, metales pesados).

2. **Responsable de Calidad (Certificaciones)**
   - Nombre completo:
   - Cargo:
   - Email corporativo:
   - Ámbito de acceso: Certificaciones AEMPS/GlobalGAP, informes de cumplimiento normativo.

3. **Responsable de IoT (Sensores)**
   - Nombre completo:
   - Cargo:
   - Email corporativo:
   - Ámbito de acceso: Datos de sensores (temperatura, humedad, pH, EC), alertas ambientales.

**Plazo:** Para agilizar el proceso, os agradeceríamos recibir esta información **antes del [fecha, ej.: 30 de noviembre de 2026]**, de modo que podamos:

- Finalizar la redacción del **Anexo IV**.
- Enviar los **acuerdos individuales de confidencialidad (NDA)** a cada miembro del equipo.
- Configurar los **permisos de acceso** en el sistema antes del lanzamiento oficial.

**Adjunto** encontraréis el borrador actual del **Anexo IV**, donde podréis ver el formato y los datos que necesitamos completar. Una vez recibamos vuestra información, actualizaremos el documento y os lo reenviaremos para su **revisión y firma**.

**Procedimiento para añadir o eliminar personal en el futuro:**

1. **Solicitud:** CTAEX enviará un email a gregorio@castuo.system con 15 días de antelación.
2. **Aprobación:** Ambas partes aprobarán por escrito (email) el cambio.
3. **Actualización:** Modificaremos el Anexo IV y notificaremos a ambas partes.

Quedamos a vuestra disposición para cualquier aclaración o ajuste necesario. Podemos coordinar una breve llamada si lo consideráis oportuno.

Recibid un cordial saludo,

**Gregorio Jiménez Bodes**  
CEO, CASTÚO-SYSTEM  
gregorio@castuo.system | +34 XXX XXX XXX

---

*Notas: Tono formal y colaborativo; destacar plazo y transparencia (adjuntar borrador Anexo IV). Incluir procedimiento futuro para evitar dudas.*

---

## 7. Plantilla de email para envío de documentos finales

**Asunto:** Documentación final para firma: Acuerdo CTAEX–CASTÚO-SYSTEM

**Destinatarios:**

- **Para:** [Nombre del Responsable Legal de CTAEX], [Nombre del CEO de CTAEX]
- **CC:** [Nombre del Responsable de RRHH de CTAEX], [Nombre del Responsable Técnico de CTAEX]
- **De:** Gregorio Jiménez Bodes \<gregorio@castuo.system\>

**Cuerpo del email:**

---

Estimado/a [Nombre del Responsable Legal de CTAEX],

Adjunto encontrará la **documentación final** del **Acuerdo de Colaboración Estratégica entre CTAEX y CASTÚO-SYSTEM**, lista para su revisión y firma. Los documentos incluyen:

**1. Acuerdo Principal** (`CTAEX-CASTUO-AGREEMENT-SUMMARY.md`):
- Resumen ejecutivo del modelo de colaboración (licencias, royalties, equity, anexos).
- **Estado:** Versión final, pendiente de firma.

**2. Anexos legales** (`docs/legal/`):
- **Anexo I:** Fondo de I+D (10% royalties, Comité Mixto).
- **Anexo II:** Protocolo de Integración Técnica (LIMS, ERP, IoT).
- **Anexo III:** Confidencialidad y Protección de Datos.
- **Anexo IV:** Lista de Personal Autorizado (**pendiente de completar** con los 3 nombres de CTAEX).
- **Anexo V:** Seguridad y Cumplimiento Normativo (GDPR, ISO 27001, RD 903/2025).
- **Anexo VI:** Plan de Contingencia y Recuperación.
- **Anexo VII:** Métricas de Éxito y KPIs.

**3. Guías de implementación:**
- `CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md`: Checklist final para lanzamiento.
- `CTAEX-CASTUO-SIGNING-PRESENTATION-OUTLINE.md`: Esquema para la presentación ejecutiva.

---

### Próximos pasos

1. **Revisión legal final:** Solicitamos que vuestro equipo legal revise los documentos **antes del [fecha, ej.: 5 de diciembre de 2026]**.

2. **Completar Anexo IV:** Necesitamos los **3 nombres del personal autorizado de CTAEX** (1 LIMS, 1 Calidad, 1 IoT) para completar el Anexo IV. Podéis responder a este email con los datos o rellenar directamente el documento adjunto.

3. **Firma y notarización:** Proponemos firmar el acuerdo en la **reunión del [fecha, ej.: 15 de diciembre de 2026]** en vuestras oficinas. Opcional: Notarización en Cáceres (nosotros gestionamos la cita).

4. **Pruebas técnicas finales:** Nuestro equipo de DevOps coordinará con vuestro equipo técnico para realizar las **pruebas de contingencia** y **validar la integración con LIMS/ERP** la semana del [fecha].

---

### Documentos adjuntos

- 📄 CTAEX-CASTUO-AGREEMENT-SUMMARY.md
- 📁 Anexos I–VII (carpeta legal/)
- 📋 CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md
- 🎤 CTAEX-CASTUO-SIGNING-PRESENTATION-OUTLINE.md

---

### Disponibilidad para reunión

Estamos disponibles para una **videollamada o reunión presencial** para resolver cualquier duda antes de la firma. Proponemos los siguientes horarios:

- [Fecha 1]: [Hora 1] – [Hora 2]
- [Fecha 2]: [Hora 1] – [Hora 2]

---

Quedamos a vuestra disposición para cualquier aclaración adicional. Esperamos poder cerrar este acuerdo que, estamos seguros, será **beneficioso para ambas partes** y marcará un hito en la **agricultura 4.0 con trazabilidad y ética**.

Recibid un cordial saludo,

**Gregorio Jiménez Bodes**  
CEO, CASTÚO-SYSTEM  
📧 gregorio@castuo.system | 📞 +34 XXX XXX XXX

---

## 8. Recomendaciones finales

### 8.1. Para la reunión de firma

- Llevar **copias impresas** del Acuerdo Principal y Anexos I–VII (por si hay ajustes de última hora).
- Preparar una **versión digital (PDF)** para firma electrónica (ej.: DocuSign).

### 8.2. Post-firma

- Enviar **copias firmadas** a ambas partes por email.
- **Archivar** una copia física en un lugar seguro (ej.: notaría).
- **Programar** la primera reunión del Comité Mixto en los **15 días** siguientes a la firma.

### 8.3. Comunicación interna y externa

- **CTAEX:** Comunicar el acuerdo internamente (ej.: email a empleados, nota en intranet).
- **CASTÚO-SYSTEM:** Publicar un comunicado de prensa (opcional) destacando la colaboración.
