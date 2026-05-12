# Prototipo CTAEX ~10 m² (referencia MQTT → CASTÚO / n8n)

Documento de **ingeniería de proyecto**, no certificación CTAEX ni presupuesto cerrado. Precios y marcas son **orientativos**: contrastar antes de compra.

## 1. Alcance

- **~10 m²** hidropónico tipo lechuga (densidad de plantas según diseño agronómico).
- **Telemetría** por nodo ESP32 → **MQTT** → **RPi** (opcional bridge) → **n8n** → **castuo-api** (LangGraph/Mistral) para análisis y registro.
- **Actuación crítica** (bombas, pH fuerte): preferir **lógica local con límites** y revisión humana; ver [LATENCY-ZERO-OPERATIONAL-TARGET.md](../architecture/LATENCY-ZERO-OPERATIONAL-TARGET.md).

## 2. BOM de referencia (no vinculante)

| Componente | Cant. | €/u (ref.) | Total (ref.) |
|------------|------:|-----------:|---------------:|
| ESP32 | 10 | 6 | 60 |
| pH (p. ej. analog tipo 4502) | 10 | 15 | 150 |
| EC probe K=1 | 10 | 12 | 120 |
| DHT22 | 10 | 5 | 50 |
| CO2 MH-Z19 (UART) | 10 | 25 | 250 |
| BH1750 (lux; no es PAR directo) | 10 | 3 | 30 |
| Relé 4ch / módulo | 10 | 8 | 80 |
| Bomba peristáltica (caudal según diseño) | 10 | 20 | 200 |
| RPi Zero 2 W (gateway) | 1 | 20 | 20 |
| Caja IP6x | 10 | 10 | 100 |
| Solar 5 W + batería (si aplica) | 10 | 13 | 130 |
| Tuberías / depósito / misc. | lote | — | ~150 |
| **Total orientativo** | | | **~1.190** |

**Nota PAR:** BH1750 mide **lux**. La conversión a **µmol·m⁻²·s⁻¹** depende del espectro del LED/sol y del factor de conversión; calibrar con medidor PAR o tabla de correlación por cultivo.

### 2.1 Tratamiento de agua (referencia de proyecto)

| Equipo | Especificación (ejemplo) | Precio ref. (€) | Función en CASTÚO |
|--------|-------------------------|------------------:|-------------------|
| Ósmosis inversa | ~200 L/día, multietapa | ~250 | Agua de bajo TDS para dilución de nutrientes (medir **TDS/EC** a la salida; objetivo típico laboratorio &lt;50 ppm según sonda, no garantía genérica) |
| Generador ozono O₃ | ~4 g/h (equivalente comercial tipo referencia) | ~400 | Desinfección / oxidación; **ORP** como proxy de proceso (p. ej. umbral orientativo **&gt;600–700 mV** según agua y sonda; calibrar) |
| **Subtotal agua** | | **~650** | |
| **IoT + agua (suma)** | | **~1.840** | Sobre base IoT ~1.190 € anterior |

**Química y normativa:** el ozono y el agua recirculada deben diseñarse con **procedimiento de seguridad** (ventilación O₃, materiales compatibles, exposición personal, vertido). “DNR 99,9 %” o “0 patógenos” son **claims de marketing** salvo ensayo microbiológico acreditado; no los afirma este repositorio.

**Rendimiento económico:** cifras tipo “yield +35 %”, “ROI 1 mes”, “€18.750/año” son **hipótesis de negocio**; dependen de mercado, cultivar, pérdidas y coste energético. Construir **modelo propio** antes de inversión.

Integración técnica agua → API y n8n: [WATER-SYSTEM-CTAEX.md](./WATER-SYSTEM-CTAEX.md).

## 3. Topics MQTT sugeridos

Alineados al patrón `castuo/...` usado en `iot/mqtt_handler.py`:

```text
castuo/ctaex/{bed_id}/telemetry   → JSON telemetría (QoS 1 recomendado para datos)
castuo/ctaex/{bed_id}/command     → comandos hacia nodo (solo con ACL y TLS en producción)
castuo/ctaex/{bed_id}/water/event → eventos agua/ORP/TDS (opcional, QoS 1)
castuo/ctaex/{site}/water/ozone_command → publicado por gateway/autómata que acciona relé ozono (no desde ESP sin revisión OT)
```

`bed_id`: `B01`…`B10` por bandeja o zona. Un **sitio** puede ser `CTAEX01` para equipos compartidos (ósmosis/ozono).

## 4. Flujo n8n (resumen)

1. **MQTT Trigger** suscrito a `castuo/ctaex/+/telemetry`.
2. Nodo **Code** que mapea JSON → `payload` para `POST …/langgraph/castuo/execute-graph` (`kind: iot_sensor` o payload hidropónico estándar).
3. Opcional: **HTTP Request** a webhook interno o tabla Postgres.

Reutilizar lógica de `n8n/workflows/castuo_n8n_iot_sensor_langgraph.json` ajustando topics y campos.

### 4.1 Agua: ORP, ozono y ósmosis (lógica sugerida)

1. **MQTT Trigger** `castuo/ctaex/+/telemetry` (u `+/water/event`) con campo `orp_mv` y/o `tds_ppm` / `tds_ro_ppm`.
2. **IF / Switch:** si `orp_mv < 600` (umbral **ajustable** tras calibración) y no hay **interbloqueo** manual → rama “ozono”.
3. **MQTT Publish** (cliente n8n con credencial) hacia `castuo/ctaex/CTAEX01/water/ozone_command` con JSON p. ej. `{"run_sec":900,"source":"n8n","reason":"orp_low"}`.
4. El **ejecutor** del relé ozono debe ser **PLC o RPi con salida aislada**, temporizado y con **parada de emergencia**; no confiar solo en el ESP en producción.
5. **Ósmosis / relleno:** sensor de nivel + TDS salida RO; n8n puede registrar y alertar; válvulas con hardware de failsafe.

**LangGraph:** puede sintetizar **recomendaciones** o registrar decisión; el **pulso eléctrico** al ozono debe cumplir política OT y tiempos máximos de exposición O₃.

Fragmento ESP32 (solo telemetría; la decisión “ozono ON” preferible en capa superior):

```cpp
float orp_mv = readORP();  // Sonda ORP → mV (calibrar offset/ganancia)
// Incluir orp_mv en el JSON de telemetry; opcional:
if (orp_mv < 600.0f && orp_mv > -2000.0f) {  // filtrar lectura inválida
  mqtt.publish("castuo/ctaex/B01/water/event",
    "{\"alert\":\"orp_low\",\"orp_mv\":1234}", false);
}
```

Evitar topic plano `castuo/ozono_on` sin `bed_id`/JSON: dificulta ACL y auditoría.

## 5. Firmware

Sketch de ejemplo: `iot/firmware/ctaex_esp32_hydro_node/ctaex_esp32_hydro_node.ino`.

## 6. Seguridad mínima

- MQTT con **usuario/contraseña** o certificados; no `allow_anonymous` en despliegue real.
- No publicar **credenciales WiFi/MQTT** en el repositorio.
- Ácido/base para pH: **dosificación** solo con hardware interbloqueado y procedimiento químico validado (fuera de alcance de este .md).

## 7. Referencias

- [IOT-MARCO-REPOSITORIO.md](../iot/IOT-MARCO-REPOSITORIO.md)
- [N8N-INITIAL-SETUP-CASTUO.md](../deploy/N8N-INITIAL-SETUP-CASTUO.md)
- `iot/docker-compose.mqtt.yml`, `iot/mqtt_handler.py`
