# Plan de migración a PostgreSQL — Cannabis y Microgreens

Migración de las bases de datos en memoria (`cannabis_licenses_db`, `cannabis_batches_db`, `microgreen_*_db`) a PostgreSQL para persistencia y escalabilidad.

---

## 1. Prerrequisitos

- PostgreSQL 15+ en ejecución (por ejemplo, contenedor en `docker-compose.ctaex.yml`).
- Tabla (o esquema) **pro_accounts** existente si los lotes referencian `account_id`. Si aún no existe, crear un esquema mínimo de Cuentas Pro o eliminar temporalmente la FK y usar `account_id` como VARCHAR sin FK.

---

## 2. Esquemas de base de datos

### 2.1. Esquema para Cannabis Medicinal

```sql
-- Schema: cannabis
CREATE SCHEMA IF NOT EXISTS cannabis;

-- Tabla: cannabis_strains (Variedades de cannabis)
CREATE TABLE cannabis.cannabis_strains (
    strain_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(100),
    thc_percentage DECIMAL(5, 2) NOT NULL,
    cbd_percentage DECIMAL(5, 2) NOT NULL,
    cultivation_license VARCHAR(50) NOT NULL,
    batch_size INT,
    compliance_standards JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_thc_limit CHECK (thc_percentage <= 100)
);

-- Tabla: cannabis_licenses (Licencias AEMPS)
CREATE TABLE cannabis.cannabis_licenses (
    license_id VARCHAR(50) PRIMARY KEY,
    holder VARCHAR(200) NOT NULL,
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    allowed_strains JSONB NOT NULL DEFAULT '[]',
    max_cultivation_area DECIMAL(10, 2),
    aemps_reference VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'revoked')),
    blockchain_tx VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: cannabis_batches (Lotes de cannabis)
-- Validaciones clave: thc_percentage <= 0.3 (RD 903/2025), blockchain_tx UNIQUE (GaiaChain), FK pro_accounts
CREATE TABLE cannabis.cannabis_batches (
    batch_id VARCHAR(50) PRIMARY KEY,
    strain_id VARCHAR(50) REFERENCES cannabis.cannabis_strains(strain_id),
    cultivation_site VARCHAR(100) NOT NULL,
    planting_date TIMESTAMP WITH TIME ZONE NOT NULL,
    harvest_date TIMESTAMP WITH TIME ZONE,
    weight DECIMAL(10, 2),
    lab_test_results JSONB,
    thc_percentage DECIMAL(5, 2) CHECK (thc_percentage <= 0.3),
    blockchain_tx VARCHAR(100) UNIQUE NOT NULL,
    certification_status VARCHAR(20) DEFAULT 'pending' CHECK (certification_status IN ('pending', 'approved', 'rejected')),
    certification_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'planted' CHECK (status IN ('planted', 'growing', 'harvested', 'drying', 'certified', 'shipped')),
    account_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- Activar cuando exista: FOREIGN KEY (account_id) REFERENCES public.pro_accounts(account_id) ON DELETE CASCADE
);

-- Tabla: cannabis_certificates (Certificados)
CREATE TABLE cannabis.cannabis_certificates (
    certificate_id VARCHAR(50) PRIMARY KEY,
    batch_id VARCHAR(50) REFERENCES cannabis.cannabis_batches(batch_id),
    strain_name VARCHAR(100),
    weight DECIMAL(10, 2),
    harvest_date TIMESTAMP WITH TIME ZONE,
    thc_percentage DECIMAL(5, 2),
    cbd_percentage DECIMAL(5, 2),
    compliance_standards JSONB,
    blockchain_tx VARCHAR(100) NOT NULL,
    issued_by VARCHAR(100) DEFAULT 'CTAEX + AEMPS',
    issue_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expiration_date TIMESTAMP WITH TIME ZONE,
    qr_code VARCHAR(200),
    status VARCHAR(20) DEFAULT 'issued' CHECK (status IN ('draft', 'issued', 'validated', 'rejected'))
);

-- Tabla: cannabis_activity_log (Registro de actividades)
CREATE TABLE cannabis.cannabis_activity_log (
    log_id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) REFERENCES cannabis.cannabis_batches(batch_id),
    action VARCHAR(100) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(50)
);

CREATE INDEX idx_cannabis_batches_account ON cannabis.cannabis_batches(account_id);
CREATE INDEX idx_cannabis_batches_status ON cannabis.cannabis_batches(status);
CREATE INDEX idx_cannabis_activity_batch ON cannabis.cannabis_activity_log(batch_id);
```

