# n8n — utilidades de repo (CASTÚO)

## Documentación larga

`docs/deploy/PRONTUARIO-AUTOMATIZACION-N8N-2026.md`

## Workflows canónicos

Export JSON en `n8n/workflows/` (no duplicar en esta carpeta).

## CLI

```bash
pip install -r scripts/ai/n8n/requirements_n8n.txt
python scripts/ai/n8n/workflow_manager.py --list
python scripts/ai/n8n/workflow_manager.py --validate castuo_system_monitor
```

Webhook (requiere n8n accesible y path real del nodo Webhook):

```bash
set CASTUO_N8N_WEBHOOK_BASE=https://tu-n8n/webhook
python scripts/ai/n8n/workflow_manager.py --trigger mi_flujo --payload "{\"ok\":true}"
```
(Opcional: `--webhook-base` en lugar de la variable de entorno.)

Validación dura de políticas: `python scripts/harden_n8n_flow.py` (ver prontuario).

## Decisión lab (ramas IF / webhooks)

```bash
python scripts/ai/n8n/ai_decision.py --data "{\"humedad\":0.8,\"temperatura\":0.2}"
# TorchScript opcional: pip install -r scripts/ai/n8n/requirements_n8n_ai.txt
# set CASTUO_N8N_DECISION_MODEL=models/mi_modelo.pt
```

## PRONT A4

`docs/deploy/PRONT-CASTUO-N8N-v1-2026.md`
