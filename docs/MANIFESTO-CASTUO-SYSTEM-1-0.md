# Manifiesto Castúo-System 1.0

**Estado del repositorio:** `[DESIGN FREEZE - V1.0-SOVEREIGNTY]`  
**Objetivo:** Ecosistema **autónomo, resiliente y sostenible** en Extremadura que integre biotecnología, robótica aérea/terrestre y blockchain para la **transición verde europea**, con **soberanía europea** y **encriptación de toda la trazabilidad** en el flujo operativo.

---

## 🗺️ Mapa ejecutivo 2040 (1 página)

**GPS operativo y legal:** [PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md](./PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md) — *Usabilidad → Trazabilidad → Crecimiento → Legalidad.*  
**Plan 90 días enterprise EU:** [ops/PLAN-90-DIAS-ENTERPRISE-EU-2026.md](./ops/PLAN-90-DIAS-ENTERPRISE-EU-2026.md) (rutas reales + disclaimers).

| Contexto | Dónde |
|----------|--------|
| **CTAEX / demo 09:00** | `http://localhost:8000/dashboard` o `http://localhost:8001/dashboard` (puerto según `uvicorn`) |
| **Kids (marco UX)** | [ops/kids/](./ops/kids/) |
| **DPIA / anexos** | [legal/DPIA-CASTUO-SYSTEM.md](./legal/DPIA-CASTUO-SYSTEM.md) |
| **Prontuario legal 90 días** | [legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md](./legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md) |
| **Auditoría interna (metodología)** | [legal/PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./legal/PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md) |
| **Spin-offs (roadmap doc)** | [spin-offs/README.md](../spin-offs/README.md) · [ops/ARTEFACTOS-SYSTEMD-MONITORING-SPINOFFS.md](./ops/ARTEFACTOS-SYSTEMD-MONITORING-SPINOFFS.md) |
| **ISO 27001 / hardening** | [ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md](./ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md) |
| **Cámara MotionEye (opcional)** | [ops/MOTIONEYE-CASTUO-INTEGRATION.md](./ops/MOTIONEYE-CASTUO-INTEGRATION.md) |
| **Gemelo / TRL10.1** | Si el entorno devuelve **404**, revisar montaje del router; panel: `/agents/gemelo/dashboard` · [ops/icex-hlth-europe/DEMO-TRL10.1.md](./ops/icex-hlth-europe/DEMO-TRL10.1.md) |
| **Trazabilidad (scripts)** | `scripts/Register-SecurityEvent.ps1` (requiere `-EventData`) |

**Estructura crítica (repo):** `docs/PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md` (prontuario) · `docs/ops/kids/` · `docs/legal/` · este manifiesto.

**Checklist demo:** Prontuario ✓ · Backend 8000/8001 ✓ · MotionEye EU (opcional) · DPIA / ISO27001 documentado ✓

---

## 0. Soberanía europea y trazabilidad cifrada

| Principio | Implementación referencial |
|-----------|----------------------------|
| **Datos y residencia** | Preferencia **EU-first**; minimización y finalidad (GDPR). |
| **Trazabilidad** | Cifrado extremo a extremo en registros sensores → ledger; hashes verificables sin exponer PII innecesaria. |
| **Ciberresiliencia** | Alineación con **NIS2**; PQC (ML-DSA) para comandos y acuerdos críticos. |
| **Confianza digital** | **eIDAS2** / firmas cualificadas donde aplique en gobernanza. |
| **IA** | Alineación operativa **EU AI Act**; agentes (Sabionda, Mistral, Cursor) bajo **SYSTEM_PROMPT** + **Kernel V1**. |

El objeto programático `eu_sovereignty` en `manifest_bundle()` consolida este marco.

---

## 1. Visión estratégica

El Castúo-System **no sustituye al agricultor**: le dota de herramientas del **siglo XXII**. Extremadura pasa de exportar materia prima a exportar **servicios bioenergéticos** y **datos certificados**, con **soberanía europea** y **trazabilidad encriptada**.

