# Guía de incorporación de nuevos nodos FL

## 1. Requisitos previos

- Docker 20.10+
- Kubernetes 1.25+
- Acceso al registro de imágenes (`ghcr.io/tu-organizacion`)
- Clave pública del coordinador (o procedimiento para obtenerla)

## 2. Configuración del nodo

### 2.1. Generación de claves del nodo

Ejecutar en un entorno seguro:

```bash
python -c "
from backend.security.end_to_end_encryption import EndToEndEncryption
e = EndToEndEncryption()
_, public_key = e.generate_key_pair()
with open('node-public-key.pem', 'wb') as f:
    f.write(public_key)
print('Clave pública guardada en node-public-key.pem')
"
```

### 2.2. Despliegue del nodo

Plantilla de deployment (sustituir `{{NODE_ID}}` por el identificador del nodo):

```yaml
# kubernetes/node-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fl-node-{{NODE_ID}}
  namespace: castuo-prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fl-node
      node-id: "{{NODE_ID}}"
  template:
    metadata:
      labels:
        app: fl-node
        node-id: "{{NODE_ID}}"
    spec:
      containers:
      - name: node
        image: ghcr.io/tu-organizacion/castuo-system:v2.1-node
        env:
        - name: NODE_ID
          value: "{{NODE_ID}}"
        volumeMounts:
        - name: node-keys
          mountPath: /etc/node-keys
      volumes:
      - name: node-keys
        secret:
          secretName: node-{{NODE_ID}}-keys
```

Crear el secret con la clave pública del nodo:

```bash
kubectl create secret generic node-{{NODE_ID}}-keys -n castuo-prod --from-file=public-key.pem=node-public-key.pem
```

### 2.3. Registro en el coordinador

El coordinador debe registrar la clave pública del nuevo nodo. Si existe un endpoint o script de registro, usarlo. En caso contrario, registrar en código o configuración:

- Añadir la clave pública del nodo al mapa `node_public_keys` del `SecureFederatedLearningCoordinator` (por ejemplo vía API de administración o ConfigMap/Secret que el coordinador lea al arrancar).

Ejemplo conceptual (ejecutar en el contexto del coordinador o mediante un Job que se conecte al servicio del coordinador):

```python
from backend.ai.secure_federated_learning import SecureFederatedLearningCoordinator
from backend.security.end_to_end_encryption import EndToEndEncryption

with open('/path/to/node-public-key.pem', 'rb') as f:
    node_public_key = f.read()

# Obtener instancia del coordinador (según arquitectura: singleton, inyector, etc.)
# coordinator.register_node('NODE_ID', node_public_key)
```

## 3. Validación del nodo

### 3.1. Conectividad

Comprobar que el nodo puede alcanzar al coordinador y a los servicios necesarios (mensajería, GaiaChain, etc.) según la arquitectura desplegada.

### 3.2. Participación en una ronda FL

Ejecutar una ronda de prueba (por ejemplo con el script de migración en modo test o un script de participación) y comprobar que el nodo aparece en los metadatos de la ronda y que la agregación termina correctamente.

## 4. Monitoreo del nodo

```bash
kubectl logs -n castuo-prod deploy/fl-node-{{NODE_ID}} --tail=50 -f
kubectl get pods -n castuo-prod -l node-id={{NODE_ID}}
```

## 5. Procedimiento de retiro

1. Desregistrar el nodo en el coordinador (quitar su entrada de `node_public_keys` o mediante API de administración).
2. Eliminar el deployment del nodo:
   ```bash
   kubectl delete deployment fl-node-{{NODE_ID}} -n castuo-prod
   ```
3. Opcional: eliminar el secret del nodo:
   ```bash
   kubectl delete secret node-{{NODE_ID}}-keys -n castuo-prod
   ```
