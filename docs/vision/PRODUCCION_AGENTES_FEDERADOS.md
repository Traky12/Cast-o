# Puesta en producción — Sistema de agentes federados CASTÚO-SYSTEM™ v2.0

Guía para desplegar en producción el sistema de agentes autónomos con Mistral AI, RabbitMQ, Vault y cifrado post-cuántico.

---

## Resumen de implementación para producción

**Novedades clave:**

1. **Variables de entorno (`.env.example`)**  
   Bloque *Agentes federados v2.0*: `MISTRAL_API_KEY_EU`, `VAULT_ADDR`, `VAULT_TOKEN`, `CASTUO_KEY_DIR`, `RABBITMQ_*`, `PROMETHEUS_URL`, `GRAFANA_URL`.  
   `MISTRAL_API_KEY_EU` es obligatorio para los agentes de IA. Si no se define `CASTUO_KEY_DIR`, se usa `backend/security/keys`.

2. **Gestión de claves con Vault (`backend/scripts/manage_vault_keys.py`)**  
   - **--init:** Genera claves Kyber-1024 y Dilithium-5 con `PostQuantumCrypto`, las sube a Vault en `castuo/keys/kyber` y `castuo/keys/dilithium`. Habilita el motor `kv-v2` en `castuo/` si no existe.  
   - **--load:** Lee claves de Vault y las escribe en `CASTUO_KEY_DIR` (permisos 600 en privadas).  
   Requiere `hvac`, Vault desbloqueado y política `castuo-admin`.

3. **Política Vault (`backend/policies/castuo-admin.hcl`)**  
   Permisos sobre `castuo/data/*`, `castuo/metadata/*` (solo list) y `sys/mounts/castuo` para que el script pueda crear el motor.  
   Aplicar: `vault policy write castuo-admin backend/policies/castuo-admin.hcl`.

4. **Agente de IA**  
   Opción `--federated-learning` para ejecutar solo el bucle de mejora continua / federated learning:  
   `python -m backend.agents.ai_agent --federated-learning`.

---

## 1. Configuración inicial

```bash
# 1. Clonar el repositorio (si no está clonado)
git clone https://github.com/tu-organizacion/castuo-system.git
cd castuo-system

# 2. Variables de entorno
cp .env.example .env
# Editar .env con: MISTRAL_API_KEY_EU, VAULT_ADDR, VAULT_TOKEN, RABBITMQ_*, etc.

# 3. Dependencias
pip install -r requirements.txt
# Opcional para agentes/Vault:
pip install mistralai pika hvac
```

Variables relevantes en `.env` (ver `.env.example`):

- **MISTRAL_API_KEY_EU** — Obligatorio para agentes de IA. Clave EU recomendada para cumplimiento.
- **VAULT_ADDR**, **VAULT_TOKEN** — Opcional. Si no se configura, se usan claves locales en `backend/security/keys`.
- **CASTUO_KEY_DIR** — Opcional. Por defecto `backend/security/keys` (no `/etc/castuo/keys` salvo que se defina).
- **RABBITMQ_HOST**, **RABBITMQ_PORT**, **RABBITMQ_USER**, **RABBITMQ_PASSWORD** — RabbitMQ (comunicación entre agentes).
- **PROMETHEUS_URL** — Prometheus (Agente Maestro).
- **GRAFANA_URL** — Grafana (dashboards).

---

## 2. Infraestructura con Docker

```bash
# 1. Levantar servicios (ajustar según tu compose)
docker-compose -f docker-compose.prod.yml up -d

# 2. Comprobar servicios
docker compose -f docker-compose.prod.yml ps
# Objetivo: rabbitmq, vault, prometheus, grafana, backend, frontend

# 3. Red overlay (si usas Swarm)
docker network create --driver overlay --attachable castuo_network
```

---

## 3. Vault: inicialización y políticas

```bash
# 1. Inicializar Vault (solo la primera vez)
vault operator init -key-shares=5 -key-threshold=3
# Guardar las 5 keys y el root token en lugar seguro

# 2. Desbloquear
vault operator unseal [KEY1]
vault operator unseal [KEY2]
vault operator unseal [KEY3]

# 3. Política y motor KV v2
vault policy write castuo-admin backend/policies/castuo-admin.hcl
vault secrets enable -path=castuo kv-v2

# 4. Comprobar
vault status
# Sealed: false
```

---

## 4. RabbitMQ: usuario y permisos

```bash
# 1. Comprobar contenedor
docker ps | grep rabbitmq

# 2. Usuario y permisos (ajustar usuario/contraseña en .env)
docker exec rabbitmq rabbitmqctl add_user castuo secure_password
docker exec rabbitmq rabbitmqctl set_user_tags castuo administrator
docker exec rabbitmq rabbitmqctl set_permissions -p / castuo ".*" ".*" ".*"

# 3. Colas (se crean al arrancar los agentes; opcional listar)
docker exec rabbitmq rabbitmqctl list_queues
```

