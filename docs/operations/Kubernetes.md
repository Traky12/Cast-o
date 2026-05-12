# Despliegue Kubernetes — CASTÚO-SYSTEM

**Objetivo**: Orquestación de microservicios en Hetzner Cloud (u otro). Escalabilidad y alta disponibilidad.

---

## Componentes

- **Cluster**: Kubernetes (kubeadm, EKS, GKE o Hetzner K3s según elección).
- **Manifiestos**: Deployments (backend, workers Celery), Services, Ingress, ConfigMaps/Secrets.
- **CI/CD**: Build de imágenes Docker y despliegue (GitHub Actions, GitLab CI o similar).

---

## Comando de referencia

```bash
kubectl apply -f deployment.yaml
```

---

## Documentación relacionada

- [Plan de Infraestructura](Infrastructure-Plan.md)
- [Roadmap 2026–2031](../validation/evolution/Roadmap-2026-2031.md)
- Docker: `docker/docker-compose.v2-production.yml`
