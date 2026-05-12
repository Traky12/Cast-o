# Prontuario maestro — sistema reforzado, seguro y evolutivo CASTÚO-System (2026)

*Blueprint de arquitectura objetivo para 2026: integra seguridad avanzada, cifrado, backup verificado, observabilidad y evolución hacia Sabionda AI. Las recetas son **plantillas**; “implementado” se considera solo cuando hay evidencia (ticket/PR/captura/informe) en el territorio. No sustituye DPIA ni revisión criptográfica.*

**Relación:** [PRONTUARIO-MAESTRO-EVALUACION-TECNICA-CASTUO-2026.md](./PRONTUARIO-MAESTRO-EVALUACION-TECNICA-CASTUO-2026.md) · [PRONTUARIO-MAESTRO-REFUERZO-INTEGRAL-2026.md](./PRONTUARIO-MAESTRO-REFUERZO-INTEGRAL-2026.md) · [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · [docs/monitoring/alerts.md](../monitoring/alerts.md) · [Sabionda-Educational-System.md](../sabionda/Sabionda-Educational-System.md)

---

## 1. Arquitectura objetivo 2026

```mermaid
graph TD
    A[Clientes / Edge] -->|TLS 1.3| B[Load Balancer (HAProxy/NLB)]
    B -->|OIDC/OAuth2 (según despliegue)| C[Microservicios Castúo]
    C -->|Caché opcional| D[Redis Cluster]
    C -->|Datos| E[PostgreSQL]
    E -->|Persistencia y copias| F[Ceph / S3 compatible]
    F -->|Backup cifrado| G[Pen drive / Air-gap + restauración verificada]
```

*Clave: Redis es caché (si se despliega). `pgcrypto` cifra en PostgreSQL; Ceph/S3 cifran según política del volumen/objeto. El lab SNN es simulación y se documenta en su prontuario.*

---

## 2. Borde seguro: HAProxy (plantilla 2.x)

### 2.1 Encabezados de seguridad (no “magic”, sino plantilla)

Recomendación: ajustar `CSP` al frontend real. `default-src 'self'` puede romper recursos externos si existen.

```haproxy
frontend https_front
    bind *:443 ssl crt /etc/haproxy/certs/haproxy.pem
    option httpchk GET /health

    http-request set-header X-Forwarded-Proto https if { ssl_fc }
    default_backend app_backend

backend app_backend
    balance leastconn
    option httpchk GET /health
    server node1 192.168.1.10:8000 check
    server node2 192.168.1.11:8000 check
    server node3 192.168.1.12:8000 check

    # Seguridad en respuestas (plantilla)
    http-response set-header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    http-response set-header X-Frame-Options "DENY"
    http-response set-header X-Content-Type-Options "nosniff"
    http-response set-header Content-Security-Policy "default-src 'self'"

    http-request set-header X-Client-IP %[src]
    http-request set-header X-Forwarded-For %[src]
```

**Validación** (plantilla):

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
sudo systemctl reload haproxy
```

*Guía completa de escalado con HAProxy/ACME y alertas: [PLAN-MEJORA-TECNICA-ESCALADO-CASTUO-2026.md](./PLAN-MEJORA-TECNICA-ESCALADO-CASTUO-2026.md).*

---

## 3. Cifrado integral por capas

### 3.1 En tránsito (TLS / VPN)

Fuente canónica: [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md) y [CHECKLIST-CIFRADO-TOTAL.md](./CHECKLIST-CIFRADO-TOTAL.md).

Regla de oro: no “prometer PQ híbrido” sin probarlo en staging; TLS estándar primero, PQ solo cuando el stack lo soporta de forma verificable.

---

### 3.2 En reposo (LUKS / cifrado de volumen)

**LUKS**: aplica cifrado a volúmenes del host o a volúmenes gestionados por proveedor (según soberanía acordada). Cualquier receta con `/dev/sdX` es de **alto riesgo**: usar siempre rutas correctas y backup de arranque.

Ejemplo conceptual (alto nivel):

```bash
sudo cryptsetup luksFormat --type luks2 /dev/sdX
sudo cryptsetup open /dev/sdX pen_castuo
sudo mkfs.ext4 /dev/mapper/pen_castuo
sudo mount /dev/mapper/pen_castuo /mnt/secure_data
```

Para detalle canónico de backups y air-gap: ver [PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md).

---

### 3.3 Cifrado en PostgreSQL (`pgcrypto`) — sin claves hardcodeadas

En el repo el patrón recomendado es `pgcrypto` como cifrado **aplicativo** (en tablas/columnas o blobs), con clave gestionada desde Vault/KMS y aplicada por sesión (p. ej. `SET LOCAL` desde app).

Plantilla segura (didáctica):

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION secure_encrypt(data TEXT) RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, current_setting('app.encryption_key', true));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

Notas de gobierno:

1. `SECURITY DEFINER` requiere análisis de permisos (owner, `search_path`, `EXECUTE`).  
2. Para TLS y secretos: ver [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md).

---

### 3.4 Backup cifrado verificado (incluye pen drive)

En este repo se evita un error frecuente: **no** usar `gpg --verify` como prueba de integridad para cifrado simétrico.

La verificación canónica es:
- manifiesto SHA256 por lote, y/o
- prueba de descifrado a `stdout`/`/dev/null` en entorno controlado.

Ver plantilla y scripts en: [PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md).

---

## 4. Monitorización y alertas (con runbook)

Fuente canónica de alertas orientativas: [docs/monitoring/alerts.md](../monitoring/alerts.md).

Reglas operativas:

1. Alertas con **dueño** y runbook (no “alerta sin brújula”).  
2. Umbrales tras baseline medido (Prometheus/Locust).  
3. Secretos del canal (Slack webhook) no van en el repo; van en ficheros en `/run/secrets` o secret store del entorno.

---

## 5. Evolución hacia Sabionda AI

Sabionda es el sistema educativo/certificación y cooperación. Lo pedagógico por edades es roadmap de producto y requiere gobernanza (menores, DPIA, consentimiento).

Referencia: [Sabionda-Educational-System.md](../sabionda/Sabionda-Educational-System.md).

Para expansión técnica y UE: [PRONTUARIO-MAESTRO-ESCALADO-CLIENTES-SABIONDA-UE-2026.md](./PRONTUARIO-MAESTRO-ESCALADO-CLIENTES-SABIONDA-UE-2026.md).

---

## 6. Checklist 2026 (cierre con evidencia)

Marca cada ítem como OK solo con evidencia:

- [ ] Mitigación LLMNR/mDNS documentada (playbook `CRITICAL_HARDENING_CHECKS`) y aplicada en staging.  
- [ ] Validación de sensores transversal documentada (tests/CI que fallan si falta esquema).  
- [ ] HAProxy con healthcheck y cabeceras de seguridad revisadas contra el frontend real.  
- [ ] TLS y cifrado en reposo verificados con comandos autorizados (no promesas).  
- [ ] Backup cifrado con manifiesto SHA256 y restauración de prueba archivada (incluye pen drive air-gap).  
- [ ] Alertas Prometheus con umbrales baselined y runbooks enlazados.  
- [ ] GaiaChain/Trazas en modo opt-in coherente con configuración (si se usa).  
- [ ] SIGPAC: flujo manual auditado o API regional real integrada (sin stubs “return True” como prod).  

---

## 7. Próximos pasos recomendados

1. Tomar [PLAN-MEJORA-INMEDIATA-CASTUO-2026.md](./PLAN-MEJORA-INMEDIATA-CASTUO-2026.md) y ejecutar fase táctica 1 (LLMNR + backups + hardening).  
2. Convertir esta arquitectura objetivo en tareas concretas en [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md).  
3. Si quieres, en el siguiente turno puedo generar un “índice de evidencia” (tabla: requisito → archivo → comando de verificación → dónde se guarda el artefacto).

