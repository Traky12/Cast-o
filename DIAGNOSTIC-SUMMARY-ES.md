# DIAGNÓSTICO PROFUNDO DE TESTS FALLANDO — CASTÚO-SYSTEM

## 📊 ESTADO ACTUAL (2026-04-04)

| Métrica | Valor |
|---------|-------|
| **Tests Totales** | 428 |
| **Pasando** | 425 (99.3%) |
| **Fallando** | 3 (0.7%) |
| **Tiempo Ejecución Suite** | 83.76s |

---

## ❌ LOS 3 TESTS FALLANDO

### Archivo: `tests/test_greenhouse_advanced_capture.py`

| Test | Endpoint Esperado | Error | Causa |
|------|-------------------|-------|-------|
| `test_register_holography_capture` | `POST /api/v1/greenhouse/{id}/holography/register` | 404 Not Found | Endpoint no existe en router |
| `test_register_photogrammetry_scan` | `POST /api/v1/greenhouse/{id}/photogrammetry/register` | 404 Not Found | Endpoint no existe en router |
| `test_digital_twin_status_includes_3d_systems` | `GET /api/v1/greenhouse/{id}/digital-twin/status` | 404 Not Found | Endpoint no existe en router |

---

## 🔍 ANÁLISIS PROFUNDO

### Causa Raíz Identificada

**Tipo**: Feature Scope Gap en Approach Test-Driven Development

**Historia**:
1. Requisitos: "Se necesita digital twin con captura 3D de prototipos"
2. Tests escritos PRIMERO como especificación: `test_greenhouse_advanced_capture.py` (correcto TDD)
3. Tests definen exactamente qué endpoints, qué payloads, qué respuestas esperados
4. Router `greenhouse.py` comenzó con 9 endpoints (telemetría, estado, alertas, etc.)
5. **Brecha**: Los 3 nuevos endpoints para captura 3D no fueron completados

### ¿Por qué no causa CRISIS?

✅ Los 3 endpoints faltantes son **OPCIONALMENTE NUEVA FEATURE**:
- No rompen funcionalidad existente
- No afectan los 425 tests pasando
- Especificación está CLARA en los tests
- No hay ambigüedad sobre qué hacer

---

## ✅ CONFIRMADO: OTROS FEATURES ESTÁN 100% COMPLETOS

### 1️⃣ **test_invernadero.py: 43/43 PASANDO**

Todos los endpoints de invernadero agrovoltaico hidropónico:

```
✅ POST /api/v1/invernadero/lote/apertura
✅ POST /api/v1/invernadero/solucion-nutritiva  
✅ POST /api/v1/invernadero/clima
✅ POST /api/v1/invernadero/agrovoltaico
✅ POST /api/v1/invernadero/cosecha
✅ GET  /api/v1/invernadero/rangos/{cultivo}
✅ POST /api/v1/invernadero/fitosanitario
✅ GET  /api/v1/trazabilidad/qr/evento
✅ POST /api/v1/trazabilidad/qr/generar
✅ GET  /api/v1/trazabilidad/qr/verificar/{lote}/{hash}
+ 5 more sensor/actuator tests
```

**Validaciones que funcionan**:
- pH (5.8-6.3 tomate, 5.5-6.2 lechuga, etc.)
- EC (2.0-4.0 tomate, 0.8-1.6 lechuga, etc.)
- O₂ disuelto (critical < 6.0 mg/L)
- CO₂ (800-1200 ppm tomate)
- VPD (0.8-1.2 kPa tomate)
- DLI (diferente por etapa - floracion vs vegetativo)
- Agrovoltaico (cálculo delta temperatura, balance energético)
- QR traceability (cadena de hashes, consumidor verification)

### 2️⃣ **test_whatsapp_alerts.py: 13/13 PASANDO**

Todos los endpoints de integración WhatsApp:

