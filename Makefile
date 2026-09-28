SHELL := /bin/bash

ENV_FILE ?= .env.cloud
PROFILES ?= core iot ai observability

.PHONY: validate up smoke down phases agent-hardening reconcile-check e2e-validar-lote \
  hub-connectivity-check test-ai terraform-plan terraform-apply test-encryption \
	test-blockchain validate-n8n test-all go-total baseline docker-audit docker-audit-all \
	test-github-operativity test-github-certification test-github-evidence ctaex-compliance-check legal-compliance-check audit-package-exhaustive \
	frontend-start frontend-init frontend-stop frontend-purge frontend-check frontend-open frontend-health \
	docker-harden docker-verify-hardening init-castuo-persistence verify-operational-stack start-all-services \
	runbook-prepilot security-hybrid-check

validate:
	@profiles_csv="$$(echo "$(PROFILES)" | tr ' ' ',')"; \
	python tests/cloud/cloud_validator.py --env-file "$(ENV_FILE)" --profiles "$$profiles_csv"

up:
	@args=""; \
	for p in $(PROFILES); do args="$$args --profile $$p"; done; \
	./scripts/cloud-deploy.sh --env-file "$(ENV_FILE)" $$args

smoke:
	@set -a; source "$(ENV_FILE)"; set +a; \
	./scripts/cloud-iot-smoke.sh --mqtt-host 127.0.0.1 --mqtt-port "$${SMOKE_MQTT_PORT:-1883}" --api-url "http://127.0.0.1:$${API_PORT:-8000}"

down:
	@args=""; \
	for p in $(PROFILES); do args="$$args --profile $$p"; done; \
	./scripts/cloud-deploy.sh --env-file "$(ENV_FILE)" $$args --down

phases: validate up smoke down

agent-hardening:
	@echo "[1/3] Ejecutando preflight..."
	bash scripts/preflight.sh
	@echo "[2/3] Exportando metricas..."
	bash scripts/metrics-sync.sh
	@echo "[3/3] Simulando caos (dry-run)..."
	bash scripts/chaos-test-sync.sh --allow-dirty --dry-run
	@echo "[OK] Hardening local completado"

