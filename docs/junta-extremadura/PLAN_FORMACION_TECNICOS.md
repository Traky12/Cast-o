# Plan de Formación Detallado para Técnicos de la Junta de Extremadura

Documento operativo para capacitar a 50 técnicos en el uso del sistema ForestOwnershipToken (cronograma, materiales y métricas de éxito).

---

## 📅 1. Cronograma de Formación (3 meses)

| Fase | Duración | Objetivos | Responsables |
|------|----------|-----------|--------------|
| **Fase 1: Preparación** | 2 semanas | Configurar entorno de prueba. Crear materiales. Seleccionar 10 parcelas piloto. | Equipo CASTÚO + Junta |
| **Fase 2: Talleres presenciales** | 4 semanas | 5 talleres (2 h cada uno). 10 técnicos por taller. | Formadores CASTÚO |
| **Fase 3: Prácticas** | 4 semanas | Mintado de 100 tokens. Reclamación de subvenciones. Simulación de talas. | Técnicos + Tutores |
| **Fase 4: Evaluación** | 2 semanas | Examen práctico. Encuesta de satisfacción. Informe de mejoras. | Equipo CASTÚO + Junta |

---

## 🎓 2. Materiales de Formación

### 2.1. Guías técnicas

| Documento | Contenido | Ubicación |
|-----------|-----------|-----------|
| **Guía Rápida de Mintado** | Pasos para tokenizar una parcela (con capturas de pantalla). | [docs/guias/guia_mintado.md](../guias/guia_mintado.md) |
| **Manual de Subvenciones** | Cómo calcular y reclamar subvenciones (PAC 2040, Decreto 45/2020). | [docs/guias/manual_subvenciones.md](../guias/manual_subvenciones.md) |
| **Protocolo de Tala Legal** | Flujos para actualizar CO₂ tras talas (Orden 15/03/2021). | [docs/guias/protocolo_talas.md](../guias/protocolo_talas.md) |
| **FAQ Técnico** | Solución a 20 problemas comunes (errores de transacción, SIGPAC, etc.). | [docs/guias/faq_tecnico.md](../guias/faq_tecnico.md) |

*Las versiones PDF se generan desde estos Markdown para distribución oficial.*

### 2.2. Videos tutoriales

| Video | Duración | Descripción |
|-------|----------|-------------|
| Mintado de una parcela | 15 min | Flujo completo con certificaciones PEFC/FSC. |
| Reclamación de subvenciones | 10 min | Uso de `calculate_subsidies_forest.py` y dashboard. |
| Actualización tras tala | 12 min | `update_carbon_after_cutting.py` y normativa. |
| Verificación con SIGPAC | 8 min | Validación de parcelas antes del mintado. |

*Enlaces YouTube/plataforma interna: por definir según acuerdos con la Junta.*

### 2.3. Entorno de prueba

- **Testnet GaiaChain:** `https://testnet.gaiachain.castuo-system.com`
- **Dashboard de prueba:** `https://dashboard-test.castuo-system.com`

Credenciales de prueba (cambiar en producción):

- Usuario: `tecnico@juntaextremadura.es`
- Contraseña: *(gestionada por la Junta; no almacenar en repo)*

---

## 👨‍🏫 3. Talleres presenciales (5 sesiones)

### 3.1. Taller 1: Introducción al sistema

- **Duración:** 2 horas  
- **Objetivos:** Entender el modelo de tokenización de propiedades forestales. Conocer la arquitectura legal y técnica (GaiaChain, SIGPAC, BRIF).  
- **Contenido:** Presentación del proyecto (30 min). Demo en vivo: mintado de una parcela (30 min). Preguntas y respuestas (1 h).  
- **Materiales:** [docs/talleres/taller1_introduccion.md](../talleres/taller1_introduccion.md), script de demo: `backend/scripts/demo_mintado.py`.

### 3.2. Taller 2: Mintado de propiedades

- **Duración:** 2 horas  
- **Objetivos:** Aprender a tokenizar parcelas con certificaciones (PEFC/FSC). Usar el dashboard de verificación.  
- **Contenido:** Teoría: ForestOwnershipToken.sol (30 min). Práctica: mintar 2 parcelas por técnico (1 h). Verificación con SIGPAC (30 min).  
- **Ejercicio práctico:**

```bash
# 1. Mintar una parcela con certificaciones
python3 backend/scripts/mint_forest_property.py \
  0xTecnico1 XT-99999-001 "39.4769°N, 6.3706°W" 10000 \
  "Quercus ilex,Pinus pinea" 5000 false "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco" \
  -c PEFC FSC

# 2. Verificar en el dashboard
# https://dashboard-test.castuo-system.com/?token_id=1
```

