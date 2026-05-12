# Herramientas de Código Abierto Integradas en CASTUO-SYSTEM

## Visión General
CASTUO-SYSTEM leverages industria-leading open-source tools para maximizar flexibilidad, transparencia y soberanía tecnológica. Cada herramienta se integra de forma orquestada para crear un stack agrícola resiliente y escalable.

---

## 1. Análisis Geoespacial & Mapping

### QGIS (Quantum GIS)
**Propósito:** Análisis geoespacial avanzado, mapeo de campos, SIG integrado

**Características:**
- Visualización de datos raster y vectorial
- Análisis de terreno (DEM, slope, aspect)
- Integración con PostGIS de Hetzner
- Exportación a múltiples formatos (GeoJSON, Shapefile, KML)

**Integración CASTUO:**
```bash
# Instalar QGIS en servidor Hetzner
apt-get install -y qgis qgis-server
systemctl enable --now qgis-server

# Conectar a PostGIS (via k8s)
# QGIS WMS Server: http://castuo-node:8080/qgis
```

**Workflow Agrícola:**
```
Sensores IoT → PostGIS → QGIS WMS → Dashboard agrícola (Grafana)
```

---

## 2. Digital Twins & Modelado 3D

### PIX4D (Open-Source Components)
*Nota: PIX4D es comercial, pero complementamos con herramientas OSS*

**Alternativa OSS: CloudCompare + OpenDroneMap**

**CloudCompare:**
- Visualización y procesamiento de nubes de puntos (LiDAR)
- Comparación de modelos 3D
- Extracción de características

**OpenDroneMap:**
- Ortofotos desde imágenes de drones
- Reconstrucción 3D
- Nubes de puntos ortorrectificadas

**Integración CASTUO:**
```python
# odm_processor.py
from subprocess import run

def process_drone_imagery(images_dir, output_dir):
    """
    Procesamiento de imágenes de drones con OpenDroneMap.
    """
    run([
        "docker", "run", "-v", f"{images_dir}:/images",
        "-v", f"{output_dir}:/outputs",
        "opendronemap/odm",
        "--project-path", "/outputs"
    ])
    
    # Exportar a GeoJSON para análisis posterior
    return f"{output_dir}/odm_orthophoto/odm_orthophoto.tif"
```

---

## 3. Monitoreo en Tiempo Real

### Grafana + Prometheus
**Propósito:** Dashboards operacionales, alertas, trazabilidad de métricas agrícolas

**Arquitectura:**
```
Sensores IoT → MQTT Broker → Prometheus → Grafana Dashboards
```

**Dashboards Pre-configurados:**
- Condiciones del campo (temperatura, humedad, pH)
- Estado del sistema (CPU, memoria, almacenamiento)
- Rendimiento de aplicaciones (latencia n8n, errores API)
- Análisis IA (uso de créditos Mistral, confianza de predicciones)

**Configuración en Hetzner:**
```bash
# Ver dashboards en ejecución
kubectl port-forward -n castuo svc/grafana 3000:3000
# Acceso: http://localhost:3000 (admin/admin, cambiar contraseña)
```

**Exportar Métricas a Sabionda:**
```python
# prometheus_exporter.py
from prometheus_client import Counter, Gauge, Histogram
import time

crop_yield_predictions = Gauge(
    'castuo_crop_yield_kg_ha', 
    'Predicted crop yield in kg/ha'
)
mistral_api_calls = Counter(
    'castuo_mistral_ai_calls_total',
    'Total Mistral AI API calls'
)
analysis_duration = Histogram(
    'castuo_analysis_duration_seconds',
    'Duration of crop analysis'
)

@app.post("/analyze")
async def analyze(data: dict):
    start = time.time()
    prediction = sabionda.predict_crop_yield(data)
    crop_yield_predictions.set(prediction['predicted_yield'])
    analysis_duration.observe(time.time() - start)
    return prediction
```

---

## 4. Orquestación Intelligent: LangGraph vs n8n

### LangGraph
**Propósito:** Flujos de IA con estado, manejo de agentes complejos

**Ventajas:**
- Control explícito de flujo (graphs/DAGs)
- Integración nativa con LLMs (OpenAI, Mistral, etc.)
- Debugging y tracing mejorado
- State management persistent