reconcile-check:
	@echo "[INFO] Ejecutando reconciliacion en dry-run..."
	@mkdir -p artifacts
	@set +e; \
	bash scripts/reconcile.sh --dry-run --output-dir ./artifacts --summary-json ./artifacts/summary.json; \
	rc=$$?; \
	set -e; \
	branch="$$(git rev-parse --abbrev-ref HEAD)"; \
	drift="$$(python3 -c 'import json;print(str(json.load(open("artifacts/summary.json")).get("drift_detected", False)).lower())' 2>/dev/null || echo false)"; \
	if [[ "$$branch" == feat/* ]]; then \
		echo "[INFO] Politica rama $$branch: report-only en dry-run"; \
		if [[ "$$drift" == "true" ]]; then \
			echo "[WARN] Drift detectado (reportado, no bloqueante en feat/*)."; \
			exit 0; \
		fi; \
		if [[ $$rc -ne 0 ]]; then \
			echo "[ERROR] reconcile fallo critico (no drift) en feat/*"; \
			exit $$rc; \
		fi; \
		echo "[OK] reconcile dry-run sin drift"; \
	else \
		echo "[INFO] Politica rama $$branch: strict"; \
		exit $$rc; \
	fi

e2e-validar-lote:
	@echo "[INFO] Ejecutando E2E validar_lote..."
	bash scripts/e2e-validar-lote.sh

hub-connectivity-check:
	@echo "[INFO] Validando conectividad de integraciones (modo estricto)..."
	bash scripts/validate_hub_connectivity.sh --env-file .env --strict --check-endpoints

# ============================================================================
# NUEVOS TARGETS: Conectores IA, Seguridad, Herramientas OSS
# ============================================================================

test-ai:
	@echo "[1/2] Testeando Mistral Connector..."
	python -m pytest tests/test_mistral_connector.py -v
	@echo "[2/2] Testeando Sabionda Connector..."
	python -m pytest tests/test_sabionda_connector.py -v
	@echo "[OK] Tests de IA completados (19 tests)"

test-encryption:
	@echo "Testeando módulo de Cifrado (AES-256 Fernet)..."
	python -m pytest tests/test_encryption.py -v --tb=short
	@echo "[OK] 12 tests de encryption pasados"

test-blockchain:
	@echo "Testeando integración GaiaChain (Blockchain)..."
	python -m pytest tests/test_gaiachain.py -v --tb=short
	@echo "[OK] 13 tests de blockchain pasados"

test-all:
	@echo "Ejecutando suite completa (44 tests)..."
	python -m pytest tests/test_mistral_connector.py tests/test_sabionda_connector.py \
	  tests/test_encryption.py tests/test_gaiachain.py -v --tb=short
	@echo "[OK] 44/44 tests ✅ PASSING"

test-github-operativity:
	@echo "[INFO] Certificando operatividad GitHub OFF/ON..."
	pytest -q test_github_integration_toggle.py

test-github-certification:
	@echo "[INFO] Ejecutando pruebas marcadas como certificacion..."
	pytest -q tests/test_github_integration_toggle.py -m certification

test-github-evidence:
	@echo "[INFO] Generando evidencia de certificacion GitHub OFF/ON..."
	@mkdir -p artifacts/operativity
	@set -o pipefail; \
	pytest -q test_github_integration_toggle.py | tee artifacts/operativity/github-operativity-latest.txt
	@echo "[OK] Evidencia: artifacts/operativity/github-operativity-latest.txt"

ctaex-compliance-check:
	@echo "[INFO] Ejecutando verificacion integral de cumplimiento CTAEX..."
	bash scripts/ctaex-compliance-check.sh

legal-compliance-check:
	@echo "[INFO] Ejecutando verificacion legal (RGPD/ISO base)..."
	chmod +x scripts/legal-compliance-check.sh
	bash scripts/legal-compliance-check.sh

audit-package-exhaustive:
	@echo "[INFO] Generando paquete de auditoria exhaustivo..."
	chmod +x scripts/generate-exhaustive-audit-package.sh
	bash scripts/generate-exhaustive-audit-package.sh

validate-n8n:
	@echo "Validando sintáxis del workflow n8n..."
	python -m json.tool n8n/workflows/mistral-wordpress-report.json > /dev/null && \
	echo "[OK] n8n workflow JSON válido (importable en n8n)" || \
	echo "[ERROR] JSON inválido en el workflow"

terraform-plan:
	@echo "Generando plan Terraform para Hetzner..."
	cd hetzner_infra && \
	terraform plan -out=tfplan && \
	echo "[OK] Plan ready. Ejecutar: make terraform-apply"

terraform-apply:
	@echo "[WARN] Esto desplegará infraestructura en Hetzner. Requiere:"
	@echo "  - TF_VAR_hcloud_token (Hetzner API token)"
	@echo "  - TF_VAR_ssh_key_id (SSH key ID en Hetzner)"
	@echo ""
	@read -p "¿Continuar? (s/n): " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Ss]$$ ]]; then \
	  cd hetzner_infra && terraform apply tfplan && \
	  echo "[OK] Infraestructura deployada. Outputs:"; \
	  terraform output deployment_info; \
	else \
	  echo "Operación cancelada."; \
	fi

# ============================================================================
# DOCUMENTACIÓN & REFERENCIAS
# ============================================================================

docs-ai:
	@echo "Documentos de IA & Conectores:"
	@echo "  - castuo_graph/ai/mistral_connector.py"
	@echo "  - castuo_graph/ai/sabionda_connector.py"
	@echo "  - tests/test_mistral_connector.py (9 tests)"
	@echo "  - tests/test_sabionda_connector.py (10 tests)"
	@echo ""
	@echo "Guía: docs/ops/HERRAMIENTAS-INTEGRACION.md (Secciones 1-4)"

docs-infra:
	@echo "Documentos de Infraestructura:"
	@echo "  - hetzner_infra/main.tf"
	@echo "  - hetzner_infra/variables.tf"
	@echo "  - hetzner_infra/user_data.yaml"
	@echo ""
	@echo "Guía: docs/ops/HUB-CONECTIVIDAD.md (Secciones 5-6)"

docs-security:
	@echo "Documentos de Seguridad:"
	@echo "  - castuo_graph/security/encryption.py (AES-256)"
	@echo "  - castuo_graph/blockchain/gaiachain.py (GaiaChain 2.0)"
	@echo "  - tests/test_encryption.py (12 tests)"
	@echo "  - tests/test_gaiachain.py (13 tests)"
	@echo ""
	@echo "Guía: docs/ops/HUB-CONECTIVIDAD.md (Sección 7)"

help-hub:
	@echo "=== HUB DE CONECTIVIDAD v2.0 ==="
	@echo ""
	@echo "Comandos principales:"
	@echo "  make test-ai                 — Validar conectores IA (Mistral, Sabionda)"
	@echo "  make test-encryption         — Validar cifrado AES-256"
	@echo "  make test-blockchain         — Validar GaiaChain blockchain"
	@echo "  make test-all                — Ejecutar todos (44 tests)"
	@echo "  make validate-n8n            — Validar workflow n8n (JSON)"
	@echo "  make terraform-plan          — Visualizar plan Hetzner (sin ejecutar)"
	@echo "  make terraform-apply         — Desplegar infraestructura en Hetzner"
	@echo "  make hub-connectivity-check  — Validar conectividad (secretos, endpoints)"
	@echo ""
	@echo "Documentación:"
	@echo "  make docs-ai                 — Referencias IA"
	@echo "  make docs-infra              — Referencias Infraestructura"
	@echo "  make docs-security           — Referencias Seguridad"
	@echo ""
	@echo "Ver: docs/ops/HUB-CONECTIVIDAD.md"
	@echo "     docs/ops/HERRAMIENTAS-INTEGRACION.md"

go-total:
	@echo "[INFO] Ejecutando validacion integral de excelencia operativa..."
	bash scripts/go-total.sh --env-file .env

baseline:
	@echo "[INFO] Ejecutando baseline de coherencia+seguridad+optimizacion..."
	bash scripts/system-baseline.sh --env-file .env

docker-audit:
	@echo "[INFO] Ejecutando auditoria Docker (contenedores activos)..."
	bash scripts/docker-audit.sh

docker-audit-all:
	@echo "[INFO] Ejecutando auditoria Docker (todos los contenedores)..."
	bash scripts/docker-audit.sh --all

# ============================================================================
# FRONTEND LOCAL WORDPRESS (PUERTO 5432)
# ============================================================================

frontend-start:
	@echo "[INFO] Arrancando frontend local..."
	bash scripts/start_frontend_8003.sh

frontend-init:
	@echo "[INFO] Arrancando e inicializando contenido frontend..."
	bash scripts/start_frontend_8003.sh --init-content

frontend-stop:
	@echo "[INFO] Deteniendo frontend local..."
	bash scripts/stop_frontend_8003.sh

frontend-purge:
	@echo "[INFO] Purgando frontend local (contenedores + volumen)..."
	bash scripts/stop_frontend_8003.sh --purge

frontend-check:
	@echo "[INFO] Verificando estado frontend..."
	bash scripts/start_frontend_8003.sh --check

frontend-open:
	@echo "[INFO] Abriendo frontend y admin en navegador..."
	bash scripts/start_frontend_8003.sh --open

frontend-health:
	@echo "[INFO] Healthcheck frontend..."
	curl -I --max-time 10 http://localhost:5432 | head -n 8

# ============================================================================
# DOCKER HARDENING AUTOMÁTICO
# ============================================================================

docker-harden:
	@echo "[INFO] Aplicando hardening automático a contenedores CASTÚO..."
	@chmod +x scripts/docker-harden.sh
	bash scripts/docker-harden.sh

docker-verify-hardening:
	@echo "[INFO] Verificando hardening aplicado..."
	@echo ""
	@echo "📊 Estado de Restart Policy:"
	@docker inspect castuo-wordpress --format='  WordPress: {{.HostConfig.RestartPolicy.Name}}' 2>/dev/null || echo "  WordPress: No disponible"
	@docker inspect castuo-mariadb --format='  MariaDB: {{.HostConfig.RestartPolicy.Name}}' 2>/dev/null || echo "  MariaDB: No disponible"
	@echo ""
	@echo "🏥 Estado de Healthchecks:"
	@docker inspect castuo-wordpress --format='  WordPress: {{if .Config.Healthcheck}}Enabled{{else}}Disabled{{end}}' 2>/dev/null || echo "  WordPress: No disponible"
	@docker inspect castuo-mariadb --format='  MariaDB: {{if .Config.Healthcheck}}Enabled{{else}}Disabled{{end}}' 2>/dev/null || echo "  MariaDB: No disponible"
	@echo ""
	@echo "💾 Límites de Recursos:"
	@docker inspect castuo-wordpress --format='  WordPress Memory: {{.HostConfig.Memory}} bytes' 2>/dev/null || echo "  WordPress: No disponible"
	@docker inspect castuo-wordpress --format='  WordPress NanoCPUs: {{.HostConfig.NanoCpus}}' 2>/dev/null || echo "  WordPress CPU: No disponible"
	@docker inspect castuo-mariadb --format='  MariaDB Memory: {{.HostConfig.Memory}} bytes' 2>/dev/null || echo "  MariaDB: No disponible"
	@docker inspect castuo-mariadb --format='  MariaDB NanoCPUs: {{.HostConfig.NanoCpus}}' 2>/dev/null || echo "  MariaDB CPU: No disponible"
	@echo ""
	@echo "🔐 Exposición de Puertos (Solo Localhost):"
	@docker ps --filter "name=castuo" --format="table {{.Names}}\t{{.Ports}}" 2>/dev/null || echo "  No hay contenedores activos"
	@echo ""
	@echo "✅ Verificación completada. Auditar con: make docker-audit --strict"

init-castuo-persistence:
	@echo "[INFO] Inicializando persistencia (users/farms/transactions/logs)..."
	bash scripts/init_castuo_persistence.sh

verify-operational-stack:
	@echo "[INFO] Ejecutando verificación operativa integral..."
	bash scripts/verify_operational_stack.sh

start-all-services:
	@echo "[INFO] Arrancando todos los servicios recomendados..."
	bash scripts/start_all_services.sh

runbook-prepilot:
	@echo "[INFO] Ejecutando runbook pre-pilot invernadero..."
	bash scripts/runbook-prepilot.sh $${HETZNER_IP:+--ip $$HETZNER_IP} $${STRICT:+--strict}

security-hybrid-check:
	@echo "[INFO] Ejecutando verificacion de seguridad hibrida (WAF/IDS/K8s)..."
	bash scripts/security-hybrid-check.sh

# CASTUO-REPOSITORY-STANDARD-V1.0
castuo-conformance:
	@python3 scripts/run_castuo_repository_conformance.py \
		--standard-root $${CASTUO_STANDARD_ROOT:-../castuo-evolution} \
		--repository-root . \
		--output artifacts/castuo-repository-conformance.json

.PHONY: castuo-conformance