### 3.3. Taller 3: Subvenciones y créditos de carbono

- **Duración:** 2 horas  
- **Objetivos:** Calcular subvenciones automáticas (PAC 2040 + Decreto 45/2020). Entender el vínculo con créditos de carbono (Reglamento UE 2018/841).  
- **Contenido:** Teoría: cálculo de subvenciones (30 min). Práctica: calcular subvenciones para 2 parcelas (1 h). Integración con CarbonCredit (30 min).  
- **Ejercicio práctico:**

```bash
# Calcular subvenciones para un token
python3 backend/scripts/calculate_subsidies_forest.py 1 -v
```

*Nota: La reclamación efectiva de subvenciones (claim_subsidy) y el mint de créditos de carbono dependen de los contratos SubsidyToken y CarbonCredit; en el taller se usa el cálculo on-chain y el dashboard.*

### 3.4. Taller 4: Talas legales y actualización de CO₂

- **Duración:** 2 horas  
- **Objetivos:** Actualizar CO₂ secuestrado tras talas (Orden 15/03/2021). Conocer la integración con BRIF para partes de incendio.  
- **Contenido:** Teoría: normativa de talas (30 min). Práctica: simular tala de 10 m³ (1 h). Validación con BRIF (30 min).  
- **Ejercicio práctico:**

```bash
# Actualizar CO₂ tras tala de 10 m³
python3 backend/scripts/update_carbon_after_cutting.py 1 10
```

### 3.5. Taller 5: Resolución de problemas

- **Duración:** 2 horas  
- **Objetivos:** Solucionar errores comunes (transacciones fallidas, SIGPAC, IPFS). Usar el FAQ técnico.  
- **Contenido:** Casos prácticos (1 h): Invalid parcelaId (SIGPAC), Insufficient gas (GaiaChain), IPFS timeout. Uso del dashboard de soporte (1 h).

---

## 📊 4. Prácticas y evaluación

### 4.1. Prácticas obligatorias

| Práctica | Objetivo | Criterio de éxito |
|-----------|----------|-------------------|
| Mintar 5 parcelas con certificaciones | Dominar el proceso de tokenización. | 5 tokens minteados en GaiaChain. |
| Calcular/reclamar subvenciones para 3 parcelas | Usar el sistema de subvenciones. | 3 transacciones o cálculos documentados. |
| Actualizar CO₂ tras tala | Aplicar normativa de talas. | 1 actualización exitosa en GaiaChain. |
| Verificar 10 parcelas en SIGPAC | Validar datos con sistemas externos. | 10 verificaciones sin errores. |

### 4.2. Examen práctico final

- **Formato:** Prueba en entorno real con 3 ejercicios:  
  1. Mintar una parcela con certificaciones PEFC/FSC.  
  2. Calcular subvenciones y valor en €.  
  3. Simular una tala y actualizar el CO₂.  
- **Criterios de aprobación:** 100 % de precisión en los 3 ejercicios. Tiempo máximo: 1 hora.

---

## 📈 5. Métricas de éxito

| Métrica | Objetivo | Herramienta de medición |
|---------|----------|--------------------------|
| Tasa de aprobación | 100 % de técnicos | Plataforma de exámenes (p. ej. Moodle). |
| Tiempo por tarea | &lt;15 min por mintado | Cronómetro en dashboard / informes. |
| Errores en producción | &lt;1 % | Logs de GaiaChain + SIGPAC. |
| Satisfacción | &gt;90 % en encuestas | Formulario post-formación (p. ej. Typeform). |

---

## 📌 6. Acuerdo con SIGPAC para acceso a API

### 6.1. Borrador de acuerdo

**Asunto:** Acuerdo de colaboración para validación de parcelas forestales.

**Partes:**

- Junta de Extremadura (Dirección General de Medio Ambiente).
- CASTÚO-SYSTEM™ (representada por Gregorio Jiménez).

**Cláusulas clave:**

- **Acceso a API de SIGPAC:**  
  Endpoint: `https://sigpac.mapa.gob.es/api/parcela/{id}`. Límite: 10.000 requests/mes. Datos: certifications, area, protected_status.
- **Validación de parcelas:** CASTÚO enviará `parcelaId` antes de mintar un token. SIGPAC responderá con un JSON del tipo:

```json
{
  "valid": true,
  "certifications": ["PEFC", "FSC"],
  "area": 10000,
  "protected": false
}
```

- **Confidencialidad:** Datos usados solo para tokenización. Cumplimiento GDPR y Ley 3/2023 de Montes.
- **Duración:** 1 año prorrogable. Coste: €0 (acuerdo de colaboración pública).

