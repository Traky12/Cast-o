# Funding — CTAEX, Fundecyt, PAC 2040

Resumen para convocatorias y pitch.

## One-pager CTAEX

- **Problema:** Trazabilidad y cumplimiento para cooperativas agrovoltaicas.
- **Solución:** CASTÚO-SYSTEM (Mistral + GaiaChain + API Cooperativas).
- **TRL:** 6 → 7 (demo sistema completo).
- **Métricas:** `/metrics` (mistral_queries, cooperativas_activas, total_kwp, pac2040_funding).

Documento completo: [One-pager-CTAEX.md](../funding/One-pager-CTAEX.md).

## PAC 2040 — Criterios

- **Submedidas:** 14.2.1 Agrovoltaica, 6.1 Jóvenes agricultores.
- **Ayuda máxima:** €120.000/hectárea (plazo 31/12/2026).
- **API:** `GET /pac2040/eligibilidad` (backend puerto 8001).

Documento completo: [PAC2040-Criterios.md](../funding/PAC2040-Criterios.md).

## TRL7 y pitch deck

- **Checklist TRL7:** [TRL7-Checklist.md](../TRL7-Checklist.md).
- **Generar deck CTAEX:** `python scripts/generate_ctaex_deck.py --json` → `docs/funding/CTAEX-Deck.md` + `CTAEX-Deck.json`.
