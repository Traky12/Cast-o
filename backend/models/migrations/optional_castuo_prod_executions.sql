-- Opcional: auditoría de orquestación n8n (tabla separada de la BD interna "n8n").
-- Ejecutar en la BD de aplicación que elijáis para castuo_prod_*.

CREATE TABLE IF NOT EXISTS castuo_prod_executions (
    execution_id VARCHAR(128) PRIMARY KEY,
    request_type VARCHAR(64) NOT NULL,
    data JSONB NOT NULL DEFAULT '{}',
    result JSONB,
    trace_hash VARCHAR(128),
    gaiachain_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS castuo_prod_mcp_executions (
    execution_id VARCHAR(128) PRIMARY KEY,
    action VARCHAR(128) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    result JSONB,
    trace_hash VARCHAR(128),
    user_id VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS castuo_prod_traceability (
    trace_hash VARCHAR(128) PRIMARY KEY,
    execution_id VARCHAR(128),
    gaiachain_http_status INT,
    langsmith_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_castuo_exec_type ON castuo_prod_executions (request_type);
CREATE INDEX IF NOT EXISTS idx_castuo_exec_time ON castuo_prod_executions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_castuo_mcp_user ON castuo_prod_mcp_executions (user_id);
CREATE INDEX IF NOT EXISTS idx_castuo_trace_exec ON castuo_prod_traceability (execution_id);

COMMENT ON TABLE castuo_prod_executions IS 'Huella API: preferir trace_hash devuelto por LangGraph; gaiachain_note texto libre si el hook del API no devuelve tx.';