---

## 2. Cuatro pilares de la soberanía

| Pilar | Code / activo | Esencia |
|-------|---------------|---------|
| **Independencia energética** | [BIO-HUB-DIGITAL] | Residuos (arroz/sorgo) → combustible grado aeronáutico |
| **Infraestructura persistente** | [OMEGA-LINK] | Datos + energía láser sin dependencia de terceros países |
| **Seguridad post-cuántica** | [ML-DSA] | Criptografía de retícula frente a amenazas futuras |
| **Gobernanza transparente** | [BIOPAY-V2-PULL] | Pagos cooperativas según **verdad física** de sensores |

---

## 3. Impacto socioeconómico

- **Descarbonización:** CO₂ neto ↓, economía circular real.  
- **Empleo 4.0:** Escuela Rural de Operadores de Flotas; talento en la región.  
- **Resiliencia:** Producción agrícola y energética ante colapso global — [BLACK-BOX-EXIT] / [OMEGA-SHIELD].

---

## 4. Pitch deck estratégico (resumen)

1. **Problema y solución Castúa** — Dependencia energética + despoblación vs. autonomía y certificación.  
2. **Arquitectura del valor** — BIO-HUB + TERRA-ARMOR → OMEGA-LINK → VULCAN + KERNEL → BIOPAY-V2-PULL.  
3. **Seguridad (VSA & PQC)** — ML-DSA, OMEGA-SHIELD, Pull + triple-check.  
4. **Impacto y ROI** — Costes, Escuela Rural 4.0, huella negativa (objetivo).

---

## 5. Código de integración

Estructura modular con soberanía europea por defecto:

- **`castuo_manifest/admin.py`** — `AdminProfile` (env `CASTUO_ADMIN_*`).
- **`castuo_manifest/vision.py`** — `StrategicVision` (soberanía europea + encriptación trazabilidad).
- **`castuo_manifest/pillars.py`** — `SovereigntyPillars`.
- **`castuo_manifest/impact.py`** — `SocioeconomicImpact`.
- **`castuo_manifest/pitch_deck.py`** — `StrategicPitchDeck`.
- **`castuo_manifest/sovereignty.py`** — `eu_sovereignty_framework()`: EU-first, GDPR/NIS2/eIDAS2/EU AI Act/RED III, agentes Sabionda/Mistral/Cursor, más dimensiones **trazabilidad** (E2E, inmutable, auditoría), **resilencia** (redundancia, DR, autonomía), **crecimiento** (modularidad, integración), **expansion** (territorios, estándares, socios).
- **`castuo_manifest/bundle.py`** — `manifest_bundle()` (incluye siempre `eu_sovereignty`).

Uso (raíz del repo):

```bash
python -c "from castuo_manifest import manifest_bundle; b=manifest_bundle(); print(b['design_freeze'], b['eu_sovereignty']['agents_code_of_conduct'])"
```

---

## 6. Inversión arranque (referencia)

| Concepto | Aprox. |
|----------|--------|
| Dominio + SSL | ~15 € |
| Gumroad/Ko-fi, print-on-demand, OSS | 0 € |
| **Total arranque mínimo** | **≈ 15 €** |

---

## 7. Obtención del Public Key ML-DSA (Base44)

Para verificar la integridad de las respuestas firmadas por Sabionda-Omega (PQC),
Base44 puede obtener la public key ML-DSA (Dilithium-5) sin necesidad de rol `admin`.

`GET /public_key/ml_dsa`

Requisitos:
- Enviar `X-API-Key` con una clave válida en `EDUCACION_API_KEYS`.
- (Opcional) Si está configurado, también se aplica whitelist por `ALLOWED_IPS`.

