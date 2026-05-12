# Integración CASTUO Cloud 5.0 + CASTUO-SYSTEM™ 4.0 + Proyecto CASTUA

Arquitectura unificada para **cáñamo industrial**, **agrovoltaica** y **economía circular**. Todos los sistemas son **españoles o europeos** (AEMPS, RD 903/2025, SII, Facturae, EU ETS, Verra, Gold Standard, GaiaChain, GDPR, AI Act, eIDAS).

## Sistemas utilizados (España / UE)

| Ámbito | Sistema | Descripción |
|--------|---------|-------------|
| Medicamento / cannabis | **AEMPS** | Agencia Española de Medicamentos y Productos Sanitarios |
| Normativa cannabis | **RD 903/2025** | Real Decreto cannabis medicinal (seguridad, trazabilidad, THC < 0,2 %) |
| Facturación | **SII / Facturae** | Agencia Tributaria España, formato Facturae 3.2.1 |
| Blockchain trazabilidad | **GaiaChain** | Blockchain privada (trazabilidad inmutable, auditoría) |
| Carbono | **Verra (VCS), Gold Standard, EU ETS** | Mercados de carbono verificados (UE/España) |
| Seguridad / identidad | **eIDAS, GDPR, AI Act** | Reglamentos UE |
| Energía | **Mercado eléctrico español / P2P** | Excedentes, autoconsumo |

## Flujo general

```
CASTUA (Cáñamo industrial) → Invernaderos agrovoltaicos → Microred
       → Datos → CASTUO Cloud 5.0 (Edge, Sentinel, Energía)
       → Blockchain GaiaChain + ZKP
       → Procesamiento → Extrusora bio-compuestos → Materiales
       → Certificaciones → Créditos de carbono (Verra/EU ETS)
       → Mercado B2B / Reinversión / Expansión UE
```

## Módulos del repositorio

### 1. CASTUA (cáñamo industrial)

- **`castua/hidroponia_manager.py`**: `CannabisHydroponicSystem`, `AgrovoltaicSystem` — torres hidropónicas, sensores (temperatura, humedad, pH, EC, luz), refrigeración/humidificador, optimización luz, cosecha. Registro en GaiaChain.
- **`castua/processing.py`**: `CannabisProcessor` — biomasa → fibra 50 %, CBD 5 %, semillas 2 %, residuos 43 %; residuos → biogás/compost; venta de productos; créditos Verra.
- **`castua/cloud_integration.py`**: `CastuaCloudIntegration` — sincronización con CASTUO Cloud 5.0 (Edge, Sentinel, EnergyManager), GaiaChain.
- **`castua/materials_integration.py`**: `CastuaMaterialsIntegration` — producción de materiales compuestos desde biomasa, venta de materiales y créditos de carbono (España/UE).

### 2. CASTUO Cloud 5.0

- **`castuo/cloud/edge.py`**: `EdgeNode` — procesamiento en borde, baja latencia, 72 h offline.
- **`castuo/cloud/sentinel.py`**: `SentinelSecurity` — detección de anomalías (temperatura, humedad, seguridad), alineado eIDAS/GDPR/AI Act.
- **`castuo/cloud/energy.py`**: `EnergyManager` — microred, batería, solar, venta de excedentes (mercado español/UE).

### 3. Blockchain

- **`blockchain/gaia_chain.py`**: `GaiaChainClient` — registro de acciones, cosechas, procesamiento, residuos, ventas, sensores, anomalías, energía, materiales, cumplimiento RD 903/2025.

### 4. Cumplimiento (España)

- **`compliance/aemps_compliance.py`**: `AEMPSCompliance` — solicitudes investigación/médico, documentos (solicitud, proyecto, plan de seguridad), envío simulado AEMPS.
- **`compliance/rd903_compliance.py`**: `RD903Compliance` — requisitos seguridad física/digital, trazabilidad (GaiaChain), control calidad (THC < 0,2 %), informes, registro de lotes.

## Uso rápido

```python
# Hidroponía + agrovoltaica
from castua import CannabisHydroponicSystem, AgrovoltaicSystem
sistema = CannabisHydroponicSystem("INV-EXT-001")
sistema.add_tower("T1", plants=150)
sistema.update_sensor_data("temperature", 28.5)
yield_data = sistema.harvest("T1")

# Procesamiento y economía circular
from castua import CannabisProcessor
proc = CannabisProcessor()
proc.process_harvest(yield_data)
proc.process_waste(100)  # kg residuos → biogás + compost

# Integración Cloud 5.0
from castua import CastuaCloudIntegration
cloud = CastuaCloudIntegration("INV-EXT-001")
cloud.sync_sensor_data({"temperature": 25, "humidity": 60})
cloud.optimize_energy_use()

# Materiales y carbono
from castua import CastuaMaterialsIntegration
mat = CastuaMaterialsIntegration()
result = mat.produce_materials(500)  # kg biomasa → compuesto + créditos
mat.sell_carbon_credits(result["carbon_credits_kg"], buyer_id="B-001", price_per_ton=70)

# Cumplimiento AEMPS y RD 903/2025
from compliance import AEMPSCompliance, RD903Compliance
aemps = AEMPSCompliance()
solicitud = aemps.prepare_investigation_application(project_data)
respuesta = aemps.submit_application(solicitud)

rd903 = RD903Compliance()
report = rd903.generate_compliance_report(facility_data, production_data)
reg = rd903.register_production_batch(batch_data)  # THC < 0,2 %
```

## Proyecciones y hitos (resumen)

- **2026**: MVP Cloud 5.0, 1 invernadero agrovoltaico, primera cosecha, trazabilidad GaiaChain.
- **2027**: 5 invernaderos, planta materiales, certificaciones, primera venta materiales.
- **2028-2029**: Escalado nacional (España/Portugal), 50 invernaderos, mercado de carbono.
- **2030+**: Expansión UE, 5.000 granjas, salida estratégica (IPO BME Growth / adquisición).

Valoración orientativa (DCF + comparables): **80–100 M€** (2026–2030).
