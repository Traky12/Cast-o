# Producción agentes federados v2.1 — Guía actualizada

Extensión de la guía principal (`PRODUCCION_AGENTES_FEDERADOS.md`) con las mejoras v2.1.

---

## Novedades en v2.1

1. **Inyección de Dependencias**: Eliminación de acoplamiento estático entre agentes.
2. **Rotación Automática de Claves PQC**: Script `rotate_pqc_keys.py` con cron job mensual.
3. **Validación Robusta en Federated Learning**: Detección de outliers (Z-score) y verificación de hash.
4. **Manejo de Conflictos en Git Hooks**: Script `handle_merge_conflicts.py`.
5. **Alertas con Contexto Normativo**: Prometheus + Alertmanager + Grafana.
6. **Integración con OPA**: Validación de acciones en tiempo real.

---

## Requisitos actualizados

| Componente       | Versión mínima | Notas                                  |
|------------------|----------------|----------------------------------------|
| Python           | 3.11           | Requerido para `pqcrypto`             |
| Docker           | 20.10          | Para Swarm y redes overlay            |
| Vault            | 1.13           | Gestión de claves PQC                 |
| RabbitMQ         | 3.11           | Comunicación entre agentes            |
| Prometheus       | 2.40           | Métricas y alertas                    |
| Grafana          | 9.3            | Visualización                        |
| OpenPolicyAgent  | 0.45           | Validación de cumplimiento           |

---

## Pasos de implementación

### 1. Configurar inyección de dependencias

```bash
python -c "
from backend.core.dependency_injector import injector
from backend.agents.selfhealing_agent import SelfHealingAgent
injector.register('SelfHealingAgent', SelfHealingAgent())
"
```

### 2. Rotación de claves (cron)

```bash
0 0 1 * * /usr/bin/python3 /ruta/castuo-system/backend/scripts/rotate_pqc_keys.py >> /var/log/castuo/key_rotation.log 2>&1
```

### 3. Verificación final

| Componente                | Comando de verificación                    | Resultado esperado    |
|---------------------------|--------------------------------------------|------------------------|
| Inyección de dependencias | `pytest tests/test_dependency_injection.py -v` | Todos los tests pasan |
| Rotación de claves        | `python backend/scripts/rotate_pqc_keys.py --dry-run` | Simulación exitosa    |
| OPA                      | `curl http://opa:8181/v1/data/castuo/compliance`     | Política cargada      |

---

## Próximos pasos

- Escalar con Kubernetes y migrar desde Docker Swarm.
- Cifrado homomórfico para agregación segura en Federated Learning.
- Auditorías automáticas semanales con OPA.
- Dashboard de Grafana para alertas con filtro por normativa.
