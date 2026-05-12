# Workflow "Zero-Leak" (Encrypt & Forward) — V2 TRL9

Objetivo: que el flujo n8n procese telemetría (llega por MQTT local), limpie datos sensibles, cifre con el backend (`POST /encrypt`) y solo envíe **ciphertext** hacia la salida configurada.

---

## Archivo canónico del workflow

- `n8n/workflows/zero_leak_encrypt_forward_v2.json`

---

## Invariantes TRL9 aplicadas

- **Cifrado real**: usa endpoint local del backend `http://api:8000/encrypt`.
- **Salida segura**: antes de cualquier salida externa, el payload se transforma en `ciphertext_json`.
- **Modo Isla (heurístico)**: incluye nodos con `try-catch` (TRL9) que pueden activar `tierra_firme_alert_activado` ante fallos del envío.
- **Feedback Loop**: publica métricas de eficiencia por MQTT a `sabionda/telemetry_anon` de forma continua (también en contingencia).

---

## Parámetros de ejecución

El workflow requiere:

1. **Entrada MQTT**
   - Topic esperado: `biohub/telemetry`
   - Broker (por defecto en el JSON): `mqtt://mqtt:1883`

2. **Salida externa (configurable por entorno)**
- Variable de entorno: `ZERO_LEAK_OUT_URL`

Para V2 además:
- Variable de entorno: `N8N_ADMIN_JWT` (Bearer) para firmar PQC y registrar/auditar eventos en endpoints locales.
- Variables de entorno de endpoints (para adaptar despliegues):
  - `CASTUO_ENCRYPT_URL` (default: `http://api:8000/encrypt`)
  - `CASTUO_PQC_SIGN_URL` (default: `http://api:8000/api/admin/pqc/sign`)
  - `CASTUO_AUDIT_REGISTER_URL` (default: `http://api:8000/api/audit/register-event`)
  - `CASTUO_COMPLIANCE_LATEST_URL` (default: `http://api:8000/api/compliance/audit/latest?tokenId=0`)
   - Debe ser un endpoint HTTPS/HTTP externo al que enviar el ciphertext (sin texto en claro).

Ejemplo (en el contenedor n8n o en variables del sistema):

```text
ZERO_LEAK_OUT_URL=https://app.socios.tld/ingest-ciphertext
```

---

## Qué se cifra (data mínimo)

El nodo `ZeroLeak_Sanitize_MinData` reduce el payload a:

- `hydrogen_pressure_bar`
- `biomass_reserve_pct`
- `ph` (si existe)
- `ec_ms_cm` (si existe)
- `timestamp`

---

## Nota operativa

Si el envío externo falla, el flujo puede activar la contingencia y publica:

- `tierra-firme/alert` (MQTT)

