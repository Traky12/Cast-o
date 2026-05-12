# Plano de Reconstrucción — Setup Composer (CASTUO Cloud 5.PRO)

Manifiesto de integridad entre **ADN digital (Git)** y **activos industriales (ZIP)**. Sin validación de checksums, el arranque medido no alcanza estado **TRUSTED**.

---

## Objetivo

1. Verificar que los binarios del ZIP no han sido alterados (SHA-256).
2. Inyectar secretos HSM solo en RAM (p. ej. desde `.pem` del ZIP, nunca commitados).
3. Bloquear **riego agresivo** y **minado BioCoin** si el entorno no es de confianza.

---

## Validación de integridad (pre-vuelo)

Antes de levantar la API, el orquestador debe validar los hashes de los activos industriales:

| Activo | Ruta en ZIP | SHA-256 esperado |
| :----- | :---------- | :--------------- |
| Modelo IA | `02_Inteligencia_IA_Soberana/Mistral8x7B_Rural_LoRA.bin` | *(ver `config/industrial_manifest.json`)* |
| Código QAOA empaquetado | `03_Optimizador_Cuantico_QAOA/qaoa_optimizer_v5.py` | *(manifest)* |
| CA raíz / HSM | `07_Certificaciones_y_Legal/root_ca.pem` | *(manifest)* |

**Generar manifiesto a partir de un ZIP oficial:**

```bash
python scripts/rebuild_system.py --zip-path ./CASTUO_industrial_v5.zip --generate-manifest > config/industrial_manifest.json
```

**Reconstrucción / verificación pre-arranque:**

```bash
python scripts/rebuild_system.py --zip-path /mnt/castuo_industrial_v5.zip --manifest config/industrial_manifest.json
```

Código de salida `0` = todos los hashes coinciden. Cualquier divergencia → **no iniciar** `uvicorn` ni mint BioCoin.

---

## Arranque medido (Measured Boot)

- **`backend/security/trust_orchestrator.py`** — `TrustOrchestrator`: registra cada módulo verificado; `secure_token_minting()` exige **todos** `True`.
- Variable **`CASTUO_MEASURED_BOOT=1`**: si está activa, rutas críticas pueden exigir `trust_orchestrator.trusted_environment`.

---

## WORM, E2EE y soberanía

- **Logs Anexo C (Jara):** volumen **WORM** (write-once); alteración de huella CO₂ rompe cadena Merkle documentada.
- **QuestDB / FIWARE:** tráfico **TLS** + claves del material industrial (inyectadas, no en Git).
- **`HSM_SLOT`:** solo `os.getenv`; valor real inyectado en runtime desde ZIP seguro.

Ver también: `docs/biocoin/REGULATORY-MICA-REACH.md`, `docs/SOBERANIA-TECNOLOGICA.md`.

---

## Pruebas de ciber-resiliencia (CI)

| Prueba | Descripción |
|--------|-------------|
| **Tamper-Evidence** | Un bit cambiado en activo del ZIP → verificación falla → BioCoinVault bloqueado vía Trust. |
| **Quantum-Safe Handshake** | Comprobar disponibilidad de capa PQC (Kyber/Dilithium) en `backend/security/pq_crypto.py` para handshakes sensibles. |
| **Circuit Breaker Químico** | Ozono confianza baja + IP no allowlist → cierre lógico permanente del sector riego (fail-safe). |

```bash
pytest tests/test_trust_resilience.py -v
```

---

## Referencias cruzadas

- `docs/README_MAESTRO.md`
- `docs/COMPLIANCE-BIOJARA-5PRO.md`
- `config/industrial_manifest.example.json`
