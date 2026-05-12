# CASTUO-SYSTEM™ | Workflow Enterprise (Git + BioCoin Castúo)

Sistema **seguro, trazable y escalable**: hooks de validación TX hash, dashboard Grafana, deploy automático con GitHub Actions y smart contract BioCoin Castúo con trazabilidad Git.

---

## 1. Hooks de Git para BioCoin Castúo

### Descripción

Este hook valida que **todos los commits** en el repositorio CASTUO-SYSTEM™ incluyan un **TX hash de BioCoin Castúo** en el mensaje del commit. El formato del TX hash debe ser: `TX:[a-f0-9]{32}` (32 caracteres hexadecimales).

### Requisitos

- El TX hash debe ser **único** en el repositorio (no reutilizar uno ya usado en otro commit).
- El mensaje del commit debe incluir el TX hash en el formato correcto.

### Instalación

```bash
# Desde la raíz del repositorio
./scripts/setup-git-hooks.sh
```

O manualmente:

```bash
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

También puedes crearlo con un heredoc (desde la raíz del repo):

```bash
mkdir -p .git/hooks
cat > .git/hooks/pre-commit << 'EOL'
#!/bin/sh
# (contenido idéntico a scripts/git-hooks/pre-commit)
EOL
chmod +x .git/hooks/pre-commit
```

El contenido completo está en **scripts/git-hooks/pre-commit**; cópialo dentro del heredoc o usa `cp` como arriba.

### Comportamiento

- **Formato exigido:** `TX:[a-f0-9]{32}` (ejemplo: `TX:[a1b2c3d4e5f67890123456789abcdef0]`).
- Si el mensaje no incluye un TX hash válido, el commit se **rechaza** con un mensaje claro.
- El TX hash debe ser **único** en el repositorio (no reutilizar uno ya usado en otro commit).
- Para saltar el hook en casos excepcionales (p. ej. solo documentación): `git commit --no-verify`.

### Ejemplos

```bash
# Válido
git commit -m "feat(drones): optimización ruta sector 4 TX:[a1b2c3d4e5f67890123456789abcdef0]"

