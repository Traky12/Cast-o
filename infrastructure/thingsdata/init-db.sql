-- ===================================================================
-- PostgreSQL Initialization Script for CASTÚO-SYSTEM IoT
-- ===================================================================
-- Crear tablas para almacenar telemetría y metadatos de Thingsdata

-- Extensiones
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS json;

-- Tabla de Sensores (metadatos)
CREATE TABLE IF NOT EXISTS sensors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(255) UNIQUE NOT NULL,
    thingsdata_sim_id VARCHAR(255),
    name VARCHAR(255),
    description TEXT,
    type VARCHAR(100),  -- 'temperature', 'humidity', 'soil_moisture', etc.
    location GEOGRAPHY,
    model VARCHAR(100),
    firmware_version VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'inactive', 'maintenance'
    owner_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_reading_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT valid_sensor_id CHECK (sensor_id ~ '^[a-zA-Z0-9_-]+$')
);

-- Table de Eventos IoT (eventos de comandos, conexiones, etc.)
CREATE TABLE IF NOT EXISTS iot_events (
    id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(255) NOT NULL REFERENCES sensors(sensor_id),
    event_type VARCHAR(50),  -- 'connection', 'disconnection', 'command', 'alert'
    event_data JSONB,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Alertas
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(255) NOT NULL REFERENCES sensors(sensor_id),
    alert_type VARCHAR(100),  -- 'temperature_high', 'humidity_low', 'offline'
    severity VARCHAR(50),  -- 'info', 'warning', 'critical'
    message TEXT,
    trigger_value NUMERIC,
    threshold_value NUMERIC,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- TABLE de Comandos Ejecutados
CREATE TABLE IF NOT EXISTS commands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(255) NOT NULL REFERENCES sensors(sensor_id),
    command_type VARCHAR(100),  -- 'set_parameter', 'execute_action', etc.
    command_payload JSONB,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'sent', 'executed', 'failed'
    result JSONB,
    executed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_sensors_status ON sensors(status);
CREATE INDEX IF NOT EXISTS idx_sensors_created ON sensors(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_iot_events_sensor ON iot_events(sensor_id);
CREATE INDEX IF NOT EXISTS idx_iot_events_time ON iot_events(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_sensor ON alerts(sensor_id);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved);
CREATE INDEX IF NOT EXISTS idx_commands_sensor ON commands(sensor_id);
CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status);

-- Views para análisis
CREATE OR REPLACE VIEW active_sensors_view AS
SELECT id, sensor_id, name, type, location, model, status, last_reading_at
FROM sensors
WHERE status = 'active'
ORDER BY last_reading_at DESC NULLS LAST;

CREATE OR REPLACE VIEW recent_alerts_view AS
SELECT id, sensor_id, alert_type, severity, message, created_at
FROM alerts
WHERE resolved = FALSE
ORDER BY created_at DESC
LIMIT 100;

-- Grants (seguridad)
GRANT SELECT, INSERT, UPDATE ON sensors TO PUBLIC;
GRANT SELECT, INSERT ON iot_events TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON alerts TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON commands TO PUBLIC;

-- Comentarios
COMMENT ON TABLE sensors IS 'Metadatos de sensores IoT registrados en Thingsdata ES';
COMMENT ON TABLE iot_events IS 'Historial de eventos de IoT (conexiones, desconexiones, comandos)';
COMMENT ON TABLE alerts IS 'Alertas generadas por condiciones anómalas de sensores';
COMMENT ON TABLE commands IS 'Comandos ejecutados en sensores IoT';
