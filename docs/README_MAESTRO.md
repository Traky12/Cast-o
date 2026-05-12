# README MAESTRO — Orquestación y despliegue rápido CASTUO 5.PRO

## 1. Qué es el Nexo Operativo

**CASTUO Agent 5.PRO** integra computación cuántica híbrida (QAOA BioGrid), IA soberana (orquestación Mistral/agents), aleaciones ecológicas Jara/Cáñamo/Chlorella (hardware) y certificación agrovoltaica (UNE 216701), bajo **Soberanía Tecnológica Europea**.

## 2. Arranque rápido (software)

```bash
# API principal
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Telemetría 7D + Quantum Confidence
streamlit run dashboard/telemetry_app.py
```

Variables útiles: `CASTUO_API_BASE`, `CASTUO_IBM_QUANTUM`, `QISKIT_IBM_TOKEN`, `CASTUO_UNE216701_IMPLEMENTED`.

## 3. Mapa de módulos críticos

| Capa | Ruta |
|------|------|
| Bucle de control + fail-safe O₃/NPK | `backend/system_orchestrator.py` |
| QAOA / BioGrid | `backend/agri_sense/quantum_optimizer.py`, `backend/biogrid_5pro.py` |
| Geotermia / ósmosis | `backend/geothermal_engine.py` |
| API AGRI-SENSE | `POST /api/agri-sense/control-cycle`, `GET /api/agri-sense/state` |
| Sinergia maestro | `POST /api/synergy/master-dashboard` |
| Federado UNE | `POST /federated/agrivoltaic/analyze` |

## 4. Documentación maestra

1. `docs/CATALOGO-ALEACIONES-ECOLOGICAS-v5PRO.md` — Jara, cáñamo, Chlorella, recubrimientos.
2. `docs/CASTUO-SOBERANIA-TOTAL-ESTRUCTURA-ZIP.md` — ZIP Soberanía Total ↔ repo.
3. `docs/SOBERANIA-TECNOLOGICA.md` — FIWARE, QuestDB, Open-Meteo, Brújula Digital 2030.
4. `docs/CASTUO-5PRO-QUANTUM.md` — QAOA y MRV hoja de ruta.
5. `docs/CASTUO-CLOUD-5X-SOBERANIA-TERRITORIAL.md` — Edge Zero-Water, NIR-Core, GaiaChain, CIS, Extremadura.
6. `docs/SEGUREJA-LASER-DESCORCHE-5.md` — descorche femtosegundo, enjambre, Fase 0.
7. `docs/ACUERDO-COOPERACION-CTAEX-CASTUO.md` — marco CTAEX.

## 5. Hardware y ZIP industrial

Los artefactos **CAD (.stp), LoRA (.bin), claves (.pem)** no se versionan aquí. Ver estructura en `CASTUO-SOBERANIA-TOTAL-ESTRUCTURA-ZIP.md` y canales seguros de entrega (CTAEX / fabricante).

---

*Bioeconomía circular europea — datos y energía bajo control del productor.*
