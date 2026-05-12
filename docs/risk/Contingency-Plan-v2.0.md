# PLAN DE CONTINGENCIA 2.0

**Versión**: 2.0  
**Fecha**: [DD/MM/2026]  
**Alineado con**: ISO 22301, GDPR, AI Act UE 2024/1689

---

## 1. OBJETIVO

Garantizar la **continuidad del negocio** ante fallos críticos, con:

- **RTO (Recovery Time Objective)**: &lt;4h para sistemas críticos.
- **RPO (Recovery Point Objective)**: &lt;1h (pérdida máxima de datos).
- **Equipos responsables**:
  - **DevOps**: Fallos técnicos (PostgreSQL, GaiaChain).
  - **Legal**: Incumplimientos normativos.
  - **Comercial**: Fallos en alianzas con distribuidores.

---

## 2. ESCENARIOS CRÍTICOS Y PROTOCOLOS

### 2.1. Fallo en PostgreSQL (Base de Datos)

**Impacto**: Pérdida de acceso a datos de lotes, certificaciones y usuarios.

**Protocolo**:

1. **Detección**:
   - Alertas en **Grafana** (consulta: `up{job="postgres"} == 0`).
   - Notificación automática a **Slack #alerts-criticas**.

2. **Acción Inmediata**:
   ```bash
   # 1. Intentar reinicio
   docker-compose restart postgres

   # 2. Si falla, activar modo degradado
   chmod +x scripts/rollback_to_memory.sh
   ./scripts/rollback_to_memory.sh
   ```

3. **Recuperación**:
   - Restaurar desde Backblaze B2 (últimos 7 días de backups).
   ```bash
   docker-compose exec postgres pg_restore -d sabionda_prod /backups/latest.dump
   ```

4. **Comunicación**:
   - Notificar a CTAEX vía email (plantilla predefinida).
   - Actualizar status page (ej: status.castuo.tech).

**Documentación**: Script de Rollback (`scripts/rollback_to_memory.sh`), Guía de Restauración PostgreSQL.

---

### 2.2. Caída de GaiaChain (Blockchain)

**Impacto**: Imposibilidad de registrar transacciones de trazabilidad.

**Protocolo**:

1. **Detección**:
   - Monitoreo de nodos con Prometheus (`gaia_chain_node_status`).
   - Alerta si &gt;5 min sin respuesta.

2. **Acción Inmediata**:
   - Activar **modo degradado**: Almacenar transacciones en Redis (cola `pending_blockchain_tx`).
   - El backend devuelve `status: "degraded"` y encola el lote para sincronización posterior.

3. **Recuperación**:
   - Sincronizar transacciones pendientes al restaurar GaiaChain (endpoint o tarea Celery `sync_pending_transactions`).

4. **Comunicación**:
   - Notificar a CTAEX que las certificaciones pueden retrasarse &lt;24h.

---

### 2.3. Incumplimiento de GDPR

**Impacto**: Multas de hasta €20M o 4% de la facturación global.

**Protocolo**:

1. **Detección**:
   - Auditorías automáticas (escaneos semanales).
   - Alertas si se detectan datos personales no enmascarados en logs.

2. **Acción Inmediata**:
   - Bloquear acceso al sistema afectado.
   - Notificar a la AEPD en &lt;72h (plantilla preaprobada).

3. **Recuperación**:
   - Eliminar datos afectados y generar informe de impacto.
   - Auditoría externa para validar la corrección.

4. **Comunicación**:
   - Comunicado público si afecta a &gt;100 usuarios (plantilla en Comunicados GDPR).

---

### 2.4. Fallo en Sensores IoT (Libelium)

**Impacto**: Pérdida de datos ambientales críticos (temperatura, humedad, pH).

**Protocolo**:

1. **Detección**:
   - Alertas en Grafana si no hay datos en &gt;15 min (`iot_sensor_last_data > 15m`).

2. **Acción Inmediata**:
   - Usar últimos datos válidos para mantener operatividad.
   - Notificar al equipo de CTAEX (email + SMS al responsable de IoT).

3. **Recuperación**:
   - Reemplazar sensor defectuoso en &lt;24h (CTAEX tiene stock de repuesto).
   - Recalibrar el nuevo sensor (ver `backend/services/calibration.py`).

4. **Comunicación**:
   - Actualizar dashboard de monitoreo con estado "degradado".

---

### 2.5. Ataque de Seguridad (Ciberataque)

**Impacto**: Robo de datos o interrupción del servicio.

**Protocolo**:

1. **Detección**:
   - SIEM (Wazuh) para detectar accesos no autorizados.
   - Alertas si hay &gt;100 solicitudes/segundo desde una IP.

2. **Acción Inmediata**:
   - Aislar sistemas afectados (script: `scripts/isolate_system.sh`).
   - Activar Cloudflare en modo "Under Attack".

3. **Recuperación**:
   - Restaurar desde backup &lt;1h (Backblaze B2).
   - Análisis forense con equipo externo (ej: S21sec).

4. **Comunicación**:
   - Notificar a clientes afectados en &lt;24h (plantilla en Incident Communication).

---

## 3. EQUIPOS Y RECURSOS

| Equipo | Responsable | Recursos |
|--------|-------------|----------|
| DevOps | CTO CASTÚO | Servidores de backup (Hetzner), scripts de recuperación, acceso a Backblaze B2 |
| Legal | Abogado CASTÚO | Plantillas para notificaciones a AEPD, contratos con auditores externos |
| Comercial | Director Comercial | Plantillas de comunicación para clientes, lista de contactos de emergencia |
| Técnico (CTAEX) | Jefe de I+D CTAEX | Stock de sensores de repuesto, acceso a datos históricos de LIMS |

---

## 4. PRUEBAS Y MANTENIMIENTO

| Prueba | Frecuencia | Responsable |
|--------|------------|-------------|
| Simulación de fallo PostgreSQL | Trimestral | DevOps |
| Caída de GaiaChain | Semestral | Blockchain Team |
| Incumplimiento GDPR | Anual | Legal Team |
| Ataque de seguridad | Anual | Seguridad |

**Mantenimiento**: Revisar el plan cada 6 meses (junio y diciembre). Actualizar contactos de emergencia cada 3 meses.

---

## 5. DOCUMENTACIÓN DE APOYO

| Documento | Ubicación |
|------------|-----------|
| Script de Rollback a Memoria | `scripts/rollback_to_memory.sh` |
| Guía de Restauración de PostgreSQL | `docs/operations/PostgreSQL-Restore-Guide.md` |
| Plantillas de Comunicación GDPR | `docs/legal/GDPR-Communication-Templates/` |
| Procedimiento de Aislamiento | `scripts/isolate_system.sh` |
| Checklist de Recuperación | `docs/risk/Recovery-Checklist.md` |
