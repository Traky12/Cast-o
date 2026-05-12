# Activación de agentes autónomos CASTÚO-SYSTEM™ v2.0

Runbook para activar, conectar y verificar los componentes críticos. Rutas y comandos adaptados a este repositorio (`backend/agents/`, `backend/scripts/`).

---

## 1. Infraestructura básica

| Componente | Acción | Comando / verificación |
|------------|--------|------------------------|
| Nodos Helsinki | Verificar conectividad | `ping ficolo-he1.castuo-system.eu` |
| Docker Swarm | Inicializar cluster | `docker swarm init` |
| Red overlay | Crear red | `docker network create --driver overlay --attachable castuo_network` |
| Firewall | Puertos 80, 443, 8080, 9090, 3000 | `ufw allow 80/tcp` (y resto) |
| Balanceador | Traefik/Nginx | `docker stack deploy -c traefik.yml traefik` |

**Verificación:**
```bash
docker node ls
docker network inspect castuo_network
```

**Volúmenes y almacenamiento:**
```bash
docker volume create gaiachain_data
docker volume inspect gaiachain_data
```

---

## 2. Seguridad y cifrado

| Componente | Acción | Comando |
|------------|--------|---------|
| Vault | Inicializar / desbloquear | `vault operator init` y `vault operator unseal` |
| Claves Kyber | Generar en Vault | `python backend/scripts/manage_vault_keys.py --init` (si existe) |
| Claves locales | Usar módulo PQC | Directorio `backend/security/keys/` o `CASTUO_KEY_DIR` |
| TLS | Let's Encrypt | `certbot certonly --nginx -d api.castuo-system.eu` |

**Verificación:**
```bash
vault status
# Claves locales (sin Vault):
python -c "from backend.security.pq_crypto import PostQuantumCrypto; c=PostQuantumCrypto(); print(c.kyber_encrypt('test'))"
```

---

## 3. Agentes autónomos

Los agentes viven en **`backend/agents/`**. Ejecución desde la raíz del repo:

| Agente | Comando | Verificación |
|--------|---------|--------------|
| Maestro | `python -m backend.agents.master_agent` (o script de arranque) | Logs / proceso |
| Self-Healing | `python -m backend.agents.selfhealing_agent` | Idem |
| IA (tunado) | `python -m backend.agents.ai_agent` | Idem |
| E-Commerce | `python -m backend.agents.ecommerce_agent` | Stub/config |
| Logística | `python -m backend.agents.logistics_agent` | Stub/config |
| Cumplimiento | `python -m backend.agents.compliance_agent` | Stub/config |

**Arranque en segundo plano (ejemplo en Linux):**
```bash
# Desde la raíz del repositorio
export PYTHONPATH="${PYTHONPATH:-.}:$(pwd)"

# Opción 1: script único
python backend/scripts/start_agents.py all --background --log-dir /var/log/castuo

# Opción 2: por proceso
nohup python -m backend.agents.master_agent > /var/log/castuo/master_agent.log 2>&1 &
nohup python -m backend.agents.selfhealing_agent > /var/log/castuo/selfhealing_agent.log 2>&1 &
nohup python -m backend.agents.ai_agent > /var/log/castuo/ai_agent.log 2>&1 &
nohup python -m backend.agents.ecommerce_agent >> /var/log/castuo/agents.log 2>&1 &
nohup python -m backend.agents.logistics_agent >> /var/log/castuo/agents.log 2>&1 &
nohup python -m backend.agents.compliance_agent >> /var/log/castuo/agents.log 2>&1 &
```

**Verificación:**
```bash
ps aux | grep "backend.agents"
tail -f /var/log/castuo/master_agent.log
```

---

## 4. Comunicación entre agentes (RabbitMQ / Redis)

| Componente | Acción | Comando |
|------------|--------|---------|
| RabbitMQ | Contenedor | `docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management` |
| Redis | Contenedor | `docker run -d --name redis -p 6379:6379 redis` |

Variables de entorno recomendadas: `RABBITMQ_URL`, `REDIS_URL`. Si no están, los agentes que usen `message_bus` harán fallback o no publicarán.

**Verificación:**
```bash
docker exec rabbitmq rabbitmq-diagnostics status
redis-cli ping
```

---

