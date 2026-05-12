# Guía de migración a Federated Learning con Cifrado Homomórfico (HE)

## 1. Requisitos previos

- Python 3.11+
- Dependencias: `tenseal`, `scikit-learn`, `numpy`
- Kubernetes 1.25+ (para despliegue en cluster)
- GaiaChain (registros de auditoría)

```bash
pip install tenseal scikit-learn numpy
```

## 2. Pasos de migración

### 2.1. Prueba inicial

```bash
# Prueba con 5 modelos de 3 capas x 100 neuronas
python backend/scripts/migrate_to_he_federated_learning.py \
  --test \
  --models 5 \
  --layers 3 \
  --layer-size 100
```

Comprobar en la salida:

- `max_diff` &lt; 0,01
- `avg_diff` &lt; 0,001
- `status`: `success`

### 2.2. Migración real

```bash
# Ejecutar migración (sin --dry-run por defecto; usar --no-dry-run para aplicar)
python backend/scripts/migrate_to_he_federated_learning.py --no-dry-run
```

Se generará `he_federated_coordinator_state.json` en la raíz del proyecto con la configuración del coordinador migrado.

### 2.3. Rotación de claves HE

```bash
# Rotación CKKS (simulación por defecto)
python backend/scripts/rotate_he_keys.py --scheme CKKS

# Rotación real
python backend/scripts/rotate_he_keys.py --scheme CKKS --no-dry-run
```

Verificación en GaiaChain (si está disponible):

```bash
curl http://gaiachain.castuo-system.eu/api/v1/events \
  --data '{"filters": {"type": "he_key_rotation"}}'
```

## 3. Configuración en Kubernetes

### 3.1. ConfigMap HE

Ver `kubernetes/he-configmap.yaml`: variables `SCHEME`, `POLY_MODULUS_DEGREE`, `COEFF_MOD_BIT_SIZES`, `OPTIMIZE_HE`, `CACHE_TTL`.

### 3.2. Deployment con HE

Ver `kubernetes/he-deployment.yaml`: coordinador con `USE_HE=true`, volúmenes para claves HE y referencias al ConfigMap.

### 3.3. CronJob de rotación

Ver `kubernetes/he-key-rotation-cronjob.yaml`: ejecución programada cada 90 días para rotación de claves HE.

## 4. Validación post-migración

### 4.1. Benchmark

```bash
# Antes
python backend/scripts/benchmark_federated_learning.py --format json > before.json

# Después
python backend/scripts/benchmark_federated_learning.py --format json > after.json

# Comparar (si existe jq)
jq '.models_per_second' before.json after.json
```

### 4.2. Informe de cumplimiento

```bash
python backend/scripts/generate_he_compliance_report.py --period last_30_days --output he_compliance_report.json
```

## 5. Solución de problemas

| Problema           | Causa probable        | Solución                          |
|--------------------|-----------------------|-----------------------------------|
| Error cifrado HE   | Versión Tenseal       | `pip install --upgrade tenseal`    |
| Diferencias &gt;0,01 | Precisión numérica HE | Ajustar `global_scale` en contexto |
| Alto uso memoria   | Modelo grande        | Reducir `poly_modulus_degree`     |
| Timeout agregación | Muchos participantes | Aumentar `cache_ttl`               |

## 6. Métricas de rendimiento esperadas

| Métrica             | Objetivo | Alerta   |
|---------------------|----------|----------|
| Tiempo de agregación| &lt;50 ms | &gt;100 ms |
| Uso de memoria      | &lt;200 MB | &gt;500 MB |
| Precisión           | &gt;99,9 % | &lt;99,5 % |
| Tasa de outliers    | &lt;0,1 % | &gt;0,5 % |

## 7. Cumplimiento normativo

| Requisito           | Normativa          | Implementación                |
|---------------------|--------------------|-------------------------------|
| Protección de datos | GDPR:Art.25        | Cifrado homomórfico + DBSCAN |
| Transparencia       | EU AI Act:Anexo IV | Registros en GaiaChain       |
| Control de acceso   | ISO 27001:A.9.1.1  | TLS 1.3                      |
| Registro actividades| GDPR:Art.30        | Eventos en GaiaChain         |

## 8. Uso del coordinador migrado en aplicación

Tras la migración, el estado se guarda en `he_federated_coordinator_state.json`. Para usar un coordinador con HE en código:

```python
from backend.ai.federated_learning import FederatedLearningCoordinator

# Coordinador con HE y DBSCAN
coordinator = FederatedLearningCoordinator(
    use_he=True,
    optimize_he=True,
    use_dbscan=True,
    use_quality_weights=True,
    cache_ttl=3600,
)

# Ronda de agregación (async)
result = await coordinator.coordinate_round(local_models)
```