**Caso de Uso: Análisis Agrícola Inteligente**
```python
# langgraph_workflow.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from castuo_graph.ai.mistral_connector import MistralConnector
from castuo_graph.ai.sabionda_connector import SabiondaConnector

class AgriculturalAnalysisState:
    sensor_data: dict
    mistral_analysis: dict
    sabionda_prediction: dict
    final_recommendation: str

workflow = StateGraph(AgriculturalAnalysisState)

# Nodo 1: Análisis Mistral
def analyze_with_mistral(state):
    mistral = MistralConnector(api_key=os.getenv("MISTRAL_API_KEY"))
    state.mistral_analysis = mistral.analyze_agricultural_data(state.sensor_data)
    return state

# Nodo 2: Predicción Sabionda
def predict_with_sabionda(state):
    sabionda = SabiondaConnector(api_key=os.getenv("SABIONDA_API_KEY"))
    state.sabionda_prediction = sabionda.predict_crop_yield(state.sensor_data)
    return state

# Nodo 3: Decisión Final
def synthesize_recommendation(state):
    state.final_recommendation = (
        f"Mistral insights: {state.mistral_analysis['choices'][0]['message']['content']}\n"
        f"Yield prediction: {state.sabionda_prediction['predicted_yield']} kg/ha\n"
        f"Confidence: {state.sabionda_prediction['confidence']}"
    )
    return state

workflow.add_node("mistral", analyze_with_mistral)
workflow.add_node("sabionda", predict_with_sabionda)
workflow.add_node("synthesize", synthesize_recommendation)

workflow.add_edge(START, "mistral")
workflow.add_edge("mistral", "sabionda")
workflow.add_edge("sabionda", "synthesize")
workflow.add_edge("synthesize", END)

graph = workflow.compile()
```

### n8n (Alternativa Visual)
**Propósito:** Automatización workflows visual, integraciones SaaS, triggers HTTP

**Ventajas sobre LangGraph:**
- UI visual (no requiere código)
- Triggers de webhooks nativos
- 300+ integraciones pre-built
- Mejor para mapeos simples

**Recomendación:**
- **LangGraph:** Análisis IA complejos, control fino del flujo
- **n8n:** Triggers, notificaciones, integraciones SaaS (WordPress, Slack, etc.)

**Coexistencia:**
```
Sensores → n8n Webhook Trigger → FastAPI → LangGraph Workflow → WordPress
```

---

## 5. Almacenamiento Descentralizado: IPFS & Arsys

### IPFS (InterPlanetary File System)
**Propósito:** Almacenamiento descentralizado, resistente a censura, P2P

**Características:**
- Content-addressable (hash-based)
- Tolerancia a fallos distribuidamente
- Versionamiento nativo
- Integración blockchain (GaiaChain)

**Caso de Uso: Trazabilidad Agrícola Inmutable**

```python
# ipfs_storage.py
from ipfshttpclient import connect

class IPFSStorageManager:
    def __init__(self, ipfs_endpoint: str = "/ip4/127.0.0.1/tcp/5001"):
        self.client = connect(ipfs_endpoint)
    
    def store_crop_data(self, data: dict) -> str:
        """
        Almacenar datos de cosecha en IPFS.
        
        Returns:
            IPFS Content Hash (CIDv1)
        """
        import json
        json_data = json.dumps(data)
        result = self.client.add_str(json_data)
        return result  # e.g., "QmXxxx..."
    
    def retrieve_crop_data(self, ipfs_hash: str) -> dict:
        """Recuperar datos de cosecha inmutables."""
        import json
        content = self.client.get_text(ipfs_hash)
        return json.loads(content)

# Uso en n8n workflow
ipfs_manager = IPFSStorageManager()
crop_record = {
    "crop": "tomate",
    "yield": 1280,
    "harvest_date": "2026-06-15",
    "blockchain_ref": gaiachain_hash
}
ipfs_hash = ipfs_manager.store_crop_data(crop_record)
# Resultado: ipfs://QmXxxx (referenciable permanentemente)
```

### Arsys Cloud (EU Infrastructure)
**Propósito:** Hosting soberano EU, GDPR-compliant, backups redundantes

**Servicios recomendados:**
- Cloud Storage (IPFS + S3-compatible)
- Backup automático para PostgreSQL/MongoDB
- CDN para contenido estático
- VPN para conexiones seguras

**Configuración:**
```yaml
# docker-compose.arsys.yml
version: '3.8'
services:
  minio:
    image: minio/minio
    environment:
      MINIO_ROOT_USER: ${ARSYS_S3_KEY}
      MINIO_ROOT_PASSWORD: ${ARSYS_S3_SECRET}
    ports:
      - 9000:9000
    volumes:
      - /mnt/castuo-data/minio:/minio_data
    command: server /minio_data

  ipfs:
    image: ipfs/kubo
    ports:
      - 5001:5001
    volumes:
      - /mnt/castuo-data/ipfs:/data/ipfs
```

