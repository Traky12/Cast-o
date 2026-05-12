# Secretos requeridos — Deploy Hetzner Producción

El workflow `deploy-to-hetzner.yml` necesita los siguientes **GitHub Actions Secrets** configurados en:

> **Settings → Secrets and variables → Actions → New repository secret**

---

## Secretos obligatorios

| Nombre | Descripción | Cómo obtenerlo |
|---|---|---|
| `HETZNER_KUBECONFIG` | Kubeconfig del clúster Kubernetes de Hetzner, codificado en **base64** | `cat ~/.kube/config \| base64 -w0` en el control-plane, o `hcloud kubeconfig get <cluster>` |
| `REGISTRY_USER` | Usuario del registry privado `registry.castuo-system.cloud` | Panel del registry / hcloud |
| `REGISTRY_PASSWORD` | Contraseña / token del registry privado | Panel del registry / hcloud |
| `JWT_SECRET_KEY` | Clave de firma JWT para la API de producción | Generar con `openssl rand -hex 32` |
| `GAIACHAIN_PRIVATE_KEY` | Clave privada hex de la cuenta GaiaChain | Wallet de producción |
| `DB_PASSWORD` | Contraseña de la base de datos PostgreSQL de producción | Configuración de la base de datos |
| `N8N_BASIC_AUTH_USER` | Usuario de autenticación básica para n8n | Elegir libremente (ej. `admin`) |
| `N8N_BASIC_AUTH_PASSWORD` | Contraseña de autenticación básica para n8n | Generar con `openssl rand -base64 16` |

## Secretos opcionales (notificaciones)

| Nombre | Descripción | Cómo obtenerlo |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram para notificaciones de despliegue | Crear un bot con `@BotFather` en Telegram |
| `TELEGRAM_CHAT_ID` | ID del chat/canal donde se enviarán las notificaciones | Usar `@userinfobot` o la API `getUpdates` |

> Si no se configuran, el paso de notificación se omite automáticamente sin fallar el workflow.

---

## Qué hace el workflow con cada secreto

1. **`HETZNER_KUBECONFIG`** — Se decodifica en base64 y se escribe en `~/.kube/config` para autenticar `kubectl` contra el clúster.
2. **`REGISTRY_USER` / `REGISTRY_PASSWORD`** — Se usan en dos pasos:
   - `docker/login-action` para hacer push de la imagen construida.
   - `kubectl create secret docker-registry regcred` para que los pods puedan hacer pull de la imagen privada.
3. **`JWT_SECRET_KEY`, `GAIACHAIN_PRIVATE_KEY`, `DB_PASSWORD`, `N8N_BASIC_AUTH_USER`, `N8N_BASIC_AUTH_PASSWORD`** — Se inyectan como el Secret de Kubernetes `castuo-secrets` (tipo `Opaque`), que los pods montan vía `envFrom`/`secretKeyRef`.
4. **`TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`** _(opcionales)_ — Si están presentes, el paso `Notify deployment status` envía un mensaje de Telegram al finalizar el job `deploy` (éxito o fallo). Si no están configurados, el paso se omite sin error.

---

## Verificar secretos ya configurados

```bash
gh secret list --repo Traky12/Castuo-system
```

## Disparar el deploy manualmente (una vez configurados los secretos)

```bash
gh workflow run deploy-to-hetzner.yml --repo Traky12/Castuo-system --ref main
```

O desde la UI: **Actions → Deploy to Hetzner (Kubernetes) → Run workflow → main**.

---

## Orden de despliegue

```
validate-secrets  →  test-api  →  build-push  →  deploy  →  rollback (solo si falla deploy)
```

El job `deploy` aplica los manifiestos en este orden:

1. `k8s/namespace.yaml`
2. `k8s/configmap.yaml`
3. `castuo-secrets` (Secret genérico desde GitHub Secrets)
4. `regcred` (Secret docker-registry para pull de imágenes)
5. `k8s/pvc.yaml`, `k8s/service.yaml`, `k8s/ingress.yaml`, `k8s/hpa.yaml`
6. `k8s/deployment.yaml`
7. `kubectl set image` con el tag construido en `build-push`

El healthcheck final valida `https://api.castuo-system.cloud/health`.
