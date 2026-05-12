-- Opcional: auditoría de lecturas IoT tras workflow n8n + LangGraph (huella en trace_hash).
-- GaiaChain: preferir el hook del API (GAIACHAIN_REGISTER_URL), no URL fija en n8n.

CREATE TABLE IF NOT EXISTS castuo_prod_sensor_readings (
    id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(128) NOT NULL,
    value_num DOUBLE PRECISION,
    reading_type VARCHAR(64),
    location VARCHAR(256),
    metadata JSONB,
    analysis_raw TEXT,
    trace_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_castuo_sensor_id_time
    ON castuo_prod_sensor_readings (sensor_id, created_at DESC);

COMMENT ON TABLE castuo_prod_sensor_readings IS 'Filas opcionales desde n8n; trazabilidad criptográfica principal en trace_hash del API LangGraph.';
