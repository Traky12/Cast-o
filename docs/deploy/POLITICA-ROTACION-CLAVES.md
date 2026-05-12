# Política — rotación de claves y certificados (plantilla)

**Relación:** [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md) · [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md)

Completar con **responsable**, **calendario** y **canal de escalado**. No pegar secretos en este archivo.

*Orientación alineada a staging:* puede acordarse una **revisión trimestral** de certificados y secretos de **laboratorio** antes de promover cambios a producción — fijar fechas en tabla inferior.

## 1. Alcance

| Activo | Rotación sugerida *(ajustar)* | Método |
|--------|------------------------------|--------|
| Certificados TLS públicos | Según CA (p. ej. ≤ 90 días ACME) | Renovación automatizada + verificación |
| Certificados internos/mTLS | Política interna (p. ej. 12 meses) | PKI interna o Vault PKI |
| Tokens Bearer (admin, lab) | Tras incidente o calendario | Regenerar + actualizar Vault/`*_FILE` |
| `ADMIN_MASTER_KEY` | Alto impacto — solo con plan de re-cifrado | Procedimiento escrito + ventana |
| Claves cadena / RPC | Según operación y compromiso | Vault KV + rotación documentada |

## 2. Procedimiento genérico

1. Generar nuevo secreto en entorno seguro.  
2. Desplegar en Vault o secret store; actualizar servicios (rolling).  
3. Verificar health checks y métricas.  
4. Revocar valor antiguo tras ventana acordada.  
5. Registrar en ticket: fecha, actor, alcance.

## 3. Excepciones e incidentes

- **Compromiso:** rotación **inmediata** de todo lo afectado; revisión de logs.  
- **Dependencias cruzadas:** orden documentado (p. ej. DB antes que workers).

## 4. Revisión

- Revisar esta política al menos **anualmente** o tras cambio de proveedor cloud.

---

*Rotar sin runbook es cambiar la cerradura dejando la copia bajo el felpudo.*
