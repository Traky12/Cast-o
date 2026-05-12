# Política de seguridad (CASTÚO-SYSTEM / n8n)

## Credenciales

- No versionar API keys ni contraseñas en Git. Los archivos `.env*` reales están en `.gitignore`.
- En n8n, preferir **Credentials** (Header Auth, OAuth2, Postgres, Slack) frente a variables de entorno para secretos.
- Rotar claves según [docs/deploy/POLITICA-ROTACION-CLAVES.md](deploy/POLITICA-ROTACION-CLAVES.md) (u operativa interna); periodo orientativo 90 días para APIs de terceros salvo proveedor exija otro ciclo.
- Para datos criptográficos de alto valor, valorar HSM o gestor de secretos (Vault, cloud KMS) alineado a DPIA.

## Red y exposición

- Restringir acceso a la UI y webhooks de n8n (VPN, allowlist de IPs de administración, o reglas en el WAF/reverse proxy).
- No confiar en rangos IP “genéricos de la UE” en configuración nginx: la geolocalización por IP es aproximada y los prefijos no se mapean a fronteras políticas. Usar lista explícita de CIDR de vuestras sedes/proveedores o control en CDN/WAF con política documentada.
- TLS 1.2+ en borde; TLS 1.3 recomendado. HSTS cuando el dominio sea estable.

## Auditoría

- Registrar operaciones relevantes en `castuo_prod_log_auditoria` (o equivalente), sin volcar datos personales innecesarios.
- Campos típicos: timestamp, workflow, acción, tabla/recurso, hash de payload, estado.

Ejemplo de registro (ilustrativo):

```json
{
  "timestamp": "2026-03-28T12:00:00Z",
  "workflow": "Guardar Cosechas",
  "user": "sistema",
  "action": "insert",
  "table": "castuo_prod_cosechas",
  "data_hash": "…",
  "status": "success"
}
```

## Copias de seguridad

- Incluir volumen de datos de n8n y base de datos de aplicación.
- Cifrado en reposo y ubicación acorde a soberanía/datos personales (evaluación RGPD).

## Cumplimiento

- AI Act, RGPD y eIDAS: mantener DPIA y registro de actividades actualizados; trazabilidad no sustituye base legal ni minimización de datos.
