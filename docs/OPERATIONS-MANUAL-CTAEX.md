# Manual de operaciones CASTUO-SYSTEM — CTAEX

Guía paso a paso para técnicos y agricultores en el piloto CTAEX.

## 1. Puesta en marcha diaria

1. **Comprobar servicios:** Backend (API), MQTT, base de datos y GaiaChain deben estar en marcha (Docker o servidor).
2. **Revisar sensores:** Confirmar que Raspberry Pi y sensores (temperatura, humedad, CO₂, EC, pH) envían datos al broker MQTT.
3. **Dashboard:** Revisar en el frontend o Grafana que las bandejas aparecen con datos en tiempo real.

## 2. Creación de lotes de microgreens

1. En la API o desde el agente IoT, crear lote:  
   `POST /api/microgreens/batches` con `variety_name` (radish, broccoli, sunflower), `tray_id` y `quantity` (gramos).
2. Anotar el `batch_id` devuelto.
3. Añadir datos ambientales cuando corresponda:  
   `POST /api/microgreens/batches/{batch_id}/environment` con temperatura, humedad, EC, pH, etc.
4. Actualizar estado: `PUT /api/microgreens/batches/{batch_id}?status=germinating` (o `growing`, `harvested`).
5. Generar certificado: `POST /api/microgreens/batches/{batch_id}/certificate`.

## 3. Control ambiental (ozono, ósmosis, UV)

- Los datos ambientales se envían a `POST /api/environment/data` (ozono, ósmosis, UV, nutrientes, CO₂, temp, humedad).
- El sistema devuelve comandos para actuadores (bomba nutrientes, pH, ozono) y alertas si se superan umbrales.
- Consultar umbrales por cultivo: `GET /api/environment/thresholds/{crop_type}` (microgreens, brotes, cannabis_vegetative).

## 4. Tratamiento de agua

- Registrar tratamiento: `POST /api/water/treatments` con datos de entrada/salida, ósmosis y calidad.
- Analizar calidad: `POST /api/water/analysis` con cuerpo de calidad de agua y `crop_type`; el sistema devuelve recomendaciones.

## 5. Certificados y exportación

- Certificado de producto: `POST /api/certificates/product` (batch_id, product_type, variety).
- Certificado de exportación: `POST /api/certificates/export` (product_cert_id, destination_country, importer).
- Verificar certificado: `GET /api/certificates/verify/{certificate_id}`.

## 6. E-commerce

- Añadir plataforma: `POST /api/ecommerce/platforms` (Shopify, WooCommerce, etc.).
- Sincronizar producto: `POST /api/ecommerce/products/sync?platform=shopify` con cuerpo del producto.
- Los pedidos entran por webhooks: `/webhooks/shopify/orders` y `/webhooks/woocommerce/orders`.
- **CTAEX / Stripe:** Crear checkout: `POST /ecommerce/create-checkout` (body: `batch_id`, opcional `success_url`, `cancel_url`, `unit_amount`). Stripe envía pagos completados a `POST /ecommerce/webhook`; configurar `STRIPE_WEBHOOK_SECRET` y la URL en el Dashboard de Stripe. Ver `docs/CTAEX-SECURITY.md`.

## 7. Protocolos de emergencia

- **Fallo en sensores:** Comprobar alimentación y conexión MQTT; revisar logs del broker y del backend.
- **Corte de energía:** Los datos en GaiaChain permanecen; al reiniciar, verificar que MQTT y backend se reconectan.
- **Nivel de ozono fuera de rango:** El sistema envía alertas y comandos de ajuste; en caso crítico, ventilar y revisar generador de ozono.
- **Fallo en ósmosis:** Revisar presión y filtros; registrar incidencia y, si aplica, un nuevo tratamiento en `/api/water/treatments`.

## 8. Pruebas y validación

- Probar todos los endpoints: `python tests/test_all_endpoints.py` (con el backend en marcha).
- Probar webhooks: `python tests/test_webhooks.py`.
- Validar flujo de certificados: `python tests/validate_certificates.py`.

## 9. Operaciones con Docker

### 9.1. Comandos básicos

| Comando | Descripción |
|---------|-------------|
| `docker compose -f docker/docker-compose.ctaex.yml build` | Construye las imágenes (desde la raíz del repo). |
| `docker compose -f docker/docker-compose.ctaex.yml up -d` | Inicia los servicios en segundo plano. |
| `docker compose -f docker/docker-compose.ctaex.yml logs backend` | Muestra logs del backend. |
| `docker compose -f docker/docker-compose.ctaex.yml restart backend` | Reinicia el backend. |
| `docker exec -it <contenedor_backend> bash` | Accede al contenedor del backend. |

