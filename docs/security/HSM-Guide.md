# Guía HSM — Hardware Security Module (Thales / AWS CloudHSM)

**Objetivo**: 100% de claves críticas almacenadas en HSM (GaiaChain, API keys, cifrado de datos).

---

## Opciones

- **Thales**: HSM on-premise o cloud.
- **AWS CloudHSM**: HSM gestionado en AWS (útil si parte de la infra está en AWS).

---

## Migración

- Inventariar claves actuales (GaiaChain, TLS, cifrado BD, secretos API).
- Migración gradual: primero claves de blockchain y firma, luego resto.
- No dejar claves críticas en variables de entorno o archivos en disco.

---

## Métrica de éxito

- **100%** de claves críticas en HSM.
- Documentar procedimientos de rotación y recuperación.
