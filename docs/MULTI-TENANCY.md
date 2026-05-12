# Multi-Tenancy Architecture - CASTÚO-SYSTEM™

## Objetivo
Implementar arquitectura multi-tenant para soportar múltiples clientes (granjas) con aislamiento de datos completo y reducción de costes del 8x.

## Modelo Actual vs Multi-Tenant

### Actual (Single-Tenant per Deployment)
```
┌─────────────────────────────┐
│   Hetzner EU Server 1       │
│  ┌───────────────────────┐  │
│  │ FastAPI (Puerto 8000) │  │
│  │ PostgreSQL (5432)     │  │
│  │ Redis (6379)          │  │
│  │ n8n (3000)            │  │
│  └───────────────────────┘  │
│        €500/mes             │
└─────────────────────────────┘

Total: 950 granjas × €500 = €475K/mes
```

### Multi-Tenant (Propuesto)
```
┌──────────────────────────────────────┐
│   Hetzner EU Server (Premium)        │
│  ┌────────────────────────────────┐  │
│  │   Load Balancer (Nginx)        │  │
│  │  - granja1.castuo.es       │  │
│  │  - granja2.castuo.es       │  │
│  │  - granja3.castuo.es       │  │
│  ├────────────────────────────────┤  │
│  │   FastAPI (Multi-tenant)       │  │
│  │   - Tenant isolation           │  │
│  │   - Request routing            │  │
│  ├────────────────────────────────┤  │
│  │   PostgreSQL (Shared)          │  │
│  │   - Schema per tenant          │  │
│  │   - RLS (Row-Level Security)   │  │
│  ├────────────────────────────────┤  │
│  │   Redis Cluster (Shared)       │  │
│  │   - Cache isolation by tenant  │  │
│  │   - Session management         │  │
│  │   - Rate limiting              │  │
│  │   - Message queues             │  │
│  └────────────────────────────────┘  │
│        €2,500/mes (shared)           │
└──────────────────────────────────────┘

Total: 950 granjas × €2.63 = €2,500/mes
AHORRO: €472.5K/mes = €5.67M/año
```

## Arquitectura Técnica

### 1. Tenant Identification

**Header-based (Recomendado):**
```http
X-Tenant-ID: granja-alpujarra-001
X-Tenant-Name: La Alpujarra Farm
```

**Subdomain-based:**
```
https://granja-alpujarra-001.castuo.es/api/v1/ganado
```

**Path-based:**
```
https://api.castuo.es/v1/tenant/granja-alpujarra-001/ganado
```

### 2. FastAPI Middleware Implementation

```python
# infrastructure/fastapi/multi-tenancy/middleware.py

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import hashlib

class MultiTenancyMiddleware(BaseHTTPMiddleware):
    """Core middleware for tenant isolation"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Extract tenant_id
        tenant_id = self._extract_tenant_id(request)
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Missing tenant_id")
        
        # 2. Validate tenant exists and is active
        tenant = await self._validate_tenant(tenant_id)
        if not tenant or not tenant['is_active']:
            raise HTTPException(status_code=403, detail="Invalid or inactive tenant")
        
        # 3. Generate tenant schema name
        tenant_schema = f"tenant_{hashlib.md5(tenant_id.encode()).hexdigest()[:12]}"
        
        # 4. Inject tenant context into request
        request.state.tenant_id = tenant_id
        request.state.tenant_schema = tenant_schema
        request.state.tenant = tenant
        
        # 5. Set PostgreSQL search_path for tenant schema
        try:
            db = request.app.state.db
            await db.execute(f"SET search_path = {tenant_schema}, public")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        
        # 6. Validate user belongs to tenant
        user_id = self._extract_user_id(request)
        if user_id:
            tenant_user_valid = await self._validate_user_tenant(user_id, tenant_id)
            if not tenant_user_valid:
                raise HTTPException(status_code=403, detail="User not authorized for this tenant")
        
        # 7. Process request
        response = await call_next(request)
        
        # 8. Add tenant info to response headers
        response.headers["X-Tenant-ID"] = tenant_id
        response.headers["X-Tenant-Schema"] = tenant_schema
        
        return response
    
    def _extract_tenant_id(self, request: Request) -> str | None:
        # Try header first
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            return tenant_id
        
        # Try subdomain
        host = request.headers.get('host', '')
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain != 'api' and subdomain != 'www':
                return subdomain
        
        # Try path
        path_parts = request.url.path.split('/')
        if len(path_parts) > 2 and path_parts[1] == 'tenant':
            return path_parts[2]
        
        return None
    
    def _extract_user_id(self, request: Request) -> str | None:
        # Extract from JWT token in Authorization header
        auth_header = request.headers.get('authorization', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]
        try:
            from jose import jwt
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get('sub')  # User ID
        except:
            return None
    
    async def _validate_tenant(self, tenant_id: str):
        db = request.app.state.db
        # Query public.tenants table (exists across all schemas)
        result = await db.fetchrow(
            "SELECT * FROM public.tenants WHERE id = $1",
            tenant_id
        )
        return result
    
    async def _validate_user_tenant(self, user_id: str, tenant_id: str) -> bool:
        db = request.app.state.db
        result = await db.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM public.user_tenant_memberships
                WHERE user_id = $1 AND tenant_id = $2 AND is_active = true
            )
            """,
            user_id, tenant_id
        )
        return result
```

