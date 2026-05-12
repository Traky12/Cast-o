# Protocolo de curado UV / Plasma — BioCoin Castuo (Aleación Castuo)

## Objetivo
Fijación química entre capas (núcleo PHB/PLA-cáñamo, microencapsulado Chlorella, nanocapa sensora) sin degradar biopolímeros ni Chlorella viva encapsulada.

## Fase 1 — Pre-tratamiento plasma (atmosfera controlada)

| Parámetro | Valor orientativo | Nota |
|-----------|-------------------|------|
| Gas | Ar + 5% O₂ o N₂ puro | Limpieza superficial, activación OH |
| Potencia RF | 80–150 W | Evitar >180 W sobre fibra cáñamo expuesta |
| Tiempo | 30–90 s por cara | Rotación si geometría cilíndrica (moneda) |
| Presión | 0.2–0.5 mbar | Descarga estable |

**Impacto en territorio:** plasma reduce VOC frente a primers solvente; alinea con REACH.

## Fase 2 — Curado UV (adhesivo intercapa + sellado bio-óptico)

| Parámetro | Valor orientativo |
|-----------|-------------------|
| Longitud de onda | 365 nm (band-pass) o LED 395 nm baja exotermia |
| Irradiancia | 50–200 mW/cm² según data-sheet fotoiniciador |
| Tiempo acumulado | 15–45 s en pulsos 5s ON / 2s OFF |
| Temperatura sustrato | < 48 °C pico (sensor piezo) |

**Control:** termopar en dummy metálico mismo masa térmica que moneda.

## Fase 3 — Post-curado térmico suave (opcional PHB)

| Parámetro | Valor |
|-----------|-------|
| T | 55–65 °C |
| Tiempo | 10–20 min |
| Atmósfera | N₂ seco |

Solo si el stack no incluye capas termolábiles (>60 °C prohibido para ciertos encapsulados).

## QC de salida

- Adherencia cinta 3M 600 (test cualitativo).
- Resistencia dieléctrica nanocapa (no publicar umbrales en abierto).
- Espectro NIR de referencia de tinta criptográfica (baseline serie).

---

*Documento de ingeniería — revisión legal y CTAEX antes de producción.*
