# Uso básico

## Ejemplos prácticos para empezar

A continuación se muestran ejemplos mínimos para cargar datos y consultar la API.

### Ejemplo 1: Cargar un dataset

```python
from api.mistral_castuo_adapter import MistralDataManager

manager = MistralDataManager(region="ES")
df = manager.load_dataset("data/cultivos.csv")
print(df.head())
```

Para JSON o Parquet, indicar el tipo o usar la extensión del archivo:

```python
df_json = manager.load_dataset("data/parcelas.json", file_type="json")
df_pq = manager.load_dataset("data/sensores.parquet", file_type="parquet")
```

### Ejemplo 2: Consultar Mistral API

```python
from api.mistral_castuo_adapter import MistralAPIClient, APIKeyManager

key_manager = APIKeyManager(region="ES")
api_key = key_manager.get_valid_key()

client = MistralAPIClient(api_key=api_key, region="ES")
response = client.query(
    model="mistral-small",
    prompt="Explica cómo optimizar el riego en cultivos de cannabis medicinal usando IA"
)
print(response["choices"][0]["message"]["content"])
```

### Ejemplo 3: Parámetros de la consulta

```python
response = client.query(
    model="mistral-small",
    prompt="Resume en 3 puntos las ventajas del agrovoltaico.",
    temperature=0.5,
    max_tokens=256,
)
```
