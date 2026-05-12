-- Plantilla AGRI-BRAIN / workflow 02-agente-diagnostico-ultra.json
-- Ejecutar en la misma base que uses con Postgres en n8n (p. ej. agri_brain en castuo-cerebros-postgres).

CREATE TABLE IF NOT EXISTS telemetria (
  id bigserial PRIMARY KEY,
  sector_id text NOT NULL,
  humedad double precision,
  temp double precision,
  fecha timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_telemetria_sector_fecha ON telemetria (sector_id, fecha DESC);

-- Ejemplo (opcional):
-- INSERT INTO telemetria (sector_id, humedad, temp) VALUES ('demo-sector-1', 42, 28);
