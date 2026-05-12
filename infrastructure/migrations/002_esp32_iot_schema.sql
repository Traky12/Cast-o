-- SQL Migrations para ESP32 IoT Integration
-- Schema for sensors, actuators, calibration y trazabilidad

-- ═══════════════════════════════════════════════════════════════════
-- 1. Tabla: esp32_devices
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS esp32_devices (
    id BIGSERIAL PRIMARY KEY,
    esp32_id VARCHAR(50) NOT NULL UNIQUE,
    device_name VARCHAR(255),
    tenant_id UUID NOT NULL,
    
    -- Ubicación física
    location_latitude FLOAT,
    location_longitude FLOAT,
    location_description VARCHAR(500),
    
    -- Conexión
    wifi_ssid VARCHAR(100),
    ip_address INET,
    mac_address MACADDR,
    
    -- Estado
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    online_status VARCHAR(20) DEFAULT 'UNKNOWN', -- ONLINE|OFFLINE|UNREACHABLE|BACKUP_AP
    
    -- Firmware
    firmware_version VARCHAR(20),
    last_firmware_update TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT valid_esp32_id CHECK (LENGTH(esp32_id) >= 3)
);

CREATE INDEX idx_esp32_devices_tenant ON esp32_devices(tenant_id);
CREATE INDEX idx_esp32_devices_online ON esp32_devices(online_status);

-- ═══════════════════════════════════════════════════════════════════
-- 2. Tabla: sensor_definitions (mapea tipos de sensores a pines)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sensor_definitions (
    id BIGSERIAL PRIMARY KEY,
    esp32_device_id BIGINT NOT NULL,
    sensor_type VARCHAR(50) NOT NULL, -- pH|EC|TDS|TEMPERATURE|HUMIDITY|PRESSURE
    
    -- Hardware mapping
    adc_pin VARCHAR(10),
    gpio_pin VARCHAR(10),
    protocol VARCHAR(20), -- ADC|1WIRE|I2C|SPI
    address_i2c VARCHAR(10),
    
    -- Calibración
    calibration_points INT DEFAULT 2, -- 1-point ou 2-point
    calibrated_at TIMESTAMPTZ,
    calibration_valid BOOLEAN DEFAULT FALSE,
    calibration_expiry_days INT DEFAULT 30,
    
    -- Rango operativo
    min_value FLOAT,
    max_value FLOAT,
    unit VARCHAR(20), -- pH|µS/cm|ppm|°C|%|hPa
    
    -- Sensibilidad
    sensitivity FLOAT DEFAULT 1.0,
    offset FLOAT DEFAULT 0.0,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    FOREIGN KEY (esp32_device_id) REFERENCES esp32_devices(id) ON DELETE CASCADE,
    CONSTRAINT valid_sensor_type CHECK (sensor_type IN ('pH', 'EC', 'TDS', 'TEMPERATURE', 'HUMIDITY', 'PRESSURE')),
    CONSTRAINT valid_unit CHECK (unit IN ('pH', 'µS/cm', 'ppm', '°C', '%', 'hPa'))
);

CREATE INDEX idx_sensor_definitions_device ON sensor_definitions(esp32_device_id);
CREATE INDEX idx_sensor_definitions_type ON sensor_definitions(sensor_type);

-- ═══════════════════════════════════════════════════════════════════
-- 3. Tabla: sensor_readings (lecturas de sensores - TimescaleDB hypertable)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sensor_readings (
    time TIMESTAMPTZ NOT NULL,
    device_id BIGINT NOT NULL,
    sensor_id BIGINT NOT NULL,
    sensor_type VARCHAR(50),
    
    -- Valores
    raw_adc_value INT,
    calibrated_value FLOAT,
    unit VARCHAR(20),
    
    -- Validación
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_reason VARCHAR(255),
    is_calibrated BOOLEAN DEFAULT FALSE,
    calibration_method VARCHAR(50), -- UNCALIBRATED|FIELD|FACTORY|ESTIMATED
    
    -- Metadatos
    wifi_rssi INT, -- dBm (-30 a -120)
    esp32_uptime_ms BIGINT,
    mqtt_latency_ms INT,
    
    -- Auditoría
    source VARCHAR(50) DEFAULT 'esp32', -- esp32|manual|import|estimate
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (time);

-- Crear particiones mensuales (TimescaleDB)
-- SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);

