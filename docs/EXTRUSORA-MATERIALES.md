# Extrusora para bio-compuestos y módulo CASTUO Materials

## 1. Prototipo extrusora (Arduino + MQTT)

- **Firmware**: `extrusora/extrusora.ino` (Arduino Mega).
  - Sensores: MAX6675 (boquilla), DS18B20 (cámara).
  - Motor NEMA 17 + A4988, relé calentador, LCD I2C.
  - Comandos Serial: `SET_TEMP 200`, `START_EXTRUSION`, `STOP_EXTRUSION`.
- **Bridge MQTT**: `extrusora/mqtt_integration.py` (Raspberry Pi). Serial ↔ MQTT:
  - Publica: `castu/extrusora/temp/boquilla`, `castu/extrusora/temp/camara`, `castu/extrusora/heat`.
  - Suscrito a: `castu/extrusora/command`.
- **Backend**: `POST /extrusora/command` con body `{"command": "START_EXTRUSION"|"STOP_EXTRUSION"|"SET_TEMP 200"}` → publica en MQTT.
- **Grafana**: importar `extrusora/grafana_extrusora_dashboard.json` (métricas: `castu_extrusora_temp`, `castu_extrusora_heat`, etc.; requieren un collector que lea MQTT y exponga Prometheus).

## 2. Módulo Odoo CASTUO Materials

- **Ruta**: `custom-addons/castu_materials/`. Depende de `base`, `sale_management`, `stock`, `account`.
- **Modelos**:
  - **castu.material**: producto (código, tipo, materia prima, propiedades, stock calculado, precio/kg). Stock = producciones finalizadas − ventas entregadas/facturadas.
  - **castu.material.production**: lote de producción (material, kg producidos, materia prima usada, energía kWh, estado draft → producing → done). Acciones: Iniciar Producción (envía START_EXTRUSION vía API), Finalizar Producción (registra en blockchain).
  - **castu.material.sale** / **castu.material.sale.line**: ventas por kg (cliente, líneas material/kg/precio). Confirmar (comprueba stock), Marcar como Entregado (registra en blockchain).
  - **castu.material.certification**: certificación ecológica (lote, organismo UNE/DIN/USDA/EcoCert, fecha, validez, documento). Acción: Registrar en Blockchain.
- **Menú**: Materiales (Inventario) → Productos, Producción, Ventas, Certificaciones.
- **Integración**: parámetro de sistema `castu.fastapi.url` para llamadas a `/extrusora/command` y `/blockchain/material/*`.

## 3. Blockchain (BioCoin Castúo)

- **Backend**: `POST /blockchain/material/register_production`, `register_sale`, `register_certification` (stub; devuelven `tx_id` hash).
- **Contrato**: `contracts/MaterialCertification.sol` (Solidity 0.8): `registerCertification`, `registerSale`, getters. Desplegar en red privada o testnet y configurar `MATERIAL_CERTIFICATION_CONTRACT` + `ETHEREUM_RPC_URL`.
- **Cliente Python**: `backend/blockchain/material_blockchain.py` — `MaterialBlockchain.registrar_produccion`, `registrar_venta`, `subir_a_ipfs`. Si no hay Web3/RPC, se usan los stubs del API.

## 4. Flujo completo

1. En Odoo se crea un **Material** (ej. Bio-compuesto de Cáñamo) y un **Lote de Producción** (kg a producir).
2. **Iniciar Producción** → API → MQTT `castu/extrusora/command` → bridge → Arduino `START_EXTRUSION`.
3. Arduino controla temperatura y motor; el bridge publica temperaturas en MQTT (opcional: exporter a Prometheus/Grafana).
4. **Finalizar Producción** → API `/blockchain/material/register_production` → se guarda `blockchain_tx` en el lote. El stock del material se actualiza por el campo calculado.
5. Ventas y certificaciones registran igualmente en blockchain (stub o contrato real).

---

## 5. Control PID avanzado (±1°C)

