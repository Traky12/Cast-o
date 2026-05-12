# DOCUMENTACIÓN DE MODELO DE IA (AI Act UE 2024/1689)

- **Nombre del Modelo**: {{ model.nombre }}
- **Versión**: {{ model.version }}
- **Tipo**: {{ model.tipo }}
- **Entrenado con**: {{ model.datos_entrenamiento }}
- **Precisión**: {{ model.precision }}%
- **Riesgo (AI Act)**: {{ model.riesgo }}
- **TX BioCoin Castúo**: [{{ tx_hash }}](https://explorer.biocoin.castu-system.com/tx/{{ tx_hash }})
- **Git Commit**: [{{ git_commit }}](https://github.com/castu-system/{{ repo }}/commit/{{ git_commit }})

## Descripción

{{ model.descripcion }}

## Datos de Entrenamiento

- **Origen**: {{ model.datos_origen }}
- **Tamaño**: {{ model.datos_tamano }} registros
- **Preprocesamiento**: {{ model.datos_preprocesamiento }}

## Métricas de Rendimiento

| Métrica   | Valor            |
|-----------|------------------|
| Precisión | {{ model.precision }}% |
| Recall    | {{ model.recall }}%   |
| F1 Score  | {{ model.f1 }}%       |

## Cumplimiento Legal

- **GDPR**: {{ model.gdpr_compliant }}
- **AI Act**: {{ model.ai_act_compliant }}
- **Auditoría**: {{ model.auditoria }}