---

## 6. Seguridad & Cumplimiento

### Criptografía Implementada

**AES-256 (Fernet en Python)**
```python
# Implementado en castuo_graph/security/encryption.py
from cryptography.fernet import Fernet

key = Fernet.generate_key()  # 32 bytes (256 bits)
cipher = Fernet(key)
encrypted = cipher.encrypt(b"datos_sensibles")
decrypted = cipher.decrypt(encrypted)
```

**Kyber-1024 (Post-Quantum)**
```bash
# Instalación (cuando sea available en cryptography)
pip install liboqs-python
# Alternativa: usar liboqs-python directamente
```

### Blockchain GaiaChain 2.0
**Propósito:** Auditoría inmutable, trazabilidad de toda la cadena de suministro

**Integración:**
```python
# Implementado en castuo_graph/blockchain/gaiachain.py
gaiachain = GaiachainConnector(endpoint="https://gaiachain.eu")

# Registrar datos de sensores
gaiachain.register_hash({
    "temperature": 25,
    "humidity": 70,
    "timestamp": "2026-04-01T10:30:00Z"
})

# Crear cadena de custodia
gaiachain.create_supply_chain_record({
    "crop": "tomate",
    "harvest_date": "2026-06-15",
    "certifications": ["organic", "fair_trade"]
})
```

---

## 7. Stack Completo: Integración Ejemplo

```
┌─────────────────────────────────────────────────────────────┐
│                       Campo (Sensores IoT)                  │
├─────────────────────────────────────────────────────────────┤
│  Temperatura, Humedad, pH → MQTT Broker → Hetzner Dask      │
├─────────────────────────────────────────────────────────────┤
│                    Orquestación (LangGraph)                  │
│  ╔═══════════╗  ╔════════════╗  ╔══════════════╗           │
│  ║ Mistral   ║→ ║  Sabionda  ║→ ║   Síntesis   ║           │
│  ║ Analysis  ║  ║ Prediction ║  ║Recomendación║           │
│  ╚═══════════╝  ╚════════════╝  ╚══════════════╝           │
├─────────────────────────────────────────────────────────────┤
│                      Persistencia Datos                      │
│  PostGIS (QGIS) + TimescaleDB + IPFS (Arsys) + GaiaChain    │
├─────────────────────────────────────────────────────────────┤
│           Presentación (WordPress + Grafana)                │
│  n8n Webhook → WordPress (Informe) + Grafana (Métricas)    │
├─────────────────────────────────────────────────────────────┤
│                 Seguridad (Fernet + Kyber)                  │
│  Cifrado en tránsito (TLS) + Datos (AES-256)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Instalación & Operación

### Hetzner + k3s
```bash
# Desplegar todas las herramientas OSS
cd hetzner_infra
export TF_VAR_hcloud_token=<token>
export TF_VAR_ssh_key_id=<id>
terraform apply

# Acceder al servidor
ssh root@<IP_SERVER>
kubectl get pods -n castuo
```

### Validación
```bash
# Verificar servicios
curl http://servidor:5678  # n8n
curl http://servidor:3000  # Grafana
curl http://servidor:9090  # Prometheus
curl http://servidor:5001  # IPFS

# Monitoreo en tiempo real
kubectl logs -f -n castuo deployment/n8n
```

---

## 9. Referencias & Documentación

| Herramienta | Docs | Licencia | Soporte |
|---|---|---|---|
| QGIS | https://docs.qgis.org | GPL-2 | Community + Professional |
| CloudCompare | https://cloudcompare.org | GPL-2 | Community |
| OpenDroneMap | https://opendronemap.org | AGPL-3 | Community |
| Grafana | https://grafana.com/docs | AGPL-3 | Community + Enterprise |
| Prometheus | https://prometheus.io/docs | Apache 2.0 | Community |
| LangGraph | https://langchain-ai.github.io/langgraph | MIT | Community |
| n8n | https://docs.n8n.io | Source Available | Community + Cloud |
| IPFS | https://docs.ipfs.tech | Dual (MIT/Apache) | Community + Protocol Labs |
| GaiaChain | https://gaiachain.io | Enterprise | Enterprise |

---

**Última actualización:** 2026-04-01  
**Versión:** 2.0 (Excelencia Operativa)  
**Responsable:** CASTUO Technical Team
