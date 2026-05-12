-- CASTÚO-SYSTEM v2.0 — Esquemas PostgreSQL para cannabis y microgreens
-- Cumplimiento normativo: RD 903/2025 (THC <= 0.3%), AEMPS, GlobalGAP

-- Esquema cannabis (trazabilidad y AEMPS)
CREATE SCHEMA IF NOT EXISTS cannabis;

-- Tabla de cuentas Pro (referenciada por cannabis_batches)
CREATE TABLE IF NOT EXISTS public.pro_accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Variedades de cannabis (catálogo)
CREATE TABLE IF NOT EXISTS cannabis.cannabis_strains (
    strain_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    species VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Lotes de cannabis (con triggers para AEMPS / RD 903/2025)
CREATE TABLE IF NOT EXISTS cannabis.cannabis_batches (
    batch_id VARCHAR(50) PRIMARY KEY,
    strain_id VARCHAR(50) NOT NULL REFERENCES cannabis.cannabis_strains(strain_id),
    thc_percentage DECIMAL(5, 2) CHECK (thc_percentage <= 0.3),
    cbd_percentage DECIMAL(5, 2),
    planting_date TIMESTAMP WITH TIME ZONE NOT NULL,
    harvest_date TIMESTAMP WITH TIME ZONE,
    weight_kg DECIMAL(10, 2),
    lab_results JSONB NOT NULL DEFAULT '{}',
    blockchain_tx VARCHAR(100) UNIQUE,
    account_id VARCHAR(50) REFERENCES public.pro_accounts(account_id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'planted' CHECK (status IN ('planted', 'growing', 'harvested', 'drying', 'certified', 'shipped')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trigger para validar THC según RD 903/2025
CREATE OR REPLACE FUNCTION cannabis.validate_thc()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.thc_percentage > 0.3 THEN
        RAISE EXCEPTION 'THC percentage exceeds legal limit (RD 903/2025): %', NEW.thc_percentage;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS check_thc_before_insert ON cannabis.cannabis_batches;
CREATE TRIGGER check_thc_before_insert
    BEFORE INSERT OR UPDATE ON cannabis.cannabis_batches
    FOR EACH ROW EXECUTE PROCEDURE cannabis.validate_thc();

-- Actualizar updated_at
CREATE OR REPLACE FUNCTION cannabis.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at_batches ON cannabis.cannabis_batches;
CREATE TRIGGER set_updated_at_batches
    BEFORE UPDATE ON cannabis.cannabis_batches
    FOR EACH ROW EXECUTE PROCEDURE cannabis.set_updated_at();

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_cannabis_batches_account_status ON cannabis.cannabis_batches (account_id, status);
CREATE INDEX IF NOT EXISTS idx_cannabis_batches_blockchain_tx ON cannabis.cannabis_batches (blockchain_tx);
CREATE INDEX IF NOT EXISTS idx_cannabis_batches_planting_date ON cannabis.cannabis_batches (planting_date);

-- Esquema microgreens (opcional, para GlobalGAP)
CREATE SCHEMA IF NOT EXISTS microgreens;

CREATE TABLE IF NOT EXISTS microgreens.microgreens_batches (
    batch_id VARCHAR(50) PRIMARY KEY,
    variety VARCHAR(100) NOT NULL,
    tray_id VARCHAR(50),
    quantity_kg DECIMAL(10, 2),
    planting_date TIMESTAMP WITH TIME ZONE,
    harvest_date TIMESTAMP WITH TIME ZONE,
    lab_results JSONB DEFAULT '{}',
    blockchain_tx VARCHAR(100),
    account_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'planted',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_microgreens_batches_account_status ON microgreens.microgreens_batches (account_id, status);
