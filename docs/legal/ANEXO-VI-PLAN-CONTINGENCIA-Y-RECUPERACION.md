# ANEXO VI — PLAN DE CONTINGENCIA Y RECUPERACIÓN ANTE DESASTRES
**Acuerdo de Colaboración Estratégica CTAEX S.L. – CASTÚO-SYSTEM**

**Versión:** 1.0  
**Fecha:** [DD/MM/AAAA]  
**Referencia:** Acuerdo marco CTAEX – CASTÚO-SYSTEM.

---

## 1. Objetivo

Establecer procedimientos para **minimizar el impacto** de interrupciones en el Sistema, garantizando:

- **Tiempo de recuperación (RTO):** <4 h para servicios críticos.
- **Punto de recuperación (RPO):** <1 h (pérdida máxima de datos).

---

## 2. Escenarios críticos

| Escenario | Impacto | Protocolo |
|-----------|--------|-----------|
| **Fallo en PostgreSQL** | Pérdida de acceso a datos de lotes. | **Rollback a base de datos en memoria** (script: `rollback_to_memory.sh`). |
| **Caída de GaiaChain** | No se pueden registrar transacciones en blockchain. | **Modo degradado:** Registrar transacciones localmente y sincronizar al restaurar GaiaChain. |
| **Ataque DDoS** | Indisponibilidad del Sistema. | **Activar Cloudflare** + **escalar servidores**. |
| **Brecha de seguridad** | Acceso no autorizado a datos. | **Aislar sistemas afectados** + **notificar a AEPD en 72 h**. |
| **Fallo en sensores IoT** | Pérdida de datos ambientales. | **Usar últimos datos válidos** + **notificar al técnico de CTAEX**. |

---

## 3. Procedimientos de recuperación

### 3.1. Fallo en PostgreSQL

1. **Detectar el fallo:**
   - Monitoreo con **Prometheus/Grafana** (alerta si `postgres_up == 0`).
2. **Activar rollback:**
   ```bash
   # Ejecutar desde la raíz del proyecto
   chmod +x scripts/rollback_to_memory.sh
   ./scripts/rollback_to_memory.sh
   ```
3. **Verificar:** Comprobar que los endpoints críticos funcionan (ej.: GET /cannabis/batches).
4. **Notificar:** Enviar alerta a Slack/email del equipo técnico.

### 3.2. Caída de GaiaChain

- **Modo degradado:** Registrar transacciones en una cola local (Redis).
- **Sincronizar al restaurar:** Script para sincronizar transacciones pendientes con GaiaChain.
- **Notificar:** Alertar a EL CLIENTE sobre el retraso en certificaciones.

### 3.3. Ataque DDoS

- **Mitigación inicial:** Activar Cloudflare (modo "Under Attack"). Escalar servidores en Docker Swarm/Kubernetes.
- **Investigar:** Analizar logs con Grafana Loki.
- **Comunicar:** Notificar a EL CLIENTE sobre el incidente y tiempo estimado de recuperación.

---

## 4. Backups y restauración

| Componente | Frecuencia | Ubicación | RTO |
|------------|------------|-----------|-----|
| **PostgreSQL** | Diario | Backblaze B2 | <1 h |
| **Blockchain (GaiaChain)** | Cada transacción | Nodos locales + IPFS | <5 min |
| **Configuraciones** | Semanal | GitHub (privado) | <30 min |
| **Logs** | Diario | Grafana Loki | <1 h |

**Procedimiento de restauración (PostgreSQL):**

```bash
# Restaurar PostgreSQL desde Backblaze
docker-compose exec postgres pg_restore -d sabionda_prod /backups/latest.dump

# Verificar integridad
psql -c "SELECT COUNT(*) FROM cannabis.cannabis_batches;"
```

---

## 5. Pruebas de contingencia

| Prueba | Frecuencia | Responsable |
|--------|------------|-------------|
| Simulación de fallo en PostgreSQL | Trimestral | DevOps |
| Caída de GaiaChain | Semestral | Blockchain Team |
| Ataque DDoS | Anual | Seguridad |
| Restauración de backups | Mensual | DevOps |

---

## 6. Responsabilidades

| Parte | Responsabilidad |
|-------|-----------------|
| **EL PROVEEDOR** | Mantener el Plan de Contingencia actualizado. Realizar pruebas periódicas. |
| **EL CLIENTE** | Notificar cualquier incidente en <1 h. Proporcionar acceso a logs si es necesario. |

---

## 7. Aceptación

Las partes aceptan este Anexo como **parte integrante** del Acuerdo Principal.
