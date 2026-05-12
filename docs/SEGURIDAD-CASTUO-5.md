# Sistema de Protección y Encriptación CASTUO 5.0

Arquitectura de seguridad en capas (defensa en profundidad) para el ecosistema CASTUO, alineada con **NIST**, **ISO 27001**, **eIDAS** y **GDPR**.

## Capas de seguridad

| Capa | Componente | Ubicación | Normativa |
|------|------------|-----------|-----------|
| 1. Física | Control de acceso biométrico, alarma, registro en GaiaChain | `security/physical_access.py` | EN 50131, ISO 28000, UNE 104008 |
| 2. Red | Firewall default-deny, IDS Suricata | `security/firewall_rules.sh`, `security/suricata_rules.yaml` | ISO 27033, NIST SP 800-41, ETSI EN 303 645 |
| 3. Datos | AES-256-GCM, TPM 2.0 opcional, masking GDPR | `security/data_encryption.py`, `security/data_masking.py` | GDPR Art. 32, ISO 27040, eIDAS |
| 4. Post-cuántica | Kyber (KEM), Dilithium (firmas) | `security/post_quantum.py`, `security/post_quantum_signatures.py` | NIST SP 800-208, ETSI QSCD |
| 5. Blockchain | Trazabilidad cáñamo, ZKP, Verra + GaiaChain | `blockchain/gaia_chain.py`, `blockchain/verra_integration.py`, `blockchain/chaincode/hemp_traceability.go` | eIDAS, ISO 22301 |
| 6. Ciberfísica | IDS/EDR Sentinel v5 | `security/sentinel_ids.py`, `security/sentinel_edr.py` | ISO 27033, NIST SP 800-94 |

## Refuerzo crítico (plan de mejora)

- **MFA físico (YubiKey + huella + PIN)**: `PhysicalMFA()` — `authenticate_user(user_id, yubikey_otp, fingerprint_data, pin)`. Tras 3 fallos se bloquea y se registra en GaiaChain. Variables: `YUBICO_API_ID`, `YUBICO_API_KEY`.
- **Sensores sísmicos**: `SeismicSensor(gpio_pin, threshold).monitor()` — detección de excavaciones/túneles; alertas y normalización en GaiaChain (`log_security_alert`, `log_security_event`).
- **Cifrado homomórfico**: `HomomorphicEncryption()` — `encrypt_data`/`decrypt_data`, `process_production_data`, `analyze_encrypted_data`. Opcional: Microsoft SEAL (pyseal); sin SEAL se usa stub.
- **Tokenización GDPR**: `DataTokenization()` — `generate_token`, `detokenize`, `tokenize_document`, `detokenize_document`; auditoría en GaiaChain.
- **Detección APT**: `APTDetector()` — `update_threat_intel`, `scan_system` (Velociraptor), `monitor_continuously`. Alertas en GaiaChain.
- **Segmentación IoT**: políticas Cilium en `security/iot_network_policy.yaml` (sensores → gateway → backend).
- **Academy**: `academy.CastuaLMS(moodle_url, token)` — `enroll_user`, `complete_module`, `issue_certificate`, `verify_certificate`; eventos y certificados en GaiaChain. Programa de certificación: `docs/CERTIFICACION-SEGURIDAD-CASTUO.md`.

## Protocolos para Menores

Matriz canonica de validacion por edad, tiempos de sesion, privacidad y trazabilidad educativa (ASCII):

- [`docs/ops/kids/validacion-por-edad-y-nivel-educativo-2026.md`](ops/kids/validacion-por-edad-y-nivel-educativo-2026.md)
- Punto de entrada: [`docs/ops/kids/README.md`](ops/kids/README.md)

Enlace cruzado al bloque educativo maestro:

- [`docs/lengua-comun/PRONT-MAESTRO-FINAL-SISTEMA-ACCION-EDUCATIVA-SABIONDA-OMEGA-2040.md`](lengua-comun/PRONT-MAESTRO-FINAL-SISTEMA-ACCION-EDUCATIVA-SABIONDA-OMEGA-2040.md) (seccion **Bloque Educativo: Validacion por Edad y Nivel**)

## Uso rápido

- **Cifrado de datos**: `DataEncryption().encrypt_data(plaintext, key)` / `decrypt_data(ciphertext, key)` con clave derivada por `generate_key(password, salt)`.
- **Enmascaramiento GDPR**: `DataMasking().mask_sensitive_data(text_or_dict)` y `anonymize_dataset(list_of_dicts)`.
- **Control de acceso físico**: `PhysicalAccessControl()` — en Raspberry Pi con RPi.GPIO; en otros entornos modo simulación. `grant_access(user, level)` registra en GaiaChain.
- **Post-cuántico**: `generate_kyber_keypair()`, `encrypt_with_kyber(pk, msg)`, `decrypt_with_kyber(sk, ct_kem, ct_aes)`. Firmas: `generate_dilithium_keypair()`, `sign_message(sk, msg)`, `verify_signature(pk, msg, sig)`. Requiere `liboqs` (opcional; sin él se usan stubs).
- **Sentinel IDS**: `SentinelIDS().monitor_system()` — monitoreo continuo de CPU, procesos y conexiones; alertas a GaiaChain.
- **Sentinel EDR**: `SentinelEDR(watch_root, quarantine_dir).monitor_file_changes()` — detección de cambios de archivos y cuarentena.

## Dependencias opcionales

- **RPi.GPIO**: solo para control de acceso físico en Raspberry Pi.
- **tpm2_pytss**: sellado de claves en TPM 2.0.
- **liboqs** (Python `oqs`): Kyber y Dilithium reales; sin él se usan stubs.
- **faker**: anonimización con datos realistas (es_ES).

## Firewall e IDS

- Aplicar reglas: `sudo bash security/firewall_rules.sh` (ajustar redes antes).
- Reglas Suricata en `security/suricata_rules.yaml` (formato de referencia; adaptar al formato nativo de Suricata en producción).

## Blockchain y Verra

- GaiaChain: `log_physical_access`, `log_security_alert`, `register_verra_project`, `register_verra_report`.
- Chaincode Go para trazabilidad de cáñamo (RD 903/2025): `blockchain/chaincode/hemp_traceability.go` (Hyperledger Fabric 2.x).
