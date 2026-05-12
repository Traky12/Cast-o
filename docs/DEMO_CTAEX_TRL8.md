# CASTÚO-SYSTEM TRL8 — Demo CTAEX
## ISO 27001: 92% | 0 Críticas | 4 PQC Keys

---

## Demo 10 minutos

### 1. Descomprimir pen D:

```cmd
REM Windows: Expand-Archive o 7-Zip
powershell -Command "Expand-Archive -Path 'D:\CASTUO-SYSTEM_TRL8_20260316.zip' -DestinationPath 'D:\CASTUO_TRL8' -Force"
REM O con 7-Zip: "C:\Program Files\7-Zip\7z.exe" x D:\CASTUO-SYSTEM_TRL8_20260316.zip -oD:\CASTUO_TRL8
```

En Linux/Mac:

```bash
unzip D:\CASTUO-SYSTEM_TRL8_20260316.zip -d /tmp/CASTUO_TRL8
```

### 2. Deploy LIVE (1 comando)

```cmd
cd D:\CASTUO_TRL8\deployment
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

O desde la raíz descomprimida:

```cmd
cd D:\CASTUO_TRL8
docker-compose -f deployment\docker-compose.staging.yml up -d
```

### 3. Demo URLs (abrir en navegadores)

| URL | Descripción |
|-----|-------------|
| http://localhost:8000/docs | Backend Swagger — API Consent + admin/emergency |
| http://localhost:3000 | Frontend Dashboard TRL8 |
| http://localhost:8200/ui | Vault HSM — Kyber-768 keys |
| http://localhost:8080 | OWASP ZAP — 0 críticas |

### 4. Pasos demo CTAEX

1. **localhost:8000/docs** → Backend Swagger LIVE — probar GET /api/health, rotation-status.
2. **localhost:3000** → Dashboard TRL8 (si el frontend está servido).
3. **localhost:8200/ui** → Vault Kyber-768 LIVE — estado unsealed, claves Transit.

---

## Métricas

- **92%** ISO 27001:2022 | Stage 1 → 5 mayo 2026
- **4 claves** PQC Kyber-768 rotando (30d)
- **Emergency seal** ejecutado 19:14 CET (evidencia en emergency_demo.png)
- **0 vulnerabilidades** OWASP ZAP