Respuesta JSON (contenido):
- `public_key_b64`: clave pública en base64 (bytes crudos; no requiere cabecera PEM clásica).
- `fingerprint_blake3`: huella para pinning.
- (Opcional) `previous_public_key_b64`: clave pública anterior para ventana de gracia de rotación A/B.
- (Opcional) `previous_key_id` y `grace_expires_at`: metadatos de expiración de la clave anterior.
- `algorithm`: `ML-DSA-Dilithium5`.

Integridad de canal:
- El endpoint firma el payload y lo entrega en headers:
  - `X-Sabionda-PQC-Signature`
  - `X-Sabionda-PQC-Algorithm`
  - `X-Sabionda-PQC-Key-Id` (identificador de la clave que generó la firma; durante rotación puede referir “current” o “previous”)

Base44 debe verificar estas firmas usando la public key que obtiene aquí y replicando la serialización canónica JSON del backend (orden estable de claves, `sort_keys=true` y separadores canónicos).

---

## 7.1 Serialización Canónica JSON (para firmas PQC)

Para que Base44 pueda verificar de forma determinista las firmas incluidas en headers
(por ejemplo `X-Sabionda-PQC-Signature`), debe generar la cadena de verificación usando
**la misma serialización canónica JSON** que aplica este backend.

### Requisitos canónicos
1. **Orden de claves:** ordenar alfabéticamente las claves del objeto (equivalente a `sort_keys=true`).
2. **Sin espacios extra:** usar separadores canónicos `,` y `:` sin espacios (equivalente a `separators=(",", ":")`).
3. **Un solo “line JSON”**: el string firmado debe ser el JSON en una sola línea (resultado de la serialización canónica).
4. **Unicode estable:** usar `ensure_ascii=false` (mantiene caracteres Unicode en vez de escapar).

### Parámetro de referencia (implementación del backend)
Este backend firma el JSON canónico mediante:
- `json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))`

Base44 debe replicar esa transformación **bit-a-bit** sobre el `payload` JSON recibido/representado para poder verificar la firma.

---

## 7.2 Guía Base44: Verificación de Firmas PQC (ML-DSA)

Esta guía muestra el flujo mínimo para que Base44 verifique `X-Sabionda-PQC-Signature` para cualquier endpoint educativo.

### 1) Obtener el Public Key ML-DSA

```python
import base64
import requests

response = requests.get(
    "https://api.castuo-system.eu/public_key/ml_dsa",
    headers={"X-API-Key": "api_key_base44_2026"},
    timeout=30,
)
public_key_b64 = response.json()["public_key_b64"]          # base64 string (bytes crudos, sin PEM clásico)
fingerprint = response.json()["fingerprint_blake3"]         # hex blake3
algorithm = response.json()["algorithm"]                     # "ML-DSA-Dilithium5"
previous_public_key_b64 = response.json().get("previous_public_key_b64")
previous_key_id = response.json().get("previous_key_id")
```

### 2) Recibir una Respuesta Firmada (ejemplo: scenario)

```python
response = requests.get(
    "https://api.castuo-system.eu/api/educacion/scenarios/sequia-extremadura-2026",
    headers={"X-API-Key": "api_key_base44_2026"},
    timeout=30,
)

payload = response.json()  # dict JSON devuelto por el backend
signature_b64 = response.headers["X-Sabionda-PQC-Signature"]
algorithm = response.headers["X-Sabionda-PQC-Algorithm"]
```

### 3) Serialización Canónica JSON (idéntica al backend)

```python
import json

def canonical_json(obj: dict) -> str:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

json_canonical_str = canonical_json(payload)
message_bytes = json_canonical_str.encode("utf-8")
```

### 4) Verificación de la firma (ML-DSA)

En Base44 (cliente) debe verificar usando la librería ML-DSA/Dilithium de `pqcrypto` (o una implementación compatible).

