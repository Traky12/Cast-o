-- Observaciones agrovoltaicas por zona; shadow_factor efectivo = shading_wm2 / irradiance_wm2 (derivado en consulta).
SET client_encoding = 'UTF8';

CREATE TABLE IF NOT EXISTS agrovoltaic_observations (
    id SERIAL PRIMARY KEY,
    zone_id VARCHAR(64) NOT NULL,
    irradiance_wm2 DOUBLE PRECISION NOT NULL,
    shading_wm2 DOUBLE PRECISION NOT NULL DEFAULT 0,
    transpiration_mmol_m2_s DOUBLE PRECISION,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    source VARCHAR(64) DEFAULT 'api'
);

CREATE INDEX IF NOT EXISTS idx_agrovoltaic_zone_time ON agrovoltaic_observations(zone_id, recorded_at DESC);
