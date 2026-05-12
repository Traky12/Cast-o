# InfluxDB + n8n + Grafana — Setup Operacional

## 1. InfluxDB en Kubernetes

InfluxDB 2.7 está desplegado como componente timeseries para almacenar lecturas de sensores del invernadero.

### Deployment actual:
```bash
kubectl apply -f k8s/monitoring/influxdb-deployment.yaml -n castuo-system
```

Verifica el estado:
```bash
kubectl get pods -l app=influxdb -n castuo-system
kubectl get svc influxdb-service -n castuo-system
```

### Acceso a InfluxDB UI:
1. **Dentro del cluster** (desde pods): `http://influxdb-service:8086`
2. **Desde host**: Port-forward:
   ```bash
   kubectl port-forward -n castuo-system svc/influxdb-service 8086:8086
   ```
   Accede a `http://localhost:8086` (usuario: admin, contraseña: cambiar)

### Configuración de credenciales:

**IMPORTANTE**: Cambiar credenciales en producción.

Edita `k8s/monitoring/influxdb-deployment.yaml` ANTES de desplegar:
```yaml
env:
  - name: INFLUXDB_DB
    value: "castuo_greenhouse"
  - name: INFLUXDB_ADMIN_USER
    value: "admin"
  - name: INFLUXDB_ADMIN_PASSWORD
    valueFrom:
      secretKeyRef:
        name: influxdb-credentials
        key: admin-password
```

Crea el Secret:
```bash
kubectl create secret generic influxdb-credentials \
  --from-literal=admin-password='TuContraseñaSeguraAqui' \
  -n castuo-system
```

### Estructura de datos esperada:

**Measurement**: `invernadero`
**Tags** (indexados, para filtrado rápido):
- `lote_id`: ID del lote (ej: `INVH-EXP-001-TOMATE-ABC123`)
- `zona`: Zona física (ej: `modulo-1`)
- `cultivo`: Tipo de cultivo (ej: `tomate`)

**Fields** (valores medibles):
- `temperatura_c`: float
- `humedad_pct`: float
- `co2_ppm`: int
- `ph`: float
- `ec_ms_cm`: float
- `luz_par`: int
- `o2_disuelto_mg_l`: float
- `vpd_kpa`: float

**Ejemplo de escritura desde API**:
```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

client = InfluxDBClient(url="http://influxdb-service:8086", token="tu-token", org="castuo")
write_api = client.write_api(write_options=SYNCHRONOUS)

point = (
    Point("invernadero")
    .tag("lote_id", "INVH-001")
    .tag("zona", "modulo-1")
    .tag("cultivo", "tomate")
    .field("temperatura_c", 24.5)
    .field("humedad_pct", 65.0)
    .field("co2_ppm", 950)
    .field("ph", 6.0)
    .field("ec_ms_cm", 2.1)
)
write_api.write(bucket="castuo_greenhouse", record=point)
```

### GDPR: Retención automática (90 días)

El CronJob en `k8s/monitoring/cleanup-old-data-cronjob.yaml` purga datos con >90 días.

**Antes de desplegar**, configura credenciales:
```bash
kubectl create secret generic influxdb-creds \
  --from-literal=INFLUX_TOKEN='tu-admin-token' \
  --from-literal=INFLUX_ORG='castuo' \
  --from-literal=INFLUX_BUCKET='castuo_greenhouse' \
  -n castuo-system
```

Desplega el CronJob:
```bash
kubectl apply -f k8s/monitoring/cleanup-old-data-cronjob.yaml -n castuo-system
```

---

## 2. n8n Workflows para Alertas

Dos workflows MQTT-basados están listos para importar en tu instancia n8n.

### Importar workflows:

1. Accede a tu n8n UI: `https://tu-n8n-instance.com`
2. **Menú principal → Import → Paste workflow**
3. Ve a [`n8n/workflows/invernadero-temp-alert.json`](../n8n/workflows/invernadero-temp-alert.json)
4. Repite con [`invernadero-ec-alert.json`](../n8n/workflows/invernadero-ec-alert.json)

### Flujos incluidos:

#### **invernadero-temp-alert.json**
**Trigger**: MQTT `invernadero/sensores/temperatura`

**Acción**:
- Si `temp > 30°C` → Activar ventilación
- Si `temp < 15°C` → Activar calefacción
- Registra alerta en API `/api/v1/invernadero/alertas`

**Código lógico**:
```javascript
if (msg.payload.temperatura > 30) {
  return { ...msg, actuador: "ventilacion", estado: "encender" };
} else if (msg.payload.temperatura < 15) {
  return { ...msg, actuador: "calefaccion", estado: "encender" };
}
return { ...msg, skipped: true };
```

#### **invernadero-ec-alert.json**
**Trigger**: MQTT `invernadero/sensores/ec`

**Acción**:
- Si `EC < 1.5 mS/cm` → Agregar nutrientes
- Si `EC > 3.0 mS/cm` → Diluir solución
- Descarta si está en rango óptimo

---

### Configuración de conexiones n8n:

#### **1. MQTT Broker**
- **Host**: `mosquitto` (o `mosquitto.castuo-system.svc.cluster.local` si está en K8s)
- **Port**: 1883
- **Protocol**: mqtt
- **Username**: (configurar en Mosquitto si required)
- **Password**: (configurar en Mosquitto si required)