**Nota:** Si `pro_accounts` existe en otro esquema (por ejemplo `public.pro_accounts`), añadir en `cannabis_batches`:

```sql
-- FOREIGN KEY (account_id) REFERENCES public.pro_accounts(account_id) ON DELETE CASCADE
```

---

### 2.2. Esquema para Microgreens

```sql
-- Schema: microgreens
CREATE SCHEMA IF NOT EXISTS microgreens;

-- Tabla: microgreen_varieties (Variedades)
CREATE TABLE microgreens.microgreen_varieties (
    variety_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(100),
    growth_cycle INT NOT NULL DEFAULT 7,
    ideal_ph DECIMAL(4, 2) NOT NULL,
    ideal_ec DECIMAL(4, 2) NOT NULL,
    ideal_temperature_min DECIMAL(4, 2) NOT NULL,
    ideal_temperature_max DECIMAL(4, 2) NOT NULL,
    ideal_humidity_min DECIMAL(4, 2) NOT NULL,
    ideal_humidity_max DECIMAL(4, 2) NOT NULL,
    nutritional_value JSONB DEFAULT '{}',
    certification_standards JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: microgreen_batches (Lotes)
-- environmental_data JSONB para datos IoT (pH, EC, temperatura). Índice compuesto para listados.
CREATE TABLE microgreens.microgreen_batches (
    batch_id VARCHAR(50) PRIMARY KEY,
    variety_id VARCHAR(50) NOT NULL REFERENCES microgreens.microgreen_varieties(variety_id),
    tray_id VARCHAR(50) NOT NULL,
    planting_date TIMESTAMP WITH TIME ZONE NOT NULL,
    harvest_date TIMESTAMP WITH TIME ZONE,
    weight DECIMAL(10, 2),
    environmental_data JSONB NOT NULL DEFAULT '{}',
    blockchain_tx VARCHAR(100),
    certification_status VARCHAR(20) DEFAULT 'pending' CHECK (certification_status IN ('pending', 'approved', 'rejected')),
    status VARCHAR(30) DEFAULT 'planted' CHECK (status IN ('planted', 'germinating', 'growing', 'harvested', 'packed', 'shipped')),
    account_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_microgreen_batches_account_status ON microgreens.microgreen_batches(account_id, status);

-- Tabla: microgreen_certificates (Certificados)
CREATE TABLE microgreens.microgreen_certificates (
    certificate_id VARCHAR(50) PRIMARY KEY,
    batch_id VARCHAR(50) NOT NULL REFERENCES microgreens.microgreen_batches(batch_id),
    variety VARCHAR(100) NOT NULL,
    weight DECIMAL(10, 2) NOT NULL,
    harvest_date TIMESTAMP WITH TIME ZONE NOT NULL,
    environmental_compliance JSONB DEFAULT '{}',
    organic_status BOOLEAN DEFAULT TRUE,
    blockchain_tx VARCHAR(100) NOT NULL,
    issued_by VARCHAR(100) NOT NULL,
    issue_date TIMESTAMP WITH TIME ZONE NOT NULL,
    expiration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    qr_code VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_microgreen_batches_account ON microgreens.microgreen_batches(account_id);
CREATE INDEX idx_microgreen_batches_status ON microgreens.microgreen_batches(status);
```

---

## 3. Pasos de migración

