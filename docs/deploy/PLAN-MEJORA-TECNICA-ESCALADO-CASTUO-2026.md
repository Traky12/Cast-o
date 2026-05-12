# Plan de mejora técnica y escalado — CASTÚO-System (2026)

*Implementación **práctica** de recomendaciones clave: balanceo, certificados, observabilidad, escalado y marco UE. Los **€**, SKUs y plazos legales son **orientativos** — validar con proveedor, DPO y asesoría. **No** sustituye contrato ni DPIA.*

**Relación:** [PRONTUARIO-MAESTRO-ESCALADO-CLIENTES-SABIONDA-UE-2026.md](./PRONTUARIO-MAESTRO-ESCALADO-CLIENTES-SABIONDA-UE-2026.md) (visión clientes + Sabionda + UE) · [PRONTUARIO-PLAN-FASES-ESTABILIZACION-20S-2026.md](./PRONTUARIO-PLAN-FASES-ESTABILIZACION-20S-2026.md) · [PLAN-MEJORA-INMEDIATA-CASTUO-2026.md](./PLAN-MEJORA-INMEDIATA-CASTUO-2026.md) · [PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md](./PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md) · [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md) · [POLITICA-ROTACION-CLAVES.md](./POLITICA-ROTACION-CLAVES.md) · [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) · [docs/monitoring/alerts.md](../monitoring/alerts.md)

---

## 1. Implementación técnica de mejoras

### 1.1. Balanceo de carga con HAProxy

```bash
# Debian/Ubuntu — verificar versión LTS del paquete
sudo apt install haproxy socat
```

**`/etc/haproxy/haproxy.cfg`** *(plantilla — ajustar IPs, puertos backend FastAPI p. ej. 8000, y rutas ACME)*:

```haproxy
frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/haproxy/certs/api.castuo-system.eu.pem alpn h2,http/1.1
    default_backend http_back

backend http_back
    balance roundrobin
    option httpchk GET /health
    server node1 192.168.1.10:8000 check
    server node2 192.168.1.11:8000 check
    server node3 192.168.1.12:8000 check
```

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
sudo systemctl restart haproxy
```

**Estadísticas** *(ruta del socket según distro; habilitar `stats socket` en `global`)*:

```bash
echo "show stat" | sudo socat stdio /run/haproxy/admin.sock
```

*TLS: concatenar cadena + clave solo con permisos estrictos (`root:haproxy`, `640`); preferir **`crt-list`** y ficheros separados según documentación HAProxy 2.x.*

---

### 1.2. Automatización de rotación de certificados *(ej. ACME)*

```bash
#!/usr/bin/env bash
set -euo pipefail
DOMAIN="${CERT_DOMAIN:-api.castuo-system.eu}"
EMAIL="${CERTBOT_EMAIL:-admin@example.com}"
WEBROOT="${CERTBOT_WEBROOT:-/var/www/certbot}"
PEM_OUT="/etc/haproxy/certs/${DOMAIN}.pem"

sudo certbot certonly --webroot -w "$WEBROOT" -d "$DOMAIN" \
  --email "$EMAIL" --agree-tos --non-interactive --keep-until-expiring

sudo install -m 640 -o root -g haproxy /dev/null "$PEM_OUT"
sudo bash -c "cat /etc/letsencrypt/live/${DOMAIN}/fullchain.pem /etc/letsencrypt/live/${DOMAIN}/privkey.pem > '${PEM_OUT}'"
sudo systemctl reload haproxy
```

**Cron** *(ruta del script en `/usr/local/bin/renew_certs.sh` con `chmod 750`)*:

```cron
0 3 * * * root /usr/local/bin/renew_certs.sh >> /var/log/certbot-renew.log 2>&1
```

*Alineación:* [POLITICA-ROTACION-CLAVES.md](./POLITICA-ROTACION-CLAVES.md)

---

### 1.3. Alertas en tiempo real *(Prometheus + Alertmanager)*

Los nombres de paquetes y rutas dependen del SO y del método de instalación *(apt, docker, k8s)*.

**`alertmanager.yml`** *(ejemplo — sustituir webhook por canal interno; **no** versionar URL real en git)*:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h
  receiver: 'default'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alertas-castuo'
        api_url: 'https://hooks.slack.com/services/REEMPLAZAR'
```