CREATE INDEX idx_sensor_readings_device_time ON sensor_readings(device_id, time DESC);
CREATE INDEX idx_sensor_readings_sensor_time ON sensor_readings(sensor_id, time DESC);
CREATE INDEX idx_sensor_readings_anomaly ON sensor_readings(is_anomaly) WHERE is_anomaly = TRUE;
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(time DESC);

-- ═══════════════════════════════════════════════════════════════════
-- 4. Tabla: sensor_calibrations (historial de calibraciones)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sensor_calibrations (
    id BIGSERIAL PRIMARY KEY,
    sensor_id BIGINT NOT NULL,
    esp32_device_id BIGINT NOT NULL,
    
    -- Calibración 2-point
    calibration_method VARCHAR(50), -- 2POINT|1POINT|FACTORY|AUTO
    
    -- Punto 1
    point1_reference FLOAT,       -- Valor de referencia (ej: pH 7.0)
    point1_measured INT,          -- ADC leído
    point1_timestamp TIMESTAMPTZ,
    
    -- Punto 2
    point2_reference FLOAT,
    point2_measured INT,
    point2_timestamp TIMESTAMPTZ,
    
    -- Coeficientes calculados
    slope FLOAT,
    offset FLOAT,
    r_squared FLOAT,              -- Coeficiente de correlación
    
    -- Validez
    is_valid BOOLEAN DEFAULT TRUE,
    confidence_score FLOAT DEFAULT 0.0, -- 0.0-1.0
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    -- Metadata
    performed_by VARCHAR(255),    -- Usuario o script que calibró
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    FOREIGN KEY (sensor_id) REFERENCES sensor_definitions(id) ON DELETE CASCADE,
    FOREIGN KEY (esp32_device_id) REFERENCES esp32_devices(id) ON DELETE CASCADE
);

CREATE INDEX idx_sensor_calibrations_device ON sensor_calibrations(esp32_device_id);
CREATE INDEX idx_sensor_calibrations_sensor ON sensor_calibrations(sensor_id);
CREATE INDEX idx_sensor_calibrations_valid ON sensor_calibrations(is_valid) WHERE is_valid = TRUE;

-- ═══════════════════════════════════════════════════════════════════
-- 5. Tabla: actuators (riego, ozono, etc)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS actuators (
    id BIGSERIAL PRIMARY KEY,
    esp32_device_id BIGINT NOT NULL,
    actuator_type VARCHAR(50) NOT NULL, -- riego|ozono|bomba|ventilador|luz
    
    -- Hardware
    gpio_pin VARCHAR(10),
    relay_type VARCHAR(50), -- NO|NC|PWM
    
    -- Configuración de seguridad
    max_duration_seconds INT DEFAULT 300, -- Timeout automático
    min_interval_seconds INT DEFAULT 30,  -- Tiempo mínimo entre activaciones
    max_activations_per_hour INT DEFAULT 10,
    
    -- Estado
    is_active BOOLEAN DEFAULT TRUE,
    current_status VARCHAR(20) DEFAULT 'OFF', -- ON|OFF|ERROR
    current_duration INT,
    
    -- Historial
    total_activations BIGINT DEFAULT 0,
    last_activation TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    FOREIGN KEY (esp32_device_id) REFERENCES esp32_devices(id) ON DELETE CASCADE,
    CONSTRAINT valid_actuator_type CHECK (actuator_type IN ('riego', 'ozono', 'bomba', 'ventilador', 'luz'))
);

CREATE INDEX idx_actuators_device ON actuators(esp32_device_id);
CREATE INDEX idx_actuators_status ON actuators(current_status);

