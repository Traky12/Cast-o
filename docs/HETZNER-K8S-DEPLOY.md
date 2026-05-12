# 🚀 Despliegue en Producción (Hetzner K8s)

## 📌 Prerequisitos

- **Hetzner Cloud Account** con un clúster Kubernetes (CX22 recomendado).
- **Registry privado** (`registry.castuo-system.cloud`) configurado.
- **GitHub Actions Secrets** configurados (ver [hetzner-prod-secrets.md](hetzner-prod-secrets.md)).
- `kubectl` disponible y autenticado contra el clúster (vía `HETZNER_KUBECONFIG`).

---

## 🔧 Pasos para Desplegar

### 1️⃣ Configurar los Secrets en GitHub

Ve a **Settings → Secrets and variables → Actions → New repository secret** y añade los siguientes secrets (ver [hetzner-prod-secrets.md](hetzner-prod-secrets.md)):

| Nombre | Descripción | Ejemplo |
|--------|-------------|---------|
| `HETZNER_KUBECONFIG` | Kubeconfig del clúster en base64 | `cat ~/.kube/config \| base64 -w0` |
| `REGISTRY_USER` | Usuario del registry | `Traky12` |
| `REGISTRY_PASSWORD` | Token del registry | `hcr_123456789abcdef` |
| `JWT_SECRET_KEY` | Clave JWT | `openssl rand -hex 32` |
| `GAIACHAIN_PRIVATE_KEY` | Clave privada de GaiaChain | `0x123...abc` |
| `DB_PASSWORD` | Contraseña de PostgreSQL | `S3cr3tP@ssw0rd!` |
| `N8N_BASIC_AUTH_USER` | Usuario de n8n | `admin` |
| `N8N_BASIC_AUTH_PASSWORD` | Contraseña de n8n | `openssl rand -base64 16` |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram _(opcional)_ | Crear con `@BotFather` |
| `TELEGRAM_CHAT_ID` | ID del chat de Telegram _(opcional)_ | Usar `@userinfobot` |

> Los secrets de Telegram son opcionales. Si no se configuran, el paso de notificación se omite sin afectar el despliegue.

---

### 2️⃣ Ejecutar el Workflow

1. Ve a **Actions → Deploy to Hetzner (Kubernetes)**.
2. Haz clic en **"Run workflow"** (rama `main`).
3. Espera a que todos los pasos se completen (≈5–10 minutos).

El pipeline sigue este orden:

```
validate-secrets  →  test-api  →  build-push  →  deploy  →  rollback (solo si falla deploy)
```

---

### 3️⃣ Verificar el Despliegue

**Pods:**

```bash
kubectl get pods -n castuo-system
```

Todos deben estar en `Running` y `READY`.

**HPA y red:**

```bash
kubectl get hpa -n castuo-system
kubectl get ingress -n castuo-system
```

**Endpoint de salud:**

```bash
curl -fsS https://api.castuo-system.cloud/health
# Respuesta esperada: {"status":"ok","version":"...","trl":9}
```

---

## 🔄 Rollback Manual

Si el despliegue falla y el job `rollback` no se ejecutó automáticamente:

```bash
kubectl rollout undo deployment/castuo-api -n castuo-system
kubectl rollout status deployment/castuo-api -n castuo-system --timeout=180s
```

---

## 🛠️ Resolución de Problemas

| Problema | Causa | Solución |
|---|---|---|
| `ImagePullBackOff` | Falta `imagePullSecrets` o credenciales del registry incorrectas. | Verifica que `regcred` exista (`kubectl get secret regcred -n castuo-system`) y que `imagePullSecrets` esté configurado en `deployment.yaml`. |
| `CrashLoopBackOff` | Error en la aplicación (ej. falta una variable de entorno). | Revisa los logs: `kubectl logs deployment/castuo-api -n castuo-system --previous` |
| `Pending` (pod sin nodo) | Recursos insuficientes en el clúster. | Escala el clúster en Hetzner o reduce `resources.requests` en `k8s/deployment.yaml`. |
| Healthcheck falla (`curl` 000/503) | Los pods no están listos dentro del timeout de 300 s. | Comprueba `kubectl describe pod -n castuo-system` y revisa eventos de error. |
| `validate-secrets` falla | Uno o más secrets no están configurados en GitHub Actions. | Añade los secrets que faltan en **Settings → Secrets and variables → Actions**. |

---

## 📚 Referencias

- [hetzner-prod-secrets.md](hetzner-prod-secrets.md) — Lista completa de secrets y cómo obtenerlos.
- [DEPLOYMENT.md](DEPLOYMENT.md) — Guía general de despliegue (local y Kubernetes).
- [ci-policies.md](ci-policies.md) — Políticas CI/CD y puertas de reconciliación.
- Workflow: `.github/workflows/deploy-to-hetzner.yml`
