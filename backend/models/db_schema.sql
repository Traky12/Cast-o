-- Trazabilidad THC: evidencia minimizada (hash + metadatos, sin espectro crudo)
CREATE TABLE IF NOT EXISTS spectra_estimations (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL,
    plant_id VARCHAR(64),
    zone_id VARCHAR(64),
    spectrum_hash VARCHAR(64) NOT NULL,
    thc_estimate DOUBLE PRECISION,
    thc_validated DOUBLE PRECISION,
    validation_method VARCHAR(64),
    lab_certificate VARCHAR(128),
    gaiachain_tx VARCHAR(128),
    status VARCHAR(32) DEFAULT 'PENDING_VALIDATION',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(batch_id, spectrum_hash)
);

CREATE INDEX IF NOT EXISTS idx_spectra_batch ON spectra_estimations(batch_id);
CREATE INDEX IF NOT EXISTS idx_spectra_plant ON spectra_estimations(plant_id);

-- Trazabilidad Hidroponía SaaS: persistencia de evidencia minimizada
CREATE TABLE IF NOT EXISTS hydroponics_sensor_readings (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(64) NOT NULL,
    sensor_type VARCHAR(32) NOT NULL,
    value FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(64),
    unit VARCHAR(16),
    zone_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(sensor_id, timestamp, zone_id)
);

CREATE INDEX IF NOT EXISTS idx_hydro_sensor_zone_type ON hydroponics_sensor_readings(zone_id, sensor_type);
CREATE INDEX IF NOT EXISTS idx_hydro_sensor_time ON hydroponics_sensor_readings(timestamp);

CREATE TABLE IF NOT EXISTS hydroponics_daily_analysis (
    id SERIAL PRIMARY KEY,
    analysis_date TIMESTAMP NOT NULL,
    zone_id VARCHAR(64) NOT NULL,
    overall_status VARCHAR(64) NOT NULL,
    issues JSONB,
    recommendations JSONB,
    trends JSONB,
    priority VARCHAR(32),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(analysis_date, zone_id)
);

CREATE INDEX IF NOT EXISTS idx_hydro_analysis_zone ON hydroponics_daily_analysis(zone_id);
CREATE INDEX IF NOT EXISTS idx_hydro_analysis_date ON hydroponics_daily_analysis(analysis_date);

-- Trazabilidad Hidroponía SaaS: cultivos y cosechas genéricas por zona
CREATE TABLE IF NOT EXISTS hydroponics_crops (
    id SERIAL PRIMARY KEY,
    crop_id VARCHAR(64) NOT NULL,
    zone_id VARCHAR(64) NOT NULL,
    plant_type VARCHAR(64) NOT NULL,
    planting_date TIMESTAMP NOT NULL,
    growth_stage VARCHAR(32) NOT NULL,
    quantity INT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    metadata JSONB,
    end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(crop_id)
);

CREATE TABLE IF NOT EXISTS hydroponics_harvests (
    id SERIAL PRIMARY KEY,
    crop_id VARCHAR(64) NOT NULL,
    harvest_date TIMESTAMP NOT NULL,
    weight FLOAT NOT NULL,
    quality VARCHAR(32) NOT NULL,
    notes TEXT,
    zone_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (crop_id) REFERENCES hydroponics_crops(crop_id)
);

CREATE INDEX IF NOT EXISTS idx_hydro_crops_zone ON hydroponics_crops(zone_id);
CREATE INDEX IF NOT EXISTS idx_hydro_crops_date ON hydroponics_crops(planting_date);
CREATE INDEX IF NOT EXISTS idx_hydro_harvests_zone ON hydroponics_harvests(zone_id);
CREATE INDEX IF NOT EXISTS idx_hydro_harvests_date ON hydroponics_harvests(harvest_date);
