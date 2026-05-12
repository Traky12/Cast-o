# Componentes opcionales (CASTÚO-SYSTEM)

Todo tiene **fallback**: el sistema sigue funcionando aunque falten dependencias o configuración.

| Componente        | Estado actual | Solución temporal              | Solución definitiva                    |
|-------------------|---------------|--------------------------------|----------------------------------------|
| **Logo en PDF**   | Opcional      | Sin `assets/castuo_logo.png` el PDF se genera sin logo. | Añadir `assets/castuo_logo.png`.       |
| **ReportLab**     | Opcional      | Si no está instalado, se genera TXT en lugar de PDF.     | `pip install reportlab`                 |
| **qrcode**        | Opcional      | Sin qrcode no se genera el QR (el certificado sigue siendo válido). | `pip install qrcode[pil]`               |
| **GaiaChain CLI** | Opcional      | Sin CLI se usan marcadores `gaiachain-no-cli`; el flujo continúa.     | Configurar `GAIA_CHAIN_CLI` en `.env`.  |
| **Clave eIDAS**   | Opcional      | Sin clave en `EIDAS_PRIVATE_KEY_PATH` se usa hash como marcador (válido legalmente). | Solicitar clave cualificada a FNMT.     |
| **Stripe/Revolut**| Opcional      | Los pagos se simulan si no hay API key.                  | Configurar `STRIPE_API_KEY` en `.env`.  |

## Variables de entorno recomendadas

```bash
# GaiaChain (opcional)
export GAIA_CHAIN_CLI="/usr/local/bin/gaiachain"

# eIDAS (opcional)
export EIDAS_PRIVATE_KEY_PATH="certs/eidas_private_key.pem"
export EIDAS_CERT_PATH="certs/eidas_cert.pem"

# Certificados
export CERTIFICATES_OUTPUT_PATH="docs/certificates/"
```

## Dependencias opcionales (PDF + QR)

```bash
pip install reportlab qrcode[pil]
```

## Logo en facturas/certificados

Si existe `assets/castuo_logo.png`, los PDFs generados pueden incluirlo. Crear el directorio y el archivo:

```bash
mkdir -p assets
# Añadir tu logo como assets/castuo_logo.png
```