### 3. PostgreSQL Schema Isolation

**Schema per Tenant:**
```sql
-- Crear schema para cada tenant
CREATE SCHEMA tenant_a1b2c3d4e5f6;
CREATE SCHEMA tenant_f5e4d3c2b1a0;

-- Criar tablas en schema de tenant
CREATE TABLE tenant_a1b2c3d4e5f6.ganado (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    codigo VARCHAR(50) NOT NULL,
    especie VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, codigo)
);

-- Crear índices
CREATE INDEX idx_ganado_tenant ON tenant_a1b2c3d4e5f6.ganado(tenant_id);

-- Row-Level Security adicional (defensa en profundidad)
ALTER TABLE tenant_a1b2c3d4e5f6.ganado ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenant_a1b2c3d4e5f6.ganado
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

**Shared Tables (Multi-Tenant):**
```sql
-- Tabla compartida con RLS obligatorio
CREATE TABLE public.user_tenant_memberships (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, tenant_id)
);

ALTER TABLE public.user_tenant_memberships ENABLE ROW LEVEL SECURITY;
CREATE POLICY see_own_memberships ON public.user_tenant_memberships
    USING (user_id = current_user_id());
```

### 4. Data Migration Strategy

**Phase 1: Identificación de Tenants**
```sql
-- Crear tabla de mapeo
CREATE TABLE public.tenant_migration (
    legacy_instance_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL UNIQUE,
    tenant_name VARCHAR(255) NOT NULL,
    migration_status VARCHAR(20) DEFAULT 'pending',
    migrated_at TIMESTAMPTZ,
    migration_rows_count INT
);
```

**Phase 2: Copiar datos**
```python
# scripts/migrate-to-multitenant.py
async def migrate_tenant(legacy_instance_id: str):
    """Migrate single-tenant to multi-tenant"""
    
    # 1. Create tenant identity
    tenant_id = await create_tenant(legacy_instance_id)
    
    # 2. Create schema for tenant
    await db.execute(f"CREATE SCHEMA IF NOT EXISTS tenant_{tenant_id}")
    
    # 3. Copy data from legacy instance
    await copy_data_by_table(
        source_db=legacy_instance_id,
        dest_schema=f"tenant_{tenant_id}",
        tables=['ganado', 'salud_animal', 'documentos', ...]
    )
    
    # 4. Verify data integrity
    source_count = await count_rows(legacy_instance_id)
    dest_count = await count_rows(f"tenant_{tenant_id}")
    assert source_count == dest_count, "Data mismatch!"
    
    # 5. Update users tenant memberships
    await assign_users_to_tenant(legacy_instance_id, tenant_id)
    
    # 6. Mark migration complete
    await db.execute(
        "UPDATE public.tenant_migration SET migration_status = %s WHERE legacy_instance_id = %s",
        ('completed', legacy_instance_id)
    )
```

### 5. Pricing & Billing per Tenant

```python
# infrastructure/billing/tenant-pricing.py

