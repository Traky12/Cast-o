# PRUEBAS AUTOMATIZADAS: FORESTOWNERSHIPTOKEN

## Requisitos

- Python 3.8+
- ChromeDriver instalado y accesible en el `PATH` (para Selenium)
- Node.js 16+ (para levantar el frontend del dashboard)
- Backend/API en ejecución (por defecto en `http://localhost:8000`)

## Instalación

```bash
pip install -r tests/requirements.txt
```

## Ejecución

### Local (modo desarrollo, navegador visible)

```bash
pytest tests/e2e/test_privacy_module.py -v
```

### CI/CD (modo headless + informe HTML)

```bash
pytest tests/e2e/test_privacy_module.py --html=report.html --self-contained-html
```

## Variables de entorno

Configura las siguientes variables (por ejemplo en `.env` o en el entorno del CI):

```env
DASHBOARD_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000
TEST_TOKEN_ID=1
TEST_WALLET_ADDRESS=0x7A1234567890abcdef1234567890abcdef12345678
TEST_EMAIL=propietario@test.com
```

## Casos de prueba

- Flujo completo del módulo de privacidad (frontend + backend + GaiaChain).
- Endpoint de borrado (validación de identidad, actualización en GaiaChain, nuevo `ipfsHash`).
- Generación de certificados (PDF con metadatos del borrado).

## Informes

Los informes de pytest-html se generan en `report.html` (formato auto-contenido) y pueden adjuntarse como artefacto en el pipeline de CI/CD.

