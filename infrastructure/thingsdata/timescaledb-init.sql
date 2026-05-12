-- ===================================================================
-- TimescaleDB Initialization for CASTÚO-SYSTEM IoT Telemetry
-- ===================================================================
-- Crear hypertables para almacenar series temporales de sensores

-- Crear extensión TimescaleDB si no existe
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ===================================================================
-- HYPERTABLES PARA SERIES TEMPORALES
-- ===================================================================

-- Tabla de telemetría principal (hypertable)
CREATE TABLE IF NOT EXISTS sensor_telemetry (
    time TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(255) NOT NULL,
    value NUMERIC(10, 4),
    unit VARCHAR(50),
    quality_flag VARCHAR(10),  -- 'good', 'uncertain', 'bad'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Convertir a hypertable si no lo es ya
SELECT create_hypertable('sensor_telemetry', 'time', if_not_exists => TRUE, 
    chunk_time_interval => INTERVAL '1 day');

-- Índices compresibles
CREATE INDEX IF NOT EXISTS idx_sensor_telemetry_sensor_time 
    ON sensor_telemetry (sensor_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_telemetry_time 
    ON sensor_telemetry (time DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_telemetry_quality 
    ON sensor_telemetry (quality_flag);

-- ===================================================================
-- AGREGACIONES CONTINUAS (Downsampling)
-- ===================================================================

-- Agregación a 1 minuto
CREATE TABLE IF NOT EXISTS sensor_telemetry_1m (
    time TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(255) NOT NULL,
    value_avg NUMERIC,
    value_min NUMERIC,
    value_max NUMERIC,
    value_count INTEGER,
    unit VARCHAR(50)
);

SELECT create_hypertable('sensor_telemetry_1m', 'time', if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '7 days');

-- Agregación a 1 hora
CREATE TABLE IF NOT EXISTS sensor_telemetry_1h (
    time TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(255) NOT NULL,
    value_avg NUMERIC,
    value_min NUMERIC,
    value_max NUMERIC,
    value_count INTEGER,
    unit VARCHAR(50)
);

SELECT create_hypertable('sensor_telemetry_1h', 'time', if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '30 days');

-- Agregación a 1 día
CREATE TABLE IF NOT EXISTS sensor_telemetry_1d (
    time TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(255) NOT NULL,
    value_avg NUMERIC,
    value_min NUMERIC,
    value_max NUMERIC,
    value_count INTEGER,
    unit VARCHAR(50)
);

SELECT create_hypertable('sensor_telemetry_1d', 'time', if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '90 days');

-- ===================================================================
-- VISTAS MATERIALIZADAS PARA ANÁLISIS
-- ===================================================================

-- Vista: Últimos valores de cada sensor
CREATE OR REPLACE VIEW latest_sensor_readings AS
SELECT DISTINCT ON (sensor_id)
    time,
    sensor_id,
    value,
    unit
FROM sensor_telemetry
ORDER BY sensor_id, time DESC;

-- Vista: Estadísticas por sensor (últimas 24 horas)
CREATE OR REPLACE VIEW sensor_stats_24h AS
SELECT
    sensor_id,
    unit,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    STDDEV(value) as stddev_value,
    COUNT(*) as reading_count
FROM sensor_telemetry
WHERE time > NOW() - INTERVAL '24 hours'
GROUP BY sensor_id, unit;

-- Vista: Anomalías (valores fuera de rango)
CREATE OR REPLACE VIEW sensor_anomalies AS
SELECT
    time,
    sensor_id,
    value,
    unit,
    CASE
        WHEN value > (AVG(value) OVER (PARTITION BY sensor_id RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW)) + 2 * (STDDEV(value) OVER (PARTITION BY sensor_id RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW))
        THEN 'HIGH_SPIKE'
        WHEN value < (AVG(value) OVER (PARTITION BY sensor_id RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW)) - 2 * (STDDEV(value) OVER (PARTITION BY sensor_id RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW))
        THEN 'LOW_SPIKE'
        ELSE 'NORMAL'
    END as anomaly_type
FROM sensor_telemetry
WHERE time > NOW() - INTERVAL '30 days';

-- ===================================================================
-- POLÍTICA DE COMPRESIÓN
-- ===================================================================
-- Comprimir datos más viejos de 7 días para ahorrar espacio

SELECT add_compression_policy('sensor_telemetry',
    INTERVAL '7 days', if_not_exists => TRUE);

SELECT add_compression_policy('sensor_telemetry_1m',
    INTERVAL '30 days', if_not_exists => TRUE);

SELECT add_compression_policy('sensor_telemetry_1h',
    INTERVAL '90 days', if_not_exists => TRUE);

-- ===================================================================
-- POLÍTICA DE RETENCIÓN (GDPR-compliant)
-- ===================================================================
-- Eliminar datos más viejos de 90 días automáticamente

SELECT add_retention_policy('sensor_telemetry',
    INTERVAL '90 days', if_not_exists => TRUE);

-- ===================================================================
-- TABLESPACES (opcional, para distribución en discos)
-- ===================================================================
-- Descomentar si tienes múltiples discos
-- CREATE TABLESPACE "ssd_space" LOCATION '/mnt/ssd/timescaledb';
-- SELECT set_chunk_time_interval('sensor_telemetry', INTERVAL '1 day');

-- ===================================================================
-- VACÍO Y ANÁLISIS AUTOMÁTICO
-- ===================================================================
-- Mantener estadísticas actualizadas para query planner

ALTER TABLE sensor_telemetry SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.005
);

-- Crear índices BRIN (mejor para series temporales)
CREATE INDEX IF NOT EXISTS idx_sensor_telemetry_brin ON sensor_telemetry 
    USING BRIN (time) WITH (pages_per_range = 128);

-- ===================================================================
-- COMENTARIOS
-- ===================================================================
COMMENT ON TABLE sensor_telemetry IS 'Hypertable principal para almacenar telemetría en tiempo real de sensores Thingsdata';
COMMENT ON TABLE sensor_telemetry_1m IS 'Agregación de datos a 1 minuto (downsampling para análisis rápido)';
COMMENT ON TABLE sensor_telemetry_1h IS 'Agregación de datos a 1 hora (análisis de tendencias)';
COMMENT ON TABLE sensor_telemetry_1d IS 'Agregación de datos a 1 día (histórico a largo plazo)';

COMMENT ON VIEW latest_sensor_readings IS 'Últimos valores registrados de cada sensor';
COMMENT ON VIEW sensor_stats_24h IS 'Estadísticas de sensores en las últimas 24 horas';
COMMENT ON VIEW sensor_anomalies IS 'Detección automática de anomalías en datos de sensores';

-- ===================================================================
-- CREACIÓN DE USUARIO ESPECÍFICO (seguridad)
-- ===================================================================
-- Descomentar en producción:
-- CREATE USER timeseries_app WITH PASSWORD 'your_secure_password';
-- GRANT CONNECT ON DATABASE castuo_timeseries TO timeseries_app;
-- GRANT USAGE ON SCHEMA public TO timeseries_app;
-- GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO timeseries_app;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT ON TABLES TO timeseries_app;
