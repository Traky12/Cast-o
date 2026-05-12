-- CASTÚO-SYSTEM™ v3.1 — PostgreSQL Init
-- Schemas: ctaex (agriculture data) + infra (system logs/events)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ── Schema ctaex ─────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS ctaex;

CREATE TABLE IF NOT EXISTS ctaex.registros (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id       VARCHAR(64) NOT NULL,
    zone            VARCHAR(8)  NOT NULL DEFAULT 'A',
    ph              NUMERIC(5,2),
    ec              NUMERIC(6,3),
    temp_agua       NUMERIC(5,2),
    temp_aire       NUMERIC(5,2),
    humedad         NUMERIC(5,2),
    co2             NUMERIC(8,2),
    luz_par         NUMERIC(8,2),
    o2_disuelto     NUMERIC(5,2),
    raw_payload     JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_registros_ts        ON ctaex.registros (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_registros_device    ON ctaex.registros (device_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_registros_zone      ON ctaex.registros (zone, timestamp DESC);

CREATE TABLE IF NOT EXISTS ctaex.alertas (
    id          BIGSERIAL PRIMARY KEY,
    device_id   VARCHAR(64)  NOT NULL,
    zone        VARCHAR(8),
    parametro   VARCHAR(32)  NOT NULL,
    valor       NUMERIC(10,3),
    nivel       VARCHAR(16)  NOT NULL CHECK (nivel IN ('baja','media','critica')),
    prioridad   NUMERIC(8,2) DEFAULT 0,
    timestamp   TIMESTAMPTZ  NOT NULL,
    notificado  BOOLEAN      DEFAULT FALSE,
    creado_por  VARCHAR(64)  DEFAULT 'n8n-ctaex',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alertas_ts       ON ctaex.alertas (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alertas_device   ON ctaex.alertas (device_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alertas_nivel    ON ctaex.alertas (nivel, created_at DESC);
-- Index for anti-spam Check Spam query
CREATE INDEX IF NOT EXISTS idx_alertas_spam     ON ctaex.alertas (device_id, parametro, nivel, created_at DESC);

CREATE TABLE IF NOT EXISTS ctaex.metricas (
    id                  BIGSERIAL PRIMARY KEY,
    timestamp           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    total_dispositivos  INTEGER      DEFAULT 0,
    zonas_activas       INTEGER      DEFAULT 0,
    kpi_json            JSONB,
    evaluaciones_json   JSONB,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metricas_ts ON ctaex.metricas (timestamp DESC);

CREATE TABLE IF NOT EXISTS ctaex.errores (
    id          BIGSERIAL PRIMARY KEY,
    timestamp   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    device_id   VARCHAR(64),
    tipo        VARCHAR(64)  NOT NULL,
    mensaje     TEXT,
    payload     JSONB,
    resuelto    BOOLEAN      DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_errores_ts       ON ctaex.errores (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_errores_resuelto ON ctaex.errores (resuelto, created_at DESC);

-- ── Schema infra ─────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS infra;

CREATE TABLE IF NOT EXISTS infra.logs (
    id          BIGSERIAL PRIMARY KEY,
    timestamp   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    servicio    VARCHAR(64)  NOT NULL,
    nivel       VARCHAR(16)  NOT NULL DEFAULT 'INFO',
    mensaje     TEXT         NOT NULL,
    contexto    JSONB,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_ts       ON infra.logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_servicio ON infra.logs (servicio, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_nivel    ON infra.logs (nivel, timestamp DESC);

CREATE TABLE IF NOT EXISTS infra.events (
    id          UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    tipo        VARCHAR(64)  NOT NULL,
    origen      VARCHAR(64),
    payload     JSONB,
    procesado   BOOLEAN      DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_ts        ON infra.events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_tipo      ON infra.events (tipo, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_procesado ON infra.events (procesado, created_at DESC);

-- ── Vistas útiles ────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW ctaex.v_ultimas_lecturas AS
SELECT DISTINCT ON (device_id)
    device_id, zone, ph, ec, temp_agua, temp_aire, humedad, co2, luz_par, o2_disuelto, timestamp
FROM ctaex.registros
ORDER BY device_id, timestamp DESC;

CREATE OR REPLACE VIEW ctaex.v_alertas_activas AS
SELECT * FROM ctaex.alertas
WHERE notificado = TRUE
  AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

CREATE OR REPLACE VIEW ctaex.v_resumen_zonas AS
SELECT
    zone,
    COUNT(DISTINCT device_id)   AS dispositivos,
    AVG(ph)                     AS ph_medio,
    AVG(ec)                     AS ec_medio,
    AVG(temp_agua)              AS temp_agua_media,
    AVG(temp_aire)              AS temp_aire_media,
    MAX(timestamp)              AS ultima_lectura
FROM ctaex.registros
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY zone
ORDER BY zone;

-- ── infra.metrics (server metrics for Grafana IT dashboard) ─────────────────

CREATE TABLE IF NOT EXISTS infra.metrics (
    id           BIGSERIAL PRIMARY KEY,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    servicio     VARCHAR(64) NOT NULL,
    cpu_usage    NUMERIC(5,2),
    memory_usage NUMERIC(5,2),
    disk_usage   NUMERIC(5,2),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_ts      ON infra.metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_servicio ON infra.metrics (servicio, timestamp DESC);

-- ── Usuarios de aplicación ────────────────────────────────────────────────────

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'castuo_app') THEN
        CREATE ROLE castuo_app LOGIN PASSWORD 'changeme_in_production';
    END IF;
END $$;

GRANT USAGE  ON SCHEMA ctaex TO castuo_app;
GRANT USAGE  ON SCHEMA infra TO castuo_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA ctaex TO castuo_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA infra TO castuo_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ctaex TO castuo_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA infra TO castuo_app;
GRANT SELECT ON ALL TABLES IN SCHEMA ctaex TO castuo_app;

-- grafana_reader: read-only user for Grafana dashboards
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'grafana_reader') THEN
        CREATE ROLE grafana_reader LOGIN PASSWORD 'changeme_in_production';
    END IF;
END $$;

GRANT USAGE  ON SCHEMA ctaex TO grafana_reader;
GRANT USAGE  ON SCHEMA infra TO grafana_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA ctaex TO grafana_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA infra TO grafana_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA ctaex GRANT SELECT ON TABLES TO grafana_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA infra GRANT SELECT ON TABLES TO grafana_reader;
