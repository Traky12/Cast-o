CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS sensor_telemetry (
    id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    readings JSONB NOT NULL,
    source VARCHAR(255) DEFAULT 'iot-bridge',
    traces_status VARCHAR(32) DEFAULT 'queued',
    metadata JSONB DEFAULT '{}'::jsonb
);

SELECT create_hypertable('sensor_telemetry', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_sensor_telemetry_sensor_id ON sensor_telemetry(sensor_id);
CREATE INDEX IF NOT EXISTS idx_sensor_telemetry_timestamp ON sensor_telemetry(timestamp DESC);
