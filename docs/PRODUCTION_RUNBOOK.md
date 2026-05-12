# Runbook de Producción — CASTÚO-SYSTEM™ v2.1

## 1. Procedimientos de emergencia

### 1.1. Fallo en el coordinador FL

**Síntomas**

- Pods en CrashLoopBackOff
- Errores 500 en `/health`
- Alertas `HighFLLatency` en Grafana

**Acciones**

1. Revisar logs:
   ```bash
   kubectl logs -n castuo-prod -l app=secure-federated-coordinator --tail=100 --previous
   ```

2. Reiniciar el deployment:
   ```bash
   kubectl rollout restart deployment/secure-federated-coordinator -n castuo-prod
   ```

3. Si persiste, escalar temporalmente:
   ```bash
   kubectl scale deployment/secure-federated-coordinator -n castuo-prod --replicas=5
   ```

4. Notificar al equipo de seguridad (Slack/PagerDuty según procedimiento interno).

---

### 1.2. Problemas de rendimiento

**Síntomas**

- Latencia >100 ms en agregación
- Uso de CPU >90 %
- Alertas `LowFLThroughput`

**Acciones**

1. Revisar métricas:
   ```bash
   kubectl top pod -n castuo-prod -l app=secure-federated-coordinator
   ```

2. Ajustar HPA (aumentar margen de CPU):
   ```bash
   kubectl edit hpa secure-federated-coordinator -n castuo-prod
   # Aumentar target averageUtilization de CPU a 80 si procede
   ```

3. Desactivar optimización HE de forma temporal:
   ```bash
   kubectl set env deployment/secure-federated-coordinator -n castuo-prod OPTIMIZE_HE=false
   ```

---

## 2. Procedimientos de mantenimiento

### 2.1. Rotación de claves HE

- **Frecuencia**: Cada 90 días (CronJob) o manual cuando se requiera.

**Procedimiento manual**

```bash
kubectl create job -n castuo-prod --from=cronjob/he-key-rotation manual-key-rotation-$(date +%s)
kubectl describe secret he-keys -n castuo-prod
kubectl rollout restart deployment/secure-federated-coordinator -n castuo-prod
```

### 2.2. Backup de trazabilidad

**Procedimiento manual**

```bash
# Exportar cadena (se guarda cifrada en el pod)
kubectl exec -n castuo-prod deploy/secure-federated-coordinator -- \
  python -m backend.scripts.verify_traceability_chain --export /var/traceability/backup_$(date +%Y%m%d).json

# Copiar al host (ajustar nombre del pod si hace falta)
kubectl cp castuo-prod/$(kubectl get pods -n castuo-prod -l app=secure-federated-coordinator -o jsonpath='{.items[0].metadata.name}'):/var/traceability/backup_*.json ./backups/
```

---

## 3. Contactos de soporte

| Área        | Responsable   | Contacto                  | Horario    |
|------------|---------------|---------------------------|------------|
| Seguridad  | (definir)     | security@castuo-system.eu | 24/7       |
| Operaciones| (definir)     | ops@castuo-system.eu      | 24/7       |
| Cumplimiento | (definir)   | compliance@castuo-system.eu | L–V 9–18 CET |
| Soporte N1 | (definir)     | support@castuo-system.eu  | 24/7       |
| Desarrollo | (definir)     | dev@castuo-system.eu      | L–V 8–20 CET |

---

## 4. Métricas clave a monitorear

| Métrica                  | Umbral crítico | Comando de verificación                          |
|--------------------------|----------------|--------------------------------------------------|
| Latencia agregación FL   | >100 ms        | `kubectl exec -n castuo-prod ... benchmark`      |
| Uso de memoria           | >1.8 Gi        | `kubectl top pod -n castuo-prod`                 |
| Tasa de errores FL       | >0.1 %         | `kubectl logs -n castuo-prod \| grep ERROR`      |
| Tiempo de respuesta API  | >200 ms        | `curl -w "%{time_total}s" http://api/health`     |
| Uso de CPU               | >80 %          | `kubectl top pod -n castuo-prod`                 |
| Tasa de éxito agregación | <99.9 %        | Métricas Prometheus / script de métricas         |

---

## 5. Procedimientos de escalado

### 5.1. Escalado horizontal

```bash
kubectl scale deployment/secure-federated-coordinator -n castuo-prod --replicas=8
kubectl edit hpa secure-federated-coordinator -n castuo-prod  # Ajustar maxReplicas si procede
```

### 5.2. Escalado vertical

```bash
kubectl set resources deployment/secure-federated-coordinator -n castuo-prod \
  --limits=cpu=4,memory=4Gi \
  --requests=cpu=2,memory=2Gi
```

### 5.3. Ajuste de parámetros HE

```bash
kubectl set env deployment/secure-federated-coordinator -n castuo-prod OPTIMIZE_HE=false
kubectl set env deployment/secure-federated-coordinator -n castuo-prod ENCRYPTION_ALGORITHM=RSA4096_AES256_GCM
```

---

## 6. Rollback

```bash
kubectl rollout undo deployment/secure-federated-coordinator -n castuo-prod
# o fijar imagen anterior:
kubectl set image deployment/secure-federated-coordinator -n castuo-prod coordinator=ghcr.io/tu-organizacion/castuo-system:v2.0-prod
kubectl rollout status deployment/secure-federated-coordinator -n castuo-prod
```
