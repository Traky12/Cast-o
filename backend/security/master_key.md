# 🔐 CASTÚO-SYSTEM™ — Clave maestra y defensa en profundidad (EU/OSS)
**Propósito**: Establecer una raíz de confianza operativa sin exponer secretos en `.env`, preservando soberanía y auditabilidad.

## Principios
- **La clave maestra (MK) nunca toca el código**: solo se usa en ceremonia (unseal/derivación) dentro de un gestor de secretos.
- **Derivación por capas**: MK → claves de servicio (cifrado/firma) → secretos operacionales.
- **Menor privilegio**: cada servicio solo accede a lo mínimo que necesita.
- **Evidencia auditable**: toda operación sensible genera trazas verificables (logs + cadena).

## Raíz de confianza (MK)
- **Gestión recomendada**: HashiCorp Vault OSS (auto‑host en UE) con *Shamir 5/3* (o HSM/KMS cuando esté disponible).
- **Custodia**: 5 fragmentos, 3 necesarios. Custodios típicos: DPO, CTO, Seguridad, backup físico, backup institucional.

## Claves derivadas (ejemplo)
- **`K_backend_consent`**: cifra/descifra secretos del micro‑API (rotación 90 días).
- **`K_gaiachain_sign`**: firma transacciones/eventos de auditoría (rotación 30–60 días).
- **`K_media_engine`**: autentica contra “sandbox media” (rotación 90 días).

## Secretos operacionales (NO en claro)
- `PRIVATE_KEY` (GaiaChain / testnet / mainnet)
- `KEYCLOAK_CLIENT_SECRET`
- API keys (IPFS/S3/Media)

## Capas EU/OSS recomendadas
- **Identidad**: Keycloak (OIDC, MFA, roles).
- **Secretos/firma**: Vault OSS (KV + Transit).
- **Perímetro**: Traefik/Nginx (TLS, rate limit, headers).
- **Auditoría/SIEM**: Wazuh + OpenSearch/Loki.

## Desarrollo local (modo seguro)
- Para pruebas locales sin Keycloak operativo, habilitar:
  - `AUTH_DISABLED=true` (solo desarrollo).
  - En producción: **prohibido**.

