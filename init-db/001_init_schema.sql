-- Arranque mínimo: extensiones y esquema CASTÚO (migraciones de negocio aparte).
SET client_encoding = 'UTF8';

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS castuo;
COMMENT ON SCHEMA castuo IS 'CASTÚO producción — tablas bajo migraciones posteriores';

GRANT USAGE ON SCHEMA castuo TO PUBLIC;
