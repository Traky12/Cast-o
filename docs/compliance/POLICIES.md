# Políticas de cumplimiento — CASTÚO-SYSTEM™ v2.0

## 1. Políticas de seguridad

### 1.1. Rotación de claves

- **Frecuencia:** Cada 30 días (configurable con cron y `backend/scripts/rotate_pqc_keys.py`).
- **Algoritmos:** Kyber-1024 (KEM), Dilithium-5 (firmas).
- **Registro:** Eventos de rotación registrados (Vault y/o GaiaChain); notificación a agentes vía message_bus.

### 1.2. Cifrado de datos

| Tipo de dato       | Algoritmo               | Rotación    | Normativa           |
|--------------------|-------------------------|------------|---------------------|
| Datos de usuarios  | AES-256-GCM + Kyber-1024| Cada 30 días | GDPR Art.32         |
| Transacciones      | Kyber-1024 + AES-256-GCM| Cada 90 días | eIDAS, ISO 27001    |
| Logs de auditoría  | Blake3 + Kyber-1024     | Inmutables | ISO 27001:A.12.4.1  |
| Modelos de IA      | AES-256-GCM             | Por versión| EU AI Act Anexo IV  |

---

## 2. Cumplimiento normativo

### 2.1. ISO 27001:2022

- **A.12.4.1:** Monitoreo de eventos (Prometheus + Alertmanager).
- **A.12.6.1:** Gestión de incidentes (SelfHealingAgent + OPA).
- **A.16.1.1:** Registro de eventos (GaiaChain, scripts de registro).

### 2.2. GDPR

- **Art. 25:** Protección por diseño (cifrado PQC, pseudonimización).
- **Art. 30:** Registro de actividades (GaiaChain, logs).
- **Art. 32:** Seguridad del tratamiento (rotación de claves, cifrado).
- **Art. 17:** Derecho al olvido (`KnowledgeBase.forget()`).

### 2.3. EU AI Act (2024/1689)

- **Anexo III:** Sistemas de IA de alto riesgo (registro en ModelRegistry).
- **Art. 13:** Transparencia (metadatos de cumplimiento en modelos).
- **Anexo IV:** Evaluación de conformidad (validación con OPA y hash de integridad).

### 2.4. NIS2

- **Art. 21:** Gestión de riesgos.
- **Art. 23:** Gestión de incidentes y continuidad (alertas y auto-reparación).

---

## 3. Procedimientos de auditoría

### 3.1. Auditoría de modelos de IA

- **Frecuencia:** Trimestral.
- **Herramientas:** ModelRegistry, OPA, scripts de auditoría si existen.
- **Salida:** Informe con modelos, score de cumplimiento y acciones correctivas.

### 3.2. Auditoría de seguridad

- **Frecuencia:** Mensual.
- **Herramientas:** Scripts de escaneo, OPA para configuraciones.
- **Salida:** Informe de vulnerabilidades, riesgo y normativas afectadas.

---

## 4. Matriz de riesgos y controles

| Riesgo                 | Impacto | Probabilidad | Control mitigante              | Normativa        |
|------------------------|---------|--------------|---------------------------------|------------------|
| Compromiso de claves PQC | Alto  | Bajo         | Rotación automática + Vault    | ISO 27001:A.10.1.1 |
| Ataque a Federated Learning | Alto | Medio        | Hash + detección de outliers   | EU AI Act Anexo IV |
| Incumplimiento normativo | Alto  | Medio        | OPA + GaiaChain                | GDPR Art.30      |
| Fallo en auto-reparación | Medio | Medio        | Validación OPA antes de actuar | ISO 27001:A.16.1.1 |
| Pérdida de datos       | Alto    | Bajo         | Backups inmutables / GaiaChain  | ISO 27001:A.12.3.1 |

---

## 5. Respuesta a incidentes

### 5.1. Clasificación

| Tipo de incidente       | Severidad | Tiempo de respuesta | Equipo     |
|-------------------------|-----------|----------------------|------------|
| Compromiso de claves PQC | Crítico | Inmediato            | Seguridad  |
| Ataque a modelo de IA   | Alto      | 1 hora               | IA + Seguridad |
| Incumplimiento normativo| Alto      | 4 horas              | Cumplimiento |
| Fallo en servicio crítico | Medio   | 1 día                | DevOps     |

### 5.2. Escalamiento

1. **Detectar:** Prometheus/Alertmanager o informe manual.
2. **Clasificar:** Matriz de riesgos (sección 4).
3. **Activar protocolo:** Crítico → reunión seguridad; Alto → notificación en 1 h; Medio → registro en backlog.
4. **Resolver:** Acciones correctivas (validadas por OPA cuando aplique).
5. **Documentar:** Registro en GaiaChain (descripción, acciones, normativas, firma).

### 5.3. Comunicación

- **Interno:** Canal de incidentes (ej. Slack #incidents-castuo) y correo a responsables.
- **Externo:** Según requisitos legales (ej. notificación AEPD 72 h para brechas GDPR).
