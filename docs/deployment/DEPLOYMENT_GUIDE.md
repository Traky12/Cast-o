# GUÍA DE DESPLIEGUE: FORESTOWNERSHIPTOKEN

## 1. Requisitos

- **Servidores**: idealmente 4 máquinas (2 para agentes, 1 para dashboard, 1 para monitoring).
- **Sistema operativo**: Ubuntu 20.04 LTS.
- **Docker**: versión 20.10+.
- **Ansible**: versión 2.10+.
- **Dominios**:
  - `staging.juntaextremadura.es` (dashboard).
  - `api-staging.juntaextremadura.es` (agentes).

## 2. Preparación

### 2.1. Configurar inventario

Edita `ansible/inventory/staging.ini` con las IPs de tus servidores de staging.

### 2.2. Configurar variables

Edita `ansible/group_vars/staging.yml` con:

- Credenciales de SIGPAC (usar Ansible Vault).
- Claves de GaiaChain.
- Contraseñas de SMTP.

### 2.3. Construir imágenes Docker

```bash
# Desde la raíz del proyecto
docker build -t registry.castuo-system.com/forestownershiptoken/sigpac-agent:latest -f agents/sigpac/Dockerfile .
docker push registry.castuo-system.com/forestownershiptoken/sigpac-agent:latest
```

## 3. Despliegue

### 3.1. Ejecutar playbook

```bash
cd ansible
ansible-playbook -i inventory/staging.ini deploy_agents.yml --vault-password-file ~/.vault_pass
```

### 3.2. Verificar servicios

```bash
# Verificar agentes
curl http://staging.juntaextremadura.es:8001/health
curl http://staging.juntaextremadura.es:8003/health

# Verificar dashboard
curl https://staging.juntaextremadura.es
```

## 4. Monitorización

- Grafana: `https://monitor.staging.juntaextremadura.es` (usuario `admin`, contraseña gestionada por Vault).
- Logs: `/var/log/forestownershiptoken/*` en cada servidor (ajustar según tu configuración real).

## 5. Rollback

```bash
cd ansible
ansible-playbook -i inventory/staging.ini rollback.yml --vault-password-file ~/.vault_pass
```

## 6. Variables de entorno clave

| Variable        | Descripción                  | Ejemplo                                       |
|----------------|------------------------------|-----------------------------------------------|
| `GAIA_CHAIN_RPC` | URL del nodo GaiaChain       | `https://testnet.gaiachain.castuo-system.com` |
| `SIGPAC_API_KEY` | Clave para la API de SIGPAC  | `abc123...` (cifrada con Vault)               |
| `SMTP_PASSWORD`  | Contraseña del servidor SMTP | `xyz789...` (cifrada con Vault)               |

## 7. Ejecución completa de ejemplo

```bash
# 1. Clonar repositorio
git clone https://github.com/castuo-system/forestownershiptoken.git
cd forestownershiptoken

# 2. Configurar Ansible Vault (solo una vez)
ansible-vault create group_vars/staging/vault.yml
# Introducir contraseñas cuando se solicite

# 3. Desplegar en staging
cd ansible
ansible-playbook -i inventory/staging.ini deploy_agents.yml --vault-password-file ~/.vault_pass

# 4. Verificar
curl https://staging.juntaextremadura.es/api/health
```

