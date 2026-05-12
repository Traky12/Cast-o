-- QuestDB — ingestión series temporales de extracciones (alta escritura)
-- Ajustar tipos según versión QuestDB; alternativa: PG + Timescale.

CREATE TABLE IF NOT EXISTS cork_extractions (
    received_at TIMESTAMP,
    event_id SYMBOL,
    tree_uuid SYMBOL,
    operator_id SYMBOL,
    laser_energy_mj DOUBLE,
    cambium_score DOUBLE,
    pqc_signature STRING,
    gaia_chain_hash SYMBOL,
    cis_generated INT
) TIMESTAMP(received_at);
