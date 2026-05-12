# Roadmap — Mistral-CASTÚO Adapter

Próximos pasos del adapter y compatibilidad con el ecosistema CASTÚO y GaiaChain 2.0.

---

## Corto plazo

| Objetivo | Descripción |
|----------|-------------|
| **Integración GaiaChain 2.0** | Envío real de hashes de transacciones a la API de GaiaChain 2.0 (actualmente solo logging local). |
| **Streaming de respuestas** | Soporte de `stream=True` en `query()` para respuestas token a token. |
| **Más regiones** | Perfiles de cumplimiento para USA (CCPA, Farm Bill), LATAM (LGPD, Lei Agro), Asia (PIPL). |

---

## Medio plazo

| Objetivo | Descripción |
|----------|-------------|
| **OAuth2** | Autenticación con OAuth2 además de API Key, para entornos enterprise. |
| **Validación de esquemas** | Esquemas JSON/CSV configurables por tipo de dataset (sensores, parcelas, etc.) y validación automática. |
| **Sabionda Educa** | Plantillas de proyectos y ejercicios listos para aula (Jupyter, scripts por región). |

---

## Largo plazo

| Objetivo | Descripción |
|----------|-------------|
| **GaiaChain 2.0 nativo** | SDK o cliente específico para registrar cada llamada Mistral como transacción inmutable. |
| **Cifrado post-cuántico** | Opción de encapsulado de claves con Kyber (ML-KEM) para datos en reposo/tránsito. |
| **Compatibilidad PAC 2040** | Reglas de cumplimiento agrovoltaico (superficies, elegibilidad) integradas en el adapter. |

---

## Compatibilidad

- **Mistral API:** v1 (chat/completions). Se seguirá la evolución de la API oficial.
- **CASTÚO-SYSTEM:** adapter alineado con la API principal y con el módulo de behavioral auth cuando aplique.
- **GaiaChain 2.0:** diseño preparado para registrar transacciones; integración real según disponibilidad del backend.