#### **2. HTTP Node (API Callbacks)**
- **URL**: `http://api:8000/api/v1/invernadero/alertas`
- **Method**: POST
- **Headers**: `Content-Type: application/json`
- **Body**:
  ```json
  {
    "lote_id": "{{ $node.MQTTSubscribe.json.lote_id }}",
    "tipo_alerta": "temperatura",
    "valor": "{{ $node.MQTTSubscribe.json.temperatura }}",
    "accion": "{{ $node.Function.json.actuador }}"
  }
  ```

### Test de workflows:

**Publicar mensaje de prueba** desde terminal:
```bash
mosquitto_pub -h mosquitto -t invernadero/sensores/temperatura \
  -m '{"temperatura": 35.0, "lote_id": "INVH-001"}'
```

Verifica los logs de n8n: debería ver la ejecución del workflow.

---

## 3. Grafana Dashboards

### Deploy Grafana en K8s (opcional, si no existe):

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana -n castuo-system
```

Obtén contraseña y acceso:
```bash
kubectl get secret -n castuo-system grafana -o jsonpath="{.data.admin-password}" | base64 --decode
kubectl port-forward -n castuo-system svc/grafana 3000:80
```

### Agregar InfluxDB como data source:

1. **Configuration → Data Sources → Add data source**
2. Selecciona **InfluxDB**
3. Configura:
   ```
   URL: http://influxdb-service:8086
   Organization: castuo
   Token: (tu admin token)
   Bucket: castuo_greenhouse
   ```
4. **Test & Save**

### Dashboard templador: Invernadero Real-Time

Importa el JSON dashboard (crear desde [Grafana JSON model](https://grafana.com/grafana/dashboards/)):

```json
{
  "dashboard": {
    "title": "Invernadero Agrovoltaico Real-Time",
    "panels": [
      {
        "title": "Temperatura (°C)",
        "targets": [
          {
            "query": "from(bucket:\"castuo_greenhouse\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"invernadero\" and r._field == \"temperatura_c\")"
          }
        ]
      },
      {
        "title": "pH Solución",
        "targets": [
          {
            "query": "from(bucket:\"castuo_greenhouse\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"invernadero\" and r._field == \"ph\")"
          }
        ]
      },
      {
        "title": "EC (mS/cm)",
        "targets": [
          {
            "query": "from(bucket:\"castuo_greenhouse\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"invernadero\" and r._field == \"ec_ms_cm\")"
          }
        ]
      },
      {
        "title": "CO₂ (ppm)",
        "targets": [
          {
            "query": "from(bucket:\"castuo_greenhouse\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"invernadero\" and r._field == \"co2_ppm\")"
          }
        ]
      }
    ]
  }
}
```

### Cuadros de rango óptimo:

Agrega threshold lines para cada cultivo (ej. tomate):
- **Temperatura**: 20-26°C (amarillo <18 o >28, rojo <15 o >32)
- **pH**: 5.8-6.3 (amarillo <5.5 o >6.5, rojo <5.0 o >7.0)
- **EC**: 2.0-4.0 mS/cm (amarillo <1.8 o >4.2, rojo <1.5 o >4.5)
- **CO₂**: 800-1200 ppm (amarillo <700 o >1300, rojo <600 o >1400)

---

## 4. Flujo completo: Invernadero → InfluxDB → n8n → Grafana

```
Sensor MQTT
    ↓
invernadero/sensores/temperatura
    ↓
n8n: invernadero-temp-alert (suscribe + threshold check)
    ↓
¿Alerta? → POST /api/v1/invernadero/alertas
    ↓
API registra en InfluxDB
    ↓
n8n: Activa actuador (ventilacion/calefaccion)
    ↓
Grafana: Visualiza timeseries + threshold lines en tiempo real
    ↓
Cosecha: Registra en blockchain (GaiaChain)+ QR para trazabilidad
```

---

## 5. Checklist de Deploy

- [ ] InfluxDB Deployment corriendo en castuo-system: `kubectl get pods -l app=influxdb`
- [ ] Secret de credenciales InfluxDB creado: `kubectl get secret influxdb-credentials`
- [ ] n8n workflows importados y activos (test de MQTT publicando)
- [ ] Grafana datasource conecta a InfluxDB
- [ ] Dashboard con paneles de temperatura/pH/EC/CO₂ visible
- [ ] CronJob de retención en ejecución: `kubectl get cronjobs -n castuo-system`
- [ ] Cosecha con blockchain: `POST /api/v1/invernadero/cosecha` devuelve `blockchain.txid`

---

## 6. Troubleshooting

### InfluxDB no arranca
```bash
kubectl logs -n castuo-system -l app=influxdb
kubectl describe pod -n castuo-system <influxdb-pod-name>
```

### n8n no conecta a MQTT
- Verifica que Mosquitto está corriendo: `kubectl get pods -l app=mosquitto`
- Prueba conectividad: `kubectl exec -it $(kubectl get pod -l app=api -n castuo-system -o name) -- nc -zv mosquitto 1883`

### Grafana no ve datos
- Verifica el token en el datasource de InfluxDB
- Revisa si hay datos escribiendo: `influx query 'from(bucket: "castuo_greenhouse") |> range(start: -1h)'`

### Cosecha no registra en blockchain
- Verifica logs de API: `kubectl logs -n castuo-system -l app=api`
- Valida que EvidenceRegistrar sea accesible: `python -c "from services.blockchain.evidence_register import EvidenceRegistrar; print('OK')"`

---

## Documentación relacionada
- [API Invernadero Endpoints](../../api/routers/invernadero.py)
- [K8s Manifests](../../k8s/)
- [n8n Workflows](../../n8n/workflows/)
- [Tests e2e Blockchain](../../tests/test_invernadero_blockchain_e2e.py)
