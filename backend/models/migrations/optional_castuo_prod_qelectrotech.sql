-- Opcional: proyectos QElectroTech → LangGraph CASTÚO (análisis + huella).
-- No guardar SVG/DXF completo en texto si supera límites operativos; usar trace_hash y JSONB.

CREATE TABLE IF NOT EXISTS castuo_prod_qelectrotech (
    id BIGSERIAL PRIMARY KEY,
    project_id VARCHAR(128) NOT NULL,
    author VARCHAR(256),
    svg_excerpt_hash VARCHAR(64),
    analysis_raw TEXT,
    plc_code TEXT,
    energy_analysis TEXT,
    trace_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_castuo_qet_project_time
    ON castuo_prod_qelectrotech (project_id, created_at DESC);

COMMENT ON TABLE castuo_prod_qelectrotech IS 'Filas desde n8n tras /langgraph/castuo/execute-graph (kind qelectrotech_svg o similar). energy_analysis: JSON serializado en TEXT (o migrar a JSONB con cast).';
