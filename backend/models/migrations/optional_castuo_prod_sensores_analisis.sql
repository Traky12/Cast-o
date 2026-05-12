-- Opcional: persistencia de análisis sensor → LangGraph (vía n8n).
-- Ejecutar en la misma base que use el nodo Postgres de n8n.

CREATE TABLE IF NOT EXISTS castuo_prod_sensores_analisis (
    id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(128) NOT NULL,
    valor DOUBLE PRECISION,
    cultivo VARCHAR(128),
    ubicacion VARCHAR(256),
    analisis TEXT,
    recomendaciones TEXT,
    trace_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_castuo_sensores_sensor_time
    ON castuo_prod_sensores_analisis (sensor_id, created_at DESC);

COMMENT ON TABLE castuo_prod_sensores_analisis IS 'Filas escritas por workflow n8n tras /langgraph/castuo/execute-graph (trace_hash, no tx on-chain obligatoria).';