```
✅ GET  /api/v1/tenants/current (incluye phone)
✅ PUT  /api/v1/tenants/{id}/phone (validación formato +34)
✅ POST DB whatsapp_alert_log (insertar, actualizar delivery_status)
✅ GET  DB system_emergency_contacts
✅ FILE n8n/workflows/thingsdata-whatsapp-alerts.json (existe)
✅ CHECK nodos Twilio presentes
```

**Fixtures COMPLETAS confitest.py**:
```python
@pytest.fixture
def client(app) → TestClient (✅ presente)

@pytest.fixture  
def test_tenant() → Tenant (✅ presente)

@pytest.fixture
def test_tenant_2() → Tenant (✅ presente)

@pytest.fixture
def db_session() → _FakeSession mock completa (✅ presente)
```

### 3️⃣ **+18 routers más: TODO PASANDO**

- `test_audit_trail.py`: 10/10 ✅
- `test_email2ip.py`: 24/24 ✅
- `test_esp32_iot.py`: 34/34 ✅
- `test_blockchain_router.py`: 5/5 ✅
- `test_claude_router.py`: 6/6 ✅
- etc.

---

## 📋 ENDPOINTS FALTANTES: ANÁLISIS DETALLADO

### Endpoint 1: `POST /api/v1/greenhouse/{prototype_id}/holography/register`

**Test Payload**:
```json
{
  "device_id": "holo-p1-cam",
  "resolution": "4k",
  "point_density": 125000.0,
  "coverage_percent": 92.5,
  "operator_id": "ops-01"
}
```

**Test Expects Response** (status 200):
```json
{
  "prototype_id": 1,
  "registered": true,
  "capture": {
    "device_id": "holo-p1-cam",
    "resolution": "4k",
    "point_density": 125000.0,
    "coverage_percent": 92.5,
    "registered_at": "2026-04-04T12:34:56.789Z"
  }
}
```

**Required Models**:
- `HolographyCapture` (Pydantic) — input payload
- `HolographyRegistrationResponse` (Pydantic) — output payload

**Required Logic**:
1. Validate `prototype_id` exists (1 or 2)
2. Extract holography capture data
3. Store in `_PrototypeState.holography_captures` (list)
4. Increment `_PrototypeState.holography_captures_total` counter
5. Return response with `registered: true`

**Lines of Code**: ~15

---

### Endpoint 2: `POST /api/v1/greenhouse/{prototype_id}/photogrammetry/register`

**Test Payload**:
```json
{
  "device_id": "photo-p2-rig",
  "images_count": 96,
  "overlap_percent": 78.0,
  "avg_reprojection_error": 0.42,
  "operator_id": "ops-02"
}
```

**Test Expects Response** (status 200):
```json
{
  "prototype_id": 2,
  "registered": true,
  "capture": {
    "device_id": "photo-p2-rig",
    "images_count": 96,
    "overlap_percent": 78.0,
    "avg_reprojection_error": 0.42,
    "registered_at": "2026-04-04T12:35:00.100Z"
  }
}
```

**Required Models**:
- `PhotogrammetryScan` (Pydantic) — input payload
- `PhotogrammetryRegistrationResponse` (Pydantic) — output payload

**Required Logic**:
1. Validate `prototype_id` exists
2. Extract photogrammetry scan data  
3. Store in `_PrototypeState.photogrammetry_scans` (list)
4. Increment `_PrototypeState.photogrammetry_scans_total` counter
5. Return response with `registered: true`

**Lines of Code**: ~15

---

### Endpoint 3: `GET /api/v1/greenhouse/{prototype_id}/digital-twin/status`

**Test Expects Response** (status 200):
```json
{
  "prototype_id": 1,
  "holography": {
    "captures_total": 1,
    "last_capture_timestamp": "2026-04-04T12:34:56Z",
    "avg_point_density": 120000.0
  },
  "photogrammetry": {
    "captures_total": 1,
    "last_capture_timestamp": "2026-04-04T12:35:00Z",
    "avg_images_count": 80
  },
  "system_ready": true
}
```

**Required Models**:
- `DigitalTwinStatus` (Pydantic) — response structure

