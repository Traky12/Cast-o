# Ejemplos para Sabionda Educa

## Aprende con ejemplos reales

Código listo para copiar y adaptar en proyectos docentes o internos.

### Ejemplo 1: Análisis de datos agrícolas

Cargar datos de sensores (Parquet) y pedir a Mistral sugerencias de optimización:

```python
from api.mistral_castuo_adapter import MistralDataManager, MistralAPIClient, APIKeyManager

# Cargar datos de sensores
manager = MistralDataManager(region="ES")
df = manager.load_dataset("data/sensores_agrovoltaica.parquet", file_type="parquet")

# Consultar Mistral API para optimización
key_manager = APIKeyManager(region="ES")
api_key = key_manager.get_valid_key()
client = MistralAPIClient(api_key=api_key, region="ES")

prompt = f"""
Analiza estos datos de sensores y sugiere ajustes para maximizar el yield:

{df.describe().to_markdown() if hasattr(df.describe(), 'to_markdown') else df.describe().to_string()}
"""
response = client.query(model="mistral-small", prompt=prompt)
print(response["choices"][0]["message"]["content"])
```

### Ejemplo 2: Generación de informes de cumplimiento

Generar un informe en Markdown a partir del dataset y normativas:

```python
from api.mistral_castuo_adapter import MistralDataManager, MistralAPIClient, APIKeyManager

manager = MistralDataManager(region="EU")
df = manager.load_dataset("data/parcelas_ue.csv")

key_manager = APIKeyManager(region="EU")
client = MistralAPIClient(api_key=key_manager.get_valid_key(), region="EU")

report_prompt = f"""
Genera un informe de cumplimiento para la UE según este dataset:

Dataset (muestra):
{df.head().to_markdown() if hasattr(df.head(), 'to_markdown') else df.head().to_string()}

Normativas: GDPR, AI Act 2024.
Formato: Markdown con secciones claras (Introducción, Datos, Riesgos, Recomendaciones).
"""
report_response = client.query(model="mistral-small", prompt=report_prompt)
content = report_response["choices"][0]["message"]["content"]

with open("informe_cumplimiento.md", "w", encoding="utf-8") as f:
    f.write(content)
print("Informe guardado en informe_cumplimiento.md")
```

### Ejemplo 3: Ejecutar el ejemplo completo del módulo

El módulo incluye una función `ejemplo_completo()` que carga datos, obtiene la API key y realiza una consulta de ejemplo:

```bash
python api/mistral_castuo_adapter.py
```

```python
from api.mistral_castuo_adapter import ejemplo_completo
ejemplo_completo()
```

Si no existe `data/agritech_samples.csv`, se usa un DataFrame de ejemplo y se sugiere crear el archivo para pruebas reales.
