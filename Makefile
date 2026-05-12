## CASTÚO-SYSTEM™ v3.1 — Makefile
## ─────────────────────────────────────────────────────────────────────────────
## Comandos para desarrollo local, testing y despliegue en Hetzner.
##
## Uso rápido:
##   make dev          → Levanta frontend (puerto 3000) + API (puerto 8000)
##   make test-smoke   → Smoke tests contra la instancia local
##   make k8s-staging  → Despliega todo en el cluster (staging)
##   make k8s-status   → Estado del cluster y certificados TLS

SHELL := /bin/bash
.DEFAULT_GOAL := help

# ── Configuración ────────────────────────────────────────────────────────────
API_LOCAL     := http://localhost:8000
FRONTEND_LOCAL:= http://localhost:3000
NAMESPACE     := castuo-system
KUBECONFIG    ?= ~/.kube/config

# ── Colores ──────────────────────────────────────────────────────────────────
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
RESET  := \033[0m
BOLD   := \033[1m

.PHONY: help dev dev-down dev-logs dev-rebuild dev-local dev-local-stop \
        test-api test-smoke test-full \
        k8s-apply k8s-apply-no-frontend k8s-delete k8s-status k8s-tls k8s-logs \
        build push lint fmt

# ─────────────────────────────────────────────────────────────────────────────
# AYUDA
# ─────────────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "$(BOLD)CASTÚO-SYSTEM™ v3.1$(RESET)"
	@echo ""
	@echo "$(YELLOW)Desarrollo local:$(RESET)"
	@echo "  make dev               Inicia frontend (3000) + API (8000) con hot-reload"
	@echo "  make dev-down          Para todos los contenedores de desarrollo"
	@echo "  make dev-logs          Logs en tiempo real (frontend + API)"
	@echo "  make dev-rebuild       Reconstruye y reinicia en dev"
	@echo ""
	@echo "$(YELLOW)Testing:$(RESET)"
	@echo "  make test-api          Smoke tests básicos contra localhost:8000"
	@echo "  make test-smoke        Suite completa de smoke tests (local)"
	@echo "  make test-full         pytest completo"
	@echo "  make test-prod         Smoke tests contra api.castuo-system.cloud"
	@echo ""
	@echo "$(YELLOW)Kubernetes / Hetzner:$(RESET)"
	@echo "  make k8s-apply         Aplica todos los manifiestos (con frontend)"
	@echo "  make k8s-apply-no-fe   Aplica manifiestos SIN frontend (API en raíz)"
	@echo "  make k8s-status        Muestra estado de pods, ingress y certificados"
	@echo "  make k8s-tls           Verifica estado TLS de los 4 dominios"
	@echo "  make k8s-logs          Logs del pod API en tiempo real"
	@echo "  make k8s-delete        Elimina todos los recursos (CUIDADO)"
	@echo ""

# ─────────────────────────────────────────────────────────────────────────────
# DESARROLLO LOCAL
# ─────────────────────────────────────────────────────────────────────────────

dev:
	@echo "$(GREEN)▶ Iniciando entorno de desarrollo...$(RESET)"
	@echo "  Frontend → $(FRONTEND_LOCAL)"
	@echo "  API      → $(API_LOCAL)"
	@echo "  Swagger  → $(API_LOCAL)/docs"
	@echo ""
	docker compose -f docker-compose.dev.yml up --build

dev-down:
	@echo "$(YELLOW)▶ Parando contenedores de desarrollo...$(RESET)"
	docker compose -f docker-compose.dev.yml down

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f --tail=50

dev-rebuild:
	docker compose -f docker-compose.dev.yml down
	docker compose -f docker-compose.dev.yml build --no-cache
	docker compose -f docker-compose.dev.yml up

# ── Sin Docker: API directa + frontend estático ────────────────────────────
# Requiere: pip install -r api/requirements.txt
# Uso:      make dev-local          → inicia API en :8000
#           make dev-local-stop     → mata el proceso uvicorn
dev-local:
	@echo "$(GREEN)▶ Iniciando API local (sin Docker)$(RESET)"
	@echo "  API     → $(API_LOCAL)"
	@echo "  Swagger → $(API_LOCAL)/docs"
	@echo "  Abre frontend/index.html en el navegador o usa python3 -m http.server 3000 --directory frontend"
	@echo ""
	@[ -f .env ] && export $$(grep -v '^#' .env | xargs) || true ; \
	  cd api && PYTHONPATH=.. ENVIRONMENT=development \
	  CASTUO_CORS_ORIGINS="http://localhost:3000,http://localhost:8000" \
	  uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

dev-local-stop:
	@pkill -f "uvicorn main:app" && echo "$(YELLOW)▶ API detenida$(RESET)" || echo "API no estaba corriendo"

dev-frontend:
	@echo "$(GREEN)▶ Servidor de frontend estático en :3000$(RESET)"
	cd frontend && python3 -m http.server 3000

# ─────────────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────────────

test-api:
	@echo "$(GREEN)▶ Smoke tests básicos ($(API_LOCAL))$(RESET)"
	@curl -sf $(API_LOCAL)/health | python3 -m json.tool || (echo "$(RED)✗ /health falló$(RESET)" && exit 1)
	@echo "$(GREEN)✓ /health OK$(RESET)"
	@curl -sf $(API_LOCAL)/api/v1/audit/actions > /dev/null && echo "$(GREEN)✓ /audit/actions OK$(RESET)" || echo "$(RED)✗ /audit/actions falló$(RESET)"
	@curl -sf $(API_LOCAL)/api/v1/claude/status > /dev/null && echo "$(GREEN)✓ /claude/status OK$(RESET)" || echo "$(RED)✗ /claude/status falló$(RESET)"
	@curl -sf $(API_LOCAL)/api/v1/github/status > /dev/null && echo "$(GREEN)✓ /github/status OK$(RESET)" || echo "$(RED)✗ /github/status falló$(RESET)"
	@curl -sf $(API_LOCAL)/api/v1/tenants/current > /dev/null && echo "$(GREEN)✓ /tenants/current OK$(RESET)" || echo "$(RED)✗ /tenants/current falló$(RESET)"
	@echo ""
	@echo "$(BOLD)Swagger UI: $(API_LOCAL)/docs$(RESET)"

test-smoke:
	@echo "$(GREEN)▶ Suite de smoke tests ($(API_LOCAL))$(RESET)"
	@echo ""
	@# Health
	@STATUS=$$(curl -so /dev/null -w "%{http_code}" $(API_LOCAL)/health) && \
	  [ "$$STATUS" = "200" ] && echo "$(GREEN)✓ GET /health → $$STATUS$(RESET)" || echo "$(RED)✗ GET /health → $$STATUS$(RESET)"
	@# Docs
	@STATUS=$$(curl -so /dev/null -w "%{http_code}" $(API_LOCAL)/docs) && \
	  [ "$$STATUS" = "200" ] && echo "$(GREEN)✓ GET /docs → $$STATUS$(RESET)" || echo "$(RED)✗ GET /docs → $$STATUS$(RESET)"
	@# Actuadores
	@STATUS=$$(curl -so /dev/null -w "%{http_code}" $(API_LOCAL)/api/v1/actuadores/estado) && \
	  [ "$$STATUS" = "200" ] && echo "$(GREEN)✓ GET /api/v1/actuadores/estado → $$STATUS$(RESET)" || echo "$(RED)✗ GET /api/v1/actuadores/estado → $$STATUS$(RESET)"
	@# Audit
	@STATUS=$$(curl -so /dev/null -w "%{http_code}" $(API_LOCAL)/api/v1/audit/actions) && \
	  [ "$$STATUS" = "200" ] && echo "$(GREEN)✓ GET /api/v1/audit/actions → $$STATUS$(RESET)" || echo "$(RED)✗ GET /api/v1/audit/actions → $$STATUS$(RESET)"
	@# Claude
	@STATUS=$$(curl -so /dev/null -w "%{http_code}" $(API_LOCAL)/api/v1/claude/status) && \
	  [ "$$STATUS" = "200" ] && echo "$(GREEN)✓ GET /api/v1/claude/status → $$STATUS$(RESET)" || echo "$(RED)✗ GET /api/v1/claude/status → $$STATUS$(RESET)"
	@# GitHub
	@STATUS=$$(curl -so /dev/null -w "%{http_code}" $(API_LOCAL)/api/v1/github/status) && \
	  [ "$$STATUS" = "200" ] && echo "$(GREEN)✓ GET /api/v1/github/status → $$STATUS$(RESET)" || echo "$(RED)✗ GET /api/v1/github/status → $$STATUS$(RESET)"
	@# Tenants
	@STATUS=$$(curl -so /dev/null -w "%{http_code}" $(API_LOCAL)/api/v1/tenants/current) && \
	  [ "$$STATUS" = "200" ] && echo "$(GREEN)✓ GET /api/v1/tenants/current → $$STATUS$(RESET)" || echo "$(RED)✗ GET /api/v1/tenants/current → $$STATUS$(RESET)"
	@# Post Claude
	@STATUS=$$(curl -so /dev/null -w "%{http_code}" -X POST $(API_LOCAL)/api/v1/claude/generate \
	  -H "Content-Type: application/json" \
	  -d '{"prompt":"pH óptimo tomate"}') && \
	  [ "$$STATUS" = "200" ] && echo "$(GREEN)✓ POST /api/v1/claude/generate → $$STATUS$(RESET)" || echo "$(RED)✗ POST /api/v1/claude/generate → $$STATUS$(RESET)"
	@echo ""
	@echo "$(BOLD)Frontend: $(FRONTEND_LOCAL)$(RESET)"
	@echo "$(BOLD)Swagger:  $(API_LOCAL)/docs$(RESET)"

test-full:
	@echo "$(GREEN)▶ pytest completo$(RESET)"
	cd api && python -m pytest ../tests/ -v --tb=short

test-prod:
	@echo "$(GREEN)▶ Smoke tests en producción (api.castuo-system.cloud)$(RESET)"
	@curl -sf https://api.castuo-system.cloud/health | python3 -m json.tool
	@curl -sf https://castuo-system.cloud/ | grep -q "CASTÚO" && \
	  echo "$(GREEN)✓ Frontend raíz OK$(RESET)" || echo "$(RED)✗ Frontend raíz falló$(RESET)"
	@echo "$(GREEN)✓ TLS OK$(RESET)"

# ─────────────────────────────────────────────────────────────────────────────
# KUBERNETES / HETZNER
# ─────────────────────────────────────────────────────────────────────────────

k8s-apply:
	@echo "$(GREEN)▶ Aplicando manifiestos Kubernetes (con frontend)$(RESET)"
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/cluster-issuer.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/frontend-service.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/hpa.yaml
	kubectl apply -f k8s/ingress.yaml
	@echo ""
	@echo "$(GREEN)▶ Estado de rollout:$(RESET)"
	kubectl rollout status deployment/castuo-api     -n $(NAMESPACE) --timeout=120s
	kubectl rollout status deployment/castuo-frontend -n $(NAMESPACE) --timeout=120s || true

k8s-apply-no-fe:
	@echo "$(YELLOW)▶ Aplicando manifiestos SIN frontend (API en raíz)$(RESET)"
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/cluster-issuer.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/hpa.yaml
	kubectl apply -f k8s/ingress-no-frontend.yaml
	kubectl rollout status deployment/castuo-api -n $(NAMESPACE) --timeout=120s

k8s-status:
	@echo "$(BOLD)── Namespace $(NAMESPACE) ────────────────────────────────$(RESET)"
	kubectl get pods,svc,ingress,certificate -n $(NAMESPACE)
	@echo ""
	@echo "$(BOLD)── HPA ─────────────────────────────────────────────────$(RESET)"
	kubectl get hpa -n $(NAMESPACE) 2>/dev/null || true
	@echo ""
	@echo "$(BOLD)── Eventos recientes ───────────────────────────────────$(RESET)"
	kubectl get events -n $(NAMESPACE) --sort-by='.lastTimestamp' | tail -10

k8s-tls:
	@echo "$(GREEN)▶ Verificando TLS en los 4 dominios$(RESET)"
	@for domain in castuo-system.cloud www.castuo-system.cloud api.castuo-system.cloud n8n.castuo-system.cloud; do \
	  printf "%-35s " "$$domain:"; \
	  EXPIRY=$$(echo | openssl s_client -servername $$domain -connect $$domain:443 2>/dev/null \
	    | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2) ; \
	  if [ -n "$$EXPIRY" ]; then \
	    echo "$(GREEN)✓ TLS OK — expira: $$EXPIRY$(RESET)"; \
	  else \
	    echo "$(RED)✗ Sin TLS o dominio no apunta al cluster$(RESET)"; \
	  fi; \
	done

k8s-logs:
	kubectl logs -n $(NAMESPACE) -l app=castuo-api -f --tail=50

k8s-delete:
	@echo "$(RED)▶ Eliminando recursos en namespace $(NAMESPACE)$(RESET)"
	@read -p "¿Estás seguro? (escribe 'si' para confirmar): " c && [ "$$c" = "si" ]
	kubectl delete all --all -n $(NAMESPACE)
	kubectl delete ingress --all -n $(NAMESPACE) 2>/dev/null || true
	kubectl delete certificate --all -n $(NAMESPACE) 2>/dev/null || true
	kubectl delete pvc --all -n $(NAMESPACE) 2>/dev/null || true

# ─────────────────────────────────────────────────────────────────────────────
# BUILD / PUSH
# ─────────────────────────────────────────────────────────────────────────────

build:
	@echo "$(GREEN)▶ Construyendo imagen API$(RESET)"
	docker build -t ghcr.io/traky12/castuo-system/castuo-api:latest ./api

push: build
	@echo "$(GREEN)▶ Publicando imagen en GHCR$(RESET)"
	docker push ghcr.io/traky12/castuo-system/castuo-api:latest

lint:
	cd api && python -m flake8 . --max-line-length=120 --exclude=__pycache__,.venv || true
	cd api && python -m mypy . --ignore-missing-imports || true

fmt:
	cd api && python -m black . --line-length 120 || true