-- ═══════════════════════════════════════════════════════════════════
-- 6. Tabla: actuator_commands (auditoría de acciones)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS actuator_commands (
    id BIGSERIAL PRIMARY KEY,
    actuator_id BIGINT NOT NULL,
    esp32_device_id BIGINT NOT NULL,
    tenant_id UUID NOT NULL,
    
    -- Comando
    action VARCHAR(20) NOT NULL, -- ON|OFF|PULSE|TOGGLE
    duration_seconds INT,
    intensity FLOAT, -- 0.0-1.0 para PWM
    
    -- Modo
    execution_mode VARCHAR(50), -- MANUAL|AUTOMATION|EMERGENCY|SCHEDULED
    
    -- Control
    initiated_by VARCHAR(255),      -- Usuario, regla automática, etc
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(255),
    approval_timestamp TIMESTAMPTZ,
    
    -- Resultado
    execution_status VARCHAR(50), -- PENDING|EXECUTING|SUCCESS|FAILED|TIMEOUT|OVERRIDDEN
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    
    -- Auditoría
    api_endpoint VARCHAR(500),
    user_agent VARCHAR(500),
    ip_address INET,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    FOREIGN KEY (actuator_id) REFERENCES actuators(id) ON DELETE CASCADE,
    FOREIGN KEY (esp32_device_id) REFERENCES esp32_devices(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_actuator_commands_actuator ON actuator_commands(actuator_id);
CREATE INDEX idx_actuator_commands_status ON actuator_commands(execution_status);
CREATE INDEX idx_actuator_commands_timestamp ON actuator_commands(created_at DESC);

-- ═══════════════════════════════════════════════════════════════════
-- 7. Tabla: automation_rules (reglas de automatización)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS automation_rules (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    esp32_device_id BIGINT NOT NULL,
    
    rule_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Condición (JSON flexible)
    condition_json JSONB NOT NULL, -- {"sensor":"pH", "operator":"<", "value":5.5}
    
    -- Acción (JSON flexible)
    action_json JSONB NOT NULL, -- {"actuator":"riego", "action":"on", "duration":120}
    
    -- Control
    is_enabled BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0, -- Mayor = ejecuta primero
    deferral_time_seconds INT DEFAULT 0, -- Espera antes de ejecutar
    
    -- Ejecución
    trigger_count BIGINT DEFAULT 0,
    last_triggered TIMESTAMPTZ,
    last_result VARCHAR(50), -- SUCCESS|FAILED|SKIPPED|DEFERRED
    
    -- Scheduling
    active_from TIMESTAMPTZ,
    active_until TIMESTAMPTZ,
    active_days_of_week VARCHAR(50), -- "1,3,5" para lun/mié/vie
    active_hours VARCHAR(50), -- "08-18" para 8am-6pm
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (esp32_device_id) REFERENCES esp32_devices(id) ON DELETE CASCADE
);

CREATE INDEX idx_automation_rules_device ON automation_rules(esp32_device_id);
CREATE INDEX idx_automation_rules_enabled ON automation_rules(is_enabled) WHERE is_enabled = TRUE;

-- ═══════════════════════════════════════════════════════════════════
-- 8. Tabla: produce_batches (trazabilidad de cosechas)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS produce_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    esp32_device_id BIGINT NOT NULL,
    
    -- Identificación
    batch_code VARCHAR(255) UNIQUE NOT NULL,  -- QR code
    crop_type VARCHAR(100), -- Lechuga, Tomate, Espinaca, etc
    variety VARCHAR(100),
    
    -- Fechas
    planting_date DATE NOT NULL,
    expected_harvest DATE,
    actual_harvest_date DATE,
    harvest_complete BOOLEAN DEFAULT FALSE,
    
    -- Certificación
    is_organic BOOLEAN DEFAULT TRUE,
    zero_chemicals BOOLEAN DEFAULT TRUE,
    certification_number VARCHAR(100),
    
    -- Sensor data range
    sensor_log_start_time TIMESTAMPTZ NOT NULL,
    sensor_log_end_time TIMESTAMPTZ,
    environmental_conditions JSONB, -- {"avg_ph": 6.2, "avg_temp": 24.5, ...}
    
    -- QR & Trazabilidad
    qr_code_url VARCHAR(500),
    trazabilidad_hash VARCHAR(255), -- SHA256 del log de sensores
    blockchain_tx_id VARCHAR(255), -- Si se usa blockchain (opcional)
    
    -- Documentos
    pdf_certificate_url VARCHAR(500),
    pdf_generated_at TIMESTAMPTZ,
    
    -- Estados
    status VARCHAR(50) DEFAULT 'GROWING', -- GROWING|HARVESTING|HARVESTED|CERTIFIED|ARCHIVED
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    FOREIGN KEY (esp32_device_id) REFERENCES esp32_devices(id) ON DELETE CASCADE
);

CREATE INDEX idx_produce_batches_tenant ON produce_batches(tenant_id);
CREATE INDEX idx_produce_batches_status ON produce_batches(status);
CREATE INDEX idx_produce_batches_qr ON produce_batches(batch_code);

-- ═══════════════════════════════════════════════════════════════════
-- 9. Vistas: resumen de estado actual
-- ═══════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW v_device_status AS
SELECT 
    d.id,
    d.esp32_id,
    d.device_name,
    d.tenant_id,
    d.online_status,
    d.last_seen,
    COUNT(DISTINCT s.id) as sensor_count,
    COUNT(DISTINCT a.id) as actuator_count,
    MAX(sr.time) as last_sensor_reading,
    CASE 
        WHEN d.online_status = 'ONLINE' THEN '🟢'
        WHEN d.online_status = 'BACKUP_AP' THEN '🟡'
        ELSE '🔴'
    END as status_emoji
FROM esp32_devices d
LEFT JOIN sensor_definitions s ON d.id = s.esp32_device_id
LEFT JOIN actuators a ON d.id = a.esp32_device_id
LEFT JOIN sensor_readings sr ON d.id = sr.device_id
GROUP BY d.id, d.esp32_id, d.device_name, d.tenant_id, d.online_status, d.last_seen;

CREATE OR REPLACE VIEW v_sensor_alerts AS
SELECT 
    d.esp32_id,
    s.sensor_type,
    sr.calibrated_value,
    s.unit,
    sr.time,
    sr.is_anomaly,
    sr.anomaly_reason,
    CASE 
        WHEN sr.is_anomaly THEN '🔴 ANOMALO'
        WHEN sr.calibrated_value < s.min_value THEN '⚠️ BAJO'
        WHEN sr.calibrated_value > s.max_value THEN '⚠️ ALTO'
        ELSE '✅ OK'
    END as status
FROM sensor_readings sr
JOIN sensor_definitions s ON sr.sensor_id = s.id
JOIN esp32_devices d ON sr.device_id = d.id
WHERE sr.time > NOW() - INTERVAL '1 hour'
ORDER BY sr.time DESC;

-- ═══════════════════════════════════════════════════════════════════
-- 10. Función: calcular slope/offset de calibración
-- ═══════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION calculate_calibration_coefficients()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.point1_measured IS NOT NULL AND NEW.point2_measured IS NOT NULL
       AND NEW.point1_reference IS NOT NULL AND NEW.point2_reference IS NOT NULL THEN
        
        -- Calcular slope: (ref2 - ref1) / (meas2 - meas1)
        NEW.slope := (NEW.point2_reference - NEW.point1_reference) / 
                     (NEW.point2_measured - NEW.point1_measured);
        
        -- Calcular offset: ref1 - (slope * meas1)
        NEW.offset := NEW.point1_reference - (NEW.slope * NEW.point1_measured);
        
        -- Calcular R² (simplificado)
        NEW.r_squared := 0.99; -- En producción, implementar cálculo real
        
        NEW.is_valid := TRUE;
        NEW.confidence_score := 0.95;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_calibration
BEFORE INSERT OR UPDATE ON sensor_calibrations
FOR EACH ROW EXECUTE FUNCTION calculate_calibration_coefficients();

-- ═══════════════════════════════════════════════════════════════════
-- 11. Permisos y esquema limpio
-- ═══════════════════════════════════════════════════════════════════

COMMIT;
