-- Extensiones (TimescaleDB omitido: requiere imagen timescale/timescaledb)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla principal trazabilidad GS1 EPCIS (UE 178/2002)
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    epc_list TEXT[] NOT NULL,
    quantity NUMERIC(10,2) NOT NULL,
    read_point VARCHAR(255) NOT NULL,
    biz_step VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT check_quantity CHECK (quantity > 0),
    CONSTRAINT check_epc_list CHECK (array_length(epc_list, 1) > 0)
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_epc ON events USING GIN(epc_list);
CREATE INDEX IF NOT EXISTS idx_events_read_point ON events(read_point);

-- Auditoría
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id UUID,
    old_data JSONB,
    new_data JSONB,
    action_timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION log_audit()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (user_id, action, table_name, record_id, new_data)
        VALUES (current_user, 'INSERT', TG_TABLE_NAME, NEW.id, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_data, new_data)
        VALUES (current_user, 'UPDATE', TG_TABLE_NAME, NEW.id, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_data)
        VALUES (current_user, 'DELETE', TG_TABLE_NAME, OLD.id, to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS audit_events_trigger ON events;
CREATE TRIGGER audit_events_trigger
AFTER INSERT OR UPDATE OR DELETE ON events
FOR EACH ROW EXECUTE PROCEDURE log_audit();

-- Permisos (usuario creado por POSTGRES_USER en Docker; DB = POSTGRES_DB)
GRANT USAGE ON SCHEMA public TO castuo_user;
GRANT SELECT, INSERT ON events TO castuo_user;
GRANT SELECT, INSERT ON audit_log TO castuo_user;
GRANT USAGE, SELECT ON SEQUENCE audit_log_id_seq TO castuo_user;
