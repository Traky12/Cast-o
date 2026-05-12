-- CASTÚO-SYSTEM — Libro de actas (auditoría Trillizo) en Postgres
-- Complementa el journal Markdown (SilverBullet); no sustituye el volumen ./cerebros/auditoria.
-- Ejecutar en la base usada por el stack cerebros (p. ej. agri_brain) o en una BD dedicada audit.
--
-- Nota jurídica/técnica: HMAC con secreto compartido aporta integridad frente a terceros sin el secreto;
-- no equivale a firma asimétrica ni a “no repudio” fuerte frente a quien también posee la clave.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS trillizo_audit_log (
    id_evento UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ts_evento TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    id_sector VARCHAR(128) NOT NULL,
    instancia_n8n_ip INET,
    workflow_id VARCHAR(128),

    payload_json JSONB NOT NULL,
    -- Hex HMAC-SHA256 del body canónico (ver scripts/n8n/sign_audit_webhook_body.py). NULL solo si el entorno no usa secreto (no recomendado en producción).
    hmac_signature TEXT,
    hash_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    tipo_accion VARCHAR(50),
    -- 0.00–1.00; si el emisor envía 0–100 (p. ej. n8n), normalizar al insertar (÷ 100).
    confidence_score NUMERIC(5, 4),
    actuador_afectado VARCHAR(64),
    valor_comando TEXT,

    auditado_humano BOOLEAN NOT NULL DEFAULT FALSE,
    id_auditor VARCHAR(128),
    notas_auditoria TEXT,

    CONSTRAINT chk_trillizo_hash_status CHECK (
        hash_status IN ('PENDING', 'VALID', 'INVALID', 'SKIPPED')
    ),
    CONSTRAINT chk_trillizo_confidence CHECK (
        confidence_score IS NULL
        OR (confidence_score >= 0 AND confidence_score <= 1)
    )
);

CREATE INDEX IF NOT EXISTS idx_trillizo_sector_ts ON trillizo_audit_log (id_sector, ts_evento DESC);
CREATE INDEX IF NOT EXISTS idx_trillizo_hmac ON trillizo_audit_log (hmac_signature)
    WHERE hmac_signature IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trillizo_tipo_ts ON trillizo_audit_log (tipo_accion, ts_evento DESC);

COMMENT ON TABLE trillizo_audit_log IS 'Registro estructurado paralelo al journal Markdown del webhook audit-trigger.';

-- Agregados por sector para informes / sensibilidad (datos reales solo tras piloto).
CREATE OR REPLACE VIEW vista_eficiencia_operativa AS
SELECT
    id_sector,
    COUNT(*) FILTER (WHERE tipo_accion = 'IA_SUGGESTION') AS total_optimizaciones,
    COUNT(*) FILTER (WHERE tipo_accion = 'OT_FORCE') AS intervenciones_seguridad,
    COUNT(*) FILTER (WHERE tipo_accion = 'MANUAL_OVERRIDE') AS anulaciones_manuales,
    AVG(confidence_score) FILTER (WHERE confidence_score IS NOT NULL) AS confianza_media_ia
FROM trillizo_audit_log
GROUP BY id_sector;