---

## 5. Claves post-cuánticas (Kyber / Dilithium)

```bash
# 1. Generar claves locales y subirlas a Vault
export VAULT_ADDR=http://vault:8200   # o localhost si Vault está en el host
export VAULT_TOKEN=<root-token>
export CASTUO_KEY_DIR=/etc/castuo/keys   # o dejar por defecto (backend/security/keys)
python backend/scripts/manage_vault_keys.py --init

# 2. En otro host o tras reinicio: cargar desde Vault al disco
python backend/scripts/manage_vault_keys.py --load

# 3. Comprobar
ls -la "$CASTUO_KEY_DIR"
# kyber_public.pem, kyber_private.pem, dilithium_public.pem, dilithium_private.pem
```

Si no usas Vault, las claves se generan solas en `CASTUO_KEY_DIR` o en `backend/security/keys` al usar `PostQuantumCrypto`.

---

## 6. Git hooks (pre-commit / post-merge)

```bash
cp docs/git-hooks/pre-commit .git/hooks/pre-commit
cp docs/git-hooks/post-merge .git/hooks/post-merge
chmod +x .git/hooks/pre-commit .git/hooks/post-merge
```

---

## 7. Arranque de agentes

```bash
# Desde la raíz del repo
export PYTHONPATH="${PYTHONPATH:-.}:$(pwd)"

# Opción A: script único (todos en segundo plano)
python backend/scripts/start_agents.py all --background --log-dir ./logs

# Opción B: procesos individuales
nohup python -m backend.agents.master_agent > logs/master_agent.log 2>&1 &
nohup python -m backend.agents.selfhealing_agent > logs/selfhealing_agent.log 2>&1 &
nohup python -m backend.agents.ai_agent > logs/ai_agent.log 2>&1 &
nohup python -m backend.agents.ecommerce_agent >> logs/agents.log 2>&1 &
nohup python -m backend.agents.logistics_agent >> logs/agents.log 2>&1 &
nohup python -m backend.agents.compliance_agent >> logs/agents.log 2>&1 &

# Opción C: solo Agente de IA en modo federated learning (segundo plano)
nohup python -m backend.agents.ai_agent --federated-learning >> logs/ai_federated.log 2>&1 &
```

Comprobar:

```bash
ps aux | grep "backend.agents"
tail -f logs/master_agent.log
```

---

## 8. Verificación de funcionamiento

**Agente de IA (recomendaciones):**

```bash
python -c "
import asyncio
from backend.agents.ai_agent import TunedAIAgent
agent = TunedAIAgent()
r = asyncio.run(agent.get_recommendations('user123', 'MG-BRO-100G', []))
print(r)
"
```

**Bus de mensajes (RabbitMQ):**

```bash
python -c "
from backend.agents.message_bus import AgentMessageBus
bus = AgentMessageBus('test_agent')
bus.publish('ecommerce', {'type': 'test', 'content': 'Hola desde test_agent'})
print('Mensaje publicado')
"
```

**Cifrado PQC:**

```bash
python -m pytest backend/security/tests/test_pq_crypto.py -v
```

**Prometheus:**

```bash
curl -s "http://localhost:9090/api/v1/query?query=up"
```

---

## 9. Checklist final

| Categoría      | Item              | Comando de verificación                    | Resultado esperado        |
|----------------|-------------------|--------------------------------------------|---------------------------|
| Infraestructura| Docker Compose    | `docker compose -f docker-compose.prod.yml ps` | Todos los servicios Up   |
| Vault          | Estado            | `vault status`                             | Sealed: false             |
| RabbitMQ       | Colas             | `docker exec rabbitmq rabbitmqctl list_queues` | Colas `agent.*` creadas   |
| Seguridad      | Claves Kyber/Dilithium | `ls -la $CASTUO_KEY_DIR` o `backend/security/keys` | Archivos .pem presentes  |
| Cifrado        | Tests PQC         | `python -m pytest backend/security/tests/test_pq_crypto.py -v` | Todos los tests pasan    |
| Agentes        | Agente Maestro    | `ps aux \| grep master_agent`              | Proceso en ejecución      |
| Agentes        | Self-Healing      | `tail -n 20 logs/selfhealing_agent.log`    | Logs de verificación de integridad |
| IA             | Recomendaciones   | `python -c "import asyncio; from backend.agents.ai_agent import TunedAIAgent; print(asyncio.run(TunedAIAgent().get_recommendations('user123','MG-BRO-100G',[])))"` | JSON con recomendaciones |
| Mensajería     | RabbitMQ          | `docker exec rabbitmq rabbitmqctl status`  | running                   |
| Mensajería     | Publicación       | `python -c "from backend.agents.message_bus import AgentMessageBus; bus=AgentMessageBus('test'); bus.publish('ecommerce', {'test': True})"` | Sin errores               |
| Git hooks      | pre-commit        | `git add . && git commit -m "test"`        | Análisis con Mistral (si configurado) |
| Git hooks      | post-merge        | `git checkout -b test-branch && git merge main` | Mejoras propuestas (si hay cambios) |
| Monitoreo      | Prometheus        | `curl http://localhost:9090/api/v1/query?query=up` | status: success           |
| Monitoreo      | Grafana           | Abrir http://localhost:3000                | Dashboards accesibles     |
| Cumplimiento   | GaiaChain         | `curl http://gaiachain.castuo-system.eu/api/v1/events` | Eventos registrados       |
| Cumplimiento   | ISO 27001         | `python backend/scripts/generate_iso_report.py` | Informe generado en compliance/ |