- **Firmware**: `extrusora/pid_control.ino` (requiere librería [PID_v1](https://github.com/br3ttb/Arduino-PID-Library)).
  - Pines: MAX6675 (4,5,6), DS18B20 (7), STEP(8), DIR(9), RELE(10), FAN(11). Salida PID en PWM por RELE_PIN (SSR).
  - Parámetros por material: PLA (Kp=2.0, Ki=0.05, Kd=0.1, 180–200°C), Cáñamo (1.8, 0.03, 0.08, 200–220°C), Nanocompuesto (2.2, 0.04, 0.12, 190–210°C). Comando serial `SET_TEMP <valor>` ajusta setpoint y tune.
  - Comandos: `SET_TEMP 210`, `SET_PID Kp Ki Kd`, `START_EXTRUSION`, `STOP_EXTRUSION`. Salida serial: `Boquilla:X, Camara:Y, PID Output:Z, Setpoint:W`.
- **Bridge MQTT PID**: `extrusora/mqtt_pid.py`. Suscribe `castu/extrusora/pid/command` (JSON: `set_temp`, `set_pid`, `autotune`), publica `castu/extrusora/pid/telemetry` (JSON: boquilla, camara, pid_output, setpoint).
- **Grafana PID**: importar `extrusora/grafana_pid_dashboard.json` (temperatura real vs setpoint, salida PID, error, parámetros Kp/Ki/Kd). Métricas desde exporter o MQTT.

## 6. Facturación Facturae SII (castu_invoicing)

- **Módulo Odoo**: `custom-addons/castu_invoicing`. Depende de `base`, `account`, `mail`, `castu_materials`.
- **Modelos**: `castu.material.invoice` (número, fecha, cliente, sale_id, líneas, total, estado draft→confirmed→sent→paid, sii_state, facturae_xml, blockchain_tx), `castu.material.invoice.line` (material, kg, price_unit, subtotal).
- **Flujo**: Confirmar → genera XML Facturae 3.2.1 (`services/facturae_generator.py`). Enviar a SII → `services/sii_client.py` (zeep SOAP; en dev simula si zeep no está). Si respuesta Correcto → `POST /blockchain/material/register_invoice` y se guarda blockchain_tx. Descargar XML con "Descargar XML Facturae".
- **Config**: `ir.config_parameter` opcional `castu_invoicing.sii_clave` para firma SII. Empresa/cliente desde company_id y partner_id (NIF en Facturae).

## 7. Prometheus + Grafana producción

- **Exporter extrusora**: `exporters/extrusora_exporter.py`. Puerto 9100. Lee MQTT `castu/extrusora/pid/telemetry` o Serial; expone `castu_extrusora_temp`, `castu_extrusora_setpoint`, `castu_extrusora_pid_output`, etc. Ejecutar: `pip install -r exporters/requirements.txt && python exporters/extrusora_exporter.py`.
- **Prometheus**: en `castu-monitoring/prometheus/prometheus.yml` está el job `extrusora` (target `extrusora-exporter:9100`). Reglas en `rules/extrusora_invoicing.yml` (TemperaturaExtrusoraAlta/Baja, StockBajoMaterial).
- **Grafana**: dashboards `extrusora/grafana_pid_dashboard.json` (solo PID) y `castu-monitoring/grafana/dashboards/castuo_production_integral.json` (temperaturas, PID, producción, ventas, energía, alertas). Refresh 5s.

## 8. Auto-calibración PID, demanda IA, carbono y alertas

- **Auto-calibración PID (cada 24h)**: `extrusora/autocalibrate.ino` (EEPROM para Kp/Ki/Kd), `extrusora/mqtt_autotune.py` (publica en `castu/extrusora/autotune`), dashboard `extrusora/grafana_autotune_dashboard.json`.
- **Predicción de demanda**: API `POST /ia/predict_demand` (body: material_id, days_ahead, history_kg_sold). Módulo Odoo `castu_demand`: `castu.demand.prediction`, `castu.demand.alert`; menú "Generar predicciones ahora" y "Predicción de Demanda".
- **Créditos de carbono**: `carbon/footprint.py` (factores de emisión, ahorro vs convencional), `contracts/CarbonCredits.sol`, `carbon/market_integration.py`. Módulo Odoo `castu_carbon`: `castu.carbon.credit`, `castu.carbon.report`, wizard de venta; API `POST /blockchain/carbon/register_credit` y `/blockchain/carbon/sell_credit`.
- **Alertas predictivas**: `alerts/predictive_model.py`, `alerts/notifications.py` (Slack/Telegram). Módulo Odoo `castu_alert`: `castu.alert.rule`, `castu.alert`; evaluación por umbral (stock mínimo/máximo), notificaciones vía `POST /notifications/alert`. Variables de entorno: `SLACK_WEBHOOK_URL` o `CASTUO_SLACK_WEBHOOK`, `CASTUO_TELEGRAM_BOT_TOKEN`, `CASTUO_TELEGRAM_CHAT_ID`.
- **Mercados carbono (Verra/Gold Standard/EU ETS)**: stubs en `carbon/verra_integration.py`, `carbon/goldstandard_integration.py`, `carbon/eu_ets_integration.py`; contrato `contracts/CarbonMarket.sol` (issueCredit, transferCredit, retireCredit).
- **Optimización de rutas**: `logistics/route_optimizer.py` (VRP con OR-Tools; capacidad y matriz de distancias). Instalar `ortools` para optimización real.
