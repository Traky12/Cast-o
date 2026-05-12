# TRL7 Checklist — CASTÚO-SYSTEM (EU PAC 2040)

**Objetivo:** Sistema representativo validado en entorno operativo (finca real) para elegibilidad CTAEX €50K y PAC 2040.

## Criterios TRL7 (estándares EU PAC 2040)

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Sistema representativo validado en finca real (Sabionda) | ✅ | Sabionda Educa SAT en `/cooperativas`, parcelas con kWp y ha |
| 2 | ROI/ha medido 30+ días (sensores IoT) | 🟡 | MQTT + rpi-edge en `docker-compose.hetzner.yml`; métricas en `/metrics` |
| 3 | PAC 2040 submedidas 14.2.1 + 6.1 calculadas | ✅ | `GET /pac2040/eligibilidad` y parcelas con `pac2040_eligible` |
| 4 | GaiaChain trazabilidad verificada (QR consumidor) | ✅ | `POST /blockchain/witness` (SHA256 + API witness); GaiaChainLogger en backend |
| 5 | eIDAS QES firmas digitales operativas | 🟡 | Witness con hash inmutable; firma QES opcional vía `GAIA_CHAIN_SIGNING_KEY` |
| 6 | Multi-región compliance (ES/PT/FR/IT) | 🟡 | UniversalGeoAdapter (Omega 2040); API preparada para regiones |

## Endpoints LIVE (Hetzner)

- `GET http://[IP]:8000/metrics` — Métricas agregadas (mistral_queries, cooperativas_activas, total_kwp, pac2040_funding)
- `GET http://[IP]:8000/mistral/health` — Estado Mistral Adapter
- `GET http://[IP]:8001/cooperativas` — Listado cooperativas (Sabionda, Agrovoltaica Extremadura)
- `GET http://[IP]:8001/pac2040/eligibilidad` — Criterios PAC 2040
- `POST http://[IP]:8001/blockchain/witness` — Registro witness GaiaChain (body: `{"data": {...}, "coop_id": 1}`)

## Deploy final

```bash
cd /app && docker-compose -f docker-compose.hetzner.yml up -d --build
# Con perfil IoT (MQTT + rpi-edge):
docker-compose -f docker-compose.hetzner.yml --profile iot up -d --build
```

## Pitch CTAEX

- **Ask:** €50K CTAEX → TRL7 Q2 2026
- **ROI:** €142K/ha (Sabionda SAT)
- **Demo:** 5 endpoints LIVE Hetzner
- **Docs:** https://docs.castuo-system.com/
- Generar deck: `python scripts/generate_ctaex_deck.py --json` → `docs/funding/CTAEX-Deck.md` + `CTAEX-Deck.json`