---

## 10. Próximos pasos recomendados

**Escalar el sistema (Docker Swarm):**
```bash
docker swarm join --token <token> <manager-ip>:2377
```

**Federated Learning programado (cron, cada 6 horas):**
```bash
0 */6 * * * cd /ruta/castuo-system && python -m backend.agents.ai_agent --federated-learning >> /var/log/castuo/federated_learning.log 2>&1
```

**Monitoreo avanzado:** configurar alertas en Grafana (p. ej. CPU > 80%, dashboard «CASTÚO-SYSTEM™ / E-Commerce»).

**Pruebas de carga (Locust):**
```bash
locust -f backend/tests/load_test.py --headless -u 1000 -r 100 --host=http://api.castuo-system.eu
```
(Si existe el script `backend/tests/load_test.py`.)

**Documentación automática:**
```bash
python backend/scripts/generate_docs.py --output docs/generated/
```
(Si existe el script.)

---

## 11. Notas finales

**Dependencias opcionales**

- **Vault:** Si no se configura, el sistema usa claves locales en `backend/security/keys`.
- **RabbitMQ:** Si no está disponible, los agentes siguen funcionando con comunicación directa (menos escalable).
- **Prometheus/Grafana:** Si no están configurados, los agentes solo registran en logs locales.

**Seguridad**

- Las comunicaciones entre agentes pueden cifrarse con Kyber-1024 (message_bus con `encrypt=True`).
- Las claves privadas no se exponen fuera de Vault o del sistema de archivos local (permisos 600).

**Cumplimiento normativo**

- **ISO 27001:** Registros de auditoría vía GaiaChain (cuando esté integrado).
- **GDPR:** Derecho al olvido en `KnowledgeBase.forget()` (Art. 17).
- **EU AI Act:** Modelos registrados en `ModelRegistry` con hash de integridad.

**Resiliencia**

- El Agente Maestro orquesta y puede disparar Self-Healing ante fallos.
- Self-Healing: detección y corrección automática (p. ej. reinicio de contenedores Docker).

---

## 12. Verificación final rápida

| Componente      | Comando de verificación                    | Resultado esperado              |
|-----------------|--------------------------------------------|---------------------------------|
| Vault           | `vault status`                             | Sealed: false                   |
| RabbitMQ        | `docker exec rabbitmq rabbitmqctl list_queues` | Colas `agent.*` creadas         |
| Claves PQC      | `ls -la $CASTUO_KEY_DIR` o `backend/security/keys` | Archivos .pem con permisos 600  |
| Agente de IA    | One-liner sección 8 (asyncio.run)           | JSON con recomendaciones        |
| Self-Healing    | `tail -n 20 logs/selfhealing_agent.log`     | Logs de verificación de integridad |
| Prometheus      | `curl http://localhost:9090/api/v1/query?query=up` | status: success                 |
| Git Hooks       | `git add . && git commit -m "test"`         | Análisis con Mistral (si configurado) |

---

## Conclusión

El sistema **CASTÚO-SYSTEM™ v2.0** queda operativo con:

- **Agentes autónomos** (IA, seguridad, mantenimiento, cumplimiento, e-commerce, logística).
- **Federación de agentes** (RabbitMQ + protocolo estándar + message_bus).
- **Auto-evolución** (git hooks + Mistral AI).
- **Cumplimiento normativo** (ISO 27001, GDPR, EU AI Act).
- **Seguridad post-cuántica** (Kyber-1024, Dilithium-5).
- **Monitoreo continuo** (Prometheus + Grafana).

Para escalar: añadir nodos al Docker Swarm (`docker swarm join ...`).

---

## Rutas de referencia en este repo

- Agentes: `backend/agents/` (master_agent, selfhealing_agent, ai_agent, ecommerce_agent, logistics_agent, compliance_agent).
- Scripts: `backend/scripts/start_agents.py`, `backend/scripts/manage_vault_keys.py`.
- Seguridad: `backend/security/pq_crypto.py`, `backend/security/tests/test_pq_crypto.py`.
- IA: `backend/ai/mistral_client.py`, `backend/ai/knowledge_base.py`, `backend/ai/model_registry.py`, `backend/ai/federated_learning.py`.
- Hooks: `docs/git-hooks/pre-commit`, `docs/git-hooks/post-merge`.
- Política Vault: `backend/policies/castuo-admin.hcl`.
