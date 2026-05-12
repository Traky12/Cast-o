.PHONY: test-thc validate-thc backup-thc cloud-validate cloud-up cloud-up-all cloud-iot-up cloud-iot-smoke cloud-down

test-thc:
	@echo "Running THC tests..."
	pytest -q tests/test_thc_estimator.py tests/test_thc_integration.py

validate-thc:
	@echo "Validating THC flow..."
	BASE_URL=http://localhost:8000 bash scripts/validate_thc_flow.sh

backup-thc:
	@echo "Running THC backup..."
	bash scripts/backup_castuo.sh

cloud-validate:
	@echo "Running cloud validator..."
	python tests/cloud/cloud_validator.py --env-file .env.cloud --compose-file docker-compose.cloud.yml --profiles core,observability,iot,ai

cloud-up:
	@echo "Deploying cloud core + observability..."
	bash scripts/cloud-deploy.sh staging core,observability --env-file .env.cloud --rollback-on-error

cloud-up-all:
	@echo "Deploying full cloud stack..."
	bash scripts/cloud-deploy.sh staging core,observability,iot,ai --env-file .env.cloud --rollback-on-error

cloud-iot-up:
	@echo "Deploying IoT profile..."
	bash scripts/cloud-deploy.sh staging iot --env-file .env.cloud --skip-healthcheck

cloud-iot-smoke:
	@echo "Running IoT smoke test..."
	bash scripts/cloud-iot-smoke.sh .env.cloud docker-compose.cloud.yml castuo/sensors/smoke

cloud-down:
	@echo "Stopping cloud stack..."
	docker compose -f docker-compose.cloud.yml --env-file .env.cloud down