class TenantBilling:
    PRICING_TIERS = {
        'basic': {
            'monthly_fee': 50,
            'features': ['basic_analytics', 'email_support'],
            'max_users': 5,
            'max_sensors': 10,
            'api_calls_per_month': 100_000
        },
        'professional': {
            'monthly_fee': 150,
            'features': ['advanced_analytics', 'priority_support', 'api'],
            'max_users': 20,
            'max_sensors': 50,
            'api_calls_per_month': 1_000_000
        },
        'enterprise': {
            'monthly_fee': 500,
            'features': ['all', 'dedicated_support', 'custom_integration'],
            'max_users': 'unlimited',
            'max_sensors': 'unlimited',
            'api_calls_per_month': 'unlimited'
        }
    }
    
    async def generate_invoice(self, tenant_id: str, month: int, year: int):
        """Generate invoice for tenant"""
        tenant = await get_tenant(tenant_id)
        tier = self.PRICING_TIERS[tenant['pricing_tier']]
        
        # Base cost
        cost = tier['monthly_fee']
        
        # Usage overages (if applicable)
        api_calls = await count_api_calls(tenant_id, month, year)
        if api_calls > tier['api_calls_per_month']:
            overage_cost = (api_calls - tier['api_calls_per_month']) * 0.00001
            cost += overage_cost
        
        # Create invoice
        invoice = {
            'tenant_id': tenant_id,
            'month': month,
            'year': year,
            'base_cost': tier['monthly_fee'],
            'overage_cost': cost - tier['monthly_fee'],
            'total_cost': cost,
            'currency': 'EUR',
            'due_date': date(year, month + 1, 5)
        }
        
        await save_invoice(invoice)
        return invoice
```

## Seguridad y Compliance

### Aislamiento de Datos

1. **Network Isolation:**
   - Cada tenant accede a través de su propio subdomain o X-Tenant-ID
   - Nginx valida y enruta correctamente
   - Firewall rules por IP de tenant

2. **Database Isolation:**
   - Schema per tenant
   - Row-Level Security (RLS) en tablas críticas
   - Conexión a db con contexto de tenant

3. **Cache Isolation (Redis):**
   ```python
   # Each cache key includes tenant_id
   cache_key = f"tenant:{tenant_id}:ganado:{animal_id}"
   await redis.set(cache_key, data, ex=3600)
   ```

4. **Audit Trail:**
   ```sql
   CREATE TABLE public.audit_log_multitenant (
       id BIGSERIAL PRIMARY KEY,
       tenant_id UUID NOT NULL,
       user_id UUID NOT NULL,
       action VARCHAR(50) NOT NULL,
       table_name VARCHAR(100) NOT NULL,
       record_id UUID,
       changes JSONB,
       timestamp TIMESTAMPTZ DEFAULT NOW()
   );
   ```

## Plan de Despliegue

### Week 1-2: Preparación
- [ ] Diseño de tenant identities
- [ ] Crear infraestructura de tenant management
- [ ] Configurar base de datos compartida

### Week 3-4: Identificación
- [ ] Mapear legacy instances a tenant IDs
- [ ] Crear tabla de migración
- [ ] Validar mappings con clientes

### Week 5-8: Migración
- [ ] Ejecutar migraciones batch
- [ ] Verificar integridad de datos
- [ ] Testing con 10% de clientes

### Week 9-10: Despliegue Gradual
- [ ] Rolling deployment de FastAPI multi-tenant
- [ ] Cutover de 25% de tenants por semana
- [ ] Monitoreo 24/7 de migración

### Week 11-12: Validación
- [ ] 100% de tenants en multi-tenant
- [ ] Decommission de legacy infrastructure
- [ ] Optimización de costos

## ROI & Métricas

| Métrica | Actual | Multi-Tenant | Mejora |
|---------|--------|--------------|--------|
| Infraestructura/granja | €500/mes | €2.63/mes | 190x |
| Costo total anual | €6M | €0.3M | 20x |
| Margen bruto | 80% | 93% | +13% |
| Tiempo deployment | 2 horas | <5 min | 24x más rápido |
| Recursos DevOps | 3 FTE | 0.5 FTE | 6x más eficiente |

## Referencias
- [PostgreSQL Multi-Tenancy](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Row-Level Security Best Practices](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