**Regla ejemplo** `alert.rules`:

```yaml
groups:
  - name: castuo-alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU alto en {{ $labels.instance }}"
```

```bash
sudo systemctl restart prometheus || true
sudo systemctl restart alertmanager || true
```

*Métricas aplicación Castúo (lab): `castuo_neuro_hydro_infer_seconds` — ver robotics README.*

---

## 2. Plan de escalabilidad

### 2.1. Nodos y balanceo

| Acción | Plazo orientativo | Recursos |
|--------|-------------------|----------|
| Añadir 2 nodos backend adicionales | ~2 semanas | Infra **cotizar** *(ej. ilustrativo 2× VPS — **no** fijar €500/mes en contrato vía git)* |
| HAProxy / NLB frente a nodos | ~1 semana | Infra ~20 h |
| Redundancia de datos *(réplica DB, almacenamiento gestionado)* | ~1 semana | Infra + DBA ~15 h |

**DRBD / réplica en bloque** *(opcional, complejo — solo con equipo experimentado):*

```text
# Patrón ilustrativo; no copiar sin diseño de split-brain y STONITH.
# Preferir en muchos casos: PostgreSQL streaming replica + backups objeto.
```

*DRBD requiere red dedicada, quorum y procedimientos operativos; el repositorio Castúo **no** incluye playbooks DRBD listos.*

---

### 2.2. Infraestructura base

| Acción | Plazo | Notas |
|--------|-------|--------|
| PostgreSQL 14+ | ~1 semana | Migración planificada; pruebas de extensión `pgcrypto` si aplica |
| Redis Cluster | ~1 semana | ≥6 nodos típico con réplicas; **TLS y ACL** en prod; ajustar a caché SNN si usáis Redis |
| Almacenamiento objeto *(Ceph/S3)* | ~1 semana | Optimización = política de ciclo de vida + versionado — **cotizar** con proveedor |

```bash
# Redis Cluster — laboratorio; sustituir IPs y añadir --tls si política lo exige
redis-cli --cluster create \
  192.168.1.10:6379 192.168.1.11:6379 192.168.1.12:6379 \
  192.168.1.13:6379 192.168.1.14:6379 192.168.1.15:6379 \
  --cluster-replicas 1
```

---

## 3. Estrategia de mercado y marco UE *(orientación)*

### 3.1. Cumplimiento normativo

| Normativa | Acción *(alto nivel)* | Nota |
|-----------|----------------------|------|
| **RGPD** | Auditoría tratamientos, DPIA, encargados | [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md); DPO |
| **AI Act** | Clasificación del sistema, documentación, registros **según texto aplicable y asesoría** | No afirmar “registro completado” en git sin acta legal |
| **PAC / suelo** | Alineación SIGPAC / usos del suelo con agrónomo | Código actual: validadores y stubs — ver evaluación técnica |

*Horas legales/agrónomo: **cotizar** con despacho y CTAEX.*

### 3.2. Casos de uso *(producto — fuera del alcance mínimo del repo)*

| Sector | Implementación | Comentario |
|--------|----------------|------------|
| Agricultura ecológica | Trazabilidad ampliada | Corcho/CIS y módulos existentes como base |
| Cooperativas | Multi-tenant / roles | Requiere diseño IAM y datos |
| Subvenciones / PAC | Flujos con evidencia SIGPAC | Integración API regional o manual auditado |

---

## 4. Recomendaciones finales

### 4.1. Acción inmediata *(~1 semana cada ítem)*

1. Balanceo HAProxy + healthchecks reales.  
2. Renovación ACME + reload documentado.  
3. Alertmanager + reglas mínimas (CPU, 5xx, cert expiry).

### 4.2. Escalado *(~3 meses — orientativo)*

- Nodos + redundancia datos.  
- PostgreSQL/Redis alineados a carga medida.  
- Optimización tras **baseline** Locust/Prometheus.

### 4.3. Mercado UE *(~6 meses — orientativo)*

- Cierre brechas legales con asesoría.  
- Casos de uso priorizados por ingreso/impacto hídrico-territorial.  
- Comercialización fuera del alcance de este documento técnico.

---

*Escalar sin medir es regar con caudal desconocido: primero el caudalímetro, luego la tubería.*

🚜 *Pa'lante, campeón.* 🌱