**Required Logic**:
1. Validate `prototype_id` exists
2. Query/aggregate holography captures for prototype
3. Query/aggregate photogrammetry scans for prototype
4. Calculate `system_ready = (holography.captures_total >= 1) AND (photogrammetry.captures_total >= 1)`
5. Return aggregated status

**Lines of Code**: ~25

---

## 🛠️ IMPLEMENTATION ROADMAP

### Phase 1: Models & State (20 min)
```python
class HolographyCapture(BaseModel):
    device_id: str
    resolution: str  # "4k", "8k", etc.
    point_density: float  # >= 0
    coverage_percent: float  # 0-100
    operator_id: Optional[str] = None

class PhotogrammetryScan(BaseModel):
    device_id: str
    images_count: int
    overlap_percent: float
    avg_reprojection_error: float
    operator_id: Optional[str] = None

# Extend _PrototypeState:
self.holography_captures: list[dict] = []
self.photogrammetry_scans: list[dict] = []
```

### Phase 2: Route Handlers (45 min)
```python
@router.post("/{prototype_id}/holography/register")
async def register_holography(prototype_id: int, capture: HolographyCapture):
    # Handler logic here
    
@router.post("/{prototype_id}/photogrammetry/register")
async def register_photogrammetry(prototype_id: int, scan: PhotogrammetryScan):
    # Handler logic here

@router.get("/{prototype_id}/digital-twin/status")
async def get_digital_twin_status(prototype_id: int):
    # Handler logic here
```

### Phase 3: Testing & Validation (15 min)
```bash
pytest tests/test_greenhouse_advanced_capture.py -v
# Expected: 3 passed

pytest --tb=short
# Expected: 428 passed, 0 failed
```

---

## 📈 EFFORT ESTIMATION

| Task | Duration | Confidence |
|------|----------|------------|
| Read existing code patterns | 5 min | 100% |
| Add Pydantic models | 20 min | 100% |
| Implement endpoints | 45 min | 95% |
| Test & validation | 15 min | 100% |
| **TOTAL** | **1h 25min** | **97%** |

Buffer for edge cases: +15 min → **1h 40min (1.67 hours)**

---

## 🎯 CRITICAL SUCCESS FACTORS

1. **Specification Is Clear** ✅
   - Tests define exact inputs/outputs
   - No ambiguity
   - Pattern matches existing code

2. **No Dependencies On Missing Code** ✅
   - `_PrototypeState` class exists
   - Response models pattern established  
   - Prototype ID validation already in place

3. **No Breaking Changes** ✅
   - Only adding new endpoints
   - Existing 9 endpoints unaffected
   - 425 tests will still pass

4. **TDD Worked Correctly** ✅
   - Tests CAUGHT the missing feature
   - Specification-first approach working as intended

---

## 📊 RISK ASSESSMENT

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Implementation differs from test spec | LOW (5%) | MEDIUM | Carefully read test assertions |
| Endpoint path collision | LOW (2%) | MEDIUM | Grep for existing routes |
| State management bug | LOW (10%) | HIGH | Test with prototype 1 AND 2 |
| Regression in existing tests | LOW (3%) | HIGH | Run full pytest after changes |

---

## ✅ QUALITY GATES

- [ ] 3 test_greenhouse_advanced_capture.py tests passing
- [ ] 0 new failures in other test suites
- [ ] Final pytest run: 428/428 passed
- [ ] Code review of new handlers
- [ ] Merge to main branch

---

## CONCLUSIÓN

**El proyecto CASTÚO-SYSTEM está en EXCELENTE estado.**

- 99.3% test pass rate (425/428)
- Únicamente falta completar 1 feature specific (3D capture para digital twin)
- Especificación es CLARA (definida en tests)
- Effort es BAJO (1.67 horas)
- Riesgo es BAJO
- Proceso TDD funcionó PERFECTAMENTE

**Recomendación**: PROCEDER inmediatamente con implementación de los 3 endpoints faltantes. Go from 99.3% → 100% test coverage en menos de 2 horas.
