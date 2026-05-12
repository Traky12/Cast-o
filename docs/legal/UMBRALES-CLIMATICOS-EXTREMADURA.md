# Umbrales climáticos Extremadura (YAML + código)

**Impacto territorial:** los umbrales orientan alertas solo con **datos medidos** reales; valores del YAML son parametrización interna revisable con asesor agro/normativo.

## Artefactos

| Pieza | Ruta |
|-------|------|
| Configuración | `config/extremadura_climate.yaml` |
| Lógica | `backend/ctaex/climate_config.py` |

## `crop_specific`

El bloque `crop_specific` fusiona umbrales por cultivo sobre los valores globales de `temperature`, `humidity`, `et0`. Cultivos definidos en YAML (revisar expediente): **`cannabis_medicinal`**, **`tomate_raf`**, **`vid`**, **`cereales`**. `ExtremaduraClimateConfig.check_violation(parameter, value, crop_type=...)` aplica esa fusión.

Parámetros con lógica de violación implementada en código: **`temperature`**, **`humidity`**, **`et0`**. Otros bloques del YAML (`solar_radiation`, `wind_speed`, `precipitation`) quedan para ampliación futura sin `check_violation` específico aún.

## Validación al cargar

Al instanciar `ExtremaduraClimateConfig`, se valida que los umbrales escalares y `optimal_range` sean **numéricos**; un YAML mal tipado lanza `ValueError` al construir (fallo rápido en despliegue).

**Relación:** [SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md](./SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md) · [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md)
