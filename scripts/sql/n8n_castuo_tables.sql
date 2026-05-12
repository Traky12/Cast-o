-- Tablas alineadas con N8N_DB_* / config/global_vars.json (PostgreSQL).
-- Ejecutar contra la base que use n8n Data Table / backend, no mezclar con DB interna de n8n salvo decisión explícita.

CREATE TABLE IF NOT EXISTS system_config (
  key TEXT PRIMARY KEY,
  value TEXT,
  category TEXT,
  last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS castuo_prod_cosechas (
  id SERIAL PRIMARY KEY,
  cultivo_id TEXT NOT NULL,
  fecha_cosecha DATE NOT NULL,
  peso_total NUMERIC(12, 2),
  calidad TEXT,
  hash_trazabilidad TEXT,
  fecha_registro TIMESTAMPTZ DEFAULT NOW(),
  immutable_record BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS castuo_prod_lecturas_sensores (
  id SERIAL PRIMARY KEY,
  sensor_id TEXT NOT NULL,
  valor NUMERIC(12, 4),
  ts TIMESTAMPTZ DEFAULT NOW(),
  hash TEXT
);

CREATE TABLE IF NOT EXISTS castuo_prod_cultivos (
  id SERIAL PRIMARY KEY,
  cultivo_codigo TEXT NOT NULL,
  nombre TEXT,
  estado TEXT,
  meta JSONB,
  fecha_registro TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS castuo_prod_analisis_diarios (
  id SERIAL PRIMARY KEY,
  dia DATE NOT NULL,
  resumen TEXT,
  payload JSONB,
  hash_trazabilidad TEXT,
  fecha_registro TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS castuo_prod_alertas (
  id SERIAL PRIMARY KEY,
  severidad TEXT,
  mensaje TEXT,
  contexto JSONB,
  ts TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS castuo_prod_reportes_cultivos (
  id SERIAL PRIMARY KEY,
  generado_en TIMESTAMPTZ DEFAULT NOW(),
  contenido JSONB
);

CREATE TABLE IF NOT EXISTS castuo_prod_reportes_optimizacion (
  id SERIAL PRIMARY KEY,
  generado_en TIMESTAMPTZ DEFAULT NOW(),
  contenido JSONB
);

CREATE TABLE IF NOT EXISTS castuo_prod_reportes_ejecutivos (
  id SERIAL PRIMARY KEY,
  generado_en TIMESTAMPTZ DEFAULT NOW(),
  contenido JSONB
);

CREATE TABLE IF NOT EXISTS castuo_prod_log_incidencias (
  id SERIAL PRIMARY KEY,
  ts TIMESTAMPTZ DEFAULT NOW(),
  origen TEXT,
  detalle JSONB
);

CREATE TABLE IF NOT EXISTS castuo_prod_log_auditoria (
  id SERIAL PRIMARY KEY,
  ts TIMESTAMPTZ DEFAULT NOW(),
  workflow TEXT,
  usuario TEXT,
  accion TEXT,
  tabla_objeto TEXT,
  data_hash TEXT,
  estado TEXT,
  payload JSONB
);

CREATE TABLE IF NOT EXISTS castuo_prod_leads_typeform (
  id SERIAL PRIMARY KEY,
  lead_id TEXT,
  payload JSONB,
  ts TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS castuo_prod_gateway_requests (
  id SERIAL PRIMARY KEY,
  ts TIMESTAMPTZ DEFAULT NOW(),
  route TEXT,
  request_id TEXT,
  payload JSONB
);

CREATE TABLE IF NOT EXISTS castuo_prod_gateway_errors (
  id SERIAL PRIMARY KEY,
  ts TIMESTAMPTZ DEFAULT NOW(),
  route TEXT,
  error_code TEXT,
  detalle JSONB
);
