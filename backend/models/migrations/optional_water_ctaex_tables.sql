-- Tablas opcionales para telemetría agua prototipo CTAEX (PostgreSQL 12+).
-- Ejecutar solo si se desea persistencia histórica.
-- Si ya tenías una versión anterior sin columnas en water_alerts, añade con ALTER (ver final).

CREATE TABLE IF NOT EXISTS water_sensor_data (
    id SERIAL PRIMARY KEY,
    sensor_type VARCHAR(20) NOT NULL,
    sensor_value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(16),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_topic VARCHAR(100),
    raw_payload TEXT,
    processed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS water_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(50),
    sensor_type VARCHAR(20),
    sensor_value DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS water_quality_metrics (
    id SERIAL PRIMARY KEY,
    orp_value DOUBLE PRECISION,
    tds_value DOUBLE PRECISION,
    ph_value DOUBLE PRECISION,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    quality_score DOUBLE PRECISION GENERATED ALWAYS AS (
        CASE
            WHEN orp_value BETWEEN 650 AND 750 AND tds_value < 50 AND ph_value BETWEEN 5.5 AND 6.5 THEN 100
            WHEN orp_value BETWEEN 600 AND 800 AND tds_value < 60 AND ph_value BETWEEN 5.0 AND 7.0 THEN 80
            ELSE 0
        END
    ) STORED,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS water_system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_ms INTEGER,
    status VARCHAR(20) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_water_sensor_time ON water_sensor_data (timestamp);
CREATE INDEX IF NOT EXISTS idx_water_sensor_type ON water_sensor_data (sensor_type);
CREATE INDEX IF NOT EXISTS idx_water_alerts_time ON water_alerts (timestamp);
CREATE INDEX IF NOT EXISTS idx_water_alerts_status ON water_alerts (status);
CREATE INDEX IF NOT EXISTS idx_water_metrics_time ON water_quality_metrics (timestamp);
CREATE INDEX IF NOT EXISTS idx_water_metrics_quality ON water_quality_metrics (quality_score);

-- Si ya existe la tabla water_alerts sin las columnas sensor_type/sensor_value:
-- ALTER TABLE water_alerts ADD COLUMN IF NOT EXISTS sensor_type VARCHAR(20);
-- ALTER TABLE water_alerts ADD COLUMN IF NOT EXISTS sensor_value DOUBLE PRECISION;
