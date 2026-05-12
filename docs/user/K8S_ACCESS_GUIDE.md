# Acceso a Kubernetes vía bastión

**Versión:** 1.0  
**Ámbito:** plantilla operativa; ajustar nombres DNS y certificados del clúster.

## 1. Requisitos

- Clave SSH autorizada en `docker/remote-access/bastion/authorized_keys`.
- `kubectl` local.
- Red Docker `castuo_remote` creada antes de `docker-compose/bastion.yml`.

## 2. Túnel

```bash
docker network create castuo_remote 2>/dev/null || true
docker compose -f docker-compose/bastion.yml up -d
```

Ajusta variables y ejecuta:

```bash
export BASTION_HOST=tu-bastion.example
bash scripts/remote-access/connect_k8s.sh ctaex
```

En otra terminal, configura `kubeconfig` para `https://127.0.0.1:6443` (o el puerto local elegido) usando el **mismo mecanismo de autenticación** que defina tu proveedor (token de SA, certificado de cliente, OIDC, etc.). Los comandos genéricos que mezclan `kubectl` dentro y fuera del clúster suelen ser **incorrectos** sin adaptación.

## 3. Comprobación

```bash
kubectl get ns
```

Si falla TLS, importa el `ca.crt` del plano de control o usa el flag que corresponda según política de seguridad (no usar `--insecure-skip-tls-verify` en producción).
