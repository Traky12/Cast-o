# ISO 27001:2022 - Control A.8: Access Control

## Propósito
Asegurar que solo personas autorizadas tengan acceso a los activos de información de CASTÚO-SYSTEM™ en línea con el negocio.

## Alcance
- Aplicaciones (FastAPI, n8n)
- Bases de datos (PostgreSQL, TimescaleDB)
- Infraestructura (Kubernetes, Hetzner Cloud)
- Documentos y datos sensibles (RGPD, eIDAS)

## Controles Implementados

### A.8.1.1 Política de Control de Acceso Documentada

**Objetivo:** Definir una política clara de control de acceso basada en principios de "Least Privilege" (PoLP).

**Implementación:**

```bash
# 1. Define access roles
export ROLES=(
  "admin"           # Full system access
  "security"        # Security operations
  "developer"       # Code and staging access
  "operator"        # Production operations
  "viewer"          # Read-only access
)

# 2. Document permissions matrix
cat > docs/iso-27001/controls/access-control-matrix.md << 'EOF'
# Access Control Matrix

| Role | Database | API | Kubernetes | Admin Console | Vault |
|------|----------|-----|-----------|            ---|-------|
| admin | write | write | write | yes | write |
| security | read | read | read | yes | read |
| developer | read/write* | write | read/write* | no | read |
| operator | read | read | write* | yes | read |
| viewer | read | read | no | no | no |

* Limited to non-production environments
EOF
```

### A.8.1.2 Autorización de Acceso

**Objetivo:** Implementar un proceso formal de solicitud y aprobación de acceso.

**Proceso:**
1. Usuario solicita acceso vía JIRA (ticket P0/P1/P2)
2. Manager autoriza (revisa permisos requeridos)
3. Security team verifica cumplimiento
4. DevOps provisiona acceso
5. Auditoría registra en logs

**Implementación con Vault:**

```hcl
# Las políticas están centralizadas en Vault
# Ejemplo: acceso a base de datos para desarrollo
path "secret/data/dev/database" {
  capabilities = ["read"]
}

path "secret/data/dev/api-keys" {
  capabilities = ["read"]
}
```

### A.8.1.3 Gestión de Derechos de Acceso Privilegiado

**Objetivo:** Proteger cuentas administrativas con MFA y auditoría exhaustiva.

**Implementación:**

1. **MFA Obligatorio:**
```python
# infrastructure/fastapi/security/mfa.py
class AdminAccessControl:
    def __init__(self):
        self.mfa_required = True
        self.session_timeout = 15  # min
    
    def grant_admin_access(self, user_id: str, reason: str):
        # 1. Require TOTP token
        # 2. Log in audit trail
        # 3. Set time-limited access
        # 4. Send notification to security team
        pass
```