**Firma:** Junta de Extremadura: _________________________ / CASTÚO-SYSTEM™: Gregorio Jiménez, _________________________

---

## 💻 7. Despliegue del dashboard en servidores de la Junta

### 7.1. Requisitos técnicos

| Componente | Especificación |
|------------|-----------------|
| Servidor | 2 CPU, 8 GB RAM, 100 GB SSD (mínimo). |
| Sistema operativo | Ubuntu 22.04 LTS. |
| Docker | Versión 20.10+. |
| Nginx | Versión 1.18+. |
| Acceso | HTTPS con certificado Let's Encrypt. |

### 7.2. Comando de despliegue

```bash
# 1. Clonar repositorio (o copiar build del frontend)
cd frontend/extremadura-dashboard
# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env: REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS, etc. (en build time)
# 3. Construir imagen Docker
docker build -t extremadura-dashboard:latest .
# 4. Desplegar con Docker Compose
docker-compose up -d
```

Configuración de referencia: [frontend/extremadura-dashboard/docker-compose.yml](../../frontend/extremadura-dashboard/docker-compose.yml). Variables de entorno: [.env.example](../../frontend/extremadura-dashboard/.env.example).

---

## 👨‍🌾 8. Plan piloto con 10 propietarios

### 8.1. Selección de propietarios

| Criterio | Detalle |
|----------|---------|
| Ubicación | Parcelas en Cáceres/Badajoz (50 % cada una). |
| Certificaciones | Al menos 2 con PEFC/FSC. |
| Tamaño | Entre 1 y 10 ha. |
| Disponibilidad | Compromiso de asistir a 2 talleres. |

Lista de ejemplo: [propietarios_piloto.csv](propietarios_piloto.csv).

### 8.2. Cronograma piloto

| Semana | Actividad | Responsable |
|--------|-----------|-------------|
| 1 | Reunión inicial con propietarios. | Equipo CASTÚO |
| 2 | Mintado de parcelas (1 por propietario). | Técnicos + Propietarios |
| 3 | Cálculo/reclamación de subvenciones. | Propietarios |
| 4 | Simulación de tala (1 parcela). | BRIF + Propietarios |
| 5 | Encuesta de satisfacción. | Junta de Extremadura |

### 8.3. Métricas de éxito piloto

| Métrica | Objetivo |
|---------|----------|
| Parcelas tokenizadas | 10/10 |
| Subvenciones calculadas/reclamadas | 10/10 |
| Talas simuladas | 1 sin errores |
| Tiempo medio por transacción | &lt;10 min |
| Satisfacción propietarios | &gt;90 % |

---

## 📌 9. Presupuesto y ROI

| Concepto | Coste (€) | Financiación |
|-----------|-----------|--------------|
| Formación (5 talleres) | 15.000 | Junta de Extremadura |
| Acuerdo SIGPAC | 0 | Colaboración pública |
| Despliegue dashboard | 5.000 | CASTÚO-SYSTEM™ |
| Soporte técnico (3 meses) | 10.000 | Junta de Extremadura |
| **Total** | **30.000** | |

**ROI estimado (100 ha):**

| Concepto | Ingresos (€/año) | Ahorros (€/año) |
|-----------|------------------|------------------|
| Subvenciones | 100.000 | — |
| Créditos de carbono | 50.000 | — |
| Reducción de fraudes | — | 50.000 |
| **Total** | **150.000** | **50.000** |
| **ROI** | **600 %** (sobre 30.000 € inversión) | |

---

## 🎯 10. Cita final para presentación

> *Este plan de formación garantiza que los técnicos de la Junta de Extremadura dominarán el sistema ForestOwnershipToken en 3 meses, con:*
>
> - *10 parcelas piloto tokenizadas (PEFC/FSC).*
> - *Subvenciones automáticas (hasta €800/ha/año).*
> - *Integración con SIGPAC y BRIF para validación en tiempo real.*
> - *ROI del 600 % en el primer año (30.000 € inversión → 150.000 € ingresos).*
>
> **Próximos pasos:** Firmar acuerdo con SIGPAC (borrador incluido). Desplegar dashboard en servidores de la Junta (guía incluida). Iniciar talleres con los primeros 10 propietarios piloto (lista adjunta).*

**Documentación adjunta:** Guías técnicas (4), talleres (5), scripts de despliegue (docker-compose), borrador de acuerdo SIGPAC, CSV de propietarios piloto.

---

[← ForestOwnershipToken](FOREST_OWNERSHIP_TOKEN.md) · [Gestión documental](GESTION_DOCUMENTAL.md)