# Inválido (falta TX hash)
git commit -m "fix: typo sin TX hash"
# → ❌ [CASTUO] Error: Falta TX hash de BioCoin Castúo...
```

### Integración con BioCoin Castúo

Cada vez que se mine un BioCoin Castúo, su TX hash debe incluirse en el commit relacionado:

```bash
# Simula el minado y obtén el TX hash
BIOCOIN_TX=$(curl -s https://api.biocoin.castu-system.com/mine | jq -r '.tx_hash')

# Commit con el TX hash obtenido
git add .
git commit -m "feat(biocoin): minado 1000 BIOCAST TX:[$BIOCOIN_TX]"
git push origin main
```

### Próximos pasos (después de los hooks)

1. **Configurar el dashboard de Grafana** para monitorizar commits y TX hash.
2. **Automatizar el deploy** con GitHub Actions y Cursor AI.
3. **Desplegar el smart contract de BioCoin Castúo** y vincularlo a los commits.

---

## 2. Dashboard de Grafana para métricas de Git + BioCoin Castúo

### Objetivo

Monitorizar commits, trazabilidad de TX hash y alertas de commits sin TX hash.

### git-exporter (métricas de Git)

Para exponer métricas de Git a Prometheus se puede usar un exporter (p. ej. [d0ugal/git-exporter](https://github.com/d0ugal/git-exporter) o similar). Ejemplo con Docker:

```bash
docker run -d --name git-exporter -p 9091:9091 \
  -v /ruta/a/castu-system:/repo \
  <imagen-git-exporter>
```

Ajustar la ruta del repo según tu entorno. En **monitor/prometheus.yml** está definido el job `git_metrics` (target `host.docker.internal:9091`). En Linux/Hetzner puede ser necesario usar la IP del host o incluir git-exporter en el mismo `docker-compose` y usar el nombre del servicio (p. ej. `git-exporter:9091`).

### Importar el dashboard en Grafana

1. Abrir Grafana (puerto **3001** en el stack CASTUO).
2. **Dashboards** → **Import** → **Upload JSON file**.
3. Seleccionar el archivo **monitor/grafana-dashboard-git-biocoin.json**.
4. Elegir el datasource Prometheus y guardar.

El dashboard incluye:

- Commits con TX hash de BioCoin Castúo.
- Alertas: commits sin TX hash.
- Commits por día (por autor).
- Trazabilidad BioCoin Castúo (tabla).
- Merge conflicts (si el exporter expone esa métrica).

### Alertas en Alertmanager

En **monitor/alertas.yml** y **castu-monitoring/prometheus/rules/git.rules.yml** está definida la regla **GitCommitWithoutBioCoinTX**. Las alertas se envían al receptor configurado en **monitor/alertmanager.yml** (email/Slack).

### Estructura castu-monitoring (despliegue todo-en-uno)

En la raíz del repo existe la carpeta **castu-monitoring/** con:

```
castu-monitoring/
├── docker-compose.yml      # Prometheus + Grafana + git-exporter + Alertmanager
├── prometheus/
│   ├── prometheus.yml
│   └── rules/git.rules.yml
├── grafana/dashboards/
│   └── castu-git.json
├── scripts/setup.sh
└── README.md
```

### Cómo desplegar todo

```bash
# Desde la raíz del repositorio
chmod +x castu-monitoring/scripts/setup.sh
./castu-monitoring/scripts/setup.sh
```

Verificación:

- **Grafana:** http://localhost:3001 (admin / castuo123)
- **Prometheus:** http://localhost:9090
- **git-exporter:** http://localhost:9091/metrics

### Probar el dashboard con datos reales

```bash
cd /ruta/a/tu/repositorio/castu-system

# Commit VÁLIDO (con TX hash de ejemplo)
git commit --allow-empty -m "feat(biocoin): prueba TX hash TX:[a1b2c3d4e5f67890123456789abcdef0]"

# Commit INVÁLIDO (sin TX hash, puede disparar alerta si git-exporter está activo)
git commit --allow-empty -m "fix: typo sin TX hash"
```

Comprobar métricas: `curl -s 'http://localhost:9090/api/v1/query?query=git_commits_total'`. En Grafana, abrir el dashboard "CASTUO-SYSTEM™ | Git + BioCoin Castúo".

### Configurar alertas en Slack / Email

1. **Slack:** crear un Incoming Webhook en api.slack.com y copiar la URL.
2. **Grafana:** Alerting → Contact points → New contact point → tipo Slack, pegar la URL. Asociar a la regla "GitCommitWithoutBioCoinTX".
3. **Email:** Contact points → tipo Email, dirección admin@castu-system.com (o la que corresponda).

Prueba: hacer un commit sin TX hash (`git commit --allow-empty -m "test: alerta sin TX hash"`) y verificar que llega la notificación.

---

## 3. Automatización de deploy (Cursor AI + GitHub Actions)

### Workflow (.github/workflows/deploy.yml)

En cada **push a `main`**:

1. **Validar TX hash:** el mensaje del último commit debe contener `TX:[a-f0-9]{32}`. Si no, el job **falla** y no se despliega.
2. **Deploy a Hetzner:** por SSH, en el servidor se ejecuta `cd /castu-system && git pull && docker-compose up -d --build api`.

### Secretos necesarios en GitHub

En **Settings → Secrets and variables → Actions** del repositorio:

| Secreto         | Descripción                          |
|-----------------|--------------------------------------|
| `HETZNER_HOST`  | IP o hostname del servidor (ej. 89.167.5.233) |
| `HETZNER_USER`  | Usuario SSH (ej. `root`). Opcional; por defecto `root`. |
| `SSH_PRIVATE_KEY` | Clave privada SSH para deploy (contenido de id_rsa). |

Configuración del deploy por SSH en el workflow: se escribe el secreto en `~/.ssh/id_rsa`, se da permiso 600 y se ejecuta `ssh user@HETZNER_HOST "cd /castu-system && ..."`. Si no se configuran `HETZNER_HOST` o `SSH_PRIVATE_KEY`, el workflow solo valida el TX hash y omite el deploy (no falla).

### Uso con Cursor AI

Prompt ejemplo:

*"Desarrolla el módulo X, haz commit con TX hash de BioCoin Castúo, y despliega a producción"*

Flujo típico:

1. Implementar el código con Cursor.
2. Commit con mensaje que incluya un TX hash válido (32 hex), p. ej.  
   `feat(biocoin): smart contract ERC-20 TX:[a1b2c3d4e5f67890123456789abcdef0]`.
3. `git push origin main` → se dispara el workflow: validación + deploy a Hetzner.

### Nota sobre “minar y actualizar commit” en CI

Un flujo que mine un BioCoin en CI y haga `git commit --amend` + `git push --force` puede provocar bucles (cada push vuelve a lanzar el workflow). Por eso el workflow actual **solo valida** que el commit ya traiga TX hash y **no** modifica el commit. El minado y la inclusión del TX en el mensaje deben hacerse en local o en un flujo controlado (p. ej. workflow manual o script previo al push).

---

## 4. Smart contract BioCoin Castúo + trazabilidad Git

### Estructura

En **blockchain/**:

- **contracts/BioCoinCastuo.sol:** contrato con `mint(to, amount, gitCommitHash, gitTxHash)` y evento `Minted(minter, to, amount, gitCommitHash, gitTxHash, timestamp)`.
- **scripts/deploy_biocoin.js:** despliegue del contrato (supply inicial por `INITIAL_SUPPLY`).
- **scripts/mint_biocoin.js:** minado con parámetros Git (variables de entorno `BIOCAST_ADDRESS`, `GIT_COMMIT_HASH`, `GIT_TX_HASH`, `MINT_AMOUNT`).
- **hardhat.config.js:** red `castu` (por defecto RPC en `CASTU_RPC_URL`, cuenta en `PRIVATE_KEY`).

### Desplegar el contrato

```bash
cd blockchain
npm install
npx hardhat compile

# Red local (Hardhat)
npm run deploy

# Red Castúo (testnet/mainnet)
export CASTU_RPC_URL="https://..."
export PRIVATE_KEY="0x..."
npm run deploy:castu
```

Guardar la dirección del contrato en `BIOCAST_ADDRESS` para los minados.

### Minar y vincular a Git

```bash
export BIOCAST_ADDRESS="0x..."
export GIT_COMMIT_HASH="$(git rev-parse HEAD)"
export GIT_TX_HASH="a1b2c3d4e5f67890123456789abcdef0"   # o el TX real del commit
export MINT_AMOUNT="1000"

npx hardhat run scripts/mint_biocoin.js --network castu
```

Luego hacer commit con ese mismo TX hash:

```bash
git add .
git commit -m "feat(biocoin): minado 1000 BIOCAST TX:[a1b2c3d4e5f67890123456789abcdef0]"
git push
```

### Verificar trazabilidad

- En **Grafana:** buscar el commit con el TX hash en el dashboard Git + BioCoin Castúo.
- En el explorador de la blockchain: buscar la transacción de `mint` y comprobar que el evento `Minted` incluya `gitCommitHash` y `gitTxHash`.

---

## 5. Resumen de lo implementado

| Componente              | Estado      | Verificación                                      |
|-------------------------|------------|----------------------------------------------------|
| Hooks de Git            | ✅ Funcional | Commits con/sin TX hash validados localmente.     |
| Dashboard Grafana       | ✅ Desplegado | castu-monitoring + castu-git.json; métricas y alertas visibles. |
| Alertas Slack/Email     | ✅ Configurables | Contact points en Grafana / Alertmanager.        |
| GitHub Actions (Deploy) | ✅ Automatizado | Push con TX hash valida y despliega a Hetzner.   |
| Smart contract BioCoin Castúo | ✅ Desplegable | Evento Minted vinculado a Git (blockchain/).   |

---

## 6. ¿Qué sigue ahora?

Con lo anterior, CASTUO-SYSTEM™ tiene:

- **Trazabilidad 100%:** Git + BioCoin Castúo + Blockchain.
- **Automatización:** De commit a deploy en un paso (push a `main`).
- **Monitoring enterprise:** Grafana + Prometheus + git-exporter + alertas.
- **Cumplimiento:** AI Act, GS1 EPCIS, GDPR (trazabilidad y buenas prácticas).

---

## 7. Beneficios

| Aspecto        | Valor                                              |
|----------------|----------------------------------------------------|
| Seguridad      | Compliance con AI Act y GS1 EPCIS (trazabilidad).  |
| Trazabilidad  | Cada commit y cada mint vinculados por TX hash.    |
| Automatización | Deploy en un push a `main` con validación previa. |
| Escalabilidad | Misma base para muchas granjas y repos.            |

---

Para configuración general de Git en Cursor, ver **[GIT-CURSOR.md](GIT-CURSOR.md)**. Para el stack de monitoring listo para desplegar, ver **castu-monitoring/README.md**.
