# Checklist: de integración TRL-6 a sistema vivo industrial (TRL 7–9)

Este documento lista **etapas verificables** para pasar de la **puerta TRL-6 del repositorio** a un servicio **operativo para usuarios finales** en condiciones industriales. No sustituye due diligence legal, técnica ni de mercado.

### Estado actual honesto (línea base)

| Ámbito | Nivel declarado en código | Significado |
|--------|---------------------------|-------------|
| Integración | TRL-6-staging | Compose, TLS, pruebas `trl6`, workflows |
| SNN Hidroponía | TRL-4-lab-sim | Simulación de laboratorio |
| Operación | Not applicable | Requiere checklist |

### Fases para TRL 7–9 (Sistema Vivo)

#### A. Observabilidad Industrial

- [ ] Monitoreo de métricas clave (SLO, SLI)
- [ ] Alertas configuradas (PagerDuty/Slack)
- [ ] Logs centralizados (ELK/Grafana)

#### B. Backups y Recuperación

- [ ] Backups automáticos diarios
- [ ] Pruebas de restauración mensuales
- [ ] Documentación de recuperación

#### C. Piloto en Entorno Real

- [ ] Despliegue en entorno de producción
- [ ] Validación con datos reales
- [ ] Ajustes basados en feedback

#### D. Sustitución/Evidencia del Modelo

- [ ] Validación de modelo SNN con datos reales
- [ ] Documentación de evidencia de TRL
- [ ] Plan de mejora continua

#### E. Acuerdos de Nivel de Servicio

- [ ] Definición de SLA
- [ ] Métricas de rendimiento
- [ ] Planes de contingencia

---

### Anexos Técnicos

#### 1. Configuración Postgres

```bash
# Configuración recomendada para producción (alinear con .env.production)
# En .env use dos puntos entre usuario y contraseña sin barra invertida (no "castuo\:pass").
DATABASE_URL=postgresql+psycopg2://castuo:CAMBIA_openssl_rand_hex_16@postgres:5432/castuo
# Opcional si el backend lo expone en tu despliegue:
# CASTUO_DB_POOL_SIZE=20
```

#### 2. Gestión de Secretos

```bash
# Ejemplo de gestión de secretos con Vault (ajustar path y políticas)
vault kv put secret/castuo/db @db-secrets.json
```

#### 3. Configuración TLS

```bash
# Configuración TLS con Let's Encrypt (webroot; coherente con deploy/setup-ssl.sh)
certbot certonly --webroot -w /var/www/certbot -d castuo.tudominio.eu
```

#### 4. Verificación de Salud

```bash
# Verificación de salud del sistema
curl http://localhost:8000/health
```

#### 5. Runbook de Operaciones

```bash
# Comandos básicos de operación (v1: docker-compose; v2: docker compose — equivalente)
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
```

**Referencias operativas:** `deploy/setup-ssl.sh`, `docs/deploy/RUNBOOK-RESPUESTA-INCIDENTES.md` (incidentes), SLO sobre `hydroponics/infer` cuando definas observabilidad industrial.

## Comandos útiles

```bash
python -m pytest tests/models/test_system_admin_playbook.py tests/integrations/test_neuromorphic.py tests/system/test_trl6.py -q
docker compose -f docker-compose.prod.yml --env-file .env.production ps
curl -fsS https://TU_DOMINIO/health
```

## Referencias cruzadas

- Ética: `agrotech/ETHICS_TRACEABILITY.md`
- Prontuario agrotech + TLS: `docs/deploy/PRONTUARIO-AGROTECH-TLS.md`
- Infra TRL6→TRL7: `docs/deploy/PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md`
- Código TRL6→TRL7: `docs/deploy/ROADMAP-TRL6-TRL7-CODE.md`
