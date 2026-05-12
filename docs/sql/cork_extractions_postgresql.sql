-- PostgreSQL — metadata árbol + eventos extracción (grado producción)
-- Ejecutar tras políticas de backup cifrado y rol de solo inserción para edge.

CREATE TABLE IF NOT EXISTS traceability_trees (
    tree_uuid UUID PRIMARY KEY,
    species VARCHAR(64) DEFAULT 'Quercus suber',
    parcel_reference TEXT,
    georef_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cork_extractions (
    event_id UUID PRIMARY KEY,
    tree_uuid UUID NOT NULL REFERENCES traceability_trees (tree_uuid) ON DELETE RESTRICT,
    operator_id VARCHAR(256) NOT NULL,
    laser_energy_mj DOUBLE PRECISION NOT NULL CHECK (laser_energy_mj > 0),
    cambium_score DOUBLE PRECISION NOT NULL CHECK (cambium_score > 0.99 AND cambium_score <= 1.0),
    pqc_signature TEXT NOT NULL,
    gaia_chain_hash VARCHAR(140) NOT NULL,
    manifest_snapshot TEXT,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    cis_generated INT NOT NULL DEFAULT 0 CHECK (cis_generated >= 0)
);

CREATE INDEX IF NOT EXISTS idx_cork_tree_time ON cork_extractions (tree_uuid, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_cork_received ON cork_extractions (received_at DESC);

COMMENT ON TABLE cork_extractions IS 'SEGUREJA + GaiaChain; integridad biológica vía cambium_score';