## 5. E-Commerce y logística

| Componente | Acción |
|------------|--------|
| Shopify | Webhooks en Shopify Admin → Settings → Notifications |
| Stripe | `stripe listen --forward-to localhost:8000/api/payments/webhook` |
| Packlink | `export PACKLINK_API_KEY="..."` en `.env` |
| Scripts | `python backend/scripts/load_products.py` (si existe), etc. |

---

## 6. Monitoreo (Prometheus / Grafana)

| Componente | Acción |
|------------|--------|
| Prometheus | Usar `docker/docker-compose.monitoring.yml` o configurar `prometheus.yml` |
| Grafana | Importar dashboards; puerto 3000 |
| Alertas | Slack: `SLACK_WEBHOOK` en secrets / .env |

**Verificación:**
```bash
curl -s http://localhost:9090/api/v1/query?query=up
curl -u admin:admin http://localhost:3000/api/dashboards/db
```

---

## 7. CI/CD y git hooks

| Componente | Acción |
|------------|--------|
| GitHub Actions | Secrets: `MISTRAL_API_KEY_EU`, `VAULT_ADDR`, `VAULT_TOKEN` |
| Workflow | `.github/workflows/autonomous_deployment.yml` se dispara en push a `main` |
| Hooks | Copiar plantillas: `cp docs/git-hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit` |

**Verificación:**
```bash
git add . && git commit -m "test: activación agentes"   # dispara pre-commit
gh workflow run autonomous_deployment.yml   # si usa gh
```

---

## 8. Cumplimiento normativo

| Componente | Acción |
|------------|--------|
| GaiaChain | Verificar API de eventos (si existe): `curl http://gaiachain.castuo-system.eu/api/v1/events` |
| ISO 27001 | `python backend/scripts/generate_iso_report.py` (si existe) |
| GDPR | `python backend/scripts/verify_gdpr_compliance.py` (si existe) |

---

## 9. Pruebas finales

| Prueba | Comando |
|--------|---------|
| Cifrado PQC | `python -m pytest backend/security/tests/test_pq_crypto.py -v` |
| Self-healing | `docker stop backend` (o nombre del servicio) y revisar logs del agente |
| Salud API | `curl -s http://api.castuo-system.eu/health` o equivalente local |

---

## 10. Checklist final

| Categoría | Item | Comando verificación |
|-----------|------|----------------------|
| Infra | Nodos / red | `docker node ls`; `docker network inspect castuo_network` |
| Seguridad | Vault / claves PQC | `vault status`; test `PostQuantumCrypto` |
| Agentes | Maestro y Self-Healing en ejecución | `ps aux \| grep backend.agents`; `tail /var/log/castuo/*.log` |
| Mensajería | RabbitMQ / Redis | `docker exec rabbitmq rabbitmq-diagnostics status`; `redis-cli ping` |
| Monitoreo | Prometheus / Grafana | `curl http://localhost:9090/api/v1/query?query=up` |
| CI/CD | Workflows y hooks | GitHub Actions tab; `git commit` con pre-commit |
| Cumplimiento | GaiaChain / informes | `curl .../api/v1/events`; scripts en `backend/scripts/` |

---

## Despliegue con Docker Compose

Para levantar agentes y servicios asociados (Ollama, etc.):

```bash
docker-compose -f docker-compose.agents.yml up -d
# Producción (cuando esté definido):
# docker stack deploy -c docker-compose.prod.yml castuo
```

---

## Arquitectura federada (resumen)

- **Núcleo:** Mistral AI (cliente en `backend/ai/mistral_client.py`).
- **Agentes:** Maestro, Self-Healing, IA tunado, E-Commerce, Logística, Cumplimiento en `backend/agents/`.
- **Comunicación:** RabbitMQ vía `backend/agents/message_bus.py`; protocolo en `backend/agents/protocol.py`.
- **Conocimiento y modelos:** `backend/ai/knowledge_base.py`, `backend/ai/model_registry.py`, `backend/ai/federated_learning.py`.
- **Cifrado:** `backend/security/pq_crypto.py` (Kyber-1024, Dilithium-5, Blake3).

Normativas integradas en prompts y registros: ISO 27001, GDPR, NIS2, EU AI Act, Ley 3/2023 Extremadura.
