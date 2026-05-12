# Implementación del Módulo de Privacidad y Endpoint FastAPI

Integración del derecho al olvido (GDPR Art. 17) en el dashboard y backend.

---

## 1. Endpoint FastAPI

**Ubicación:** [api/main.py](../../api/main.py)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/property/{token_id}` | Datos de la propiedad para el dashboard (parcelaId, area, certifications, owner, ipfsHash). |
| `POST` | `/api/privacy/request-erasure` | Ejercicio del derecho al olvido. Body: `token_id`, `wallet_address`, `email` (opcional). |
| `GET` | `/certificates/{cert_id}.pdf` | Descarga del certificado de borrado en PDF. |

**CORS:** Se permiten `http://localhost:3000` y `https://dashboard.juntaextremadura.es` (configurable con `CORS_ORIGINS`).

**Variables de entorno:**

- `FOREST_OWNERSHIP_TOKEN_ADDRESS` — Dirección del contrato ForestOwnershipToken en GaiaChain.
- `JUNTA_PRIVATE_KEY` o `PRIVATE_KEY` — Clave para firmar `updateMetadata`.
- `GAIA_CHAIN_RPC` — RPC de GaiaChain (opcional).
- `SMTP_PASSWORD`, `SMTP_HOST`, `SMTP_FROM` — Opcionales, para envío de email de confirmación.

---

## 2. Servicios de privacidad

**Ubicación:** [api/services/privacy_service.py](../../api/services/privacy_service.py)

- **verify_identity(wallet_address, token_id):** Comprueba que la wallet sea `ownerOf(token_id)`.
- **erase_personal_data(token_id):** Obtiene metadatos del contrato/IPFS, elimina Propietario/DNI/Email, sube nuevo JSON a IPFS.
- **update_metadata_in_blockchain(token_id, new_ipfs_hash):** Llama a `ForestOwnershipToken.updateMetadata`.
- **generate_erasure_certificate(...):** Genera PDF con ReportLab en `api/certificates/`.
- **send_erasure_confirmation_email(email, certificate, tx_hash):** Envía email con certificado adjunto si SMTP está configurado.

---

## 3. Dashboard (React)

- **Rutas:** `/` (Dashboard), `/privacidad` (PrivacyModule).
- **Componentes:** [Dashboard.js](../../frontend/extremadura-dashboard/src/components/Dashboard.js), [PrivacyModule.js](../../frontend/extremadura-dashboard/src/components/PrivacyModule.js).
- **Estilos:** [PrivacyModule.css](../../frontend/extremadura-dashboard/src/components/PrivacyModule.css).
- El módulo de privacidad carga la propiedad vía `GET /api/property/{token_id}` o, si falla, desde el contrato con Web3. Envía la solicitud con `POST /api/privacy/request-erasure` y muestra `request_id`, `transaction_hash`, enlace al certificado y botón de descarga.

---

## 4. Registro de actividad (GDPR Art. 30)

Plantilla de registro por cada solicitud de derecho al olvido:

```json
{
  "solicitud_id": "REQ-20260415100001",
  "fecha": "2026-04-15T10:00:00Z",
  "token_id": 1,
  "wallet_address": "0x7A...1234",
  "accion": "derecho_al_olvido",
  "estado": "completado",
  "old_ipfs_hash": "QmOldHash123...",
  "new_ipfs_hash": "QmNewHash456...",
  "campos_borrados": ["Propietario", "DNI", "Email"],
  "transaccion_gaiachain": "0x789abc123...",
  "certificado_pdf": "certificates/CERT-20260415100001.pdf",
  "responsable": "Gregorio Jiménez Bodes",
  "firma_digital": "0x123...456"
}
```

En producción, este registro debe generarse en cada llamada a `request-erasure` y almacenarse en un log o base de datos con control de acceso (DPO).

---

## 5. Cumplimiento legal

- **Art. 17 GDPR:** Procedimiento técnico implementado (borrado selectivo en metadatos, actualización en blockchain, certificado).
- **Art. 30 GDPR:** Registro de actividades de tratamiento mediante la plantilla anterior (y logs del servidor).
- **ISO 27001 (A.18.1.4):** Borrado seguro vía nuevo contenido IPFS y actualización on-chain; certificado como prueba.

**Documentos de referencia:** [ANEXO_VII_DERECHO_AL_OLVIDO.md](ANEXO_VII_DERECHO_AL_OLVIDO.md), [ANEXO_VI_DERECHO_AL_OLVIDO.md](ANEXO_VI_DERECHO_AL_OLVIDO.md).

---

## 6. Próximos pasos

1. **Desplegar el backend:**  
   `uvicorn api.main:app --host 0.0.0.0 --port 8000`  
   (En producción, usar SSL: `--ssl-keyfile key.pem --ssl-certfile cert.pem`.)

2. **Construir el frontend:**  
   `cd frontend/extremadura-dashboard && npm install && npm run build`

3. **Probar el flujo:**  
   Acceder a `https://dashboard.juntaextremadura.es/privacidad` (o `http://localhost:3000/privacidad`), seleccionar token, ejercer derecho al olvido y descargar el certificado.

4. **Registrar la actividad** en el log de cumplimiento GDPR para cada solicitud (ver §4).

---

[← Documentación final de envío](DOCUMENTACION_FINAL_ENVIO_JUNTA.md) · [Anexo VII Derecho al olvido](ANEXO_VII_DERECHO_AL_OLVIDO.md)