2. **Auditoría de Acceso Administrativo:**
```sql
SELECT
    user_id,
    action,
    table_name,
    timestamp,
    source_ip,
    mfa_verified
FROM audit_log_admin_access
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### A.8.1.4 Gestión del Cambio de Derechos de Acceso

**Objetivo:** Asegurar que los cambios de acceso se documenten y auditan.

**Proceso:**
1. Cambio de rol requiere ticket JIRA
2. PR en rama `feat/compliance/access-changes`
3. Code review por 2 security engineers
4. Despliegue con validación
5. Auditoría de cambios en Vault

**Git Workflow:**
```bash
git checkout -b feat/compliance/access-changes/user-role-update
# Actualizar archivo de políticas
git commit -m "docs: update access control for user@example.com"
gh pr create --title "Access Control: user@example.com promoted to operator"
```

### A.8.2.1 Gestión de Usuario

**Objetivo:** Asegurar aprovisión y desaprovisionamiento correcto de usuarios.

**Implementación:**

```python
# infrastructure/user-management/provisioning.py
class UserProvisioning:
    async def provision_user(self, user_data: UserRequest):
        """Crear usuario en todos los sistemas"""
        # 1. Create in PostgreSQL
        await db.execute("""
            INSERT INTO users (email, name, role, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (user_data.email, user_data.name, user_data.role))
        
        # 2. Create in n8n
        n8n_user = await n8n_client.create_user(
            email=user_data.email,
            role=map_role_to_n8n(user_data.role)
        )
        
        # 3. Create in Kubernetes RBAC
        k8s_role = await k8s_client.create_role_binding(
            user_name=user_data.email,
            role=user_data.role
        )
        
        # 4. Provision in Vault
        vault_token = await vault.create_token(
            policies=[f"{user_data.role}-policy"],
            ttl="24h"
        )
        
        # 5. Log in audit trail
        await audit_log.insert({
            'action': 'user_provisioned',
            'user': user_data.email,
            'timestamp': datetime.utcnow()
        })
        
        return {
            'status': 'provisioned',
            'vault_token': vault_token,
            'n8n_user_id': n8n_user.id
        }
    
    async def deprovision_user(self, user_id: str):
        """Remover usuario de todos los sistemas (GDPR)"""
        # 1. Disable in PostgreSQL
        await db.execute(
            "UPDATE users SET disabled = true WHERE id = %s",
            (user_id,)
        )
        
        # 2. Revoke in n8n
        await n8n_client.disable_user(user_id)
        
        # 3. Remove Kubernetes access
        await k8s_client.revoke_role_binding(user_id)
        
        # 4. Revoke Vault tokens
        await vault.revoke_tokens_for_user(user_id)
        
        # 5. Log audit trail
        await audit_log.insert({
            'action': 'user_deprovisioned',
            'user_id': user_id,
            'timestamp': datetime.utcnow()
        })
```

### A.8.2.2 Restricción de Acceso a Información

**Objetivo:** Implementar Row-Level Security (RLS) en bases de datos.

**Implementación en PostgreSQL:**

```sql
-- Enable RLS on sensitive tables
ALTER TABLE documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE ganado ENABLE ROW LEVEL SECURITY;
ALTER TABLE salud_animal ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own documents
CREATE POLICY documents_isolation ON documentos
  USING (tenant_id = current_setting('app.current_tenant'));

-- Policy: Operators can see all documents in their assigned farms
CREATE POLICY operator_farm_access ON documentos
  USING (
    farm_id IN (
      SELECT farm_id FROM operator_assignments
      WHERE operator_id = current_user_id()
    )
  );

-- Policy for audit logs (immutable)
ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;
CREATE POLICY audit_log_readonly ON audit_log AS RESTRICTIVE
  USING (true)
  WITH CHECK (false);  -- No one can insert directly
```

### A.8.2.3 Gestión de Contraseñas

**Objetivo:** Garantizar contraseñas seguras y cambio regular.

**Requisitos:**
- Mínimo 16 caracteres
- Debe incluir mayúsculas, minúsculas, números, símbolos
- Cambio cada 90 días
- Prohibir re-uso de últimas 12 contraseñas
- Almacenar con PBKDF2-SHA256 con salt

**Implementación:**

```python
import hashlib
import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__rounds=100000
)

class PasswordManagement:
    REQUIRED_LENGTH = 16
    PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{16,}$'
    MAX_AGE_DAYS = 90
    
    def validate_password(self, password: str) -> bool:
        import re
        if len(password) < self.REQUIRED_LENGTH:
            return False
        return bool(re.match(self.PATTERN, password))
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, password: str, hash: str) -> bool:
        return pwd_context.verify(password, hash)
    
    def check_password_expiry(self, user_id: str) -> bool:
        """Check if password needs renewal"""
        from datetime import datetime, timedelta
        last_change = db.query(
            "SELECT password_changed_at FROM users WHERE id = %s",
            (user_id,)
        )[0][0]
        
        if not last_change:
            return True  # Force change on first login
        
        age = (datetime.utcnow() - last_change).days
        return age > self.MAX_AGE_DAYS
```

## Evidencia de Cumplimiento

### Auditoría Trimestral

```bash
#!/bin/bash
# scripts/audit-access-control.sh - Quarterly audit

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="audit-reports/access-control-${REPORT_DATE}.md"

# 1. Usuarios activos por role
psql -h timescaledb -U castuo_iot castuo_telemetry << SQL | tee "$REPORT_FILE"
## Access Control Audit - $REPORT_DATE

### Active Users by Role
$(psql -c "SELECT role, COUNT(*) FROM users WHERE disabled = false GROUP BY role;")

### Inactive Users (>90 days)
$(psql -c "SELECT COUNT(*) FROM users WHERE last_login < NOW() - INTERVAL '90 days';")

### Privileged Access Events
$(psql -c "SELECT COUNT(*) FROM audit_log_admin_access WHERE date >= CURRENT_DATE - INTERVAL '90 days';")
SQL

# 2. Enviar a compliance team
mail -s "Access Control Audit Report - ${REPORT_DATE}" compliance@castuo.es < "$REPORT_FILE"
```

## Referencias Cruzadas
- [RGPD Compliance](../../../docs/GDPR-COMPLIANCE.md)
- [Security Guide](../../../docs/SECURITY-GUIDE.md)
- [MFA Setup](../../../docs/MFA-SETUP.md)
- [Vault Documentation](https://www.vaultproject.io/docs)