| Paso | Acción | Comando / descripción |
|------|--------|------------------------|
| 1 | Crear esquemas y tablas | Ejecutar los bloques SQL de las secciones 2.1 y 2.2 en la base `castuo_ctaex` (o la que use el backend). |
| 2 | Seed de variedades (opcional) | Insertar en `cannabis.cannabis_strains` y `microgreens.microgreen_varieties` los datos iniciales (ej. variedades de microgreens: radish, broccoli). |
| 3 | Adaptar el backend | Sustituir en `backend/routers/pro_accounts.py` los diccionarios `cannabis_licenses_db`, `cannabis_batches_db`, `microgreen_varieties_db`, `microgreen_batches_db`, `microgreen_certificates_db` por acceso a PostgreSQL (SQLAlchemy, asyncpg o psycopg2). |
| 4 | Variables de entorno | Configurar `DATABASE_URL` (o `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) para que el backend se conecte a PostgreSQL. |
| 5 | Migración de datos existentes (si hay) | Script que lea los diccionarios en memoria (o un export JSON) e inserte en las tablas antes de desplegar la nueva versión. |
| 6 | Pruebas | Verificar creación de licencias, lotes, cosecha, certificados y listados vía API contra PostgreSQL. |
| 7 | Despliegue | Desplegar backend con persistencia PostgreSQL y retirar uso de diccionarios en memoria. |

---

## 4. Consideraciones

- **Límite THC:** El estándar UE para cannabis no medicinal es &lt;0,3 %. Validar en aplicación; el CHECK en `cannabis_strains` puede relajarse si se usan variedades medicinales con otro límite.
- **Relación con Pro Accounts:** Si la tabla `pro_accounts` no existe aún, mantener `account_id` como VARCHAR sin FK hasta tener el esquema de cuentas en PostgreSQL.
- **Backups:** Incluir los esquemas `cannabis` y `microgreens` en los backups regulares de PostgreSQL (por ejemplo `scripts/backup_postgres_ctaex.sh`).
- **Índices:** Los índices creados mejoran listados por `account_id` y `status`; añadir más si hay consultas frecuentes por fecha o `batch_id`.

---

## 5. Conexión y variables de entorno

### 5.1. Módulo de conexión (`backend/database.py`)

Instalar `psycopg2-binary` cuando se use PostgreSQL. Ejemplo de conexión:

```python
# backend/database.py
import os
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

def get_db_connection():
    if not psycopg2:
        raise RuntimeError("psycopg2 no instalado. Ejecutar: pip install psycopg2-binary")
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "castuo_ctaex"),
        user=os.getenv("DB_USER", "castuo_admin"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        cursor_factory=RealDictCursor,
    )
```

### 5.2. Variables de entorno (`.env`)

```env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=sabionda_prod
DB_USER=sabionda_admin
DB_PASSWORD=secure_password
```

---

## 6. Script de migración de datos

Ejemplo para migrar datos desde los diccionarios en memoria a PostgreSQL (ejecutar cuando la BD esté creada y el backend tenga los datos en memoria):

```python
# scripts/migrate_cannabis_microgreens_to_postgres.py
def migrate_cannabis_batches(conn, cannabis_batches_db):
    with conn.cursor() as cur:
        for batch_id, batch in cannabis_batches_db.items():
            strain = batch.strain
            cur.execute("""
                INSERT INTO cannabis.cannabis_batches
                (batch_id, strain_id, cultivation_site, planting_date, harvest_date, weight,
                 lab_test_results, blockchain_tx, status, certification_status, account_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (batch_id) DO NOTHING
            """, (
                batch.batch_id,
                strain.strain_id,
                batch.cultivation_site,
                batch.planting_date,
                batch.harvest_date,
                batch.weight,
                psycopg2.extras.Json(batch.lab_test_results) if batch.lab_test_results else None,
                batch.blockchain_tx or "",
                batch.status,
                getattr(batch, "certification_status", "pending"),
                batch.account_id or "",
            ))
    conn.commit()
