# Guía OAuth 2.0 — Autenticación para Terceros (Distribuidores UE)

**Objetivo**: Autenticación segura para APIs externas (distribuidores, integradores). 100% de APIs externas con OAuth 2.0.

---

## Implementación

- **Biblioteca**: Authlib (Python) para servidor de autorización y recursos.
- **Flujos**: Authorization Code + PKCE para clientes públicos (SPA, móvil).
- **Tokens**: JWT o tokens opacos; refresh tokens con rotación.

---

## Roles

- **Resource Owner**: Usuario final (ej. técnico del distribuidor).
- **Client**: Aplicación del distribuidor (registrada con client_id/client_secret).
- **Authorization Server**: CASTÚO (endpoints /oauth/authorize, /oauth/token).
- **Resource Server**: API CASTÚO (validar access_token en cada petición).

---

## Validación

- Probar con OAuth.com o herramienta equivalente.
- Documentar en OpenAPI los flujos y scopes (ej. `read:batches`, `write:certifications`).
