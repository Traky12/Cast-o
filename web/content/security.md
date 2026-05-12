# Seguridad en capas (referencia Castúo)

1. **Borde**: TLS, WAF, rate limit y geo según política real — ver `.cursor/security/network_rules.json` como plantilla de intención.
2. **Aplicación**: validación de esquemas en API y webhooks; n8n con secretos en credenciales, no en JSON exportado.
3. **Datos**: cifrado autenticado (`scripts/crypto/quantum_encrypt.py`); Kyber768 vía `oqs` cuando el runtime lo tenga.
4. **Auditoría**: endpoints propios (`GAIACHAIN_*` en n8n) con contrato HTTP explícito; no asumir consenso BFT sin backend real.

Para el panel HTML de agentes: `frontend/public/sabionda-n8n-agents-dashboard.html` y la sección *api/query* en `docs/architecture/SABIONDA-N8N-WEB-FRONTEND.md`.
