# Seguridad (bloque educativo) — offline-first

Estas utilidades priorizan:

- **mínima dependencia** (funciona sin red)
- **resiliencia** (si falta una librería, falla con mensaje claro)
- **integridad** (hashes reproducibles)

## Scripts

- `encriptar_aes_gcm.py` — cifrado simétrico AES-GCM (requiere `cryptography`, opcional).
- `validar_integridad.py` — genera y verifica hashes SHA-256 de rutas críticas.

