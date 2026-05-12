# CASTÚO Dashboard v1.7.5

- **http://localhost:3000** → Frontend (Next.js 14 + Tailwind cuando se migre; actualmente `public/` estático + extremadura-dashboard React CRA)
- **CSP headers** implementados (ISO 27001 A.14.2.5): ver `next.config.js` para cuando se use Next.js; en CRA/estático configurar en nginx/Traefik o meta en index.html
- **API:** http://localhost:8000/docs (Swagger Consent API)

## Servir en local

```bash
cd frontend/public/
npx serve -p 3000
```

Abrir: http://localhost:3000

## Dashboards

| Ruta | Descripción |
|------|-------------|
| frontend/public/ | HTML estático (Tailwind) |
| frontend/extremadura-dashboard/ | React CRA — ConsentManager, AuditTrail |
| frontend/verification-dashboard/ | Verificación licencias |
| frontend/marketplace/ | Marketplace carbono |