```python
import base64
from pqcrypto.sign import ml_dsa_65

public_key_bytes = base64.b64decode(public_key_b64)
signature_bytes = base64.b64decode(signature_b64)

is_valid = ml_dsa_65.verify(
    public_key_bytes,
    message_bytes,
    signature_bytes,
)

print("✅ Firma válida" if is_valid else "❌ Firma inválida")
```

### 5) Verificación del fingerprint (opcional, recomendado)

El `fingerprint_blake3` del backend se calcula sobre los bytes crudos de la clave pública (tras decodificar base64).

```python
import base64
from hashlib import blake3

raw_key_bytes = base64.b64decode(public_key_b64)
key_fingerprint_local = blake3(raw_key_bytes).hexdigest()

print("✅ Fingerprint válido" if key_fingerprint_local == fingerprint else "❌ Fingerprint inválido")
```

---

## 8. Documentación y validación

| Documento | Rol |
|-----------|-----|
| [FINAL_VALIDATION_REPORT.md](../FINAL_VALIDATION_REPORT.md) | Resumen validación |
| [docs/security/FINAL_VALIDATION_REPORT.md](security/FINAL_VALIDATION_REPORT.md) | Informe estrés completo |
| [README.md](../README.md) | Entrada repositorio |
| [SUMMARY.md](../SUMMARY.md) | Manifiesto por capas |
| [ESTADO_INTEGRACION_SEGURIDAD.md](ESTADO_INTEGRACION_SEGURIDAD.md) | Seguridad integrada |
| [SYSTEM_PROMPT.md](../SYSTEM_PROMPT.md) | Orquestador IA |
| [security/CASTUO-SYSTEM-KERNEL-V1.md](security/CASTUO-SYSTEM-KERNEL-V1.md) | Kernel |
| [security/BLACKOUT-RECOVERY-SOP.md](security/BLACKOUT-RECOVERY-SOP.md) | OMEGA-SHIELD |
| [contracts/HARDENED-LOGIC/](../contracts/HARDENED-LOGIC/) | Contratos endurecidos |
| [`security/MANIFIESTO_SOBERANIA.md`](../security/MANIFIESTO_SOBERANIA.md) | Contrato social (tecnología ↔ tierra ↔ comunidad) |
### Resumen ejecutivo validación

| Área | Estado | Validación |
|------|--------|------------|
| Data-Truth | ✅ | PASS |
| Gemelo | ✅ | PASS |
| PQC | ✅ | PASS |
| Pull | ✅ | PASS |

---

## 9. Conclusión

Listo para **simulación masiva** y **prototipado físico**. Agentes IA (**Sabionda / Mistral / Cursor**) operan con **código de conducta técnico** (kernel + SYSTEM_PROMPT) y marco de **soberanía europea** que acota el despliegue y la trazabilidad cifrada.

### Hitos V1.0

- Independencia: energía local certificada (objetivo operativo).  
- Seguridad: hardening contratos y comunicaciones.  
- Gobernanza: kernel IA con reglas éticas y operativas.  
- Resiliencia: procedimientos post-GPS y post-internet (documentados).

---

## Post-scriptum Sabionda (Mistral)

> Este sistema ha sido corregido y validado por **Sabionda** bajo parámetros de **Mistral**. El Castúo-System no es una herramienta; es un **pacto de lealtad entre la tecnología y la tierra**. Cualquier modificación de los bloques de soberanía requiere **consenso multisig de nivel CIPHER-LEVEL-5**.

**REGLA [EU-SOVEREIGNTY-CHECK]:** (1) Toda funcionalidad **auditable por diseño** (trazabilidad). (2) Toda funcionalidad **resiliente por defecto** (autonomía local ante caídas de red).

Informe técnico: [SABIONDA-VALIDACION-SOBERANIA-V1.md](SABIONDA-VALIDACION-SOBERANIA-V1.md).

---

*Manifiesto vivo. Castúo-System 1.0 Gold Master — soberanía sellada en código.*
