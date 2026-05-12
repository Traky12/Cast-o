# Runbook de Despliegue Satelital en Hetzner

Objetivo: desplegar una unica plataforma operativa con ingestión satelital, analítica NDVI/NDMI, trazabilidad blockchain y automatización n8n/Kafka, con validación GO/NO-GO.

## 0) Prerrequisitos

- Acceso al cluster Hetzner/K3s con kubectl.
- Secretos cargados en .env y carpeta secrets/.
- Docker disponible si se construyen imagenes localmente.

## 1) Preflight de secretos y entorno

Ejecutar desde la raiz del repo:

source .env
bash scripts/validate_secrets.sh

Criterio GO:
- All required secrets are present

## 2) Configurar kubectl para Hetzner

Metodo recomendado (variable base64):

bash scripts/configure-kubectl-hetzner.sh --from-env-b64

Metodo alternativo (extraccion por SSH):

bash scripts/configure-kubectl-hetzner.sh --from-ssh --server-ip 89.167.5.233 --ssh-user root --ssh-key ~/.ssh/castuo_hel1

Verificar:

kubectl get nodes

Criterio GO:
- Nodo(s) en Ready

## 3) Construir y publicar imagenes

Si se usa registry externo, ajustar nombre de imagen en manifests de k8s y publicar:

docker-compose -f docker-compose.satellite.yml build
docker-compose -f docker-compose.satellite.yml push

Criterio GO:
- Build y push sin errores

## 4) Aplicar stack en Kubernetes por capas

Aplicar en orden:

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/satellite/
kubectl apply -f k8s/storage/
kubectl apply -f k8s/blockchain/
kubectl apply -f k8s/kafka/
kubectl apply -f k8s/api/

Criterio GO:
- Todos los apply con configured o created sin errores de schema

## 5) Verificaciones operativas GO/NO-GO

Validacion automatica principal:

bash scripts/validate_deployment.sh

Validaciones manuales complementarias:

kubectl get pods -n castuo-system
kubectl get hpa -n castuo-system
kubectl logs deployment/stac-ingestion -n castuo-system --tail=200
kubectl get svc -n castuo-system

Smoke API interna (desde pod o bastion con DNS cluster):

kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl -- \
  curl -sS http://satellite-api-service.castuo-system.svc.cluster.local/health

Criterio GO:
- >= 90% pods Running
- HPAs visibles y sin errores
- stac-ingestion sin ERROR critico
- satellite-api-service disponible
- health HTTP 200

## 6) Importar workflow n8n de alertas NDVI

Workflow listo en:
- n8n/workflows/satellite-ndvi-alerts.json

Pasos:
- Importar JSON en n8n.
- Configurar credenciales Kafka y endpoint de alertas.
- Definir NDVI_THRESHOLD si procede.

Criterio GO:
- Mensajes ndvi-alerts generan alertas cuando NDVI < threshold.

## 7) Rollback rapido

Si falla una capa concreta:

kubectl rollout undo deployment/stac-ingestion -n castuo-system
kubectl rollout undo deployment/ndvi-worker -n castuo-system
kubectl rollout undo deployment/ndmi-worker -n castuo-system
kubectl rollout undo deployment/satellite-api -n castuo-system
kubectl rollout undo deployment/evidence-registrar -n castuo-system
kubectl rollout undo deployment/kafka -n castuo-system
kubectl rollout undo deployment/minio -n castuo-system

Rollback total de capa satelital:

kubectl delete -f k8s/api/
kubectl delete -f k8s/kafka/
kubectl delete -f k8s/blockchain/
kubectl delete -f k8s/storage/
kubectl delete -f k8s/satellite/

## 8) Evidencia de auditoria

Guardar salida de:

git rev-parse HEAD
kubectl get pods -n castuo-system -o wide
kubectl get hpa -n castuo-system
bash scripts/validate_deployment.sh

Recomendado: almacenar en artifacts/ y adjuntar a PR o reporte operativo.
