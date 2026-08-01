# Cast-o — Entorno de Testing, Validación y Automatización para CASTÚO-SYSTEM

Cast-o es un repositorio técnico base (template) diseñado para estructurar, automatizar y validar el ecosistema de CASTÚO-SYSTEM mediante tests, scripts, infraestructura como código y herramientas de integración.

No es la plataforma productiva en sí, sino un **framework operativo de soporte** para asegurar calidad, reproducibilidad y despliegue consistente.

---

## 🎯 Propósito

Este repositorio proporciona un entorno unificado para:

- Automatizar tests (unitarios, integración y E2E)
- Validar configuraciones de infraestructura y despliegue
- Ejecutar pipelines de CI/CD reproducibles
- Probar integraciones (IoT, IA, workflows, APIs)
- Centralizar diagnósticos técnicos y auditorías

---

## 🧩 Qué incluye realmente el repositorio

### 1. Testing framework

- Tests en Python (`pytest`) y JavaScript
- Tests E2E (`test_e2e.py`)
- Tests de integración de componentes (ej. GitHub toggle, orquestación)
- Configuración unificada (`pytest.ini`, `tests/conftest.py`)
- Archivo `.coverage` para análisis de cobertura

Ejemplo:
- `test_github_integration_toggle.py` valida flags de integración
- `test_e2e.py` prueba flujos completos del sistema

### 2. CI/CD básico

- GitHub Actions configurado para entorno Python (Conda)
- Scripts de validación:
  - `ci_validation.sh`
  - `hardening_checklist.sh`

Objetivo:
- Garantizar reproducibilidad de entorno
- Validar cambios antes de integración

### 3. Infraestructura como código (base)

- Terraform (Hetzner):
  - `hetzner_infra/`
- Kubernetes manifests:
  - `k8s/`
  - `infrastructure/`

Esto permite:
- Simular despliegues reales
- Validar configuraciones antes de producción

### 4. Entornos Docker modulares

Múltiples configuraciones según caso de uso:

- `docker-compose.yml` (base)
- `docker-compose.iot.yml`
- `docker-compose.microservices.yml`
- `docker-compose.cloud.yml`
- `docker-compose.ha.yml`
- `docker-compose.whatsapp.yml`

Uso:
- Testing local de distintos escenarios
- Validación de arquitectura distribuida

### 5. Integración IoT y edge

- Código para ESP32 (`esp32_code/`)
- Configuración IoT (Thingsdata, MQTT, etc.)
- Variables de entorno específicas (`.env.thingsdata`)

### 6. Automatización y workflows

- Flujos n8n (`n8n/workflows/`)
- Scripts auxiliares (`scripts/`)
- Workers y servicios desacoplados (`workers/`, `services/`)

### 7. Observabilidad y operaciones

- Configuración de monitoring (`monitoring/`)
- Logs, artefactos y resultados (`artifacts/`)
- Auditorías (`audits/`)

### 8. Documentación técnica y diagnósticos

Gran parte del valor del repo está aquí:

- Diagnósticos estructurados:
  - `DIAGNOSTICO-SISTEMA.md`
  - `DIAGNOSTIC-*.json`
- Checklists:
  - `INTEGRATION-CHECKLIST.md`
- Guías operativas:
  - `INICIA-AQUI.md`
  - `EJECUTOR-PASOS.md`
- Informes de contingencia:
  - `CONTINGENCY_REPORT.md`

### 9. Backend y API (base)

- Estructura de API (`api/`, `backend/`)
- No es un backend completo productivo, sino base para testing e integración

---

## ⚙️ Uso básico

### Clonar repositorio

```bash
git clone https://github.com/Traky12/Cast-o.git
cd Cast-o
```

### Configurar entorno

```bash
cp .env.example .env
```

### Levantar entorno base

```bash
docker compose up -d
```

### Ejecutar tests

```bash
pytest tests/ -v
```

---

## 🧪 Casos de uso reales

Este repo es útil para:

- Validar cambios antes de integrarlos en CASTÚO-SYSTEM
- Probar configuraciones de infraestructura sin afectar producción
- Simular escenarios IoT y workflows automatizados
- Ejecutar auditorías técnicas y de seguridad
- Servir como base para nuevos entornos o despliegues

Ejemplo:
Un cambio en la API puede validarse aquí ejecutando tests + Docker antes de desplegar en el sistema principal.

---

## 🧱 Estructura del proyecto (simplificada)

- `api/` → endpoints y lógica base
- `backend/` → servicios backend
- `tests/` → tests automatizados
- `scripts/` → utilidades CLI
- `infrastructure/`, `k8s/` → despliegue
- `hetzner_infra/` → Terraform
- `monitoring/` → observabilidad
- `n8n/workflows/` → automatización
- `esp32_code/` → edge/IoT
- `docs/` → documentación técnica

---

## 🔐 Seguridad

- Archivo `SECURITY.md` con política de vulnerabilidades
- Scripts de hardening incluidos
- Soporte para análisis estático (ej. Semgrep, Trivy)

---

## 📌 Estado del proyecto

- Template funcional
- Estructura completa, pero parcialmente poblada
- Enfocado a evolución y adaptación
- No representa un sistema productivo desplegado

---

## ⚖️ Licencia

- Código: AGPL-3.0 (según repositorio)

---

## 🧭 Enfoque

Cast-o no busca ser un producto final, sino un **entorno de ingeniería** que permita:

- Reducir riesgo en despliegues
- Aumentar calidad del software
- Estandarizar procesos técnicos
- Acelerar iteración en proyectos complejos (IoT + IA + SaaS)