### 9.2. Monitoreo

- **Estado de contenedores:** `docker compose -f docker/docker-compose.ctaex.yml ps`
- **Logs en tiempo real:** `docker compose -f docker/docker-compose.ctaex.yml logs --tail=50 -f backend`
- **Actualizar solo el backend:** `docker compose -f docker/docker-compose.ctaex.yml build backend && docker compose -f docker/docker-compose.ctaex.yml up -d --no-deps backend`

### 9.3. Solución de problemas

| Problema | Solución |
|----------|----------|
| Error de conexión a PostgreSQL | Comprobar `DB_PASSWORD` en `.env` y que el servicio postgres esté levantado. |
| Error 500 en endpoints | Revisar logs: `docker compose -f docker/docker-compose.ctaex.yml logs backend`. |
| MQTT no responde | Verificar `docker/mosquitto.conf` y creación de `passwords.txt` si se usa autenticación. |
| Frontend no carga / CORS | Verificar que la API esté en la URL esperada; en ecommerce.html usar `?api=http://IP:8000` si el front está en otro puerto. |
| Stripe webhook 400/500 | Comprobar `STRIPE_WEBHOOK_SECRET` y que la URL en Stripe Dashboard coincida (ej. `https://dominio/ecommerce/webhook`). |

Para roles, firewall, Nginx y Docker Secrets, ver **docs/CTAEX-SECURITY.md**.

---

## 10. Arquitectura y Roadmap de SABIONDA Pro

Para detalles técnicos sobre la **arquitectura modular**, **flujos de trabajo**, **cumplimiento normativo** y **hoja de ruta de implementación**, consulta el documento:

📄 **[SABIONDA-PRO-ARCHITECTURE-ROADMAP.md](SABIONDA-PRO-ARCHITECTURE-ROADMAP.md)**

### Resumen de componentes clave

| **Módulo** | **Funcionalidad** | **Documentación relacionada** |
|------------|-------------------|-------------------------------|
| **Cuentas Pro** | Gestión jerárquica de usuarios (RBAC), permisos y restricciones de contenido. | [PRO-ACCOUNTS-GUIDE.md](PRO-ACCOUNTS-GUIDE.md) |
| **Cannabis Medicinal** | Licencias AEMPS, lotes, trazabilidad blockchain (GaiaChain) y cumplimiento RD 903/2025. | CANNABIS-COMPLIANCE.md (próximamente) |
| **Microgreens** | Variedades, lotes, certificaciones GlobalGAP y monitoreo IoT. | MICROGREENS-OPERATIONS.md |
| **Blockchain (GaiaChain)** | Trazabilidad inmutable para lotes de cannabis y microgreens. | BLOCKCHAIN-INTEGRATION.md |
| **IoT** | Sensores para datos ambientales (temperatura, humedad, pH, EC). | IOT-SENSORS-GUIDE.md |
| **Cumplimiento normativo** | Validación automática de GDPR, AI Act UE, ISO 27001, RD 903/2025. | COMPLIANCE-MANUAL.md |
| **Legacy Systems** | Conectores para SAP, LIMS y bases de datos antiguas. | LEGACY-INTEGRATION.md (en desarrollo) |
| **Internacionalización** | Soporte para exportación (certificados fitosanitarios, normas por país). | INTERNATIONAL-EXPORT.md (próximamente) |

### Flujos de trabajo operativos

1. **Creación de Cuentas Pro**
   - Usar `POST /pro-accounts/` con `tier="enterprise"` para cannabis.
   - Ejemplo: Crear cuenta Pro (ver [PRO-ACCOUNTS-GUIDE.md](PRO-ACCOUNTS-GUIDE.md)).

2. **Gestión de lotes de cannabis**
   - Registrar lote → Validar con AEMPS → Certificar → Blockchain.
   - Endpoints: `POST /pro-accounts/{account_id}/cannabis/batches`, `POST .../batches/{batch_id}/certify`.

3. **Monitoreo de microgreens**
   - Sensores IoT → Alertas en tiempo real → Ajustes automáticos.
   - Endpoints: `GET/POST /pro-accounts/{account_id}/microgreens/batches/{batch_id}/iot`, `GET .../iot/analysis`.

4. **Exportación internacional**
   - Generar certificados fitosanitarios → Validar con normas del país destino → Logística (DHL/FedEx).
   - Endpoints: `/international/asia/*` y `/international/canada/*` (documentos y logística).
