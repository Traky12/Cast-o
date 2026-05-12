SHELL := /bin/bash

ENV_FILE ?= .env.cloud
PROFILES ?= core iot ai observability

.PHONY: validate up smoke down phases

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
