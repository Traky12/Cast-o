# Arquitectura Castuo-System — Valor 5.0 (Micro-Grid térmica y eléctrica)

## Triángulo de eficiencia: Solar + Agua + Geotermia

| Vértice | Rol | Módulo / API |
|---------|-----|----------------|
| **Solar** | Generación FV, sombra agrícola, excedente para cargas | `backend.agrivoltaic`, UNE 216701 |
| **Agua** | RO, ozono, riego, pH/CE/NPK | LSS + Chemical Guardian + Nutrient Manager |
| **Geotermia** | Estabilidad térmica, COP bomba, pre-tratamiento RO | `backend.geothermal_engine`, sinergia en `geothermal_synergy` |

La **ósmosis inversa** es más eficiente con agua de entrada **20–25 °C** (menor presión en membranas). Si el agua entra fría, la geotermía **pre-calienta** antes del RO. En verano, el circuito geotérmico puede actuar como **sumidero de frío** para estabilizar **O₃** (más estable a menor temperatura).

---

## Inventario de servicios (7 dimensiones Gran Maestro)

| # | Servicio | Responsabilidad | Parámetros clave |
|---|----------|-----------------|------------------|
| 1 | **Agro-Solar Core** | UNE 216701, sombra, LUE | kWh/ha, LUE, excedente solar kW est. |
| 2 | **Geotermia** | Intercambio térmico, COP | `depth`, `ground_temp`, `fluid_velocity`, ΔT fluido |
| 3 | **Water Treatment (LSS)** | RO, ozono | T entrada RO, presión, estado O₃ |
| 4 | **Nutrient Manager** | N/P/K precisión | pH, bloqueo nitratos |
| 5 | **Irrigation Engine** | Electroválvulas | m³/h, bar |
| 6 | **Chemical Guardian** | Estabilidad agua | pH, CE |
| 7 | **Audit & Gateway** | Trazabilidad | `audit_id`, eventos synergy |

---

## API y módulos técnicos

| Recurso | Descripción |
|---------|-------------|
| `POST /api/synergy/master-dashboard` | Reglas: excedente solar + depósito → RO; pH>7.5 → alerta nitratos; geotermia + T agua |
| `backend/geothermal_engine.py` | `calculate_thermal_exchange`, `estimate_heat_pump_cop`, `osmosis_inlet_thermal_advisory`, `solar_surplus_kw_estimate` |
| `backend/agrivoltaic/geothermal_synergy.py` | Enriquece métricas con COP, flujo térmico, priorización intercambiador si **excedente > 5 kW** |
| `backend/agrivoltaic_metrics.py` | `compute_hybrid_agrivoltaic_geothermal(...)` |
| `AnalysisRequest` | Campos opcionales: `ground_temperature_10m`, `heat_pump_status`, `delta_t_fluid` (+ sensores agua entrada en dict) |

---

## Lógica de ejemplo (Dashboard Maestro)

1. **Si** `Solar_Excedent > 5 kW` **Y** `Tank_Level < 20 %` → recomendar **Ósmosis inversa** (consumo eléctrico alto solo con excedente).
2. **Si** `pH > 7.5` → alertar **Nutrient Manager** (bloqueo de nitratos).
3. **Si** `T_agua_entrada_RO < 18 °C` **Y** hay `ground_temperature_10m` → **pre-calentar** vía intercambiador geotérmico (ahorro RO ~15–20 % energía eléctrica estimado en modelo).

---

## Sinergia química y radicular

- **O₃ + pH**: agua tratada no debe dañar raíces; control conjunto con CE.
- **Nitrato / potasio**: absorción óptima si el riego **no sufre choques térmicos** frente a la solución radicular; la geotermia amortigua ΔT estacional.

---

## AGRI-SENSE-CORE (bucle de control)

| Componente | Descripción |
|------------|-------------|
| `backend/system_orchestrator.py` | Bucle de retroalimentación negativa: Geotermia+Ósmosis (flujo bomba según CE), Ozono+pH (sincronización O₃ para no oxidar N/K), Solar+Riego (sombra UNE + ET). Fail-safe: sensor O₃ fallido → válvula NPK cerrada. |
| `backend/agri_sense/` | `UltraPrecisionSchema` (tolerance, confidence_score), filtro EWMA para N/K, constantes fail-safe. |
| `POST /api/agri-sense/control-cycle` | Un ciclo atómico con lock; respuesta con `audit_id` y causa raíz. |
| `GET /api/agri-sense/state` | Estado actual para telemetría. |
| `POST /api/agri-sense/manual-intervention` | Forzar ciclo ozono, ajustar COP o setpoint geotérmico. |

## Dashboard de telemetría (7D)

- **`dashboard/telemetry_app.py`** (Streamlit + Plotly): energía híbrida (Solar / Bomba calor / Ósmosis), panel químico (pH, N, K con zonas de alerta), estado hídrico y O₃, mapa térmico subterráneo, últimos audit_id con código de colores por gravedad, botón de intervención manual. Conectado al orquestador vía `CASTUO_API_BASE`.

## CASTUO 5.PRO+ (QAOA BioGrid)

- **`backend/agri_sense/quantum_optimizer.py`**: QAOA (Qiskit) o enumeración clásica; techo **Perovskita + Biogás**.
- **`backend/biogrid_5pro.py`**: Presupuesto energético del BioGrid 2.0.
- Orquestador: recalcula si **irradiancia cambia >10%**.
- **`docs/CASTUO-5PRO-QUANTUM.md`**, **`requirements-castuo-quantum.txt`**.

## Soberanía tecnológica (stack UE)

- **`docs/SOBERANIA-TECNOLOGICA.md`**: FIWARE NGSI-LD, QuestDB, Keycloak, Open-Meteo, Brújula Digital 2030.

---

## Referencias cruzadas

- `docs/ARQUITECTURA-AGROVOLTAICA-API.md` — contratos agrivoltaicos federados.
- `docs/ACUERDO-COOPERACION-CTAEX-CASTUO.md` — marco CTAEX.
- `docs/SOBERANIA-TECNOLOGICA.md` — stack europeo y abierto.
