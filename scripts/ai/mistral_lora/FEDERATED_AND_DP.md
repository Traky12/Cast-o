# Federación, DP y LLM — límites honestos

## SIGPAC (`scripts/ai/sigpac/federated_trainer.py`)

- Flower **FedAvg** sobre un **vector 8D** derivado de estadísticas GeoTIFF (no píxeles completos).
- No sustituye a un pipeline FL sobre **Mistral 7B**: el coste de red, memoria y compatibilidad Opacus/DP por capa es otro orden de magnitud.

## FL + LoRA + Mistral

- En la práctica hace falta: **varios nodos con GPU**, estrategia de agregación sobre **pesos LoRA** (o similares), seguridad de transporte, y **análisis de privacidad** (ε, δ) acorde al mecanismo real — no basta con flags `--dp_epsilon`.
- **Opacus** está pensado para bucles de entrenamiento diferenciables clásicos; acoplarlo a un LM 7B 4-bit + PEFT + Flower requiere ingeniería específica y revisión legal.
- Este repositorio **no** incluye ese stack como “listo para producción” para no afirmar garantías falsas.

## Si avanzáis a piloto

- Documentar: base legal, DPIA, minimización, acuerdos entre responsables y encargados.
- Medir: tamaño de actualizaciones, fuga memorización, evaluación en hold-out por nodo.