```

Usar **bulk inserts** (executemany o COPY) para optimizar si hay muchos registros (objetivo &lt;1 min/100 registros).

---

## 7. Validaciones técnicas post-migración

| Componente | Prueba | Resultado esperado |
|------------|--------|--------------------|
| Conexión PostgreSQL | `from backend.database import get_db_connection; get_db_connection().status` | Conexión exitosa |
| Migración de datos | Ejecutar script y `SELECT COUNT(*) FROM cannabis.cannabis_batches` | 100 % migrados |
| Consultas por estado | `SELECT COUNT(*) FROM cannabis.cannabis_batches WHERE status = 'certified'` | Coherente con datos |
| Blockchain único | `SELECT COUNT(DISTINCT blockchain_tx) = COUNT(*) FROM cannabis.cannabis_batches` | Sin duplicados |
| IoT / JSONB | `UPDATE microgreens.microgreen_batches SET environmental_data = '{"ph": 6.0, "ec": 1.2}' WHERE batch_id = 'test'` | Datos guardados |
| Relación account_id | `SELECT COUNT(*) FROM cannabis.cannabis_batches WHERE account_id = 'test_account'` | Coherente |

---

## 8. Rendimiento y optimización

| Métrica | Objetivo | Optimización |
|---------|----------|--------------|
| Tiempo de respuesta GET /batches | &lt;100 ms | Índice en (account_id, status) |
| Uso de CPU (PostgreSQL) | &lt;70 % | Monitorizar con Grafana |
| Latencia Blockchain | &lt;2 s | Conexión persistente (Session) a GaiaChain |
| Tiempo de migración | &lt;1 min/100 reg | Bulk inserts en script de migración |

---

## 9. Próximos pasos recomendados

**Inmediato (1–2 semanas):** Validar backups (Backblaze B2), añadir índices, pruebas de carga con Locust, actualizar PRO-ACCOUNTS-GUIDE, revisar logs tras migración.

**Mediano (1 mes):** Integración API real AEMPS, nodos reales GaiaChain, preparar Kubernetes, auditoría ISO 27001, alianzas comerciales.

**Largo (3–6 meses):** Certificación JAS Organic (Asia), patentes IA ética, sensores IoT reales, localización Japón, conector SAP.

---

## 10. Checklist para despliegue en producción

**Pre-despliegue:** Esquemas creados y validados; datos de prueba migrados; backend adaptado a PostgreSQL; variables de entorno configuradas; pruebas de integración pasadas.

**Despliegue:** `docker compose -f docker/docker-compose.ctaex.yml up -d`; verificar logs del backend; probar endpoints críticos (POST/GET cannabis/batches, GET microgreens/batches); monitorear Grafana.

**Post-despliegue:** Generar informe con `SELECT COUNT(*)` por tabla; documentar lecciones aprendidas en este documento; planificar integración AEMPS y GaiaChain.

---

## 11. Plan de contingencia (rollback)

Si falla PostgreSQL en producción, volver temporalmente a diccionarios en memoria:

1. `docker compose -f docker/docker-compose.ctaex.yml down`
2. Revertir cambios en `backend/database.py` y routers (usar rama o copia sin PostgreSQL).
3. Asegurarse de que `DB_HOST` no esté definido en `.env` (o que el backend use memoria cuando no hay conexión).
4. `docker compose -f docker/docker-compose.ctaex.yml up -d`

**Script de rollback:** `scripts/rollback_to_memory.sh` (ejecutar desde la raíz del repo; en Windows usar Git Bash o ejecutar los pasos manualmente). Ver también `.env.example` para variables DB_*.

Documentar el rollback y corregir causa antes de reintentar la migración.

---

## 12. Métricas de éxito post-migración

| Métrica | Valor esperado | Herramienta | Frecuencia |
|---------|----------------|-------------|------------|
| Tiempo de respuesta API | &lt;100 ms | Prometheus/Grafana | Diaria |
| Éxito en certificaciones | 99 % | Sentry | Semanal |
| Uptime | 99,9 % | UptimeRobot | Diaria |
| Uso de CPU (PostgreSQL) | &lt;50 % | Grafana | Diaria |
| Lotes certificados/día | &gt;50 | Contador en BD | Diaria |

---

## 13. Referencias

- Modelos actuales en memoria: `backend/routers/pro_accounts.py` (cannabis_*_db, microgreen_*_db).
- Modelos Pydantic: `backend/models/cannabis_specific.py`, `backend/models/microgreens_specific.py`.
- Docker CTAEX: `docker/docker-compose.ctaex.yml`, variables DB_* en `.env`.
- Pruebas de carga: `tests/load_test_locust.py` (ejecutar: `locust -f tests/load_test_locust.py --host=http://localhost:8000`).
- Conexión BD: `backend/database.py`.
- Script de migración: `scripts/migrate_cannabis_microgreens_to_postgres.py` (PYTHONPATH=. python scripts/...).

### 13.1. Recomendaciones post-migración

**Integración con AEMPS:** Sustituir la simulación en `CannabisComplianceValidator` por la API real cuando esté disponible (validación de licencias con `AEMPS_API_KEY`).

**GaiaChain:** Usar conexión persistente (p. ej. `requests.Session()` o cliente gRPC persistente) en `blockchain_integration.py` para reducir latencia por debajo de 2 s.

**Pruebas de carga:** Simular 1.000 usuarios con Locust:  
`locust -f tests/load_test_locust.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s`
